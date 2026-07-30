"""Analytics: dashboard KPIs + column profiling."""
from __future__ import annotations

from typing import Any

import polars as pl

from ..core.logger import get_logger
from ..models import AnalyticsSummary, Dataset

log = get_logger(__name__)


class AnalyticsEngine:
    def summarise(self, datasets: list[Dataset]) -> AnalyticsSummary:
        s = AnalyticsSummary()
        if not datasets:
            return s

        files = {d.source.file_path for d in datasets if d.source}
        s.total_files = len(files)
        s.total_sheets = sum(1 for d in datasets if d.source)
        s.total_rows = sum(d.rows for d in datasets)

        # Uniqueness (using row hash across all cols)
        unique_total = 0
        for d in datasets:
            if d.rows == 0:
                continue
            try:
                unique_total += d.df.unique().height
            except Exception:  # pragma: no cover
                unique_total += d.rows
        s.unique_rows = unique_total
        s.duplicate_rows = max(0, s.total_rows - s.unique_rows)

        # Missing values
        missing = 0
        cols = 0
        largest = ("", 0)
        for d in datasets:
            cols += d.cols
            for c in d.columns:
                missing += d.df[c].null_count()
            if d.source and d.source.file_size > largest[1]:
                largest = (d.source.file_path, d.source.file_size)
        s.missing_values = missing
        s.columns_profiled = cols
        s.largest_file = largest[0]

        total_cells = max(1, sum(d.rows * max(1, d.cols) for d in datasets))
        s.data_quality_score = round(100.0 - (100.0 * missing / total_cells), 2)
        s.validation_score = round(100.0 - (100.0 * s.duplicate_rows / max(1, s.total_rows)), 2)
        return s

    def profile_column(self, dataset: Dataset, column: str) -> dict[str, Any]:
        if column not in dataset.df.columns:
            return {}
        col = dataset.df[column]
        prof: dict[str, Any] = {
            "column": column, "dtype": str(col.dtype),
            "count": col.len(), "nulls": col.null_count(),
            "unique": col.n_unique(),
        }
        if col.dtype in (pl.Int64, pl.Int32, pl.Float64, pl.Float32):
            prof.update({
                "min": col.min(), "max": col.max(),
                "mean": float(col.mean() or 0), "median": col.median(),
                "std": float(col.std() or 0),
            })
        elif col.dtype == pl.Utf8:
            vc = col.value_counts(sort=True).head(10)
            prof["top_values"] = vc.to_dicts()
        return prof

    def top_values(self, dataset: Dataset, column: str, n: int = 10) -> list[dict[str, Any]]:
        if column not in dataset.df.columns:
            return []
        return dataset.df[column].value_counts(sort=True).head(n).to_dicts()
