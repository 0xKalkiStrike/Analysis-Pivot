"""Intelligent merge/join engine with conflict detection."""
from __future__ import annotations

import polars as pl

from ..core.logger import get_logger
from ..models import Dataset, MergeResult

log = get_logger(__name__)

JOIN_MAP = {
    "inner": "inner",
    "left": "left",
    "right": "right",
    "outer": "full",
    "full": "full",
    "cross": "cross",
}


class MergeEngine:
    """Join two datasets and highlight conflicts on non-key columns."""

    def merge(
        self,
        left: Dataset,
        right: Dataset,
        on: list[str] | str,
        how: str = "inner",
        suffix: str = "_right",
    ) -> MergeResult:
        keys = [on] if isinstance(on, str) else list(on)
        for k in keys:
            if k not in left.df.columns or k not in right.df.columns:
                raise ValueError(f"Merge key '{k}' missing in one of the datasets")

        polars_how = JOIN_MAP.get(how.lower())
        if not polars_how:
            raise ValueError(f"Unsupported join type: {how}")

        # Coerce key column types to Utf8 for safe joining
        lc = left.df.with_columns([pl.col(k).cast(pl.Utf8) for k in keys])
        rc = right.df.with_columns([pl.col(k).cast(pl.Utf8) for k in keys])

        joined = lc.join(rc, on=keys, how=polars_how, suffix=suffix)

        # Conflict detection on shared non-key columns
        shared = [c for c in left.df.columns if c in right.df.columns and c not in keys]
        conflicts: list[dict] = []
        for c in shared:
            rcol = f"{c}{suffix}"
            if rcol not in joined.columns:
                continue
            diff_mask = (joined[c].cast(pl.Utf8) != joined[rcol].cast(pl.Utf8)) & \
                        joined[c].is_not_null() & joined[rcol].is_not_null()
            diff_rows = joined.filter(diff_mask)
            if diff_rows.height == 0:
                continue
            for row in diff_rows.iter_rows(named=True):
                conflicts.append({
                    "column": c,
                    "keys": {k: row[k] for k in keys},
                    "left_value": row[c],
                    "right_value": row[rcol],
                })

        matched = joined.filter(
            pl.all_horizontal([pl.col(k).is_not_null() for k in keys])
        ).height

        # Best-effort unmatched counts
        left_keys = lc.select(keys).unique()
        right_keys = rc.select(keys).unique()
        joined_keys = joined.select(keys).unique()
        unmatched_left = max(0, left_keys.height - joined_keys.height) if how in ("right", "inner") else 0
        unmatched_right = max(0, right_keys.height - joined_keys.height) if how in ("left", "inner") else 0

        ds = Dataset(name=f"{left.name} ⋈ {right.name}", df=joined)
        return MergeResult(
            dataset=ds, matched=matched,
            unmatched_left=unmatched_left, unmatched_right=unmatched_right,
            conflicts=conflicts,
        )

    def resolve_conflicts(
        self,
        result: MergeResult,
        strategy: str = "keep_left",  # keep_left | keep_right | prefer_non_null | keep_longest
        suffix: str = "_right",
    ) -> Dataset:
        df = result.dataset.df
        for col in list(df.columns):
            if not col.endswith(suffix):
                continue
            base = col[: -len(suffix)]
            if base not in df.columns:
                continue
            if strategy == "keep_left":
                df = df.drop(col)
            elif strategy == "keep_right":
                df = df.drop(base).rename({col: base})
            elif strategy == "prefer_non_null":
                df = df.with_columns(
                    pl.coalesce([pl.col(base), pl.col(col)]).alias(base)
                ).drop(col)
            elif strategy == "keep_longest":
                df = df.with_columns(
                    pl.when(pl.col(base).cast(pl.Utf8).str.len_chars().fill_null(0)
                            >= pl.col(col).cast(pl.Utf8).str.len_chars().fill_null(0))
                    .then(pl.col(base)).otherwise(pl.col(col)).alias(base)
                ).drop(col)
        return Dataset(name=result.dataset.name, df=df)
