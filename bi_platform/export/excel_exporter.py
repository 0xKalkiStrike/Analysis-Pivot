"""Excel exporter using XlsxWriter — formatted, filtered, coloured."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

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
