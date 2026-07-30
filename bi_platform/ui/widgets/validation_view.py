"""Validation widget — run engine, view issues, export."""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QHBoxLayout, QHeaderView, QLabel, QMessageBox,
                                QPushButton, QTableView, QVBoxLayout, QWidget)

from ...engine import ValidationEngine
from ...models import Dataset
from .table_model import PolarsTableModel


class ValidationViewWidget(QWidget):
    export_requested = Signal(list)

    def __init__(self) -> None:
        super().__init__()
        self.dataset: Dataset | None = None
        self.issues = []

        v = QVBoxLayout(self); v.setContentsMargins(16, 16, 16, 16); v.setSpacing(12)
        title = QLabel("Data Validation")
        title.setStyleSheet("font-size:18px; font-weight:600; color:#c9b6ff;")
        v.addWidget(title)

        controls = QHBoxLayout()
        self.btn_run = QPushButton("Validate"); self.btn_run.clicked.connect(self.run)
        self.btn_export = QPushButton("Export…"); self.btn_export.setProperty("flat", True)
        self.btn_export.clicked.connect(lambda: self.export_requested.emit(self.issues))
        controls.addWidget(self.btn_run); controls.addStretch(1); controls.addWidget(self.btn_export)
        v.addLayout(controls)

        self.summary = QLabel("Load a dataset then click Validate.")
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
        self.issues = []
        self.model.set_dataframe(dataset.df.head(0))
        self.summary.setText(f"Ready: {dataset.name}")

    def run(self) -> None:
        if not self.dataset:
            QMessageBox.information(self, "No data", "Load a dataset first."); return
        eng = ValidationEngine()
        self.issues = eng.validate(self.dataset)
        score = eng.quality_score(self.dataset, self.issues)
        self.model.set_dataframe(eng.to_dataframe(self.issues))
        errs = sum(1 for i in self.issues if i.severity == "error")
        warns = sum(1 for i in self.issues if i.severity == "warning")
        infos = sum(1 for i in self.issues if i.severity == "info")
        self.summary.setText(
            f"Quality score: {score}  ·  {errs} errors · {warns} warnings · {infos} info"
        )
