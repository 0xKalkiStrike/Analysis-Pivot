"""DuckDB manager — fast in-process analytics backed by Polars/Arrow."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import polars as pl

try:
    import duckdb
    HAS_DUCKDB = True
except Exception:  # pragma: no cover
    HAS_DUCKDB = False

import sqlite3

from ..core.logger import get_logger

log = get_logger(__name__)


class DBManager:
    """Thin wrapper that prefers DuckDB and falls back to SQLite."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = str(path)
        if HAS_DUCKDB:
            self.backend = "duckdb"
            self.conn = duckdb.connect(self.path)
        else:  # pragma: no cover
            self.backend = "sqlite"
            self.conn = sqlite3.connect(self.path)

    def register(self, name: str, df: pl.DataFrame) -> None:
        if self.backend == "duckdb":
            self.conn.register(name, df.to_arrow())
        else:  # pragma: no cover
            df.to_pandas().to_sql(name, self.conn, if_exists="replace", index=False)

    def sql(self, query: str) -> pl.DataFrame:
        if self.backend == "duckdb":
            res = self.conn.execute(query).arrow()
            return pl.from_arrow(res)
        # sqlite fallback
        import pandas as pd
        return pl.from_pandas(pd.read_sql(query, self.conn))

    def tables(self) -> list[str]:
        if self.backend == "duckdb":
            rows = self.conn.execute("SHOW TABLES").fetchall()
            return [r[0] for r in rows]
        cur = self.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return [r[0] for r in cur.fetchall()]

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass
