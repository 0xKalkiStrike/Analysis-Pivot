"""Polars ↔ Qt table model. Handles large frames via lazy pagination."""
from __future__ import annotations

from typing import Any

import polars as pl
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


class PolarsTableModel(QAbstractTableModel):
    """Read-only virtualised Qt model over a Polars DataFrame."""

    PAGE = 5000

    def __init__(self, df: pl.DataFrame | None = None) -> None:
        super().__init__()
        self._df = df if df is not None else pl.DataFrame()
        self._visible_rows = min(self.PAGE, self._df.height)

    def set_dataframe(self, df: pl.DataFrame) -> None:
        self.beginResetModel()
        self._df = df
        self._visible_rows = min(self.PAGE, df.height)
        self.endResetModel()

    def dataframe(self) -> pl.DataFrame:
        return self._df

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return self._visible_rows

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return self._df.width

    def canFetchMore(self, parent: QModelIndex) -> bool:  # noqa: N802
        return self._visible_rows < self._df.height

    def fetchMore(self, parent: QModelIndex) -> None:  # noqa: N802
        remaining = self._df.height - self._visible_rows
        to_add = min(self.PAGE, remaining)
        if to_add <= 0:
            return
        self.beginInsertRows(QModelIndex(), self._visible_rows, self._visible_rows + to_add - 1)
        self._visible_rows += to_add
        self.endInsertRows()

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid() or role not in (Qt.DisplayRole, Qt.ToolTipRole):
            return None
        try:
            v = self._df[index.row(), index.column()]
        except Exception:
            return None
        if v is None:
            return "—"
        s = str(v)
        return s if len(s) <= 200 else s[:200] + "…"

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:  # noqa: N802
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self._df.columns[section] if section < self._df.width else ""
        return str(section + 1)
