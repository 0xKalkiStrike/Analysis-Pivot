"""Immutable data-transfer models used across the engine layer."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import polars as pl


@dataclass
class SheetInfo:
    file_path: str
    sheet_name: str
    rows: int
    cols: int
    columns: list[str]
    dtypes: dict[str, str]
    file_size: int
    loaded_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def display_name(self) -> str:
        return f"{Path(self.file_path).name} :: {self.sheet_name}"


@dataclass
class Dataset:
    """A named data frame + provenance metadata."""

    name: str
    df: pl.DataFrame
    source: SheetInfo | None = None

    @property
    def rows(self) -> int:
        return self.df.height

    @property
    def cols(self) -> int:
        return self.df.width

    @property
    def columns(self) -> list[str]:
        return self.df.columns


@dataclass
class DuplicateGroup:
    key: str
    rows: list[dict[str, Any]]
    confidence: float
    method: str
    reason: str

    @property
    def size(self) -> int:
        return len(self.rows)


@dataclass
class ValidationIssue:
    row_index: int
    column: str
    value: Any
    severity: str  # error | warning | info
    rule: str
    message: str


@dataclass
class MergeResult:
    dataset: Dataset
    matched: int
    unmatched_left: int
    unmatched_right: int
    conflicts: list[dict[str, Any]]

    @property
    def total(self) -> int:
        return self.dataset.rows


@dataclass
class AnalyticsSummary:
    total_files: int = 0
    total_sheets: int = 0
    total_rows: int = 0
    unique_rows: int = 0
    duplicate_rows: int = 0
    conflicts: int = 0
    missing_values: int = 0
    largest_file: str = ""
    processing_time_sec: float = 0.0
    data_quality_score: float = 100.0
    validation_score: float = 100.0
    columns_profiled: int = 0
