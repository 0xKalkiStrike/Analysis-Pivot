"""Merge wizard — pick 2 datasets, key + join type, preview + save."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox,
                                QFormLayout, QHBoxLayout, QHeaderView, QLabel,
                                QMessageBox, QPushButton, QTableView,
                                QVBoxLayout, QWidget)

from ...engine import MergeEngine
from ...models import Dataset, MergeResult
from .table_model import PolarsTableModel


class MergeWizardDialog(QDialog):
    def __init__(self, datasets: dict[str, Dataset], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Merge Wizard")
        self.setMinimumSize(880, 620)
        self.datasets = datasets
        self.result_obj: MergeResult | None = None

        v = QVBoxLayout(self); v.setContentsMargins(20, 20, 20, 16); v.setSpacing(14)

        title = QLabel("Merge Datasets")
        title.setStyleSheet("font-size:20px; font-weight:600; color:#c9b6ff;")
        v.addWidget(title)

        form = QFormLayout(); form.setSpacing(10)
        self.left_combo = QComboBox(); self.left_combo.addItems(list(datasets.keys()))
        self.right_combo = QComboBox(); self.right_combo.addItems(list(datasets.keys()))
        if self.right_combo.count() > 1:
            self.right_combo.setCurrentIndex(1)
        self.key_combo = QComboBox()
        self.how_combo = QComboBox(); self.how_combo.addItems(["inner", "left", "right", "outer"])

        form.addRow("Left dataset", self.left_combo)
        form.addRow("Right dataset", self.right_combo)
        form.addRow("Join key", self.key_combo)
        form.addRow("Join type", self.how_combo)
        v.addLayout(form)

        actions = QHBoxLayout()
        self.btn_preview = QPushButton("Preview Merge"); self.btn_preview.clicked.connect(self.preview)
        actions.addWidget(self.btn_preview); actions.addStretch(1)
        v.addLayout(actions)

        self.summary = QLabel(""); self.summary.setStyleSheet("color:#8b8ba8;")
        v.addWidget(self.summary)

        self.model = PolarsTableModel()
        self.table = QTableView(); self.table.setModel(self.model)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        v.addWidget(self.table, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        v.addWidget(buttons)

        self.left_combo.currentTextChanged.connect(self._refresh_keys)
        self.right_combo.currentTextChanged.connect(self._refresh_keys)
        self._refresh_keys()

    def _refresh_keys(self) -> None:
        left = self.datasets.get(self.left_combo.currentText())
        right = self.datasets.get(self.right_combo.currentText())
        if not left or not right:
            return
        common = [c for c in left.columns if c in right.columns]
        self.key_combo.clear(); self.key_combo.addItems(common)

    def preview(self) -> None:
        left = self.datasets[self.left_combo.currentText()]
        right = self.datasets[self.right_combo.currentText()]
        key = self.key_combo.currentText()
        how = self.how_combo.currentText()
        if not key:
            QMessageBox.warning(self, "No key", "No shared column to join on."); return
        try:
            self.result_obj = MergeEngine().merge(left, right, on=key, how=how)
        except Exception as e:
            QMessageBox.critical(self, "Merge failed", str(e)); return
        self.model.set_dataframe(self.result_obj.dataset.df)
        self.summary.setText(
            f"Rows: {self.result_obj.total:,}  ·  Matched: {self.result_obj.matched:,}  ·  "
            f"Conflicts: {len(self.result_obj.conflicts)}"
        )
