"""Unit tests for the Advanced Data Analysis & Duplicate Detection Engine."""
from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

import polars as pl
import pytest

from bi_platform.engine import (
    ColumnDetector,
    CrossFileAnalyzer,
    DiscoveryEngine,
    JobController,
)
from bi_platform.export import ExcelExporter
from bi_platform.models import Dataset, SheetInfo


@pytest.fixture
def sample_datasets():
    df1 = pl.DataFrame({
        "Customer Name": ["John Smith", "Alice Johnson", "Robert Brown"],
        "Customer Address": ["123 Main St, NYC", "456 Oak Ave, LA", "789 Pine Rd, CHI"],
        "Email Address": ["john@example.com", "alice@example.com", "robert@example.com"],
        "Phone": ["9876543210", "1234567890", "5551234567"],
    })
    ds1 = Dataset(
        name="customers_region_a.xlsx :: Sheet1",
        df=df1,
        source=SheetInfo(
            file_path="customers_region_a.xlsx",
            sheet_name="Sheet1",
            rows=3, cols=4,
            columns=df1.columns,
            dtypes={},
            file_size=1024,
        ),
    )

    df2 = pl.DataFrame({
        "Name": ["JOHN SMITH", "Jon Smith", "Robert Brown"],
        "Address": ["123 Main St, NYC", "123 Main St, NYC", "789 Pine Rd, CHI"],
        "Mail ID": ["john@example.com", "jon@example.com", "robert_new@example.com"],
        "Contact Number": ["9876543210", "9876543210", "9998887777"],
    })
    ds2 = Dataset(
        name="customers_region_b.xlsx :: Sheet1",
        df=df2,
        source=SheetInfo(
            file_path="customers_region_b.xlsx",
            sheet_name="Sheet1",
            rows=3, cols=4,
            columns=df2.columns,
            dtypes={},
            file_size=1024,
        ),
    )

    return [ds1, ds2]


def test_column_detector():
    detector = ColumnDetector()
    mapped = detector.map_columns(["Customer Name", "Customer Address", "Phone", "Email Address", "Custom_Field"])
    assert mapped["Customer Name"] == "Name"
    assert mapped["Customer Address"] == "Address"
    assert mapped["Phone"] == "Phone Number"
    assert mapped["Email Address"] == "Email"
    assert mapped["Custom_Field"] == "Custom_Field"

    detector.add_alias("Name", "Client_Full_Name")
    assert detector.map_column("Client_Full_Name") == "Name"


def test_discovery_engine():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create sample excel / csv files
        csv1 = tmp_path / "sample1.csv"
        csv1.write_text("Name,Email\nJohn,john@test.com\n", encoding="utf-8")

        # Create duplicate file hash
        csv2 = tmp_path / "sample2.csv"
        csv2.write_text("Name,Email\nJohn,john@test.com\n", encoding="utf-8")

        # Create zip archive containing nested zip
        zip1_path = tmp_path / "archive.zip"
        with zipfile.ZipFile(zip1_path, "w") as zf:
            zf.writestr("nested.csv", "Name,Email\nAlice,alice@test.com\n")

        discovery = DiscoveryEngine()
        report = discovery.scan_workspace(tmp_path)

        assert report.total_files >= 3
        assert report.duplicate_files_count >= 1
        assert report.total_records >= 2


def test_cross_file_analyzer(sample_datasets):
    analyzer = CrossFileAnalyzer()
    controller = JobController()

    progress_steps = []

    def progress_cb(pct, stage, cur_file, stats):
        progress_steps.append((pct, stage))

    result = analyzer.analyze(
        datasets=sample_datasets,
        controller=controller,
        progress_callback=progress_cb,
    )

    assert result.total_files == 2
    assert result.total_worksheets == 2
    assert result.total_records == 6
    assert len(progress_steps) > 0

    # Verify matching levels present
    all_exact = [g for g in result.exact_duplicates]
    assert len(all_exact) > 0
    assert any("Exact Match" in g.match_level for g in all_exact)

    # Verify high confidence or similar match present
    all_similar = result.similar_records + result.possible_matches
    assert len(all_similar) > 0


def test_duplicate_report_export(sample_datasets):
    analyzer = CrossFileAnalyzer()
    result = analyzer.analyze(datasets=sample_datasets)

    with tempfile.TemporaryDirectory() as tmpdir:
        report_file = Path(tmpdir) / "Duplicate_Report.xlsx"
        exporter = ExcelExporter()
        out_path = exporter.generate_duplicate_report(result, report_file)

        assert Path(out_path).exists()
        assert Path(out_path).stat().st_size > 0
