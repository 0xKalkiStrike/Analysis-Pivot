"""Pivot table engine — Excel/Power BI style cross-tabs with Polars."""
from __future__ import annotations

from typing import Iterable

import polars as pl

from ..models import Dataset

AGGS = {
    "sum": "sum",
    "mean": "mean",
    "avg": "mean",
    "count": "len",
    "count_distinct": "n_unique",
    "min": "min",
    "max": "max",
    "median": "median",
    "std": "std",
}


class PivotEngine:
    """Build pivot tables from a Dataset."""

    def pivot(
        self,
        dataset: Dataset,
        rows: list[str],
        columns: list[str] | None,
        values: str | None,
        aggregate: str = "sum",
    ) -> pl.DataFrame:
        if not rows:
            raise ValueError("At least one 'rows' field is required")
        agg = AGGS.get(aggregate.lower())
        if agg is None:
            raise ValueError(f"Unknown aggregate '{aggregate}'. Use one of {list(AGGS)}")

        df = dataset.df

        # Count table (no values column) → count of rows in each cell.
        if values is None:
            df = df.with_columns(pl.lit(1).alias("__count__"))
            values = "__count__"
            if aggregate.lower() not in ("count", "sum"):
                aggregate = "count"
            agg = "sum" if aggregate.lower() == "count" else agg

        if columns:
            # Multi-column pivot: reduce columns list to a single composite key.
            col_expr = pl.concat_str([pl.col(c).cast(pl.Utf8) for c in columns], separator=" · ")
            df = df.with_columns(col_expr.alias("__col__"))
            result = df.pivot(
                index=rows, on="__col__", values=values, aggregate_function=agg,
            )
        else:
            result = df.group_by(rows).agg(getattr(pl.col(values), agg)().alias(f"{aggregate}({values})"))

        # Sort rows for deterministic output
        try:
            result = result.sort(rows)
        except Exception:
            pass
        return result
