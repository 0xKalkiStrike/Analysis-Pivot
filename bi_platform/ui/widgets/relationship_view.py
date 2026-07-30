"""Relationship Viewer — table + visual graph of discovered FK links."""
from __future__ import annotations

import math

import pyqtgraph as pg
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (QHBoxLayout, QHeaderView, QLabel, QMessageBox,
                                QPushButton, QSplitter, QTableView,
                                QVBoxLayout, QWidget)

from ...engine import Relationship, RelationshipEngine
from ...models import Dataset
from .table_model import PolarsTableModel


class _GraphView(pg.PlotWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setBackground((18, 18, 28))
        self.hideAxis("left"); self.hideAxis("bottom")
        self.setMouseEnabled(x=True, y=True); self.showGrid(x=False, y=False)

    def draw(self, datasets: list[str], rels: list[Relationship]) -> None:
        self.clear()
        if not datasets:
            return
        n = len(datasets)
        # Place datasets on a circle
        radius = max(2.5, n * 0.55)
        positions: dict[str, tuple[float, float]] = {}
        for i, name in enumerate(datasets):
            angle = 2 * math.pi * i / n - math.pi / 2
            positions[name] = (radius * math.cos(angle), radius * math.sin(angle))

        # Draw edges first
        for r in rels:
            if r.left_dataset not in positions or r.right_dataset not in positions:
                continue
            x1, y1 = positions[r.left_dataset]
            x2, y2 = positions[r.right_dataset]
            width = 1 + 4 * (r.confidence / 100.0)
            color = self._confidence_color(r.confidence)
            line = pg.PlotDataItem([x1, x2], [y1, y2], pen=pg.mkPen(color, width=width))
            self.addItem(line)
            # Midpoint label
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            label = pg.TextItem(f"{r.left_column} ↔ {r.right_column}", color=color, anchor=(0.5, 0.5))
            label.setFont(QFont("Inter", 8))
            label.setPos(mx, my)
            self.addItem(label)

        # Draw nodes
        for name, (x, y) in positions.items():
            circle = pg.QtWidgets.QGraphicsEllipseItem(x - 0.35, y - 0.35, 0.7, 0.7)
            circle.setBrush(QColor("#5b4be0"))
            circle.setPen(pg.mkPen(QColor("#c9b6ff"), width=2))
            self.addItem(circle)
            text = pg.TextItem(self._shorten(name), color="#ffffff", anchor=(0.5, 0.5))
            text.setFont(QFont("Inter", 9, QFont.Bold))
            text.setPos(x, y)
            self.addItem(text)

        self.setRange(xRange=(-radius - 1.5, radius + 1.5),
                      yRange=(-radius - 1.5, radius + 1.5))
        self.setAspectLocked(True)

    @staticmethod
    def _shorten(name: str, n: int = 20) -> str:
        return name if len(name) <= n else name[: n - 1] + "…"

    @staticmethod
    def _confidence_color(conf: float) -> QColor:
        if conf >= 90: return QColor("#4be0a8")
        if conf >= 75: return QColor("#7c5cff")
        if conf >= 60: return QColor("#ffb84b")
        return QColor("#8b8ba8")


class RelationshipViewWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._datasets_ref: dict[str, Dataset] = {}
        self._rels: list[Relationship] = []

        v = QVBoxLayout(self); v.setContentsMargins(16, 16, 16, 16); v.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Relationship Discovery")
        title.setStyleSheet("font-size:18px; font-weight:600; color:#c9b6ff;")
        header.addWidget(title); header.addStretch(1)
        self.btn_scan = QPushButton("Scan Relationships"); self.btn_scan.clicked.connect(self.scan)
        header.addWidget(self.btn_scan)
        v.addLayout(header)

        self.summary = QLabel("Load at least two datasets and click Scan.")
        self.summary.setStyleSheet("color:#8b8ba8;")
        v.addWidget(self.summary)

        splitter = QSplitter(Qt.Horizontal)
        self.graph = _GraphView()
        self.model = PolarsTableModel()
        self.table = QTableView(); self.table.setModel(self.model)
        self.table.setAlternatingRowColors(True); self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        splitter.addWidget(self.graph)
        splitter.addWidget(self.table)
        splitter.setSizes([540, 540])
        v.addWidget(splitter, 1)

    def set_datasets(self, datasets: dict[str, Dataset]) -> None:
        self._datasets_ref = datasets

    def scan(self) -> None:
        if len(self._datasets_ref) < 2:
            QMessageBox.information(self, "Relationships",
                                    "Load at least two datasets to discover relationships.")
            return
        self._rels = RelationshipEngine().discover(self._datasets_ref)
        self.model.set_dataframe(RelationshipEngine.to_dataframe(self._rels))
        self.graph.draw(list(self._datasets_ref.keys()), self._rels)
        self.summary.setText(
            f"Discovered {len(self._rels)} relationship(s) across {len(self._datasets_ref)} dataset(s)."
        )

    def clear(self) -> None:
        self._rels = []
        self.graph.clear()
        self.model.set_dataframe(RelationshipEngine.to_dataframe([]))
        self.summary.setText("Load at least two datasets and click Scan.")
