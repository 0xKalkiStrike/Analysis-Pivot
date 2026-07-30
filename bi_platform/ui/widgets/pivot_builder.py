"""Pivot Builder — drag-friendly, drop-down driven cross-tab builder."""
from __future__ import annotations

import polars as pl
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QFileDialog,
                                QHBoxLayout, QHeaderView, QLabel, QListWidget,
                                QListWidgetItem, QMessageBox, QPushButton,
                                QSizePolicy, QTableView, QVBoxLayout, QWidget)

from ...engine import PIVOT_AGGS, PivotEngine
from ...export import ExcelExporter
from ...models import Dataset
from .table_model import PolarsTableModel


class _DropList(QListWidget):
    """A QListWidget that accepts columns dragged from the fields list."""
    changed = Signal()

    def __init__(self, placeholder: str) -> None:
        super().__init__()
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setMinimumHeight(70)
        self._placeholder = placeholder
        self.setStyleSheet(
            "QListWidget { background:#12121c; border:1px dashed #3a3a55;"
            " border-radius:10px; padding:6px; color:#e6e6f0; }"
            "QListWidget::item { padding:6px 10px; margin:2px; background:#1e1e30;"
            " border-radius:6px; }"
        )

    def dropEvent(self, event) -> None:  # noqa: N802
        super().dropEvent(event)
        self.changed.emit()

    def items_text(self) -> list[str]:
        return [self.item(i).text() for i in range(self.count())]

    def keyPressEvent(self, e) -> None:  # noqa: N802
        if e.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            for it in self.selectedItems():
                self.takeItem(self.row(it))
            self.changed.emit()
            return
        super().keyPressEvent(e)


