"""Command Palette — fuzzy-search everything (Ctrl+P)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from rapidfuzz import fuzz
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (QAbstractItemView, QDialog, QLineEdit,
                                QListWidget, QListWidgetItem, QVBoxLayout,
                                QLabel)


@dataclass
class Command:
    """A single palette entry."""
    label: str
    action: Callable[[], None]
    category: str = "Action"     # Action | Dataset | View | File
    shortcut: str = ""
    hint: str = ""

    @property
    def searchable(self) -> str:
        return f"{self.label} {self.category} {self.hint}".lower()


class CommandPalette(QDialog):
    """Modeless-friendly dialog that appears on Ctrl+P."""

    executed = Signal(Command)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setModal(True)
        self.setFixedWidth(640)
        self.setMinimumHeight(420)
        self._commands: list[Command] = []
        self._filtered: list[Command] = []

        v = QVBoxLayout(self); v.setContentsMargins(2, 2, 2, 2); v.setSpacing(0)
        wrap = QVBoxLayout(); wrap.setContentsMargins(16, 16, 16, 16); wrap.setSpacing(10)

        title = QLabel("Command Palette")
        title.setStyleSheet("color:#8b8ba8; font-size:11px; letter-spacing:1px; text-transform:uppercase;")
        wrap.addWidget(title)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Type to search actions, files, views, datasets…")
        self.input.textChanged.connect(self._refresh)
        wrap.addWidget(self.input)

        self.list = QListWidget()
        self.list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list.itemActivated.connect(lambda _it: self._execute_current())
        self.list.setStyleSheet(
            "QListWidget { background:#12121c; border:1px solid #2b2b45; border-radius:10px; }"
            "QListWidget::item { padding:10px 12px; border-bottom:1px solid #1c1c2c; }"
            "QListWidget::item:selected { background:#3a2f8a; color:white; border-radius:4px; }"
        )
        wrap.addWidget(self.list, 1)

        hint = QLabel("↑↓ navigate · Enter to run · Esc to close")
        hint.setStyleSheet("color:#6a6a80; font-size:11px;")
        wrap.addWidget(hint)

        container = QLabel()
        container.setStyleSheet("background:#0f0f14; border:1px solid #2b2b45; border-radius:14px;")
        container.setLayout(wrap)
        v.addWidget(container)

        self.input.installEventFilter(self)

    # ------------------------------------------------------------------ api
    def set_commands(self, commands: list[Command]) -> None:
        self._commands = list(commands)
        self._refresh()

    def open(self) -> None:
        self.input.setText("")
        self._refresh()
        self.input.setFocus()
        parent = self.parent()
        if parent is not None:
            geo = parent.geometry()
            x = geo.x() + (geo.width() - self.width()) // 2
            y = geo.y() + 120
            self.move(x, y)
        self.show()

    # ------------------------------------------------------------------ internals
    def _refresh(self) -> None:
        q = self.input.text().strip().lower()
        if not q:
            self._filtered = self._commands[:60]
        else:
            scored = [(fuzz.WRatio(q, c.searchable), c) for c in self._commands]
            scored = [x for x in scored if x[0] > 40]
            scored.sort(key=lambda x: x[0], reverse=True)
            self._filtered = [c for _, c in scored[:60]]

        self.list.clear()
        for c in self._filtered:
            it = QListWidgetItem()
            it.setText(f"  {c.category:10}  {c.label}"
                       + (f"    ⌘ {c.shortcut}" if c.shortcut else "")
                       + (f"    — {c.hint}" if c.hint else ""))
            it.setData(Qt.UserRole, c)
            self.list.addItem(it)
        if self.list.count():
            self.list.setCurrentRow(0)

    def _execute_current(self) -> None:
        it = self.list.currentItem()
        if not it:
            return
        cmd: Command = it.data(Qt.UserRole)
        self.hide()
        self.executed.emit(cmd)
        try:
            cmd.action()
        except Exception as e:  # pragma: no cover
            from ...core.logger import get_logger
            get_logger(__name__).error(f"Command '{cmd.label}' failed: {e}")

    # ------------------------------------------------------------------ input hooks
    def eventFilter(self, obj, event):  # noqa: N802
        if obj is self.input and isinstance(event, QKeyEvent) and event.type() == QKeyEvent.KeyPress:
            key = event.key()
            if key == Qt.Key_Down:
                self.list.setCurrentRow(min(self.list.currentRow() + 1, self.list.count() - 1))
                return True
            if key == Qt.Key_Up:
                self.list.setCurrentRow(max(self.list.currentRow() - 1, 0))
                return True
            if key in (Qt.Key_Return, Qt.Key_Enter):
                self._execute_current()
                return True
            if key == Qt.Key_Escape:
                self.hide()
                return True
        return super().eventFilter(obj, event)
