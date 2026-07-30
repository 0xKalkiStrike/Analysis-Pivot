"""Validation engine — rule-based data quality checks."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any

import polars as pl

from ..core.logger import get_logger
from ..models import Dataset, ValidationIssue

log = get_logger(__name__)

EMAIL_RE = re.compile(r"^[\w.+\-]+@[\w\-]+\.[\w\-.]+$")
PHONE_RE = re.compile(r"^\+?\d[\d\s\-()]{5,}$")
GSTIN_RE = re.compile(r"^\d{2}[A-Z]{5}\d{4}[A-Z]{1}\d[Z][A-Z\d]$")
ZIP_RE = re.compile(r"^\d{3,10}(-\d{3,5})?$")


class ValidationEngine:
    """Detect data quality issues and produce structured issues + report."""

    def validate(self, dataset: Dataset) -> list[ValidationIssue]:
        df = dataset.df
        issues: list[ValidationIssue] = []

        # Missing columns / headers
        empty_headers = [c for c in df.columns if not c or c.startswith("column")]
        for c in empty_headers:
            issues.append(ValidationIssue(-1, c, None, "warning", "missing_header",
                                          "Column has missing / auto-generated header"))

        # Missing / null values
        for c in df.columns:
            nulls = df[c].null_count()
            if nulls > 0:
                issues.append(ValidationIssue(-1, c, None, "info", "null_values",
                                              f"{nulls} null / missing values"))

        # Column-based rules
        rows = df.to_dicts()
        for i, row in enumerate(rows):
            for col, val in row.items():
                if val is None or val == "":
                    continue
                lc = col.lower()
                sval = str(val)
                if "email" in lc and not EMAIL_RE.match(sval):
                    issues.append(ValidationIssue(i, col, val, "error", "invalid_email", "Not a valid email"))
                elif any(k in lc for k in ("phone", "mobile", "contact")):
                    digits = re.sub(r"\D", "", sval)
                    if len(digits) < 6 or len(digits) > 15:
                        issues.append(ValidationIssue(i, col, val, "error", "invalid_phone", "Phone length invalid"))
                elif "gst" in lc and not GSTIN_RE.match(sval.upper()):
                    issues.append(ValidationIssue(i, col, val, "warning", "invalid_gst", "Not a GSTIN pattern"))
                elif ("zip" in lc or "pin" in lc or "postal" in lc) and not ZIP_RE.match(sval):
                    issues.append(ValidationIssue(i, col, val, "warning", "invalid_zip", "ZIP/PIN pattern invalid"))
                elif "date" in lc:
                    if not self._parses_as_date(sval):
                        issues.append(ValidationIssue(i, col, val, "warning", "invalid_date", "Unrecognised date"))

        # Numeric outliers (simple 1.5*IQR)
        for c, dt in df.schema.items():
            if dt in (pl.Int64, pl.Int32, pl.Float32, pl.Float64):
                s = df[c].drop_nulls()
                if s.len() < 4:
                    continue
                q1 = s.quantile(0.25) or 0
                q3 = s.quantile(0.75) or 0
                iqr = q3 - q1
                if iqr == 0:
                    continue
                lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
                mask = (df[c] < lo) | (df[c] > hi)
                for i, is_out in enumerate(mask.to_list()):
                    if is_out:
                        issues.append(ValidationIssue(
                            i, c, df[c][i], "info", "outlier",
                            f"Outside [{lo:.2f}, {hi:.2f}]"
                        ))

        return issues

    def quality_score(self, dataset: Dataset, issues: list[ValidationIssue]) -> float:
        total_cells = max(1, dataset.rows * max(1, dataset.cols))
        weights = {"error": 3, "warning": 2, "info": 1}
        cost = sum(weights.get(i.severity, 1) for i in issues)
        score = max(0.0, 100.0 - (100.0 * cost / total_cells))
        return round(score, 2)

    @staticmethod
    def to_dataframe(issues: list[ValidationIssue]) -> pl.DataFrame:
        if not issues:
            return pl.DataFrame(schema={"row": pl.Int64, "column": pl.Utf8, "value": pl.Utf8,
                                        "severity": pl.Utf8, "rule": pl.Utf8, "message": pl.Utf8})
        return pl.DataFrame([
            {"row": i.row_index, "column": i.column,
             "value": None if i.value is None else str(i.value),
             "severity": i.severity, "rule": i.rule, "message": i.message}
            for i in issues
        ])

    @staticmethod
    def _parses_as_date(v: str) -> bool:
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y",
                    "%Y/%m/%d", "%d %b %Y", "%d %B %Y", "%Y-%m-%d %H:%M:%S"):
            try:
                datetime.strptime(v, fmt)
                return True
            except ValueError:
                continue
        return False
