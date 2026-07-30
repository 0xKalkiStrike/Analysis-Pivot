"""KPI dashboard — Power BI style KPI cards + charts with cross-filter clicks."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QComboBox, QFrame, QGridLayout, QHBoxLayout,
                                QLabel, QVBoxLayout, QWidget)

from ...models import AnalyticsSummary, Dataset
from ...utils import format_number
from .chart_view import ChartViewWidget


class KpiCard(QFrame):
    def __init__(self, label: str, value: str, accent: str = "#7c5cff") -> None:
        super().__init__()
        self.setProperty("kpi", True)
        self.setMinimumHeight(110)
        v = QVBoxLayout(self); v.setContentsMargins(18, 14, 18, 14); v.setSpacing(4)
        lbl = QLabel(label); lbl.setProperty("kpi-label", True)
        val = QLabel(value); val.setProperty("kpi-value", True)
        val.setStyleSheet(f"color:{accent};")
        val.setFont(QFont("Inter", 26, QFont.Bold))
        v.addWidget(lbl); v.addWidget(val); v.addStretch(1)
        self.value_lbl = val

    def update_value(self, value: str) -> None:
        self.value_lbl.setText(value)


class DashboardWidget(QWidget):
    # Cross-filter signals
    dataset_selected = Signal(str)         # bar in "Rows by Sheet" clicked
    quality_selected = Signal(str)         # pie slice in composition clicked
    top_value_selected = Signal(str, str)  # (column, value) — bar in top-values clicked

    def __init__(self) -> None:
        super().__init__()
        self._active_dataset: Dataset | None = None
        outer = QVBoxLayout(self); outer.setContentsMargins(24, 24, 24, 24); outer.setSpacing(20)

        header = QHBoxLayout()
        title = QLabel("Analytics Dashboard")
        title.setStyleSheet("font-size:26px; font-weight:700; color:#c9b6ff; letter-spacing:-0.02em;")
        subtitle = QLabel("Click any bar or slice to cross-filter the workspace")
        subtitle.setStyleSheet("color:#8b8ba8;")
        head_v = QVBoxLayout(); head_v.setSpacing(2); head_v.addWidget(title); head_v.addWidget(subtitle)
        header.addLayout(head_v); header.addStretch(1)
        outer.addLayout(header)

        # KPI grid
        grid = QGridLayout(); grid.setSpacing(16)
        self.cards: dict[str, KpiCard] = {}
        defs = [
            ("Files", "0", "#7c5cff"), ("Sheets", "0", "#b06bff"),
            ("Total Rows", "0", "#5bd4ff"), ("Unique Rows", "0", "#4be0a8"),
            ("Duplicates", "0", "#ffb84b"), ("Missing Values", "0", "#ff6b6b"),
            ("Quality Score", "100", "#4be0a8"), ("Validation Score", "100", "#c9b6ff"),
        ]
        for i, (name, val, accent) in enumerate(defs):
            card = KpiCard(name, val, accent)
            grid.addWidget(card, i // 4, i % 4)
            self.cards[name] = card
        outer.addLayout(grid)

        # Insights row 1
        section = QLabel("Insights")
        section.setStyleSheet("font-size:16px; font-weight:600; color:#c9b6ff; margin-top:8px;")
        outer.addWidget(section)

        charts_wrap = QHBoxLayout(); charts_wrap.setSpacing(16)
        self.chart_left = ChartViewWidget(title="Rows by Sheet  ·  click to activate")
        self.chart_right = ChartViewWidget(title="Data Quality Composition  ·  click a slice")
        charts_wrap.addWidget(self.chart_left, 1)
        charts_wrap.addWidget(self.chart_right, 1)
        outer.addLayout(charts_wrap, 1)

        # Top Values chart with column selector
        tv_bar = QHBoxLayout()
        tv_bar.addWidget(QLabel("Top values by column:"))
        self.column_selector = QComboBox(); self.column_selector.setMinimumWidth(200)
        self.column_selector.currentTextChanged.connect(self._on_column_changed)
        tv_bar.addWidget(self.column_selector); tv_bar.addStretch(1)
        outer.addLayout(tv_bar)

        self.chart_top_values = ChartViewWidget(title="Top Values  ·  click a bar to filter data")
        outer.addWidget(self.chart_top_values, 1)

        # Wire click signals
        self.chart_left.category_clicked.connect(self._on_bar_clicked)
        self.chart_right.category_clicked.connect(lambda label, _v: self.quality_selected.emit(label))
        self.chart_top_values.category_clicked.connect(self._on_top_value_clicked)

    # ------------------------------------------------------------------ api
    def update_summary(
        self,
        s: AnalyticsSummary,
        per_sheet: list[tuple[str, int]] | None = None,
    ) -> None:
        self.cards["Files"].update_value(format_number(s.total_files))
        self.cards["Sheets"].update_value(format_number(s.total_sheets))
        self.cards["Total Rows"].update_value(format_number(s.total_rows))
        self.cards["Unique Rows"].update_value(format_number(s.unique_rows))
        self.cards["Duplicates"].update_value(format_number(s.duplicate_rows))
        self.cards["Missing Values"].update_value(format_number(s.missing_values))
        self.cards["Quality Score"].update_value(f"{s.data_quality_score:.1f}")
        self.cards["Validation Score"].update_value(f"{s.validation_score:.1f}")

        self._sheet_labels: list[str] = []
        if per_sheet:
            names_full = [n for n, _ in per_sheet]
            names = [n[:24] for n in names_full]
            vals = [v for _, v in per_sheet]
            self._sheet_labels = list(zip(names, names_full))
            self.chart_left.bar_chart(names, vals, ylabel="Rows")

        quality_parts = {
            "Unique": s.unique_rows,
            "Duplicates": s.duplicate_rows,
            "Missing": s.missing_values,
        }
        quality_parts = {k: v for k, v in quality_parts.items() if v > 0}
        if quality_parts:
            self.chart_right.pie_chart(list(quality_parts.keys()), list(quality_parts.values()))

    def set_active_dataset(self, dataset: Dataset | None) -> None:
        self._active_dataset = dataset
        self.column_selector.blockSignals(True)
        self.column_selector.clear()
        if dataset:
            for c in dataset.columns:
                self.column_selector.addItem(c)
        self.column_selector.blockSignals(False)
        self._refresh_top_values()

    # ------------------------------------------------------------------ internals
    def _on_bar_clicked(self, short_name: str, _val: float) -> None:
        # Map back to the full sheet name
        for short, full in getattr(self, "_sheet_labels", []):
            if short == short_name:
                self.dataset_selected.emit(full)
                return
        self.dataset_selected.emit(short_name)

    def _on_column_changed(self, _text: str) -> None:
        self._refresh_top_values()

    def _refresh_top_values(self) -> None:
        col = self.column_selector.currentText()
        ds = self._active_dataset
        if not ds or not col:
            self.chart_top_values.clear()
            return
        try:
            vc = ds.df[col].value_counts(sort=True).head(10).to_dicts()
        except Exception:
            self.chart_top_values.clear(); return
        labels = [str(r.get(col))[:18] for r in vc]
        counts = [int(r.get("count", r.get("counts", 0))) for r in vc]
        if not labels:
            self.chart_top_values.clear(); return
        self.chart_top_values.set_title(f"Top values in '{col}'  ·  click a bar to filter data")
        self.chart_top_values.bar_chart(labels, counts, ylabel="Count")
        self._current_top_column = col

    def _on_top_value_clicked(self, label: str, _v: float) -> None:
        col = getattr(self, "_current_top_column", "")
        if col:
            self.top_value_selected.emit(col, label)
