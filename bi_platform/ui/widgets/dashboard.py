"""KPI dashboard — Power BI style KPI cards + charts."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel,
                                QScrollArea, QVBoxLayout, QWidget)

from ...models import AnalyticsSummary
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
    def __init__(self) -> None:
        super().__init__()
        outer = QVBoxLayout(self); outer.setContentsMargins(24, 24, 24, 24); outer.setSpacing(20)

        header = QHBoxLayout()
        title = QLabel("Analytics Dashboard")
        title.setStyleSheet("font-size:26px; font-weight:700; color:#c9b6ff; letter-spacing:-0.02em;")
        subtitle = QLabel("Real-time KPIs across all loaded datasets")
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

        # Chart area
        section = QLabel("Insights")
        section.setStyleSheet("font-size:16px; font-weight:600; color:#c9b6ff; margin-top:8px;")
        outer.addWidget(section)

        charts_wrap = QHBoxLayout(); charts_wrap.setSpacing(16)
        self.chart_left = ChartViewWidget(title="Rows by Sheet")
        self.chart_right = ChartViewWidget(title="Data Quality Composition")
        charts_wrap.addWidget(self.chart_left, 1)
        charts_wrap.addWidget(self.chart_right, 1)
        outer.addLayout(charts_wrap, 1)

    def update_summary(self, s: AnalyticsSummary, per_sheet: list[tuple[str, int]] | None = None) -> None:
        self.cards["Files"].update_value(format_number(s.total_files))
        self.cards["Sheets"].update_value(format_number(s.total_sheets))
        self.cards["Total Rows"].update_value(format_number(s.total_rows))
        self.cards["Unique Rows"].update_value(format_number(s.unique_rows))
        self.cards["Duplicates"].update_value(format_number(s.duplicate_rows))
        self.cards["Missing Values"].update_value(format_number(s.missing_values))
        self.cards["Quality Score"].update_value(f"{s.data_quality_score:.1f}")
        self.cards["Validation Score"].update_value(f"{s.validation_score:.1f}")

        if per_sheet:
            names = [n[:24] for n, _ in per_sheet]
            vals = [v for _, v in per_sheet]
            self.chart_left.bar_chart(names, vals, ylabel="Rows")

        quality_parts = {
            "Unique": s.unique_rows,
            "Duplicates": s.duplicate_rows,
            "Missing": s.missing_values,
        }
        # Remove zero categories
        quality_parts = {k: v for k, v in quality_parts.items() if v > 0}
        if quality_parts:
            self.chart_right.pie_chart(list(quality_parts.keys()), list(quality_parts.values()))
