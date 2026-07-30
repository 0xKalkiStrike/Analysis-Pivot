from pathlib import Path

from bi_platform.engine import AnalyticsEngine, ExcelEngine
from bi_platform.export import ExcelExporter, ReportGenerator
from bi_platform.models import AnalyticsSummary


def test_analytics_summary_multiple_datasets(sample_files_dir):
    files = list(sample_files_dir.glob("*.xlsx"))[:3]
    dsets = [ExcelEngine().load_sheet(f) for f in files]
    summary = AnalyticsEngine().summarise(dsets)
    assert summary.total_sheets == len(dsets)
    assert summary.total_rows > 0
    assert 0 <= summary.data_quality_score <= 100


def test_excel_exporter_writes_file(customers_dataset, tmp_path):
    p = tmp_path / "out.xlsx"
    result = ExcelExporter().export_dataset(customers_dataset, p)
    assert Path(result).exists() and Path(result).stat().st_size > 0


def test_report_generator_outputs(tmp_path):
    s = AnalyticsSummary(total_files=1, total_sheets=2, total_rows=100, unique_rows=90,
                         duplicate_rows=10, missing_values=5, data_quality_score=95.5,
                         validation_score=97.0, columns_profiled=10)
    rg = ReportGenerator()
    j = rg.summary_json(s, tmp_path / "s.json")
    h = rg.summary_html(s, [], [], tmp_path / "s.html")
    p = rg.summary_pdf(s, [], tmp_path / "s.pdf")
    for f in (j, h, p):
        assert Path(f).exists() and Path(f).stat().st_size > 100
