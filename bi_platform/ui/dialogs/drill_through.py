"""Drill-through dialog — show underlying rows for a pivot cell."""
from __future__ import annotations

from typing import Any

import polars as pl
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QFileDialog,
                                QHeaderView, QLabel, QPushButton, QTableView,
                                QVBoxLayout)

from ...export import ExcelExporter
from ...models import Dataset
from ..widgets.table_model import PolarsTableModel


class DrillThroughDialog(QDialog):
    """Filter the source Dataset by row/column key(s) and display rows."""

    def __init__(
        self,
        dataset: Dataset,
        row_filters: dict[str, Any],
        column_filters: dict[str, Any] | None = None,
        value_column: str | None = None,
        aggregate: str = "sum",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Drill-through")
        self.setMinimumSize(900, 560)
        self.dataset = dataset
        self.row_filters = row_filters or {}
        self.column_filters = column_filters or {}
        self.value_column = value_column
        self.aggregate = aggregate

        v = QVBoxLayout(self); v.setContentsMargins(20, 20, 20, 16); v.setSpacing(10)

        title = QLabel("Drill-through — underlying rows")
        title.setStyleSheet("font-size:18px; font-weight:600; color:#c9b6ff;")
        v.addWidget(title)

        filters_txt = self._filter_summary()
        subtitle = QLabel(filters_txt); subtitle.setStyleSheet("color:#8b8ba8;")
        subtitle.setWordWrap(True)
        v.addWidget(subtitle)

        # Compute filtered rows
        self.filtered = self._compute_filtered()
        self.info = QLabel(
            f"{self.filtered.height:,} row(s) match. "
            + (f"Aggregate {aggregate}({value_column}) = {self._compute_aggregate():,.2f}"
               if value_column and value_column != "__count__" else "")
        )
        self.info.setStyleSheet("color:#c9b6ff; font-weight:600;")
        v.addWidget(self.info)

        self.model = PolarsTableModel(self.filtered)
        self.table = QTableView(); self.table.setModel(self.model)
        self.table.setAlternatingRowColors(True); self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        v.addWidget(self.table, 1)

        bottom = QDialogButtonBox()
        self.btn_export = QPushButton("Export Rows…")
        self.btn_export.clicked.connect(self._export)
        bottom.addButton(self.btn_export, QDialogButtonBox.ActionRole)
        bottom.addButton(QDialogButtonBox.Close)
        bottom.rejected.connect(self.reject)
        bottom.accepted.connect(self.accept)
        v.addWidget(bottom)

    # ------------------------------------------------------------------
    def _filter_summary(self) -> str:
        parts = []
        for k, v in self.row_filters.items():
            parts.append(f"{k}={v!r}")
        for k, v in self.column_filters.items():
            parts.append(f"{k}={v!r}")
        return "Where " + " and ".join(parts) if parts else "No filters"

    def _compute_filtered(self) -> pl.DataFrame:
        df = self.dataset.df
        all_filters = {**self.row_filters, **self.column_filters}
        for col, val in all_filters.items():
            if col not in df.columns or val is None:
                continue
            # Compare as strings for safety (pivot cells often stringify keys)
            df = df.filter(pl.col(col).cast(pl.Utf8) == str(val))
        return df

    def _compute_aggregate(self) -> float:
        if not self.value_column or self.value_column == "__count__" or self.filtered.is_empty():
            return float(self.filtered.height)
        col = self.filtered[self.value_column]
        try:
            if self.aggregate == "sum":
                return float(col.sum() or 0)
            if self.aggregate in ("mean", "avg"):
                return float(col.mean() or 0)
            if self.aggregate == "min":
                return float(col.min() or 0)
            if self.aggregate == "max":
                return float(col.max() or 0)
            if self.aggregate == "median":
                return float(col.median() or 0)
            if self.aggregate in ("count", "len"):
                return float(col.len())
        except Exception:
            pass
        return float(self.filtered.height)

    def _export(self) -> None:
        p, _ = QFileDialog.getSaveFileName(self, "Export rows", "drill_through.xlsx", "Excel (*.xlsx)")
        if not p:
            return
        from ...models import Dataset as DS
        ExcelExporter().export_dataset(DS(name="DrillThrough", df=self.filtered), p)
