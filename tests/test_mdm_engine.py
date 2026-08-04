import os
from pathlib import Path
import polars as pl
from bi_platform.engine import MasterConsolidationEngine, ColumnDetector, PREDEFINED_MATCHING_RULES
from bi_platform.export import ExcelExporter
from bi_platform.models import Dataset, SheetInfo


def test_master_mdm_consolidation():
    # Build 3 sample datasets representing Excel 1, Excel 2, Excel 3
    ds1 = Dataset(
        name="Customers1.xlsx",
        df=pl.DataFrame({
            "Customer Name": ["Deep", "Rahul"],
            "Office Address": ["Petlad", "Surat"],
            "City": ["Anand", "Surat"],
            "State": ["Gujarat", "Gujarat"],
            "Contact Number": ["7894561230", "9876543210"],
            "Email": ["deep@example.com", "rahul@example.com"],
        }),
        source=SheetInfo(file_path="samples/Customers1.xlsx", sheet_name="Sheet1", rows=2, cols=6, columns=[], dtypes={}, file_size=1024)
    )

    ds2 = Dataset(
        name="Customers2.xlsx",
        df=pl.DataFrame({
            "Full Name": ["Deep", "Anita"],
            "Customer Address": ["Petlad", "Ahmedabad"],
            "City": ["Anand", "Ahmedabad"],
            "State": ["Gujarat", "Gujarat"],
            "Phone Number": ["7894561230", "9123456789"],
            "Mail ID": ["deep@example.com", "anita@example.com"],
        }),
        source=SheetInfo(file_path="samples/Customers2.xlsx", sheet_name="Sheet2", rows=2, cols=6, columns=[], dtypes={}, file_size=1024)
    )

    ds3 = Dataset(
        name="Customers3.xlsx",
        df=pl.DataFrame({
            "Name": ["Deep", "Rahul"],
            "Address": ["Petlad", "Surat"],
            "Town": ["Anand", "Surat"],
            "Province": ["Gujarat", "Gujarat"],
            "Mobile": ["7894561230", "9876543210"],
            "Email Address": ["deep@example.com", "rahul@example.com"],
        }),
        source=SheetInfo(file_path="samples/Customers3.xlsx", sheet_name="Customers", rows=2, cols=6, columns=[], dtypes={}, file_size=1024)
    )

    engine = MasterConsolidationEngine(column_detector=ColumnDetector())
    res = engine.process_mdm(datasets=[ds1, ds2, ds3], rule_id="rule_1")

    # Assertions
    assert res.total_files == 3
    assert res.total_worksheets == 3
    assert res.total_records == 6

    # "Deep" exists in all 3 files -> Consolidates into ONE Master Record M000001
    deep_master = next((m for m in res.master_records if m.name == "Deep"), None)
    assert deep_master is not None
    assert deep_master.master_id.startswith("M")
    assert deep_master.source_count == 3
    assert deep_master.duplicate_count == 2
    assert deep_master.total_occurrences == 3
    assert len(deep_master.references) == 3

    # Generate 8-sheet Master_Data.xlsx
    output_path = Path("samples/test_Master_Data.xlsx")
    exporter = ExcelExporter()
    exported_file = exporter.generate_master_workbook(res, output_path)

    assert Path(exported_file).exists()
    assert Path(exported_file).stat().st_size > 0

    # Clean up test output file
    if output_path.exists():
        import gc
        gc.collect()
        try:
            output_path.unlink()
        except PermissionError:
            time.sleep(0.1)
            try:
                output_path.unlink()
            except Exception:
                pass
