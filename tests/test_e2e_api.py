"""End-to-end live testing script for ExcelIntel API endpoints."""
from __future__ import annotations

import time
import urllib.request
import json
import pytest

BASE_URL = "http://127.0.0.1:8000/api"


def test_root_endpoint():
    req = urllib.request.Request(f"{BASE_URL}/")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert data.get("app") == "ExcelIntel"
        assert data.get("status") == "ok"


def test_samples_endpoint():
    req = urllib.request.Request(f"{BASE_URL}/samples")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert "files" in data
        assert "count" in data


def test_discovery_endpoint():
    req = urllib.request.Request(f"{BASE_URL}/discovery")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert "total_files" in data
        assert "total_worksheets" in data
        assert "total_records" in data


def test_aliases_endpoint():
    # GET aliases
    req = urllib.request.Request(f"{BASE_URL}/aliases")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert "aliases" in data
        assert "Name" in data["aliases"]

    # POST new alias
    post_data = json.dumps({"canonical": "Name", "alias": "Client_Full_Name_E2E"}).encode()
    req_post = urllib.request.Request(
        f"{BASE_URL}/aliases",
        data=post_data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req_post) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert "Client_Full_Name_E2E" in data["aliases"]["Name"]


def test_advanced_duplicate_job():
    # Start advanced duplicate analysis
    req_start = urllib.request.Request(
        f"{BASE_URL}/analyze-duplicates-advanced",
        data=b"{}",
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req_start) as resp:
        assert resp.status == 200

    # Poll status until completed or timeout
    completed = False
    for _ in range(120):
        time.sleep(0.5)
        req_status = urllib.request.Request(f"{BASE_URL}/job/status")
        with urllib.request.urlopen(req_status) as resp:
            data = json.loads(resp.read().decode())
            if data.get("status") == "completed":
                completed = True
                assert data["result"] is not None
                assert "summary" in data["result"]
                assert "exact_duplicates" in data["result"]
                break

    assert completed, "Job did not complete within expected timeframe"


def test_download_report_endpoint():
    req = urllib.request.Request(f"{BASE_URL}/download-duplicate-report")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        assert resp.headers.get("Content-Type") == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        content = resp.read()
        assert len(content) > 0


def test_upload_batch_unzipped_folder():
    import io
    import requests
    url = f"{BASE_URL}/upload-batch"
    
    files = [
        ('files', ('MyFolder/file1.csv', io.BytesIO(b"Name,Email\nJohn,john@test.com\n"), 'text/csv')),
        ('files', ('MyFolder/subfolder/file2.csv', io.BytesIO(b"Name,Email\nAlice,alice@test.com\n"), 'text/csv')),
    ]
    data = [
        ('paths', 'MyFolder/file1.csv'),
        ('paths', 'MyFolder/subfolder/file2.csv'),
    ]
    
    resp = requests.post(url, files=files, data=data)
    assert resp.status_code == 200
    res_json = resp.json()
    assert res_json["status"] == "success"
    assert res_json["files_uploaded"] == 2
    assert "discovery" in res_json


if __name__ == "__main__":
    pytest.main([__file__])
