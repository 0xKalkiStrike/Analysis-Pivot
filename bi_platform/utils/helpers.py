"""Small utilities used across the app."""
from __future__ import annotations

import time
from contextlib import contextmanager


def format_bytes(n: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    v = float(n)
    for u in units:
        if v < 1024:
            return f"{v:.1f} {u}"
        v /= 1024
    return f"{v:.1f} PB"


def format_number(n: int | float) -> str:
    if isinstance(n, float):
        return f"{n:,.2f}"
    return f"{n:,}"


@contextmanager
def timing(name: str = "op"):
    t0 = time.perf_counter()
    yield lambda: time.perf_counter() - t0
