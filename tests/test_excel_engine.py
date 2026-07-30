from bi_platform.engine import ExcelEngine


def test_scan_folder_finds_supported_files(sample_files_dir):
    engine = ExcelEngine()
    files = engine.scan_folder(sample_files_dir)
    assert len(files) >= 4
    assert all(f.suffix.lower() in {".xlsx", ".csv", ".tsv", ".xls", ".xlsm", ".xlsb"} for f in files)


def test_list_sheets_xlsx(sample_files_dir):
    files = list(sample_files_dir.glob("*.xlsx"))
    assert files
    sheets = ExcelEngine().list_sheets(files[0])
    assert sheets and isinstance(sheets, list)


def test_load_sheet_returns_dataset(sample_files_dir):
    f = next(sample_files_dir.glob("customers_region_a.xlsx"))
    ds = ExcelEngine().load_sheet(f)
    assert ds.rows > 100
    assert ds.cols >= 10
    assert "customer_id" in ds.columns
    assert ds.source is not None


def test_load_csv(sample_files_dir):
    f = next(sample_files_dir.glob("*.csv"))
    ds = ExcelEngine().load_sheet(f)
    assert ds.rows > 0
    assert ds.source.sheet_name == f.stem
