from bi_platform.engine import MergeEngine


def test_inner_join(customers_dataset, orders_dataset):
    result = MergeEngine().merge(customers_dataset, orders_dataset, on="customer_id", how="inner")
    ids = set(result.dataset.df["customer_id"].to_list())
    assert ids == {"C1", "C2", "C4"}
    assert result.matched == 3


def test_left_join(customers_dataset, orders_dataset):
    result = MergeEngine().merge(customers_dataset, orders_dataset, on="customer_id", how="left")
    assert result.dataset.rows == 5


def test_outer_join(customers_dataset, orders_dataset):
    result = MergeEngine().merge(customers_dataset, orders_dataset, on="customer_id", how="outer")
    assert result.dataset.rows >= 6


def test_resolve_conflicts_keep_left(customers_dataset, orders_dataset):
    # Introduce a shared column with conflicting values
    left = customers_dataset
    right_df = orders_dataset.df.with_columns(orders_dataset.df["customer_id"].alias("customer_id"))
    from bi_platform.models import Dataset
    right = Dataset(name="orders", df=right_df.with_columns(
        __import__("polars").lit("Different Name").alias("name"),
    ))
    engine = MergeEngine()
    result = engine.merge(left, right, on="customer_id", how="inner")
    resolved = engine.resolve_conflicts(result, strategy="keep_left")
    assert "name_right" not in resolved.df.columns