class PivotBuilderWidget(QWidget):
    drill_through_requested = Signal(dict)  # {row_filters, column_filters, value_column, aggregate}

    def __init__(self) -> None:
        super().__init__()
        self.dataset: Dataset | None = None
        self._last_config: dict = {}

        outer = QVBoxLayout(self); outer.setContentsMargins(16, 16, 16, 16); outer.setSpacing(12)

        title = QLabel("Pivot Builder")
        title.setStyleSheet("font-size:18px; font-weight:600; color:#c9b6ff;")
        outer.addWidget(title)

        # top row: dataset picker + aggregate + value + actions
        row = QHBoxLayout(); row.setSpacing(8)
        row.addWidget(QLabel("Dataset:"))
        self.dataset_combo = QComboBox(); self.dataset_combo.setMinimumWidth(200)
        self.dataset_combo.currentTextChanged.connect(self._on_dataset_changed)
        row.addWidget(self.dataset_combo)

        row.addWidget(QLabel("Values:"))
        self.value_combo = QComboBox(); self.value_combo.setMinimumWidth(140)
        row.addWidget(self.value_combo)

        row.addWidget(QLabel("Aggregate:"))
        self.agg_combo = QComboBox()
        self.agg_combo.addItems(sorted(set(PIVOT_AGGS.keys())))
        self.agg_combo.setCurrentText("sum")
        row.addWidget(self.agg_combo)

        row.addStretch(1)
        self.btn_build = QPushButton("Build Pivot"); self.btn_build.clicked.connect(self.build)
        self.btn_export = QPushButton("Export…"); self.btn_export.setProperty("flat", True)
        self.btn_export.clicked.connect(self.export)
        row.addWidget(self.btn_build); row.addWidget(self.btn_export)
        outer.addLayout(row)

        # fields + drop zones
        cols = QHBoxLayout(); cols.setSpacing(12)

        fields_col = QVBoxLayout(); fields_col.setSpacing(6)
        fields_col.addWidget(QLabel("Fields"))
        self.fields_list = QListWidget()
        self.fields_list.setDragEnabled(True)
        self.fields_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.fields_list.setDragDropMode(QAbstractItemView.DragOnly)
        self.fields_list.setStyleSheet(
            "QListWidget { background:#12121c; border:1px solid #2b2b45; border-radius:10px; }"
            "QListWidget::item { padding:6px 10px; }"
            "QListWidget::item:hover { background:#1e1e30; }"
        )
        fields_col.addWidget(self.fields_list, 1)

        rows_col = QVBoxLayout(); rows_col.setSpacing(6)
        rows_col.addWidget(QLabel("Rows  (drag fields here)"))
        self.rows_list = _DropList("Rows")
        rows_col.addWidget(self.rows_list, 1)

        cols_col = QVBoxLayout(); cols_col.setSpacing(6)
        cols_col.addWidget(QLabel("Columns  (drag fields here)"))
        self.cols_list = _DropList("Columns")
        cols_col.addWidget(self.cols_list, 1)

        for c in (fields_col, rows_col, cols_col):
            w = QWidget(); w.setLayout(c); w.setMinimumWidth(180)
            w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            cols.addWidget(w, 1)
        outer.addLayout(cols)

        # result
        outer.addWidget(QLabel("Result  ·  double-click a cell to drill-through"))
        self.model = PolarsTableModel()
        self.table = QTableView(); self.table.setModel(self.model)
        self.table.setAlternatingRowColors(True); self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.doubleClicked.connect(self._on_double_click)
        outer.addWidget(self.table, 2)

    # ------------------------------------------------------------------ api
    def set_datasets(self, datasets: dict[str, Dataset], select: str | None = None) -> None:
        self._datasets_ref = datasets
        current = select or self.dataset_combo.currentText()
        self.dataset_combo.blockSignals(True)
        self.dataset_combo.clear(); self.dataset_combo.addItems(list(datasets.keys()))
        if current and current in datasets:
            self.dataset_combo.setCurrentText(current)
        self.dataset_combo.blockSignals(False)
        self._on_dataset_changed(self.dataset_combo.currentText())

    def _on_dataset_changed(self, name: str) -> None:
        self.dataset = self._datasets_ref.get(name) if hasattr(self, "_datasets_ref") else None
        self.fields_list.clear(); self.rows_list.clear(); self.cols_list.clear()
        self.value_combo.clear(); self.value_combo.addItem("(count of rows)")
        if not self.dataset:
            return
        for c in self.dataset.columns:
            self.fields_list.addItem(QListWidgetItem(c))
            self.value_combo.addItem(c)

    def build(self) -> None:
        if not self.dataset:
            QMessageBox.information(self, "Pivot", "Load a dataset first."); return
        rows = self.rows_list.items_text()
        cols = self.cols_list.items_text() or None
        val_text = self.value_combo.currentText()
        value = None if val_text.startswith("(count") else val_text
        agg = self.agg_combo.currentText()
        if not rows:
            QMessageBox.information(self, "Pivot", "Drag at least one field to the Rows box."); return
        try:
            result = PivotEngine().pivot(self.dataset, rows=rows, columns=cols, values=value, aggregate=agg)
        except Exception as e:
            QMessageBox.critical(self, "Pivot error", str(e)); return
        self.model.set_dataframe(result)
        self._last_config = {
            "rows": rows, "cols": cols or [],
            "value_column": value, "aggregate": agg,
        }

    def export(self) -> None:
        df = self.model.dataframe()
        if df is None or df.is_empty():
            QMessageBox.information(self, "Export", "Build a pivot first."); return
        p, _ = QFileDialog.getSaveFileName(self, "Export pivot", "pivot.xlsx", "Excel (*.xlsx)")
        if not p: return
        from ...models import Dataset as DS
        ExcelExporter().export_dataset(DS(name="Pivot", df=df), p)
        QMessageBox.information(self, "Export", f"Written {p}")

    # ------------------------------------------------------------------ drill-through
    def _on_double_click(self, index) -> None:
        if not self.dataset or not self._last_config:
            return
        df = self.model.dataframe()
        if df is None or df.is_empty():
            return
        row_i, col_i = index.row(), index.column()
        if row_i < 0 or col_i < 0 or row_i >= df.height or col_i >= df.width:
            return

        rows = self._last_config.get("rows", [])
        cols = self._last_config.get("cols", [])
        result_columns = df.columns
        clicked_column_name = result_columns[col_i]

        # Row filters — pick pivot row keys
        row_filters: dict = {}
        for k in rows:
            if k in df.columns:
                row_filters[k] = df[k][row_i]

        # Column filters — reconstruct if user clicked a data cell (not a row-key col)
        column_filters: dict = {}
        if cols and clicked_column_name not in rows:
            # The result column name is the concatenated column-key values (" · " separator)
            parts = str(clicked_column_name).split(" · ")
            if len(parts) == len(cols):
                for k, v in zip(cols, parts):
                    column_filters[k] = v

        payload = {
            "row_filters": row_filters,
            "column_filters": column_filters,
            "value_column": self._last_config.get("value_column"),
            "aggregate": self._last_config.get("aggregate", "sum"),
            "dataset": self.dataset,
        }
        self.drill_through_requested.emit(payload)

    # ------------------------------------------------------------------ view state
    def get_state(self) -> dict:
        return {
            "pivot_rows": self.rows_list.items_text(),
            "pivot_cols": self.cols_list.items_text(),
            "pivot_value": self.value_combo.currentText(),
            "pivot_agg": self.agg_combo.currentText(),
        }

    def apply_state(self, state: dict) -> None:
        self.rows_list.clear(); self.cols_list.clear()
        for r in state.get("pivot_rows", []):
            self.rows_list.addItem(QListWidgetItem(r))
        for c in state.get("pivot_cols", []):
            self.cols_list.addItem(QListWidgetItem(c))
        v = state.get("pivot_value")
        if v and self.value_combo.findText(v) >= 0:
            self.value_combo.setCurrentText(v)
        a = state.get("pivot_agg")
        if a and self.agg_combo.findText(a) >= 0:
            self.agg_combo.setCurrentText(a)
