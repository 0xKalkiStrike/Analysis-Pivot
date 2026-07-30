"""File watcher — emits signals when source files change on disk."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher, QObject, QTimer, Signal

from ..core.logger import get_logger

log = get_logger(__name__)


class FileWatcher(QObject):
    """Debounced wrapper around QFileSystemWatcher.

    Emits ``file_changed(path)`` at most once per debounce window per file.
    """

    file_changed = Signal(str)

    def __init__(self, debounce_ms: int = 400, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._watcher = QFileSystemWatcher(self)
        self._watcher.fileChanged.connect(self._on_changed)
        self._pending: dict[str, QTimer] = {}
        self._debounce = debounce_ms
        self._enabled = True

    # -------------------------------------------------- api
    def add_paths(self, paths: list[str]) -> None:
        existing = set(self._watcher.files())
        to_add = [p for p in paths if p and Path(p).exists() and p not in existing]
        if to_add:
            self._watcher.addPaths(to_add)
            log.info(f"Watching {len(to_add)} file(s)")

    def remove_paths(self, paths: list[str]) -> None:
        if paths:
            self._watcher.removePaths(paths)

    def clear(self) -> None:
        files = self._watcher.files()
        if files:
            self._watcher.removePaths(files)

    def files(self) -> list[str]:
        return list(self._watcher.files())

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    def is_enabled(self) -> bool:
        return self._enabled

    # -------------------------------------------------- internals
    def _on_changed(self, path: str) -> None:
        if not self._enabled:
            return
        # Some editors atomically replace files (write-then-rename), which drops
        # them from the watcher. Re-add if missing but still on disk.
        if Path(path).exists() and path not in self._watcher.files():
            self._watcher.addPath(path)

        if path in self._pending:
            self._pending[path].stop()
        timer = QTimer(self); timer.setSingleShot(True)
        timer.timeout.connect(lambda p=path: self._fire(p))
        self._pending[path] = timer
        timer.start(self._debounce)

    def _fire(self, path: str) -> None:
        self._pending.pop(path, None)
        log.info(f"File changed: {path}")
        self.file_changed.emit(path)
