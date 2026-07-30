"""Test drill-through row filtering logic (no UI required)."""
from __future__ import annotations

import polars as pl

from bi_platform.models import Dataset


def _sales() -> Dataset:
    df = pl.DataFrame({
        "region": ["N", "N", "N", "S", "S", "E"],
        "product": ["A", "B", "A", "A", "B", "A"],
        "amount": [10.0, 20.0, 15.0, 30.0, 40.0, 50.0],
    })
    return Dataset(name="sales", df=df)


def _filter(dataset: Dataset, row_filters: dict, column_filters: dict) -> pl.DataFrame:
    """Extracted from DrillThroughDialog._compute_filtered for headless testing."""
    df = dataset.df
    for col, val in {**row_filters, **column_filters}.items():
        if col not in df.columns or val is None:
            continue
        df = df.filter(pl.col(col).cast(pl.Utf8) == str(val))
    return df


def test_drill_through_row_only():
    ds = _sales()
    result = _filter(ds, {"region": "N"}, {})
    assert result.height == 3
    assert set(result["product"].to_list()) == {"A", "B"}


def test_drill_through_row_and_column():
    ds = _sales()
    result = _filter(ds, {"region": "N"}, {"product": "A"})
    assert result.height == 2
    assert all(r == "A" for r in result["product"].to_list())
    assert result["amount"].sum() == 25.0


def test_drill_through_no_matches():
    ds = _sales()
    result = _filter(ds, {"region": "Z"}, {})
    assert result.height == 0


def test_drill_through_multi_key():
    ds = _sales()
    result = _filter(ds, {"region": "S"}, {"product": "B"})
    assert result.height == 1
    assert result["amount"].to_list() == [40.0]
