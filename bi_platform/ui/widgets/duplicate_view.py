"""Duplicate detection widget — configure, run, review, export."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QComboBox, QDoubleSpinBox, QHBoxLayout,
                                QHeaderView, QLabel, QMessageBox, QPushButton,
                                QTableView, QVBoxLayout, QWidget, QCheckBox)

from ...engine import CleaningEngine, DuplicateEngine, FuzzyEngine
from ...models import Dataset
from ...utils import format_number
from .table_model import PolarsTableModel


class DuplicateViewWidget(QWidget):
    export_requested = Signal(list)  # list[DuplicateGroup]

    def __init__(self) -> None:
        super().__init__()
        self.dataset: Dataset | None = None
        self.groups = []

        v = QVBoxLayout(self); v.setContentsMargins(16, 16, 16, 16); v.setSpacing(12)

        title = QLabel("Duplicate Detection")
        title.setStyleSheet("font-size:18px; font-weight:600; color:#c9b6ff;")
        v.addWidget(title)

        controls = QHBoxLayout(); controls.setSpacing(10)
        controls.addWidget(QLabel("Column:"))
        self.column_combo = QComboBox(); self.column_combo.addItem("Smart (auto)")
        self.column_combo.setMinimumWidth(180)
        controls.addWidget(self.column_combo)

        controls.addWidget(QLabel("Algorithm:"))
        self.algo_combo = QComboBox()
        self.algo_combo.addItems(list(FuzzyEngine.ALGOS.keys()))
        self.algo_combo.setCurrentText("weighted_ratio")
        controls.addWidget(self.algo_combo)

        controls.addWidget(QLabel("Threshold:"))
        self.threshold = QDoubleSpinBox()
        self.threshold.setRange(50, 100); self.threshold.setValue(88); self.threshold.setSuffix(" %")
        controls.addWidget(self.threshold)

        self.chk_clean = QCheckBox("Clean before scan"); self.chk_clean.setChecked(True)
        controls.addWidget(self.chk_clean)

        controls.addStretch(1)
        self.btn_run = QPushButton("Detect Duplicates"); self.btn_run.clicked.connect(self.run)
        self.btn_export = QPushButton("Export…"); self.btn_export.setProperty("flat", True)
        self.btn_export.clicked.connect(lambda: self.export_requested.emit(self.groups))
        controls.addWidget(self.btn_run); controls.addWidget(self.btn_export)
        v.addLayout(controls)

        self.summary = QLabel("Load a dataset and click Detect Duplicates.")
        self.summary.setStyleSheet("color:#8b8ba8;")
        v.addWidget(self.summary)

        self.model = PolarsTableModel()
        self.table = QTableView(); self.table.setModel(self.model)
        self.table.setAlternatingRowColors(True); self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        v.addWidget(self.table, 1)

    def set_dataset(self, dataset: Dataset) -> None:
        self.dataset = dataset
        self.column_combo.clear(); self.column_combo.addItem("Smart (auto)")
        for c in dataset.columns:
            self.column_combo.addItem(c)
        self.groups = []
        self.model.set_dataframe(dataset.df.head(0))
        self.summary.setText(f"Ready: {dataset.name} — {format_number(dataset.rows)} rows.")

    def run(self) -> None:
        if not self.dataset:
            QMessageBox.information(self, "No data", "Load a dataset first."); return
        ds = self.dataset
        if self.chk_clean.isChecked():
            ds = CleaningEngine().clean(ds)
        engine = DuplicateEngine(FuzzyEngine(self.algo_combo.currentText()))
        col = self.column_combo.currentText()
        threshold = float(self.threshold.value())
        if col == "Smart (auto)":
            self.groups = engine.detect_smart(ds, threshold=threshold)
        else:
            self.groups = engine.detect_fuzzy(ds, col, threshold=threshold)
        df = DuplicateEngine.to_dataframe(self.groups)
        self.model.set_dataframe(df)
        total_rows = sum(g.size for g in self.groups)
        self.summary.setText(
            f"Detected {len(self.groups)} duplicate groups — {total_rows} rows flagged "
            f"(threshold {threshold:.0f}%, algo {self.algo_combo.currentText()})."
        )
