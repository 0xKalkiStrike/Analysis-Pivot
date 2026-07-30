"""Chart widget using pyqtgraph — bar, pie, line, scatter, histogram."""
from __future__ import annotations

import math

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QVBoxLayout, QLabel, QWidget

pg.setConfigOption("background", (18, 18, 28))
pg.setConfigOption("foreground", (230, 230, 240))

PALETTE = [
    "#7c5cff", "#b06bff", "#5bd4ff", "#4be0a8",
    "#ffb84b", "#ff6b6b", "#c9b6ff", "#f38bff",
]


class ChartViewWidget(QWidget):
    def __init__(self, title: str = "") -> None:
        super().__init__()
        v = QVBoxLayout(self); v.setContentsMargins(12, 12, 12, 12); v.setSpacing(8)
        self.setStyleSheet("background-color:#12121c; border:1px solid #2b2b45; border-radius:12px;")

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color:#c9b6ff; font-weight:600; font-size:14px; background:transparent; border:none;")
        v.addWidget(self.title_label)

        self.plot = pg.PlotWidget()
        self.plot.setBackground((18, 18, 28))
        self.plot.showGrid(x=True, y=True, alpha=0.15)
        v.addWidget(self.plot, 1)

    def set_title(self, title: str) -> None:
        self.title_label.setText(title)

    def clear(self) -> None:
        self.plot.clear()

    # ----- charts
    def bar_chart(self, categories: list[str], values: list[float], ylabel: str = "") -> None:
        self.clear()
        if not categories:
            return
        x = np.arange(len(categories))
        brushes = [QColor(PALETTE[i % len(PALETTE)]) for i in range(len(categories))]
        bg = pg.BarGraphItem(x=x, height=values, width=0.7, brushes=brushes, pen=None)
        self.plot.addItem(bg)
        axis = self.plot.getAxis("bottom")
        axis.setTicks([list(zip(x.tolist(), categories))])
        self.plot.setLabel("left", ylabel)
        self.plot.getAxis("bottom").setStyle(tickTextOffset=8, tickFont=QFont("Inter", 8))

    def line_chart(self, x: list, y: list, name: str = "") -> None:
        self.clear()
        self.plot.plot(x, y, pen=pg.mkPen(color=PALETTE[0], width=2), name=name)

    def scatter_chart(self, x: list, y: list) -> None:
        self.clear()
        scatter = pg.ScatterPlotItem(size=10, brush=pg.mkBrush(PALETTE[0]), pen=None)
        scatter.addPoints(x=x, y=y)
        self.plot.addItem(scatter)

    def histogram(self, values: list[float], bins: int = 20) -> None:
        self.clear()
        if not values:
            return
        y, x = np.histogram(values, bins=bins)
        bg = pg.BarGraphItem(x=(x[:-1] + x[1:]) / 2, height=y, width=(x[1] - x[0]) * 0.9,
                             brush=QColor(PALETTE[2]), pen=None)
        self.plot.addItem(bg)

    def pie_chart(self, labels: list[str], values: list[float]) -> None:
        """Simple pie drawn on the plot using QGraphicsEllipseItem sectors."""
        self.clear()
        self.plot.hideAxis("left"); self.plot.hideAxis("bottom"); self.plot.showGrid(x=False, y=False)
        if not values:
            return
        total = sum(values) or 1
        radius = 1.0
        start_angle = 0
        for i, (label, val) in enumerate(zip(labels, values)):
            span = 360.0 * val / total
            path = pg.QtGui.QPainterPath()
            path.moveTo(0, 0)
            path.arcTo(-radius, -radius, 2 * radius, 2 * radius, start_angle, span)
            path.closeSubpath()
            item = pg.QtWidgets.QGraphicsPathItem(path)
            item.setBrush(QColor(PALETTE[i % len(PALETTE)]))
            item.setPen(pg.mkPen(color=(20, 20, 30), width=1))
            self.plot.addItem(item)

            # Label
            mid_angle = math.radians(start_angle + span / 2)
            lx = math.cos(mid_angle) * radius * 1.25
            ly = math.sin(mid_angle) * radius * 1.25
            text = pg.TextItem(f"{label}: {val:,.0f}", color=PALETTE[i % len(PALETTE)],
                               anchor=(0.5, 0.5))
            text.setPos(lx, ly)
            self.plot.addItem(text)
            start_angle += span
        self.plot.setRange(xRange=(-1.8, 1.8), yRange=(-1.5, 1.5))
        self.plot.setAspectLocked(True)
