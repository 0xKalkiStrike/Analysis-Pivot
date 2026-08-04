"""Enterprise Master Data Management (MDM) Engine.

Consolidates identical and matching records across thousands of spreadsheets into
ONE Master Dataset containing unique records (M000001, M000002...).

Features:
1. Unique Master Dataset generation (M000001...)
2. Complete Duplicate References Audit Trail (Master ID, File, Sheet, Row, Folder Path, Date)
3. Source Count & Duplicate Count metrics per Master Record
4. Customizable Rule-Based Comparison Engine (Name+Address+City+State+Contact, Email Only, GST, Customer ID, Custom)
5. Interactive Conflict Detection & Resolution Workflow
6. Polars/Arrow performance with memory tracking and job control
"""
from __future__ import annotations

import datetime
import os
import psutil
import re
import time
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import polars as pl
from rapidfuzz import fuzz

from ..core.logger import get_logger
from ..models import Dataset
from .column_detector import ColumnDetector

log = get_logger(__name__)


@dataclass
class DuplicateReference:
    master_id: str
    source_file: str
    sheet_name: str
    row_number: int
    folder_path: str
    import_date: str
    raw_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "master_id": self.master_id,
            "source_file": self.source_file,
            "sheet_name": self.sheet_name,
            "row_number": self.row_number,
            "folder_path": self.folder_path,
            "import_date": self.import_date,
            "raw_data": self.raw_data,
        }


@dataclass
class MasterRecord:
    master_id: str
    name: str
    address: str
    city: str
    state: str
    contact_number: str
    email: str
    company: str
    gst_number: str
    customer_id: str
    source_count: int
    duplicate_count: int
    total_occurrences: int
    sources: list[str]
    created_date: str
    canonical_data: dict[str, Any] = field(default_factory=dict)
    references: list[DuplicateReference] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "master_id": self.master_id,
            "name": self.name,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "contact_number": self.contact_number,
            "email": self.email,
            "company": self.company,
            "gst_number": self.gst_number,
            "customer_id": self.customer_id,
            "source_count": self.source_count,
            "duplicate_count": self.duplicate_count,
            "total_occurrences": self.total_occurrences,
            "sources": self.sources,
            "created_date": self.created_date,
            "canonical_data": self.canonical_data,
            "references_count": len(self.references),
        }


@dataclass
class ConflictItem:
    conflict_id: str
    master_id: str
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
    status: str = "pending"  # "pending", "resolved_keep_first", "resolved_keep_second", "resolved_merged", "ignored"

    def to_dict(self) -> dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "master_id": self.master_id,
            "entity_name": self.entity_name,
            "field_name": self.field_name,
            "value_a": str(self.value_a) if self.value_a is not None else "—",
            "source_a": self.source_a,
            "sheet_a": self.sheet_a,
            "row_a": self.row_a,
            "value_b": str(self.value_b) if self.value_b is not None else "—",
            "source_b": self.source_b,
            "sheet_b": self.sheet_b,
            "row_b": self.row_b,
            "status": self.status,
        }


@dataclass
class MatchingRule:
    rule_id: str
    rule_name: str
    fields: list[str]
    description: str


PREDEFINED_MATCHING_RULES = [
    MatchingRule(
        rule_id="rule_1",
        rule_name="Full Profile Match (Name + Address + City + State + Contact)",
        fields=["Name", "Address", "City", "State", "Contact Number"],
        description="Matches records having identical Name, Address, City, State, and Contact Number.",
    ),
    MatchingRule(
        rule_id="rule_2",
        rule_name="Email Only Match",
        fields=["Email"],
        description="Matches records with identical normalized email address.",
    ),
    MatchingRule(
        rule_id="rule_3",
        rule_name="GST Number Match",
        fields=["GST Number"],
        description="Matches records with identical GSTIN / Tax Identification numbers.",
    ),
    MatchingRule(
        rule_id="rule_4",
        rule_name="Customer ID Match",
        fields=["Customer ID"],
        description="Matches records sharing the exact same Customer/Account ID.",
    ),
    MatchingRule(
        rule_id="rule_5",
        rule_name="Name & Contact Match",
        fields=["Name", "Contact Number"],
        description="Matches records sharing the same Name and Contact Phone Number.",
    ),
]


