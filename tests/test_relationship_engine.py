import polars as pl

from bi_platform.engine import RelationshipEngine
from bi_platform.models import Dataset


def _customers() -> Dataset:
    return Dataset(name="customers", df=pl.DataFrame({
        "customer_id": [f"C{i}" for i in range(20)],
        "name": [f"Cust {i}" for i in range(20)],
    }))


def _orders() -> Dataset:
    return Dataset(name="orders", df=pl.DataFrame({
        "order_id": [f"O{i}" for i in range(30)],
        "customer_id": [f"C{i % 20}" for i in range(30)],
        "amount": [i * 10 for i in range(30)],
    }))


def _unrelated() -> Dataset:
    return Dataset(name="products", df=pl.DataFrame({
        "sku": [f"S{i}" for i in range(15)],
        "name": [f"Product {i}" for i in range(15)],
    }))


def test_discover_finds_customer_orders_link():
    ds = {"customers": _customers(), "orders": _orders(), "products": _unrelated()}
    rels = RelationshipEngine(min_overlap=0.5, min_shared=5).discover(ds)
    assert any(r.left_column == "customer_id" or r.right_column == "customer_id" for r in rels)


def test_no_relationship_when_no_overlap():
    ds = {"customers": _customers(), "products": _unrelated()}
    rels = RelationshipEngine().discover(ds)
    assert rels == []


def test_cardinality_N_to_1():
    ds = {"customers": _customers(), "orders": _orders()}
    rels = RelationshipEngine(min_overlap=0.5, min_shared=5).discover(ds)
    # customers.customer_id (20 unique, all appear in orders) → left overlap high (1:1 or N:1 depending on order)
    assert rels
    top = rels[0]
    assert top.cardinality in {"1:1", "N:1", "1:N"}
    assert top.confidence >= 60


def test_names_compatible_edge_cases():
    e = RelationshipEngine()
    assert e._names_compatible("customer_id", "customer")
    assert e._names_compatible("SKU", "sku")
    assert not e._names_compatible("customer", "product")
