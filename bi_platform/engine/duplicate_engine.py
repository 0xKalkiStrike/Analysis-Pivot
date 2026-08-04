"""Multi-strategy duplicate detection.

Combines exact, normalised, hash-based and fuzzy techniques into one
engine that returns explainable DuplicateGroup objects.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Iterable

import polars as pl
from rapidfuzz import process

from ..core.constants import COLUMN_HINTS
from ..core.logger import get_logger
from ..models import Dataset, DuplicateGroup
from .fuzzy_engine import FuzzyEngine

log = get_logger(__name__)

_WS = re.compile(r"\s+")


class DuplicateEngine:
    """Detect duplicates and near-duplicates with confidence + reason."""

    def __init__(self, fuzzy: FuzzyEngine | None = None) -> None:
        self.fuzzy = fuzzy or FuzzyEngine()

    # ---------------------------------------------------------------- normalise
    @staticmethod
    def _norm(val: object) -> str:
        if val is None:
            return ""
        s = str(val)
        s = unicodedata.normalize("NFKC", s)
        s = _WS.sub(" ", s).strip().lower()
        return s

    @classmethod
    def _row_key(cls, row: dict, cols: Iterable[str]) -> str:
        return "|".join(cls._norm(row.get(c)) for c in cols)

    @classmethod
    def _row_hash(cls, row: dict, cols: Iterable[str]) -> str:
        return hashlib.sha1(cls._row_key(row, cols).encode()).hexdigest()

    # ---------------------------------------------------------------- detection
    def detect_exact(self, dataset: Dataset, subset: list[str] | None = None) -> list[DuplicateGroup]:
        df = dataset.df
        cols = subset or df.columns
        rows = df.to_dicts()
        buckets: dict[str, list[dict]] = {}
        for i, r in enumerate(rows):
            r = {**r, "_row_index": i}
            key = self._row_hash(r, cols)
            buckets.setdefault(key, []).append(r)
        return [
            DuplicateGroup(
                key=k, rows=v, confidence=100.0,
                method="hash", reason=f"Identical values across {len(cols)} columns",
            )
            for k, v in buckets.items() if len(v) > 1
        ]

    def detect_by_column(self, dataset: Dataset, column: str) -> list[DuplicateGroup]:
        df = dataset.df
        if column not in df.columns:
            return []
        rows = df.to_dicts()
        buckets: dict[str, list[dict]] = {}
        for i, r in enumerate(rows):
            r = {**r, "_row_index": i}
            key = self._norm(r.get(column))
            if not key:
                continue
            buckets.setdefault(key, []).append(r)
        return [
            DuplicateGroup(
                key=k, rows=v, confidence=100.0,
                method="column_exact", reason=f"Same '{column}' value",
            )
            for k, v in buckets.items() if len(v) > 1
        ]

    def detect_fuzzy(
        self,
        dataset: Dataset,
        column: str,
        threshold: float = 88.0,
        limit: int | None = None,
    ) -> list[DuplicateGroup]:
        df = dataset.df
        if column not in df.columns:
            return []

        rows = df.to_dicts()
        # Group row indices by normalized string key first
        key_to_indices: dict[str, list[int]] = {}
        for i, r in enumerate(rows):
            v = r.get(column)
            if v is not None:
                norm_v = self._norm(v)
                if norm_v:
                    key_to_indices.setdefault(norm_v, []).append(i)

        if not key_to_indices:
            return []

        unique_keys = list(key_to_indices.keys())
        seen_keys: set[str] = set()
        groups: list[DuplicateGroup] = []

        for key in unique_keys:
            if key in seen_keys:
                continue

            matches = process.extract(
                key, unique_keys, scorer=self.fuzzy.scorer,
                limit=limit or len(unique_keys), score_cutoff=threshold,
            )

            group_rows = []
            matched_key_count = 0
            for match_val, score, match_pos in matches:
                m_key = unique_keys[match_pos]
                if m_key in seen_keys and m_key != key:
                    continue
                seen_keys.add(m_key)
                matched_key_count += 1
                for real_idx in key_to_indices[m_key]:
                    r = dict(rows[real_idx])
                    r["_row_index"] = real_idx
                    r["_similarity"] = float(score)
                    group_rows.append(r)

            if len(group_rows) > 1:
                avg = sum(r["_similarity"] for r in group_rows) / len(group_rows)
                groups.append(DuplicateGroup(
                    key=key, rows=group_rows, confidence=avg,
                    method=f"fuzzy:{self.fuzzy.algorithm}",
                    reason=f"'{column}' similarity ≥ {threshold:.0f}%",
                ))
        return groups

    def detect_smart(
        self,
        dataset: Dataset,
        threshold: float = 88.0,
    ) -> list[DuplicateGroup]:
        """Combined smart detection using semantic columns."""
        semantic = self._detect_semantic_columns(dataset.df.columns)
        results: list[DuplicateGroup] = []

        priority = ("email", "phone", "id", "invoice", "gst", "product", "name")
        for kind in priority:
            for col in semantic.get(kind, []):
                if kind in ("email", "phone", "id", "invoice", "gst"):
                    results.extend(self.detect_by_column(dataset, col))
                else:
                    results.extend(self.detect_fuzzy(dataset, col, threshold))

        # Fallback: exact row hash
        results.extend(self.detect_exact(dataset))
        return self._dedupe_groups(results)

    @staticmethod
    def _detect_semantic_columns(cols: list[str]) -> dict[str, list[str]]:
        found: dict[str, list[str]] = {}
        lower = {c: c.lower().replace(" ", "_") for c in cols}
        for kind, hints in COLUMN_HINTS.items():
            for c, cl in lower.items():
                if any(h in cl for h in hints):
                    found.setdefault(kind, []).append(c)
        return found

    @staticmethod
    def _dedupe_groups(groups: list[DuplicateGroup]) -> list[DuplicateGroup]:
        """Merge overlapping groups by row_index sets."""
        merged: list[DuplicateGroup] = []
        seen_sets: list[set[int]] = []
        for g in groups:
            idxs = {r["_row_index"] for r in g.rows}
            overlap = None
            for i, s in enumerate(seen_sets):
                if idxs & s:
                    overlap = i
                    break
            if overlap is None:
                seen_sets.append(idxs)
                merged.append(g)
            else:
                seen_sets[overlap] |= idxs
        return merged

    # ---------------------------------------------------------------- reporting
    @staticmethod
    def to_dataframe(groups: list[DuplicateGroup]) -> pl.DataFrame:
        records: list[dict] = []
        for gi, g in enumerate(groups):
            for r in g.rows:
                r2 = {k: v for k, v in r.items() if not k.startswith("_")}
                r2.update({
                    "_group_id": gi,
                    "_group_size": g.size,
                    "_confidence": round(g.confidence, 2),
                    "_method": g.method,
                    "_reason": g.reason,
                    "_row_index": r.get("_row_index"),
                })
                records.append(r2)
        if not records:
            return pl.DataFrame()
        return pl.DataFrame(records)
