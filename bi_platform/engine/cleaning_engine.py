"""Intelligent data cleaning."""
from __future__ import annotations

import re
import unicodedata

import polars as pl

from ..core.logger import get_logger
from ..models import Dataset

log = get_logger(__name__)

_MULTI_SPACE = re.compile(r"\s+")
_INVISIBLE = re.compile(r"[\u200b-\u200f\u202a-\u202e\ufeff\u00ad]")
_PHONE_STRIP = re.compile(r"[^\d+]")
_EMAIL_RE = re.compile(r"^[\w.+\-]+@[\w\-]+\.[\w\-.]+$")


class CleaningEngine:
    """Vectorised cleaning operations for a Dataset."""

    def clean(
        self,
        dataset: Dataset,
        trim: bool = True,
        dedupe_spaces: bool = True,
        strip_invisible: bool = True,
        unicode_normalize: bool = True,
        fix_case: str | None = None,  # None | "title" | "lower" | "upper"
        normalize_phones: bool = True,
        normalize_emails: bool = True,
    ) -> Dataset:
        df = dataset.df
        str_cols = [c for c, t in df.schema.items() if t == pl.Utf8]

        exprs: list[pl.Expr] = []
        for c in str_cols:
            e = pl.col(c)
            if strip_invisible:
                e = e.str.replace_all(_INVISIBLE.pattern, "", literal=False)
            if unicode_normalize:
                e = e.map_elements(
                    lambda v: unicodedata.normalize("NFKC", v) if v is not None else v,
                    return_dtype=pl.Utf8,
                )
            if dedupe_spaces:
                e = e.str.replace_all(r"\s+", " ")
            if trim:
                e = e.str.strip_chars()
            if fix_case == "title":
                e = e.str.to_titlecase()
            elif fix_case == "lower":
                e = e.str.to_lowercase()
            elif fix_case == "upper":
                e = e.str.to_uppercase()
            exprs.append(e.alias(c))

        if exprs:
            df = df.with_columns(exprs)

        # Semantic normalisation
        for col in df.columns:
            lc = col.lower()
            if normalize_emails and "email" in lc and df.schema[col] == pl.Utf8:
                df = df.with_columns(pl.col(col).str.to_lowercase().alias(col))
            if normalize_phones and any(k in lc for k in ("phone", "mobile", "contact")) and df.schema[col] == pl.Utf8:
                df = df.with_columns(
                    pl.col(col)
                    .map_elements(lambda v: _PHONE_STRIP.sub("", v) if v else v, return_dtype=pl.Utf8)
                    .alias(col)
                )

        return Dataset(name=dataset.name, df=df, source=dataset.source)

    @staticmethod
    def is_valid_email(value: str | None) -> bool:
        return bool(value and _EMAIL_RE.match(value))
