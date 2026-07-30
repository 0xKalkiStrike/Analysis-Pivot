"""Data viewer — high-performance Polars table + search + column profile."""
from __future__ import annotations

import polars as pl
from PySide6.QtCore import QSortFilterProxyModel, Qt
from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QHeaderView, QLabel,
                                QLineEdit, QTableView, QVBoxLayout, QWidget)

from ...models import Dataset
from ...utils import format_number
from .table_model import PolarsTableModel


class DataViewerWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        v = QVBoxLayout(self); v.setContentsMargins(16, 16, 16, 16); v.setSpacing(12)

        header = QHBoxLayout()
        self.title = QLabel("No dataset loaded")
        self.title.setStyleSheet("font-size:18px; font-weight:600; color:#c9b6ff;")
        self.meta = QLabel("")
        self.meta.setStyleSheet("color:#8b8ba8;")
        left = QVBoxLayout(); left.setSpacing(2); left.addWidget(self.title); left.addWidget(self.meta)
        header.addLayout(left); header.addStretch(1)

        # Search + column filter
        self.column_combo = QComboBox(); self.column_combo.addItem("All columns")
        self.column_combo.setMinimumWidth(180)
        self.search = QLineEdit(); self.search.setPlaceholderText("Search rows…")
        self.search.setMinimumWidth(240)
        self.search.textChanged.connect(self._apply_filter)
        self.column_combo.currentIndexChanged.connect(self._apply_filter)
        header.addWidget(self.column_combo); header.addWidget(self.search)
        v.addLayout(header)

        # Table
        self.model = PolarsTableModel()
        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy.setFilterKeyColumn(-1)  # all columns

        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.verticalHeader().setDefaultSectionSize(28)
        v.addWidget(self.table, 1)

    def set_dataset(self, dataset: Dataset) -> None:
        self.title.setText(dataset.name)
        self.meta.setText(
            f"{format_number(dataset.rows)} rows × {dataset.cols} columns"
            + (f" · {dataset.source.file_path}" if dataset.source else "")
        )
        self.model.set_dataframe(dataset.df)
        self.column_combo.blockSignals(True)
        self.column_combo.clear(); self.column_combo.addItem("All columns")
        for c in dataset.columns:
            self.column_combo.addItem(c)
        self.column_combo.blockSignals(False)
        # Set reasonable column widths
        for i in range(min(dataset.cols, 20)):
            self.table.setColumnWidth(i, 160)

    def current_dataframe(self) -> pl.DataFrame:
        return self.model.dataframe()

    def _apply_filter(self) -> None:
        pattern = self.search.text().strip()
        col_idx = self.column_combo.currentIndex() - 1  # 0=all
        self.proxy.setFilterKeyColumn(col_idx if col_idx >= 0 else -1)
        self.proxy.setFilterFixedString(pattern)