@dataclass
class MDMAnalysisResult:
    total_files: int = 0
    total_worksheets: int = 0
    total_records: int = 0
    total_columns: int = 0
    processing_size_bytes: int = 0
    estimated_processing_time_sec: float = 0.0

    master_records_count: int = 0
    duplicate_groups_count: int = 0
    duplicate_records_count: int = 0
    unique_records_count: int = 0
    conflicting_records_count: int = 0
    missing_records_count: int = 0

    processing_time_sec: float = 0.0
    memory_usage_mb: float = 0.0
    storage_used_bytes: int = 0

    matching_rule_used: str = "rule_1"
    matching_fields_used: list[str] = field(default_factory=list)

    master_records: list[MasterRecord] = field(default_factory=list)
    duplicate_references: list[DuplicateReference] = field(default_factory=list)
    unique_records: list[MasterRecord] = field(default_factory=list)
    conflicts: list[ConflictItem] = field(default_factory=list)
    missing_data: list[dict[str, Any]] = field(default_factory=list)
    processing_logs: list[str] = field(default_factory=list)

    def to_summary_dict(self) -> dict[str, Any]:
        return {
            "total_files": self.total_files,
            "total_worksheets": self.total_worksheets,
            "total_records": self.total_records,
            "total_columns": self.total_columns,
            "processing_size_bytes": self.processing_size_bytes,
            "processing_size_mb": round(self.processing_size_bytes / (1024 * 1024), 2),
            "estimated_processing_time_sec": round(self.estimated_processing_time_sec, 2),
            "master_records_count": self.master_records_count,
            "duplicate_groups_count": self.duplicate_groups_count,
            "duplicate_records_count": self.duplicate_records_count,
            "unique_records_count": self.unique_records_count,
            "conflicting_records_count": self.conflicting_records_count,
            "missing_records_count": self.missing_records_count,
            "processing_time_sec": round(self.processing_time_sec, 2),
            "memory_usage_mb": round(self.memory_usage_mb, 2),
            "storage_used_bytes": self.storage_used_bytes,
            "matching_rule_used": self.matching_rule_used,
            "matching_fields_used": self.matching_fields_used,
        }


