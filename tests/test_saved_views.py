from bi_platform.services import SavedView


def test_saved_view_defaults_and_roundtrip():
    v = SavedView(name="View 1", tab="pivot", dataset="customers")
    d = v.to_dict()
    v2 = SavedView.from_dict(d)
    assert v2.name == "View 1"
    assert v2.tab == "pivot"
    assert v2.dataset == "customers"


def test_saved_view_ignores_unknown_fields():
    v = SavedView.from_dict({"name": "x", "tab": "data", "unknown_field": 42})
    assert v.name == "x"
    assert v.tab == "data"


def test_saved_view_pivot_state_roundtrip():
    v = SavedView(name="p", tab="pivot",
                  pivot_rows=["region"], pivot_cols=["product"],
                  pivot_value="amount", pivot_agg="sum")
    d = v.to_dict()
    v2 = SavedView.from_dict(d)
    assert v2.pivot_rows == ["region"]
    assert v2.pivot_cols == ["product"]
    assert v2.pivot_value == "amount"
    assert v2.pivot_agg == "sum"
