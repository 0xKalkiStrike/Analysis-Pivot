"""Relationship discovery — infer foreign-key candidates across datasets."""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from typing import Iterable

import polars as pl

from ..core.logger import get_logger
from ..models import Dataset

log = get_logger(__name__)


@dataclass
class Relationship:
    """A discovered link between two dataset columns."""
    left_dataset: str
    left_column: str
    right_dataset: str
    right_column: str
    overlap: float           # fraction of left values present in right
    reverse_overlap: float   # fraction of right values present in left
    shared_values: int
    cardinality: str         # "1:1" | "1:N" | "N:1" | "N:N"
    confidence: float        # 0-100
    reason: str = ""

    @property
    def label(self) -> str:
        return f"{self.left_dataset}.{self.left_column} → {self.right_dataset}.{self.right_column}"


class RelationshipEngine:
    """Detect FK-like relationships between datasets."""

    def __init__(self, min_overlap: float = 0.6, min_shared: int = 5) -> None:
        self.min_overlap = min_overlap
        self.min_shared = min_shared

    # ------------------------------------------------------------------ discovery
    def discover(self, datasets: dict[str, Dataset]) -> list[Relationship]:
        """Discover FK candidates across every pair of datasets."""
        rels: list[Relationship] = []
        names = list(datasets.keys())
        # Precompute unique value sets per candidate column
        cache: dict[tuple[str, str], set] = {}

        def get_values(ds_name: str, col: str) -> set:
            key = (ds_name, col)
            if key not in cache:
                ds = datasets[ds_name]
                s = ds.df[col].drop_nulls().cast(pl.Utf8)
                # Skip columns that look like free text (too high uniqueness + long strings)
                cache[key] = set(s.to_list())
            return cache[key]

        for a, b in combinations(names, 2):
            da, db = datasets[a], datasets[b]
            for ca in self._candidate_columns(da):
                for cb in self._candidate_columns(db):
                    if not self._names_compatible(ca, cb):
                        continue
                    va = get_values(a, ca)
                    vb = get_values(b, cb)
                    if not va or not vb:
                        continue
                    shared = va & vb
                    if len(shared) < self.min_shared:
                        continue
                    ov_ab = len(shared) / len(va)
                    ov_ba = len(shared) / len(vb)
                    if max(ov_ab, ov_ba) < self.min_overlap:
                        continue
                    cardinality = self._cardinality(ov_ab, ov_ba)
                    conf = 100.0 * (ov_ab + ov_ba) / 2
                    reason = self._reason(ca, cb, ov_ab, ov_ba)
                    rels.append(Relationship(
                        left_dataset=a, left_column=ca,
                        right_dataset=b, right_column=cb,
                        overlap=round(ov_ab, 4), reverse_overlap=round(ov_ba, 4),
                        shared_values=len(shared),
                        cardinality=cardinality,
                        confidence=round(conf, 2),
                        reason=reason,
                    ))
        rels.sort(key=lambda r: r.confidence, reverse=True)
        log.info(f"Discovered {len(rels)} relationships across {len(datasets)} datasets")
        return rels

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _candidate_columns(ds: Dataset) -> Iterable[str]:
        cols = []
        for c in ds.columns:
            dt = ds.df.schema[c]
            # Skip pure floats — rarely FKs
            if dt in (pl.Float32, pl.Float64):
                continue
            # Skip very high-uniqueness free-text columns
            unique_ratio = (ds.df[c].n_unique() / max(1, ds.rows))
            avg_len_col = ds.df[c].cast(pl.Utf8).str.len_chars().mean() or 0
            if dt == pl.Utf8 and unique_ratio > 0.95 and avg_len_col > 40:
                continue
            cols.append(c)
        return cols

    @staticmethod
    def _names_compatible(a: str, b: str) -> bool:
        """Loose name compatibility — same name, or 'X_id' vs 'X' patterns."""
        a_l, b_l = a.lower(), b.lower()
        if a_l == b_l:
            return True
        for suffix in ("_id", "id", "_no", "_code", "_key"):
            if a_l.endswith(suffix) and a_l[: -len(suffix)] == b_l:
                return True
            if b_l.endswith(suffix) and b_l[: -len(suffix)] == a_l:
                return True
        # Substring hit (e.g. customer_id vs customerid)
        stripped_a = a_l.replace("_", "").replace("-", "")
        stripped_b = b_l.replace("_", "").replace("-", "")
        return stripped_a == stripped_b

    @staticmethod
    def _cardinality(ov_ab: float, ov_ba: float) -> str:
        # ov_ab ~ 1: left fully contained in right; ov_ba ~ 1: right fully in left
        left_all_in = ov_ab > 0.98
        right_all_in = ov_ba > 0.98
        if left_all_in and right_all_in:
            return "1:1"
        if right_all_in:
            return "N:1"
        if left_all_in:
            return "1:N"
        return "N:N"

    @staticmethod
    def _reason(a: str, b: str, ov_ab: float, ov_ba: float) -> str:
        if a.lower() == b.lower():
            return f"Same column name; {ov_ab:.0%} / {ov_ba:.0%} value overlap"
        return f"Compatible names ({a} ~ {b}); overlaps {ov_ab:.0%} / {ov_ba:.0%}"

    @staticmethod
    def to_dataframe(rels: list[Relationship]) -> pl.DataFrame:
        if not rels:
            return pl.DataFrame(schema={
                "left": pl.Utf8, "right": pl.Utf8, "cardinality": pl.Utf8,
                "confidence": pl.Float64, "shared": pl.Int64, "reason": pl.Utf8,
            })
        return pl.DataFrame([{
            "left": f"{r.left_dataset}.{r.left_column}",
            "right": f"{r.right_dataset}.{r.right_column}",
            "cardinality": r.cardinality,
            "confidence": r.confidence,
            "shared": r.shared_values,
            "reason": r.reason,
        } for r in rels])
