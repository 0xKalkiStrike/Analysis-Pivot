"""Cross-File Multi-Strategy Duplicate Detection and Data Quality Engine.

Compares records across ALL uploaded spreadsheets/worksheets, categorizing matches into:
1. Exact Match (100%)
2. High Confidence Match (95–99%)
3. Similar Match (80–95%)
4. Possible Match

Also discovers Conflicting Records and Missing Data metrics.
Supports real-time progress callbacks and job cancellation/pause.
"""
from __future__ import annotations

import re
import time
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import polars as pl
from rapidfuzz import fuzz, process

from ..core.logger import get_logger
from ..models import Dataset
from .column_detector import ColumnDetector

log = get_logger(__name__)


@dataclass
class DuplicateRecordItem:
    source_file: str
    sheet_name: str
    row_number: int
    raw_data: dict[str, Any]
    canonical_data: dict[str, Any]


@dataclass
class MatchGroup:
    group_id: int
    match_level: str  # "Exact Match (100%)" | "High Confidence Match (95-99%)" | "Similar Match (80-95%)" | "Possible Match"
    confidence_score: float
    matching_fields: list[str]
    reason: str
    records: list[DuplicateRecordItem] = field(default_factory=list)


@dataclass
class ConflictRecord:
    entity_name: str
    field_name: str
    value_a: Any
    source_a: str
    sheet_a: str
    row_a: int
    value_b: Any
    source_b: str
    sheet_b: str
    row_b: int


@dataclass
class MissingDataItem:
    source_file: str
    sheet_name: str
    row_number: int
    missing_column: str
    details: str


@dataclass
class CrossFileAnalysisResult:
    total_files: int = 0
    total_worksheets: int = 0
    total_records: int = 0
    exact_duplicates_count: int = 0
    similar_records_count: int = 0
    possible_matches_count: int = 0
    unique_records_count: int = 0
    conflicting_records_count: int = 0
    missing_records_count: int = 0
    processing_time_sec: float = 0.0

    exact_duplicates: list[MatchGroup] = field(default_factory=list)
    similar_records: list[MatchGroup] = field(default_factory=list)
    possible_matches: list[MatchGroup] = field(default_factory=list)
    conflicting_records: list[ConflictRecord] = field(default_factory=list)
    missing_data: list[MissingDataItem] = field(default_factory=list)

    def to_summary_dict(self) -> dict[str, Any]:
        return {
            "total_files": self.total_files,
            "total_worksheets": self.total_worksheets,
            "total_records": self.total_records,
            "exact_duplicates": self.exact_duplicates_count,
            "similar_records": self.similar_records_count,
            "possible_matches": self.possible_matches_count,
            "unique_records": self.unique_records_count,
            "conflicting_records": self.conflicting_records_count,
            "missing_records": self.missing_records_count,
            "processing_time_sec": round(self.processing_time_sec, 2),
        }


class JobController:
    """Controls job execution state (pause, resume, cancel)."""

    def __init__(self) -> None:
        self.is_paused = False
        self.is_cancelled = False

    def pause(self) -> None:
        self.is_paused = True

    def resume(self) -> None:
        self.is_paused = False

    def cancel(self) -> None:
        self.is_cancelled = True

    def check_state(self) -> None:
        while self.is_paused and not self.is_cancelled:
            time.sleep(0.2)
        if self.is_cancelled:
            raise InterruptedException("Job was cancelled by user.")


class InterruptedException(Exception):
    pass


