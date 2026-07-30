"""SQL console powered by DuckDB — run ad-hoc queries across datasets."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QHBoxLayout, QHeaderView, QLabel, QMessageBox,
                                QPlainTextEdit, QPushButton, QSplitter,
                                QTableView, QVBoxLayout, QWidget)

from ...database import DBManager
from ...models import Dataset
from .table_model import PolarsTableModel


class SqlConsoleWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.db = DBManager()

        v = QVBoxLayout(self); v.setContentsMargins(16, 16, 16, 16); v.setSpacing(12)
        title = QLabel(f"SQL Console  ·  backend: {self.db.backend}")
        title.setStyleSheet("font-size:18px; font-weight:600; color:#c9b6ff;")
        v.addWidget(title)

        splitter = QSplitter(Qt.Vertical)

        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText(
            "-- Datasets are registered as tables (see tables list on top)\n"
            "-- Example:\n"
            "SELECT * FROM t0 LIMIT 100;"
        )
        splitter.addWidget(self.editor)

        self.model = PolarsTableModel()
        self.table = QTableView(); self.table.setModel(self.model)
        self.table.setAlternatingRowColors(True); self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        splitter.addWidget(self.table)
        splitter.setSizes([180, 400])
        v.addWidget(splitter, 1)

        controls = QHBoxLayout()
        self.tables_label = QLabel("Tables: (none)"); self.tables_label.setStyleSheet("color:#8b8ba8;")
        controls.addWidget(self.tables_label); controls.addStretch(1)
        self.btn_run = QPushButton("Run  ▶")
        self.btn_run.clicked.connect(self.execute)
        controls.addWidget(self.btn_run)
        v.addLayout(controls)

    def register_datasets(self, datasets: dict[str, Dataset]) -> None:
        # Give short table aliases
        aliases: list[str] = []
        for i, (name, ds) in enumerate(datasets.items()):
            alias = f"t{i}"
            self.db.register(alias, ds.df)
            aliases.append(f"{alias} = {name}")
        self.tables_label.setText("Tables: " + " · ".join(aliases) if aliases else "Tables: (none)")

    def execute(self) -> None:
        q = self.editor.toPlainText().strip().rstrip(";")
        if not q:
            return
        try:
            df = self.db.sql(q)
            self.model.set_dataframe(df)
        except Exception as e:
            QMessageBox.critical(self, "Query error", str(e))
