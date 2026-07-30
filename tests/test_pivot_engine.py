import polars as pl

from bi_platform.engine import PivotEngine
from bi_platform.models import Dataset


def _sales_dataset() -> Dataset:
    df = pl.DataFrame({
        "region": ["N", "N", "S", "S", "E", "E", "W", "W"],
        "product": ["A", "B", "A", "B", "A", "B", "A", "B"],
        "amount": [100, 200, 150, 250, 300, 350, 400, 450],
    })
    return Dataset(name="sales", df=df)


def test_pivot_sum_by_region():
    ds = _sales_dataset()
    result = PivotEngine().pivot(ds, rows=["region"], columns=None, values="amount", aggregate="sum")
    assert set(result["region"].to_list()) == {"N", "S", "E", "W"}
    # W = 400+450 = 850
    row = result.filter(pl.col("region") == "W").row(0, named=True)
    val_col = [c for c in result.columns if c != "region"][0]
    assert row[val_col] == 850


def test_pivot_cross_tab():
    ds = _sales_dataset()
    result = PivotEngine().pivot(ds, rows=["region"], columns=["product"], values="amount", aggregate="sum")
    assert "A" in result.columns and "B" in result.columns
    assert result.height == 4


def test_pivot_count_of_rows_when_no_value():
    ds = _sales_dataset()
    result = PivotEngine().pivot(ds, rows=["region"], columns=None, values=None, aggregate="count")
    assert result.height == 4


def test_pivot_mean():
    ds = _sales_dataset()
    result = PivotEngine().pivot(ds, rows=["product"], columns=None, values="amount", aggregate="mean")
    assert result.height == 2
