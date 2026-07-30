"""Saved Views panel — persist and restore workspace snapshots per project."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QAbstractItemView, QHBoxLayout, QInputDialog,
                                QLabel, QListWidget, QListWidgetItem,
                                QMessageBox, QPushButton, QVBoxLayout, QWidget)

from ...services import SavedView


class SavedViewsWidget(QWidget):
    save_current_requested = Signal(str)     # emits view name
    apply_view_requested = Signal(SavedView)  # emits chosen view
    views_changed = Signal(list)              # emits current list[SavedView] for persistence

    def __init__(self) -> None:
        super().__init__()
        self._views: list[SavedView] = []

        v = QVBoxLayout(self); v.setContentsMargins(14, 14, 14, 14); v.setSpacing(10)

        title = QLabel("Saved Views")
        title.setStyleSheet("color:#c9b6ff; font-weight:600; font-size:14px;")
        v.addWidget(title)

        self.list = QListWidget()
        self.list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list.itemDoubleClicked.connect(self._on_apply)
        v.addWidget(self.list, 1)

        actions = QHBoxLayout(); actions.setSpacing(6)
        self.btn_save = QPushButton("Save Current")
        self.btn_apply = QPushButton("Apply"); self.btn_apply.setProperty("flat", True)
        self.btn_delete = QPushButton("Delete"); self.btn_delete.setProperty("flat", True)
        self.btn_save.clicked.connect(self._on_save)
        self.btn_apply.clicked.connect(self._on_apply)
        self.btn_delete.clicked.connect(self._on_delete)
        actions.addWidget(self.btn_save); actions.addWidget(self.btn_apply); actions.addWidget(self.btn_delete)
        v.addLayout(actions)

        hint = QLabel("Double-click a view to apply it.\nViews save to the current project file.")
        hint.setStyleSheet("color:#6a6a80; font-size:11px;")
        hint.setWordWrap(True)
        v.addWidget(hint)

    # ------------------------------------------------------------------ api
    def set_views(self, views: list[SavedView]) -> None:
        self._views = list(views)
        self._refresh()

    def views(self) -> list[SavedView]:
        return list(self._views)

    def add(self, view: SavedView) -> None:
        # Replace if same name
        self._views = [v for v in self._views if v.name != view.name] + [view]
        self._refresh()
        self.views_changed.emit(self._views)

    def _refresh(self) -> None:
        self.list.clear()
        for v in sorted(self._views, key=lambda x: x.name.lower()):
            it = QListWidgetItem(v.name)
            it.setToolTip(f"Tab: {v.tab}\nDataset: {v.dataset or '(none)'}\nCreated: {v.created_at}")
            it.setData(Qt.UserRole, v)
            self.list.addItem(it)

    # ------------------------------------------------------------------ handlers
    def _on_save(self) -> None:
        name, ok = QInputDialog.getText(self, "Save View", "View name:")
        if not ok or not name.strip():
            return
        self.save_current_requested.emit(name.strip())

    def _on_apply(self) -> None:
        it = self.list.currentItem()
        if not it:
            QMessageBox.information(self, "Saved Views", "Pick a view first."); return
        view: SavedView = it.data(Qt.UserRole)
        self.apply_view_requested.emit(view)

    def _on_delete(self) -> None:
        it = self.list.currentItem()
        if not it:
            return
        view: SavedView = it.data(Qt.UserRole)
        self._views = [v for v in self._views if v.name != view.name]
        self._refresh()
        self.views_changed.emit(self._views)
