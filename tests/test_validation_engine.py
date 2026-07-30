import polars as pl

from bi_platform.engine import ValidationEngine
from bi_platform.models import Dataset


def test_invalid_email_detected():
    ds = Dataset(name="test", df=pl.DataFrame({"email": ["good@x.com", "not-an-email", "b@y.org"]}))
    issues = ValidationEngine().validate(ds)
    assert any(i.rule == "invalid_email" for i in issues)


def test_null_values_flagged():
    ds = Dataset(name="test", df=pl.DataFrame({"name": ["A", None, "B", None]}))
    issues = ValidationEngine().validate(ds)
    assert any(i.rule == "null_values" for i in issues)


def test_quality_score_bounds():
    ds = Dataset(name="test", df=pl.DataFrame({"x": [1, 2, 3, 4, 5]}))
    engine = ValidationEngine()
    issues = engine.validate(ds)
    score = engine.quality_score(ds, issues)
    assert 0.0 <= score <= 100.0


def test_phone_length_error():
    ds = Dataset(name="test", df=pl.DataFrame({"phone": ["1234567890", "abc"]}))
    issues = ValidationEngine().validate(ds)
    assert any(i.rule == "invalid_phone" for i in issues)


def test_to_dataframe_schema_stable_when_empty():
    df = ValidationEngine.to_dataframe([])
    assert set(df.columns) >= {"row", "column", "value", "severity", "rule", "message"}
