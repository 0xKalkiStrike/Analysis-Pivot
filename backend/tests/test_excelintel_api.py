"""Backend API tests for ExcelIntel preview."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://pivot-powerhouse.preview.emergentagent.com").rstrip("/")


@pytest.fixture
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# --- root
def test_root(client):
    r = client.get(f"{BASE_URL}/api/")
    assert r.status_code == 200
    d = r.json()
    assert d["app"] == "ExcelIntel"
    assert d["status"] == "ok"
    assert "version" in d


# --- samples
def test_samples(client):
    r = client.get(f"{BASE_URL}/api/samples")
    assert r.status_code == 200
    d = r.json()
    assert d["count"] >= 5
    names = [f["name"] for f in d["files"]]
    for expected in ["customers.csv", "customers_region_a.xlsx", "customers_region_b.xlsx",
                     "invoices_2024.xlsx", "products_catalog.xlsx"]:
        assert expected in names, f"missing {expected}"


# --- summary
def test_summary(client):
    r = client.get(f"{BASE_URL}/api/summary")
    assert r.status_code == 200
    d = r.json()
    kpis = d["kpis"]
    assert kpis["files"] >= 1
    assert kpis["sheets"] >= 1
    assert kpis["total_rows"] > 0
    assert "data_quality_score" in kpis
    assert "validation_score" in kpis
    assert isinstance(d["per_sheet"], list) and len(d["per_sheet"]) >= 1
    assert isinstance(d["quality_composition"], list)


# --- duplicates
def test_duplicates(client):
    r = client.get(f"{BASE_URL}/api/duplicates", params={"file": "customers_region_a.xlsx"})
    assert r.status_code == 200
    d = r.json()
    assert "total_groups" in d
    assert "groups" in d
    assert d["threshold"] == 88.0


def test_duplicates_threshold(client):
    r = client.get(f"{BASE_URL}/api/duplicates",
                   params={"file": "customers_region_a.xlsx", "threshold": 75})
    assert r.status_code == 200
    assert r.json()["threshold"] == 75.0


# --- relationships
def test_relationships(client):
    r = client.get(f"{BASE_URL}/api/relationships")
    assert r.status_code == 200
    d = r.json()
    assert "relationships" in d
    assert "datasets" in d
    # Should discover at least 1 relationship between customer datasets
    assert len(d["relationships"]) >= 1


# --- screenshots
def test_screenshot(client):
    r = client.get(f"{BASE_URL}/api/screenshots/screenshot_dashboard.png")
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("image/")


def test_screenshot_404(client):
    r = client.get(f"{BASE_URL}/api/screenshots/does_not_exist.png")
    assert r.status_code == 404


# --- dataset preview
def test_dataset(client):
    r = client.get(f"{BASE_URL}/api/dataset", params={"file": "customers_region_a.xlsx"})
    assert r.status_code == 200
    d = r.json()
    assert d["rows"] > 0
    assert isinstance(d["columns"], list) and len(d["columns"]) > 0
    assert isinstance(d["preview"], list)
