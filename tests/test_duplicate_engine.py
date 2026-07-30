from bi_platform.engine import CleaningEngine, DuplicateEngine


def test_detect_by_email(customers_dataset):
    ds = CleaningEngine().clean(customers_dataset)
    groups = DuplicateEngine().detect_by_column(ds, "email")
    assert len(groups) == 1
    assert groups[0].size >= 2
    assert groups[0].confidence == 100.0


def test_detect_exact(customers_dataset):
    groups = DuplicateEngine().detect_exact(customers_dataset)
    # No two rows are strictly identical without cleaning
    assert isinstance(groups, list)


def test_detect_fuzzy_name(customers_dataset):
    ds = CleaningEngine().clean(customers_dataset)
    groups = DuplicateEngine().detect_fuzzy(ds, "name", threshold=85)
    # Alice group should be discovered
    assert any(g.size >= 2 for g in groups)


def test_smart_detection(customers_dataset):
    groups = DuplicateEngine().detect_smart(customers_dataset, threshold=80)
    assert len(groups) >= 1


def test_to_dataframe_has_metadata(customers_dataset):
    ds = CleaningEngine().clean(customers_dataset)
    engine = DuplicateEngine()
    groups = engine.detect_by_column(ds, "email")
    df = engine.to_dataframe(groups)
    for col in ("_group_id", "_confidence", "_method", "_reason"):
        assert col in df.columns
