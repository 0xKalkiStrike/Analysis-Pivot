"""Shared test fixtures."""
from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from bi_platform.models import Dataset


@pytest.fixture
def customers_df() -> pl.DataFrame:
    return pl.DataFrame({
        "customer_id": ["C1", "C2", "C3", "C4", "C5"],
        "name": ["Alice Smith", "alice smith", "  Alice  Smith ", "Bob Jones", "Carol Ray"],
        "email": ["alice@x.com", "ALICE@x.com", "alice@x.com", "bob@y.org", "carol@z.io"],
        "phone": ["1234567890", "+1 234-567-890", "1234567890", "9876543210", "555-1234"],
    })


@pytest.fixture
def customers_dataset(customers_df) -> Dataset:
    return Dataset(name="test :: customers", df=customers_df)


@pytest.fixture
def orders_df() -> pl.DataFrame:
    return pl.DataFrame({
        "customer_id": ["C1", "C2", "C4", "C6"],
        "total": [100.0, 200.0, 300.0, 400.0],
        "status": ["paid", "paid", "pending", "paid"],
    })


@pytest.fixture
def orders_dataset(orders_df) -> Dataset:
    return Dataset(name="test :: orders", df=orders_df)


@pytest.fixture
def sample_files_dir() -> Path:
    d = Path(__file__).resolve().parent.parent / "samples"
    if not d.exists() or not list(d.glob("*.xlsx")):
        pytest.skip("samples not generated; run scripts/generate_samples.py")
    return d