class CrossFileAnalyzer:
    """High-performance cross-file record analyzer and duplicate detector."""

    def __init__(self, column_detector: ColumnDetector | None = None) -> None:
        self.detector = column_detector or ColumnDetector()

    @staticmethod
    def _clean_str(val: Any) -> str:
        if val is None:
            return ""
        s = str(val)
        s = unicodedata.normalize("NFKC", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    @classmethod
    def _norm_exact(cls, val: Any) -> str:
        return cls._clean_str(val).lower()

    @classmethod
    def _norm_high_confidence(cls, val: Any) -> str:
        """Strip punctuation, special chars, and case for 95-99% matching."""
        s = cls._norm_exact(val)
        s = re.sub(r"[^\w\s]", "", s)
        return s.strip()

    def analyze(
        self,
        datasets: list[Dataset],
        threshold: float = 80.0,
        controller: JobController | None = None,
        progress_callback: Callable[[float, str, str, dict[str, Any]], None] | None = None,
    ) -> CrossFileAnalysisResult:
        start_time = time.time()
        controller = controller or JobController()
        result = CrossFileAnalysisResult()

        unique_files = {ds.source.file_path for ds in datasets if ds.source}
        result.total_files = len(unique_files) if unique_files else len(datasets)
        result.total_worksheets = len(datasets)

        # --------------------------------------------------------- Step 1: Scanning Files
        if progress_callback:
            progress_callback(10.0, "Scanning Files...", f"Loaded {len(datasets)} worksheets", {})
        controller.check_state()

        # Build normalized unified record index
        all_records: list[DuplicateRecordItem] = []
        missing_items: list[MissingDataItem] = []

        for ds_idx, ds in enumerate(datasets):
            controller.check_state()
            src_file = ds.source.file_path if ds.source else ds.name
            file_name = Path(src_file).name
            sheet_name = ds.source.sheet_name if ds.source else "Sheet1"

            if progress_callback:
                progress = 10.0 + (ds_idx / max(1, len(datasets))) * 25.0
                progress_callback(
                    progress,
                    "Analyzing Records...",
                    file_name,
                    {"rows": len(all_records), "sheets_processed": ds_idx + 1},
                )

            col_map = self.detector.map_columns(ds.columns)
            col_base_map = {
                orig_col: re.sub(r"\s+\(\d+\)$", "", col_map.get(orig_col, orig_col))
                for orig_col in ds.columns
            }
            rows = ds.df.to_dicts()

            for r_idx, row in enumerate(rows, start=1):
                canonical_data: dict[str, Any] = {}
                for orig_col, val in row.items():
                    can_col_base = col_base_map.get(orig_col, orig_col)
                    canonical_data[can_col_base] = val

                    # Track missing data
                    if val is None or str(val).strip() == "":
                        missing_items.append(
                            MissingDataItem(
                                source_file=file_name,
                                sheet_name=sheet_name,
                                row_number=r_idx,
                                missing_column=orig_col,
                                details=f"Field '{orig_col}' is empty",
                            )
                        )

                rec = DuplicateRecordItem(
                    source_file=file_name,
                    sheet_name=sheet_name,
                    row_number=r_idx,
                    raw_data=row,
                    canonical_data=canonical_data,
                )
                all_records.append(rec)

        result.total_records = len(all_records)
        result.missing_data = missing_items
        result.missing_records_count = len(missing_items)

        # --------------------------------------------------------- Step 2: Finding Duplicates
        if progress_callback:
            progress_callback(40.0, "Finding Duplicates...", "Indexing & comparing cross-file records", {})
        controller.check_state()

        # Target evaluate fields
        eval_fields = ["Name", "Company", "Email", "Phone Number", "Address", "Customer ID", "GST Number"]

        # Grouping buckets for speed
        exact_buckets: dict[str, list[DuplicateRecordItem]] = {}
        high_conf_buckets: dict[str, list[DuplicateRecordItem]] = {}
        processed_indices: set[int] = set()

        # Step 2a: Exact Matches (100%)
        for idx, rec in enumerate(all_records):
            # Create exact composite key from non-empty evaluated canonical fields
            key_parts = []
            for f in eval_fields:
                v = rec.canonical_data.get(f)
                if v is not None and str(v).strip() != "":
                    key_parts.append(f"{f}:{self._norm_exact(v)}")
            if key_parts:
                k = "||".join(sorted(key_parts))
                exact_buckets.setdefault(k, []).append(rec)

        exact_groups: list[MatchGroup] = []
        group_counter = 1

        for k, recs in exact_buckets.items():
            if len(recs) > 1:
                matched_fields = list({kp.split(":")[0] for kp in k.split("||")})
                exact_groups.append(
                    MatchGroup(
                        group_id=group_counter,
                        match_level="Exact Match (100%)",
                        confidence_score=100.0,
                        matching_fields=matched_fields,
                        reason=f"Identical values across {len(matched_fields)} canonical field(s): {', '.join(matched_fields)}",
                        records=recs,
                    )
                )
                group_counter += 1

        result.exact_duplicates = exact_groups
        result.exact_duplicates_count = sum(len(g.records) for g in exact_groups)

        # Step 2b: High Confidence (95-99%) & Similar (80-95%) Matches
        if progress_callback:
            progress_callback(70.0, "Finding Duplicates...", "Performing fuzzy & format similarity search", {})
        controller.check_state()

        # Filter out records already in exact duplicate groups to avoid duplicate reporting
        exact_matched_recs = {id(r) for g in exact_groups for r in g.records}
        remaining_recs = [r for r in all_records if id(r) not in exact_matched_recs]

        # Pre-normalize remaining records to avoid repeating regex & unicode operations inside comparison loops
        class PreRecord:
            __slots__ = ("rec", "name", "email", "phone", "addr", "n_clean", "n_exact")
            def __init__(self, rec, clean_f, norm_exact_f, norm_hc_f):
                self.rec = rec
                self.name = clean_f(rec.canonical_data.get("Name") or rec.canonical_data.get("Company"))
                self.email = norm_exact_f(rec.canonical_data.get("Email"))
                self.phone = norm_hc_f(rec.canonical_data.get("Phone Number"))
                self.addr = norm_hc_f(rec.canonical_data.get("Address"))
                self.n_clean = norm_hc_f(self.name) if self.name else ""
                self.n_exact = norm_exact_f(self.name) if self.name else ""

        pre_recs = [
            PreRecord(r, self._clean_str, self._norm_exact, self._norm_high_confidence)
            for r in remaining_recs
        ]

        similar_groups: list[MatchGroup] = []
        possible_groups: list[MatchGroup] = []
        conflicts: list[ConflictRecord] = []

        for i in range(len(pre_recs)):
            if i % 200 == 0:
                controller.check_state()
                if progress_callback:
                    pct = 70.0 + (i / max(1, len(pre_recs))) * 20.0
                    progress_callback(
                        pct,
                        "Finding Duplicates...",
                        f"Comparing record {i+1} of {len(pre_recs)}",
                        {"exact_groups": len(exact_groups), "similar_groups": len(similar_groups)},
                    )

            p1 = pre_recs[i]
            r1 = p1.rec
            if not (p1.name or p1.email or p1.phone):
                continue

            for j in range(i + 1, min(i + 200, len(pre_recs))):  # Window comparison for speed
                p2 = pre_recs[j]
                r2 = p2.rec

                # 1. High Confidence Match (95-99%)
                if p1.name and p2.name:
                    if p1.n_clean and p1.n_clean == p2.n_clean and p1.name != p2.name:
                        similar_groups.append(
                            MatchGroup(
                                group_id=group_counter,
                                match_level="High Confidence Match (95-99%)",
                                confidence_score=97.0,
                                matching_fields=["Name/Company"],
                                reason=f"Case/formatting difference only ('{p1.name}' vs '{p2.name}')",
                                records=[r1, r2],
                            )
                        )
                        group_counter += 1
                        continue

                # 2. Similar Match (80-95%)
                if p1.name and p2.name and p1.n_exact and p2.n_exact:
                    # Length-based pruning before running fuzz.ratio
                    if abs(len(p1.n_exact) - len(p2.n_exact)) <= 10:
                        sim = fuzz.ratio(p1.n_exact, p2.n_exact)
                        if 80.0 <= sim < 95.0:
                            similar_groups.append(
                                MatchGroup(
                                    group_id=group_counter,
                                    match_level="Similar Match (80-95%)",
                                    confidence_score=round(float(sim), 1),
                                    matching_fields=["Name/Company"],
                                    reason=f"Minor spelling difference ({sim:.0f}% similarity: '{p1.name}' vs '{p2.name}')",
                                    records=[r1, r2],
                                )
                            )
                            group_counter += 1
                            continue

                # 3. Possible Match & Conflicting Records
                # Match on Name/Address but difference in Phone/Email
                if p1.name and p2.name and p1.n_exact == p2.n_exact:
                    # Check for conflicts
                    if p1.email and p2.email and p1.email != p2.email:
                        conflicts.append(
                            ConflictRecord(
                                entity_name=p1.name,
                                field_name="Email",
                                value_a=r1.canonical_data.get("Email"),
                                source_a=r1.source_file,
                                sheet_a=r1.sheet_name,
                                row_a=r1.row_number,
                                value_b=r2.canonical_data.get("Email"),
                                source_b=r2.source_file,
                                sheet_b=r2.sheet_name,
                                row_b=r2.row_number,
                            )
                        )
                    if p1.phone and p2.phone and p1.phone != p2.phone:
                        conflicts.append(
                            ConflictRecord(
                                entity_name=p1.name,
                                field_name="Phone Number",
                                value_a=r1.canonical_data.get("Phone Number"),
                                source_a=r1.source_file,
                                sheet_a=r1.sheet_name,
                                row_a=r1.row_number,
                                value_b=r2.canonical_data.get("Phone Number"),
                                source_b=r2.source_file,
                                sheet_b=r2.sheet_name,
                                row_b=r2.row_number,
                            )
                        )

                    # Possible match entry
                    possible_groups.append(
                        MatchGroup(
                            group_id=group_counter,
                            match_level="Possible Match",
                            confidence_score=75.0,
                            matching_fields=["Name"],
                            reason=f"Same Name ('{p1.name}'), but differing details across files",
                            records=[r1, r2],
                        )
                    )
                    group_counter += 1

        result.similar_records = similar_groups
        result.similar_records_count = sum(len(g.records) for g in similar_groups)
        result.possible_matches = possible_groups
        result.possible_matches_count = len(possible_groups)
        result.conflicting_records = conflicts
        result.conflicting_records_count = len(conflicts)

        # Unique records
        all_flagged_recs = exact_matched_recs | {
            id(r) for g in similar_groups for r in g.records
        } | {id(r) for g in possible_groups for r in g.records}

        result.unique_records_count = max(0, len(all_records) - len(all_flagged_recs))

        # --------------------------------------------------------- Step 3: Completed
        result.processing_time_sec = time.time() - start_time
        if progress_callback:
            progress_callback(100.0, "Generating Reports...", "Done", result.to_summary_dict())

        return result
