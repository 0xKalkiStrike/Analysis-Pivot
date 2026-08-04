"""Backend API tests for ExcelIntel preview."""
import pytest
from fastapi.testclient import TestClient
from backend.server import app


@pytest.fixture
def client():
    return TestClient(app)


# --- root
def test_root(client):
    r = client.get("/api/")
    assert r.status_code == 200
    d = r.json()
    assert d["app"] == "ExcelIntel"
    assert d["status"] == "ok"
    assert "version" in d


# --- samples
def test_samples(client):
    r = client.get("/api/samples")
    assert r.status_code == 200
    d = r.json()
    assert d["count"] >= 5
    names = [f["name"] for f in d["files"]]
    for expected in ["customers.csv", "customers_region_a.xlsx", "customers_region_b.xlsx",
                     "invoices_2024.xlsx", "products_catalog.xlsx"]:
        assert expected in names, f"missing {expected}"


# --- summary
def test_summary(client):
    r = client.get("/api/summary")
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
    r = client.get("/api/duplicates", params={"file": "customers_region_a.xlsx"})
    assert r.status_code == 200
    d = r.json()
    assert "total_groups" in d
    assert "groups" in d
    assert d["threshold"] == 88.0


def test_duplicates_threshold(client):
    r = client.get("/api/duplicates",
                   params={"file": "customers_region_a.xlsx", "threshold": 75})
    assert r.status_code == 200
    assert r.json()["threshold"] == 75.0


# --- relationships
def test_relationships(client):
    r = client.get("/api/relationships")
    assert r.status_code == 200
    d = r.json()
    assert "relationships" in d
    assert "datasets" in d
>>>>>>> a4386bf (Initial commit)
    assert len(d["relationships"]) >= 1


# --- screenshots
def test_screenshot(client):
<<<<<<< HEAD
    r = client.get(f"{BASE_URL}/api/screenshots/screenshot_dashboard.png")
=======
    r = client.get("/api/screenshots/screenshot_dashboard.png")
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("image/")


def test_screenshot_404(client):
    r = client.get("/api/screenshots/does_not_exist.png")
    assert r.status_code == 404


# --- dataset preview
def test_dataset(client):
    r = client.get("/api/dataset", params={"file": "customers_region_a.xlsx"})
    assert r.status_code == 200
    d = r.json()
    assert d["rows"] > 0
    assert isinstance(d["columns"], list) and len(d["columns"]) > 0
    assert isinstance(d["preview"], list)
<<<<<<< HEAD
=======


# --- pivot
def test_pivot(client):
    r = client.get("/api/pivot", params={"file": "customers_region_a.xlsx", "rows": "customer_id", "value": "phone", "aggregate": "count"})
    assert r.status_code == 200
    d = r.json()
    assert "columns" in d
    assert "rows" in d


# --- download desktop app bundle
def test_download_desktop(client):
    r = client.get("/api/download-desktop")
    assert r.status_code == 200
    assert r.headers.get("content-type") == "application/zip"


# --- file upload
def test_upload(client):
    files = {'file': ('test_upload.csv', b'id,name,value\n1,Alpha,100\n2,Beta,200\n', 'text/csv')}
    r = client.post("/api/upload", files=files)
    assert r.status_code == 200
    d = r.json()
    assert d["status"] == "success"
    assert d["filename"] == "test_upload.csv"


>>>>>>> a4386bf (Initial commit)
