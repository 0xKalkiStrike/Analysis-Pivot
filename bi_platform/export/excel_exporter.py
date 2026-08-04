"""Excel exporter using XlsxWriter — formatted, filtered, coloured."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import polars as pl
import xlsxwriter

from ..core.logger import get_logger
from ..models import Dataset, DuplicateGroup, ValidationIssue

log = get_logger(__name__)


class ExcelExporter:
    """Produce styled Excel workbooks."""

    def export_dataset(self, dataset: Dataset, path: str | Path) -> str:
        return self.export_multi([(dataset.name[:31] or "Sheet1", dataset.df)], path)

    def export_multi(self, sheets: Iterable[tuple[str, pl.DataFrame]], path: str | Path) -> str:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        wb = xlsxwriter.Workbook(str(path), {"nan_inf_to_errors": True})
        header_fmt = wb.add_format({
            "bold": True, "bg_color": "#5B4BE0", "font_color": "white",
            "border": 1, "align": "center", "valign": "vcenter",
        })
        alt_fmt = wb.add_format({"bg_color": "#F5F3FF"})

        for name, df in sheets:
            safe = self._safe_sheet(name)
            ws = wb.add_worksheet(safe)
            cols = df.columns
            for j, c in enumerate(cols):
                ws.write(0, j, c, header_fmt)
            rows = df.to_dicts()
            for i, row in enumerate(rows, start=1):
                fmt = alt_fmt if i % 2 == 0 else None
                for j, c in enumerate(cols):
                    v = row.get(c)
                    if fmt:
                        ws.write(i, j, "" if v is None else v, fmt)
                    else:
                        ws.write(i, j, "" if v is None else v)
            # Auto width (bounded)
            for j, c in enumerate(cols):
                width = min(40, max(len(str(c)) + 2, 12))
                ws.set_column(j, j, width)
            ws.autofilter(0, 0, max(1, len(rows)), max(0, len(cols) - 1))
            ws.freeze_panes(1, 0)
        wb.close()
        log.info(f"Excel export written: {path}")
        return str(path)

<<<<<<< HEAD
=======
    def generate_duplicate_report(self, analysis_result: Any, path: str | Path = "Duplicate_Report.xlsx") -> str:
        """Generate comprehensive Duplicate_Report.xlsx containing 5 styled sheets:

        1. Exact Duplicates
        2. Similar Records
        3. Conflicting Records
        4. Missing Data
        5. Summary
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        wb = xlsxwriter.Workbook(str(path), {"nan_inf_to_errors": True})

        # Formats
        header_fmt = wb.add_format({
            "bold": True, "bg_color": "#1E293B", "font_color": "#F8FAFC",
            "border": 1, "align": "center", "valign": "vcenter", "font_size": 11,
        })
        title_fmt = wb.add_format({
            "bold": True, "font_size": 14, "font_color": "#0F172A",
        })
        metric_label_fmt = wb.add_format({
            "bold": True, "bg_color": "#F1F5F9", "border": 1, "font_size": 10,
        })
        metric_val_fmt = wb.add_format({
            "align": "right", "border": 1, "font_size": 10, "bold": True, "font_color": "#2563EB",
        })
        alt_fmt = wb.add_format({"bg_color": "#F8FAFC"})

        # ------------------------------------------------------------- 1. Exact Duplicates
        ws_exact = wb.add_worksheet("Exact Duplicates")
        headers_exact = ["Name", "Address", "Email", "Phone", "Source File", "Sheet", "Row", "Match Type", "Confidence Score"]
        for j, h in enumerate(headers_exact):
            ws_exact.write(0, j, h, header_fmt)

        row_idx = 1
        for group in getattr(analysis_result, "exact_duplicates", []):
            for rec in group.records:
                fmt = alt_fmt if row_idx % 2 == 0 else None
                cd = rec.canonical_data
                row_vals = [
                    cd.get("Name") or cd.get("Company") or "",
                    cd.get("Address") or "",
                    cd.get("Email") or "",
                    cd.get("Phone Number") or "",
                    rec.source_file,
                    rec.sheet_name,
                    rec.row_number,
                    group.match_level,
                    f"{group.confidence_score:.0f}%",
                ]
                for j, v in enumerate(row_vals):
                    ws_exact.write(row_idx, j, "" if v is None else v, fmt)
                row_idx += 1

        for j, h in enumerate(headers_exact):
            ws_exact.set_column(j, j, max(14, len(h) + 3))
        ws_exact.autofilter(0, 0, max(1, row_idx - 1), len(headers_exact) - 1)
        ws_exact.freeze_panes(1, 0)

        # ------------------------------------------------------------- 2. Similar Records
        ws_sim = wb.add_worksheet("Similar Records")
        headers_sim = ["Group ID", "Name / Primary Entity", "Similarity", "Matching Fields", "Source Files", "Details"]
        for j, h in enumerate(headers_sim):
            ws_sim.write(0, j, h, header_fmt)

        row_idx = 1
        for group in getattr(analysis_result, "similar_records", []) + getattr(analysis_result, "possible_matches", []):
            fmt = alt_fmt if row_idx % 2 == 0 else None
            names = [r.canonical_data.get("Name") or r.canonical_data.get("Company") or "" for r in group.records]
            sources = list({f"{r.source_file} ({r.sheet_name}:L{r.row_number})" for r in group.records})
            primary_name = names[0] if names else "N/A"

            row_vals = [
                group.group_id,
                primary_name,
                f"{group.confidence_score:.1f}%",
                ", ".join(group.matching_fields),
                " | ".join(sources),
                group.reason,
            ]
            for j, v in enumerate(row_vals):
                ws_sim.write(row_idx, j, "" if v is None else v, fmt)
            row_idx += 1

        for j, h in enumerate(headers_sim):
            ws_sim.set_column(j, j, max(16, len(h) + 3))
        ws_sim.autofilter(0, 0, max(1, row_idx - 1), len(headers_sim) - 1)
        ws_sim.freeze_panes(1, 0)

        # ------------------------------------------------------------- 3. Conflicting Records
        ws_conf = wb.add_worksheet("Conflicting Records")
        headers_conf = ["Entity Name", "Field", "Old Value", "New Value", "Source A", "Source B"]
        for j, h in enumerate(headers_conf):
            ws_conf.write(0, j, h, header_fmt)

        row_idx = 1
        for c in getattr(analysis_result, "conflicting_records", []):
            fmt = alt_fmt if row_idx % 2 == 0 else None
            row_vals = [
                c.entity_name,
                c.field_name,
                str(c.value_a),
                str(c.value_b),
                f"{c.source_a} ({c.sheet_a}:L{c.row_a})",
                f"{c.source_b} ({c.sheet_b}:L{c.row_b})",
            ]
            for j, v in enumerate(row_vals):
                ws_conf.write(row_idx, j, "" if v is None else v, fmt)
            row_idx += 1

        for j, h in enumerate(headers_conf):
            ws_conf.set_column(j, j, max(16, len(h) + 3))
        ws_conf.autofilter(0, 0, max(1, row_idx - 1), len(headers_conf) - 1)
        ws_conf.freeze_panes(1, 0)

        # ------------------------------------------------------------- 4. Missing Data
        ws_miss = wb.add_worksheet("Missing Data")
        headers_miss = ["File", "Sheet", "Row", "Missing Column", "Details"]
        for j, h in enumerate(headers_miss):
            ws_miss.write(0, j, h, header_fmt)

        row_idx = 1
        for m in getattr(analysis_result, "missing_data", [])[:2000]:  # Cap at top 2000 for excel size
            fmt = alt_fmt if row_idx % 2 == 0 else None
            row_vals = [m.source_file, m.sheet_name, m.row_number, m.missing_column, m.details]
            for j, v in enumerate(row_vals):
                ws_miss.write(row_idx, j, "" if v is None else v, fmt)
            row_idx += 1

        for j, h in enumerate(headers_miss):
            ws_miss.set_column(j, j, max(16, len(h) + 3))
        ws_miss.autofilter(0, 0, max(1, row_idx - 1), len(headers_miss) - 1)
        ws_miss.freeze_panes(1, 0)

        # ------------------------------------------------------------- 5. Summary
        ws_sum = wb.add_worksheet("Summary")
        ws_sum.write(1, 1, "Data Analysis & Duplicate Engine Summary Report", title_fmt)

        metrics = [
            ("Total Files Processed", getattr(analysis_result, "total_files", 0)),
            ("Total Worksheets Analyzed", getattr(analysis_result, "total_worksheets", 0)),
            ("Total Records Analyzed", getattr(analysis_result, "total_records", 0)),
            ("Exact Duplicate Records", getattr(analysis_result, "exact_duplicates_count", 0)),
            ("Similar Match Records", getattr(analysis_result, "similar_records_count", 0)),
            ("Possible Match Records", getattr(analysis_result, "possible_matches_count", 0)),
            ("Unique Records", getattr(analysis_result, "unique_records_count", 0)),
            ("Conflicting Records Flagged", getattr(analysis_result, "conflicting_records_count", 0)),
            ("Missing Data Instances", getattr(analysis_result, "missing_records_count", 0)),
            ("Processing Time (Seconds)", f"{getattr(analysis_result, 'processing_time_sec', 0.0):.2f}s"),
        ]

        ws_sum.set_column(1, 1, 32)
        ws_sum.set_column(2, 2, 20)

        for i, (label, val) in enumerate(metrics, start=3):
            ws_sum.write(i, 1, label, metric_label_fmt)
            ws_sum.write(i, 2, val, metric_val_fmt)

        wb.close()
        log.info(f"Duplicate_Report.xlsx successfully generated: {path}")
        return str(path)

    def generate_master_workbook(self, mdm_result: Any, path: str | Path = "Master_Data.xlsx") -> str:
        """Generate comprehensive 8-sheet Enterprise Master_Data.xlsx workbook:

        1. 1_Master_Records
        2. 2_Duplicate_References
        3. 3_Unique_Records
        4. 4_Conflicting_Records
        5. 5_Missing_Data
        6. 6_Statistics
        7. 7_Analysis_Summary
        8. 8_Processing_Log
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        wb = xlsxwriter.Workbook(str(path), {"nan_inf_to_errors": True})

        # Corporate Design Formats
        header_fmt = wb.add_format({
            "bold": True, "bg_color": "#0F172A", "font_color": "#F8FAFC",
            "border": 1, "align": "center", "valign": "vcenter", "font_size": 11,
        })
        title_fmt = wb.add_format({
            "bold": True, "font_size": 14, "font_color": "#1E293B",
        })
        metric_label_fmt = wb.add_format({
            "bold": True, "bg_color": "#F1F5F9", "border": 1, "font_size": 10,
        })
        metric_val_fmt = wb.add_format({
            "align": "right", "border": 1, "font_size": 10, "bold": True, "font_color": "#2563EB",
        })
        alt_fmt = wb.add_format({"bg_color": "#F8FAFC"})
        accent_fmt = wb.add_format({"bg_color": "#EFF6FF", "bold": True, "font_color": "#1D4ED8"})

        # ------------------------------------------------------------- 1. 1_Master_Records
        ws_master = wb.add_worksheet("1_Master_Records")
        headers_master = [
            "Master ID", "Name", "Address", "City", "State",
            "Contact Number", "Email", "Company", "GST Number", "Customer ID",
            "Source Count", "Duplicate Count", "Total Occurrences", "Created Date"
        ]
        for j, h in enumerate(headers_master):
            ws_master.write(0, j, h, header_fmt)

        row_idx = 1
        for m in getattr(mdm_result, "master_records", []):
            fmt = alt_fmt if row_idx % 2 == 0 else None
            vals = [
                m.master_id, m.name, m.address, m.city, m.state,
                m.contact_number, m.email, m.company, m.gst_number, m.customer_id,
                m.source_count, m.duplicate_count, m.total_occurrences, m.created_date
            ]
            for j, v in enumerate(vals):
                ws_master.write(row_idx, j, "" if v is None else v, fmt)
            row_idx += 1

        for j, h in enumerate(headers_master):
            ws_master.set_column(j, j, max(15, len(h) + 3))
        ws_master.autofilter(0, 0, max(1, row_idx - 1), len(headers_master) - 1)
        ws_master.freeze_panes(1, 0)

        # ------------------------------------------------------------- 2. 2_Duplicate_References
        ws_refs = wb.add_worksheet("2_Duplicate_References")
        headers_refs = ["Master ID", "Source File", "Worksheet", "Row Number", "Folder Path", "Import Date"]
        for j, h in enumerate(headers_refs):
            ws_refs.write(0, j, h, header_fmt)

        row_idx = 1
        for r in getattr(mdm_result, "duplicate_references", []):
            fmt = alt_fmt if row_idx % 2 == 0 else None
            vals = [r.master_id, r.source_file, r.sheet_name, r.row_number, r.folder_path, r.import_date]
            for j, v in enumerate(vals):
                ws_refs.write(row_idx, j, "" if v is None else v, fmt)
            row_idx += 1

        for j, h in enumerate(headers_refs):
            ws_refs.set_column(j, j, max(16, len(h) + 3))
        ws_refs.autofilter(0, 0, max(1, row_idx - 1), len(headers_refs) - 1)
        ws_refs.freeze_panes(1, 0)

        # ------------------------------------------------------------- 3. 3_Unique_Records
        ws_uniq = wb.add_worksheet("3_Unique_Records")
        for j, h in enumerate(headers_master):
            ws_uniq.write(0, j, h, header_fmt)

        row_idx = 1
        for m in getattr(mdm_result, "unique_records", []):
            fmt = alt_fmt if row_idx % 2 == 0 else None
            vals = [
                m.master_id, m.name, m.address, m.city, m.state,
                m.contact_number, m.email, m.company, m.gst_number, m.customer_id,
                m.source_count, m.duplicate_count, m.total_occurrences, m.created_date
            ]
            for j, v in enumerate(vals):
                ws_uniq.write(row_idx, j, "" if v is None else v, fmt)
            row_idx += 1

        for j, h in enumerate(headers_master):
            ws_uniq.set_column(j, j, max(15, len(h) + 3))
        ws_uniq.autofilter(0, 0, max(1, row_idx - 1), len(headers_master) - 1)
        ws_uniq.freeze_panes(1, 0)

        # ------------------------------------------------------------- 4. 4_Conflicting_Records
        ws_conf = wb.add_worksheet("4_Conflicting_Records")
        headers_conf = ["Conflict ID", "Master ID", "Entity Name", "Field Name", "Value A", "Source A (Sheet:Row)", "Value B", "Source B (Sheet:Row)", "Status"]
        for j, h in enumerate(headers_conf):
            ws_conf.write(0, j, h, header_fmt)

        row_idx = 1
        for c in getattr(mdm_result, "conflicts", []):
            fmt = alt_fmt if row_idx % 2 == 0 else None
            vals = [
                c.conflict_id, c.master_id, c.entity_name, c.field_name,
                str(c.value_a), f"{c.source_a} ({c.sheet_a}:L{c.row_a})",
                str(c.value_b), f"{c.source_b} ({c.sheet_b}:L{c.row_b})",
                c.status
            ]
            for j, v in enumerate(vals):
                ws_conf.write(row_idx, j, "" if v is None else v, fmt)
            row_idx += 1

        for j, h in enumerate(headers_conf):
            ws_conf.set_column(j, j, max(16, len(h) + 3))
        ws_conf.autofilter(0, 0, max(1, row_idx - 1), len(headers_conf) - 1)
        ws_conf.freeze_panes(1, 0)

        # ------------------------------------------------------------- 5. 5_Missing_Data
        ws_miss = wb.add_worksheet("5_Missing_Data")
        headers_miss = ["File", "Worksheet", "Row Number", "Folder Path", "Missing Column", "Details"]
        for j, h in enumerate(headers_miss):
            ws_miss.write(0, j, h, header_fmt)

        row_idx = 1
        for item in getattr(mdm_result, "missing_data", [])[:3000]:
            fmt = alt_fmt if row_idx % 2 == 0 else None
            vals = [
                item.get("source_file"), item.get("sheet_name"), item.get("row_number"),
                item.get("folder_path"), item.get("missing_column"), item.get("details")
            ]
            for j, v in enumerate(vals):
                ws_miss.write(row_idx, j, "" if v is None else v, fmt)
            row_idx += 1

        for j, h in enumerate(headers_miss):
            ws_miss.set_column(j, j, max(16, len(h) + 3))
        ws_miss.autofilter(0, 0, max(1, row_idx - 1), len(headers_miss) - 1)
        ws_miss.freeze_panes(1, 0)

        # ------------------------------------------------------------- 6. 6_Statistics
        ws_stats = wb.add_worksheet("6_Statistics")
        ws_stats.write(1, 1, "Enterprise MDM Consolidation Statistics", title_fmt)

        stats_metrics = [
            ("Total Spreadsheets Found", getattr(mdm_result, "total_files", 0)),
            ("Total Worksheets Scanned", getattr(mdm_result, "total_worksheets", 0)),
            ("Total Indexed Records", getattr(mdm_result, "total_records", 0)),
            ("Total Unique Columns", getattr(mdm_result, "total_columns", 0)),
            ("Processing Data Size (MB)", f"{getattr(mdm_result, 'processing_size_bytes', 0) / (1024*1024):.2f} MB"),
            ("Master Dataset Records", getattr(mdm_result, "master_records_count", 0)),
            ("Duplicate Record Groups", getattr(mdm_result, "duplicate_groups_count", 0)),
            ("Total Duplicate References", getattr(mdm_result, "duplicate_records_count", 0)),
            ("Unique Records (Non-Duplicate)", getattr(mdm_result, "unique_records_count", 0)),
            ("Conflicting Field Instances", getattr(mdm_result, "conflicting_records_count", 0)),
            ("Missing Field Entries", getattr(mdm_result, "missing_records_count", 0)),
        ]

        ws_stats.set_column(1, 1, 35)
        ws_stats.set_column(2, 2, 22)

        for i, (label, val) in enumerate(stats_metrics, start=3):
            ws_stats.write(i, 1, label, metric_label_fmt)
            ws_stats.write(i, 2, val, metric_val_fmt)

        # ------------------------------------------------------------- 7. 7_Analysis_Summary
        ws_summary = wb.add_worksheet("7_Analysis_Summary")
        ws_summary.write(1, 1, "MDM Executive Analysis & Matching Summary", title_fmt)

        sum_items = [
            ("Matching Rule Name", getattr(mdm_result, "matching_rule_used", "Rule 1")),
            ("Matching Fields Evaluated", ", ".join(getattr(mdm_result, "matching_fields_used", []))),
            ("Processing Duration (Seconds)", f"{getattr(mdm_result, 'processing_time_sec', 0.0):.2f}s"),
            ("System RAM Usage (MB)", f"{getattr(mdm_result, 'memory_usage_mb', 0.0):.2f} MB"),
            ("Estimated Processing Time", f"{getattr(mdm_result, 'estimated_processing_time_sec', 0.0):.2f}s"),
        ]

        ws_summary.set_column(1, 1, 35)
        ws_summary.set_column(2, 2, 45)

        for i, (label, val) in enumerate(sum_items, start=3):
            ws_summary.write(i, 1, label, metric_label_fmt)
            ws_summary.write(i, 2, val, metric_val_fmt)

        # ------------------------------------------------------------- 8. 8_Processing_Log
        ws_log = wb.add_worksheet("8_Processing_Log")
        ws_log.write(0, 0, "Timestamp / Step Log", header_fmt)

        for i, log_line in enumerate(getattr(mdm_result, "processing_logs", []), start=1):
            ws_log.write(i, 0, log_line)

        ws_log.set_column(0, 0, 80)
        ws_log.freeze_panes(1, 0)

        wb.close()
        log.info(f"Master_Data.xlsx successfully generated: {path}")
        return str(path)

>>>>>>> a4386bf (Initial commit)
    def export_duplicates(self, groups: list[DuplicateGroup], path: str | Path) -> str:
        from ..engine.duplicate_engine import DuplicateEngine
        df = DuplicateEngine.to_dataframe(groups)
        if df.is_empty():
            df = pl.DataFrame({"info": ["No duplicates detected"]})
        return self.export_multi([("Duplicates", df)], path)

    def export_validation(self, issues: list[ValidationIssue], path: str | Path) -> str:
        from ..engine.validation_engine import ValidationEngine
        df = ValidationEngine.to_dataframe(issues)
        if df.is_empty():
            df = pl.DataFrame({"info": ["No validation issues detected"]})
        return self.export_multi([("Validation", df)], path)

    @staticmethod
    def _safe_sheet(name: str) -> str:
        bad = set('[]:*?/\\')
        clean = "".join("_" if ch in bad else ch for ch in name)[:31]
        return clean or "Sheet"
