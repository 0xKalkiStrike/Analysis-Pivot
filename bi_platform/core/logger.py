"""Rich-powered structured logging."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from rich.logging import RichHandler

from .config import get_config

_configured = False


def setup_logging(level: int = logging.INFO) -> None:
    global _configured
    if _configured:
        return

    cfg = get_config()
    cfg.ensure_dirs()
    log_file = Path(cfg.logs_dir) / "excelintel.log"

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()

    rich = RichHandler(rich_tracebacks=True, markup=True, show_time=True, show_path=False)
    rich.setLevel(level)
    rich.setFormatter(logging.Formatter("%(message)s"))
    root.addHandler(rich)

    file_h = RotatingFileHandler(log_file, maxBytes=5_000_000, backupCount=3, encoding="utf-8")
    file_h.setLevel(logging.DEBUG)
    file_h.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")
    )
    root.addHandler(file_h)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    if not _configured:
        setup_logging()
    return logging.getLogger(name)
