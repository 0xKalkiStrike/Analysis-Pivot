"""File explorer sidebar — folder tree + loaded sheets list."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QAbstractItemView, QFileDialog, QHBoxLayout,
                                QLabel, QLineEdit, QListWidget, QListWidgetItem,
                                QPushButton, QVBoxLayout, QWidget)

from ...core.constants import SUPPORTED_ALL
from ...utils import format_bytes


class FileExplorerWidget(QWidget):
    file_activated = Signal(str, str)  # path, sheet
    open_folder_requested = Signal(str)
    open_files_requested = Signal(list)

    def __init__(self) -> None:
        super().__init__()
        v = QVBoxLayout(self); v.setContentsMargins(14, 14, 14, 14); v.setSpacing(10)

        title = QLabel("Data Sources")
        title.setStyleSheet("color:#c9b6ff; font-weight:600; font-size:14px;")
        v.addWidget(title)

        # Actions
        actions = QHBoxLayout(); actions.setSpacing(6)
        self.btn_files = QPushButton("Open Files")
        self.btn_folder = QPushButton("Open Folder")
        self.btn_folder.setProperty("flat", True)
        for b in (self.btn_files, self.btn_folder):
            b.setCursor(Qt.PointingHandCursor)
        self.btn_files.clicked.connect(self._on_open_files)
        self.btn_folder.clicked.connect(self._on_open_folder)
        actions.addWidget(self.btn_files); actions.addWidget(self.btn_folder)
        v.addLayout(actions)

        # Search
        self.search = QLineEdit()
        self.search.setPlaceholderText("Filter loaded sheets…")
        self.search.textChanged.connect(self._on_filter)
        v.addWidget(self.search)

        # Loaded sheets list
        self.list = QListWidget()
        self.list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list.itemDoubleClicked.connect(self._on_item_activated)
        self.list.itemActivated.connect(self._on_item_activated)
        v.addWidget(self.list, 1)

        self.hint = QLabel("Drop files anywhere in the window.\nSupported: xlsx, xls, xlsm, xlsb, csv, tsv")
        self.hint.setStyleSheet("color:#6a6a80; font-size:11px;")
        self.hint.setWordWrap(True)
        v.addWidget(self.hint)

    def add_dataset(self, path: str, sheet: str, rows: int, cols: int, size: int) -> None:
        item = QListWidgetItem(f"{Path(path).name}  ›  {sheet}")
        item.setData(Qt.UserRole, (path, sheet))
        item.setToolTip(f"{path}\n{sheet}\n{rows:,} rows × {cols} cols\n{format_bytes(size)}")
        self.list.addItem(item)

    def clear(self) -> None:
        self.list.clear()

    def _on_open_files(self) -> None:
        exts = " ".join(f"*{e}" for e in SUPPORTED_ALL)
        paths, _ = QFileDialog.getOpenFileNames(self, "Open data files", "", f"Spreadsheets ({exts})")
        if paths:
            self.open_files_requested.emit(paths)

    def _on_open_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Open folder")
        if folder:
            self.open_folder_requested.emit(folder)

    def _on_item_activated(self, item: QListWidgetItem) -> None:
        path, sheet = item.data(Qt.UserRole)
        self.file_activated.emit(path, sheet)

    def _on_filter(self, text: str) -> None:
        text = text.lower()
        for i in range(self.list.count()):
            it = self.list.item(i)
            it.setHidden(text not in it.text().lower())