class MasterConsolidationEngine:
    """Enterprise Master Data Consolidation & Analysis Platform Engine."""

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
    def _norm_phone(cls, val: Any) -> str:
        s = cls._clean_str(val)
        digits = re.sub(r"\D", "", s)
        if digits.startswith("91") and len(digits) == 12:
            digits = digits[2:]
        return digits

    @classmethod
    def _norm_email(cls, val: Any) -> str:
        s = cls._clean_str(val).lower()
        return s.strip()

    def process_mdm(
        self,
        datasets: list[Dataset],
        rule_id: str = "rule_1",
        custom_fields: list[str] | None = None,
        controller: Any | None = None,
        progress_callback: Callable[[float, str, str, dict[str, Any]], None] | None = None,
    ) -> MDMAnalysisResult:
        start_time = time.time()
        import_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logs: list[str] = [f"MDM Consolidation Job Started at {import_date}"]

        result = MDMAnalysisResult()
        rule = next((r for r in PREDEFINED_MATCHING_RULES if r.rule_id == rule_id), None)
        if custom_fields:
            matching_fields = custom_fields
            rule_name = "Custom Matching Fields"
        elif rule:
            matching_fields = rule.fields
            rule_name = rule.rule_name
        else:
            matching_fields = ["Name", "Contact Number"]
            rule_name = "Default Match (Name + Contact)"

        result.matching_rule_used = rule_name
        result.matching_fields_used = matching_fields

        # --------------------------------------------------------- Step 1: Scan & Metrics
        unique_files = {ds.source.file_path for ds in datasets if ds.source}
        result.total_files = len(unique_files) if unique_files else len(datasets)
        result.total_worksheets = len(datasets)

        total_cols_set: set[str] = set()
        total_bytes = 0

        for ds in datasets:
            total_cols_set.update(ds.columns)
            if ds.source and ds.source.file_path:
                try:
                    p = Path(ds.source.file_path)
                    if p.exists():
                        total_bytes += p.stat().st_size
                except Exception:
                    pass

        result.total_columns = len(total_cols_set)
        result.processing_size_bytes = total_bytes
        result.storage_used_bytes = total_bytes

        logs.append(f"Scanned {result.total_files} file(s), {result.total_worksheets} worksheet(s), size: {round(total_bytes / (1024*1024), 2)} MB.")

        if progress_callback:
            progress_callback(10.0, "Reading Excel Files...", f"Loaded {len(datasets)} worksheets", {})
        if controller and hasattr(controller, "check_state"):
            controller.check_state()

        # --------------------------------------------------------- Step 2: Read & Canonical Index (Multi-Threaded)
        indexed_rows: list[dict[str, Any]] = []
        missing_list: list[dict[str, Any]] = []
        total_rows_count = 0

        from concurrent.futures import ThreadPoolExecutor

        def _process_dataset(ds_tuple: tuple[int, Dataset]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int, str]:
            ds_idx, ds = ds_tuple
            src_file_path = ds.source.file_path if ds.source else ds.name
            file_name = Path(src_file_path).name
            folder_path = str(Path(src_file_path).parent).replace("\\", "/")
            sheet_name = ds.source.sheet_name if ds.source else "Sheet1"

            col_map = self.detector.map_columns(ds.columns)
            col_base_map = {
                orig_col: re.sub(r"\s+\(\d+\)$", "", col_map.get(orig_col, orig_col))
                for orig_col in ds.columns
            }
            rows = ds.df.to_dicts()
            local_indexed = []
            local_missing = []

            for r_idx, row in enumerate(rows, start=1):
                canonical_data: dict[str, Any] = {}
                for orig_col, val in row.items():
                    can_col_base = col_base_map.get(orig_col, orig_col)
                    canonical_data[can_col_base] = val

                    # Missing data tracking
                    if val is None or str(val).strip() == "":
                        local_missing.append({
                            "source_file": file_name,
                            "sheet_name": sheet_name,
                            "row_number": r_idx,
                            "folder_path": folder_path,
                            "missing_column": orig_col,
                            "details": f"Field '{orig_col}' is empty",
                        })

                local_indexed.append({
                    "source_file": file_name,
                    "sheet_name": sheet_name,
                    "row_number": r_idx,
                    "folder_path": folder_path,
                    "raw_data": row,
                    "canonical_data": canonical_data,
                })

            return local_indexed, local_missing, len(rows), file_name

        max_workers = min(32, (os.cpu_count() or 4) * 4)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            dataset_tuples = list(enumerate(datasets))
            futures = [executor.submit(_process_dataset, t) for t in dataset_tuples]
            for f in futures:
                local_idx, local_miss, r_cnt, f_name = f.result()
                indexed_rows.extend(local_idx)
                missing_list.extend(local_miss)
                total_rows_count += r_cnt

        result.total_records = total_rows_count
        result.missing_data = missing_list
        result.missing_records_count = len(missing_list)
        result.estimated_processing_time_sec = round(total_rows_count / 10000.0 + 0.1, 2)

        logs.append(f"Indexed {total_rows_count} total record(s) across {max_workers} worker threads. Found {len(missing_list)} missing field item(s).")

        # --------------------------------------------------------- Step 3: Consolidation & Grouping (Parallel Key Extraction)
        if progress_callback:
            progress_callback(45.0, "Consolidating Master Records...", "Matching records with active rule", {})
        if controller and hasattr(controller, "check_state"):
            controller.check_state()

        # Grouping by normalized composite key based on active matching fields
        group_buckets: dict[str, list[dict[str, Any]]] = {}

        def _compute_key(rec: dict[str, Any]) -> tuple[str, dict[str, Any]]:
            cd = rec["canonical_data"]
            key_parts = []
            for f in matching_fields:
                val = cd.get(f)
                if f in ("Phone Number", "Mobile", "Contact Number"):
                    norm_val = self._norm_phone(val)
                elif f == "Email":
                    norm_val = self._norm_email(val)
                else:
                    norm_val = self._norm_exact(val)

                if norm_val:
                    key_parts.append(f"{f}:{norm_val}")

            if key_parts:
                k = "||".join(sorted(key_parts))
            else:
                k = f"_raw_row_{rec['source_file']}_{rec['sheet_name']}_{rec['row_number']}"
            return k, rec

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            key_results = executor.map(_compute_key, indexed_rows)
            for k, rec in key_results:
                group_buckets.setdefault(k, []).append(rec)

        logs.append(f"Grouped records into {len(group_buckets)} distinct entity bucket(s).")

        # --------------------------------------------------------- Step 4: Build Master Records & References
        master_records: list[MasterRecord] = []
        all_references: list[DuplicateReference] = []
        unique_records: list[MasterRecord] = []
        conflicts: list[ConflictItem] = []

        master_counter = 1
        conflict_counter = 1
        dup_groups_count = 0
        total_dup_records_count = 0

        for k, group_recs in group_buckets.items():
            master_id = f"M{master_counter:06d}"
            master_counter += 1

            # Consolidate canonical fields: merge non-empty values from group
            consolidated_cd: dict[str, Any] = {}
            distinct_sources = sorted(list({r["source_file"] for r in group_recs}))
            source_cnt = len(distinct_sources)
            total_occ = len(group_recs)
            dup_cnt = max(0, total_occ - 1)

            if dup_cnt > 0:
                dup_groups_count += 1
                total_dup_records_count += dup_cnt

            # Aggregate best non-empty canonical values across group records
            all_can_keys: set[str] = set()
            for r in group_recs:
                all_can_keys.update(r["canonical_data"].keys())

            for col in all_can_keys:
                non_empty_vals = [r["canonical_data"].get(col) for r in group_recs if r["canonical_data"].get(col) is not None and str(r["canonical_data"].get(col)).strip() != ""]
                consolidated_cd[col] = non_empty_vals[0] if non_empty_vals else None

            # Detect field conflicts within duplicate group
            if len(group_recs) > 1:
                first_r = group_recs[0]
                for other_r in group_recs[1:]:
                    for f_check in ["Contact Number", "Phone Number", "Email", "Address", "City", "State"]:
                        val_a = first_r["canonical_data"].get(f_check)
                        val_b = other_r["canonical_data"].get(f_check)
                        norm_a = self._norm_exact(val_a)
                        norm_b = self._norm_exact(val_b)
                        if norm_a and norm_b and norm_a != norm_b:
                            conflicts.append(ConflictItem(
                                conflict_id=f"CONF-{conflict_counter:05d}",
                                master_id=master_id,
                                entity_name=str(consolidated_cd.get("Name") or consolidated_cd.get("Company") or master_id),
                                field_name=f_check,
                                value_a=val_a,
                                source_a=first_r["source_file"],
                                sheet_a=first_r["sheet_name"],
                                row_a=first_r["row_number"],
                                value_b=val_b,
                                source_b=other_r["source_file"],
                                sheet_b=other_r["sheet_name"],
                                row_b=other_r["row_number"],
                                status="pending",
                            ))
                            conflict_counter += 1

            # Build Duplicate References Audit Trail
            group_refs: list[DuplicateReference] = []
            for r in group_recs:
                ref = DuplicateReference(
                    master_id=master_id,
                    source_file=r["source_file"],
                    sheet_name=r["sheet_name"],
                    row_number=r["row_number"],
                    folder_path=r["folder_path"],
                    import_date=import_date,
                    raw_data=r["raw_data"],
                )
                group_refs.append(ref)
                all_references.append(ref)

            m_rec = MasterRecord(
                master_id=master_id,
                name=self._clean_str(consolidated_cd.get("Name") or consolidated_cd.get("Company")),
                address=self._clean_str(consolidated_cd.get("Address")),
                city=self._clean_str(consolidated_cd.get("City")),
                state=self._clean_str(consolidated_cd.get("State")),
                contact_number=self._clean_str(consolidated_cd.get("Contact Number") or consolidated_cd.get("Phone Number")),
                email=self._clean_str(consolidated_cd.get("Email")),
                company=self._clean_str(consolidated_cd.get("Company")),
                gst_number=self._clean_str(consolidated_cd.get("GST Number")),
                customer_id=self._clean_str(consolidated_cd.get("Customer ID")),
                source_count=source_cnt,
                duplicate_count=dup_cnt,
                total_occurrences=total_occ,
                sources=distinct_sources,
                created_date=import_date,
                canonical_data=consolidated_cd,
                references=group_refs,
            )

            master_records.append(m_rec)
            if dup_cnt == 0:
                unique_records.append(m_rec)

        result.master_records = master_records
        result.master_records_count = len(master_records)
        result.duplicate_references = all_references
        result.unique_records = unique_records
        result.unique_records_count = len(unique_records)
        result.duplicate_groups_count = dup_groups_count
        result.duplicate_records_count = total_dup_records_count
        result.conflicts = conflicts
        result.conflicting_records_count = len(conflicts)

        # Performance & Memory Metrics
        result.processing_time_sec = time.time() - start_time
        try:
            process = psutil.Process(os.getpid())
            result.memory_usage_mb = process.memory_info().rss / (1024 * 1024)
        except Exception:
            result.memory_usage_mb = 128.0

        logs.append(f"MDM Consolidation complete: {result.master_records_count} Master Record(s), {result.unique_records_count} Unique, {result.duplicate_records_count} Duplicate References, {result.conflicting_records_count} Conflicts.")
        result.processing_logs = logs

        if progress_callback:
            progress_callback(100.0, "Consolidation Completed", "Done", result.to_summary_dict())

        return result
