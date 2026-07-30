"""ExcelIntel Web Preview — FastAPI wrapper around bi_platform engines."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

# Ensure we can import bi_platform from /app
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.cors import CORSMiddleware

load_dotenv(Path(__file__).parent / ".env")

# Import the engines lazily so backend boots even if a dependency is missing
from bi_platform import __version__ as bi_version
from bi_platform.engine import (AnalyticsEngine, CleaningEngine, DuplicateEngine,
                                 ExcelEngine, FuzzyEngine, MergeEngine,
                                 PivotEngine, RelationshipEngine,
                                 ValidationEngine)
from bi_platform.models import Dataset

APP_ROOT = ROOT
SAMPLES_DIR = APP_ROOT / "samples"
DOCS_DIR = APP_ROOT / "docs"

app = FastAPI(title="ExcelIntel Preview API", version=bi_version)
api = APIRouter(prefix="/api")

# ---------------------------------------------------------------------------- state
_engine = ExcelEngine()
_dataset_cache: dict[str, Dataset] = {}


def _ds_key(file: str, sheet: str) -> str:
    return f"{Path(file).name} :: {sheet}"


def _load(file: str, sheet: str | None = None) -> Dataset:
    p = SAMPLES_DIR / file
    if not p.exists():
        raise HTTPException(404, f"Sample file not found: {file}")
    sheet = sheet or _engine.list_sheets(p)[0]
    key = _ds_key(str(p), sheet)
    if key not in _dataset_cache:
        _dataset_cache[key] = _engine.load_sheet(p, sheet_name=sheet)
    return _dataset_cache[key]


def _all_datasets() -> dict[str, Dataset]:
    result: dict[str, Dataset] = {}
    for f in _engine.scan_folder(SAMPLES_DIR):
        if f.suffix.lower() == ".csv":
            continue
        try:
            for sh in _engine.list_sheets(f):
                key = _ds_key(str(f), sh)
                if key not in _dataset_cache:
                    _dataset_cache[key] = _engine.load_sheet(f, sheet_name=sh)
                result[key] = _dataset_cache[key]
        except Exception:  # pragma: no cover
            continue
    return result


def _df_to_records(df, limit: int = 200) -> list[dict[str, Any]]:
    rows = df.head(limit).to_dicts()
    for r in rows:
        for k, v in list(r.items()):
            if v is None:
                r[k] = None
            elif isinstance(v, (int, float, str, bool)):
                pass
            else:
                r[k] = str(v)
    return rows


# ---------------------------------------------------------------------------- routes

@api.get("/")
def root():
    return {"app": "ExcelIntel", "version": bi_version, "status": "ok"}


@api.get("/samples")
def list_samples():
    files = []
    for f in sorted(SAMPLES_DIR.glob("*")):
        if f.suffix.lower() not in (".xlsx", ".csv", ".xls", ".xlsm", ".xlsb", ".tsv"):
            continue
        try:
            sheets = _engine.list_sheets(f)
        except Exception:
            sheets = []
        files.append({
            "name": f.name,
            "size": f.stat().st_size,
            "sheets": sheets,
        })
    return {"files": files, "count": len(files)}


@api.get("/dataset")
def get_dataset(file: str, sheet: str | None = None, limit: int = 100):
    ds = _load(file, sheet)
    return {
        "name": ds.name,
        "rows": ds.rows,
        "cols": ds.cols,
        "columns": ds.columns,
        "dtypes": {c: str(ds.df.schema[c]) for c in ds.columns},
        "preview": _df_to_records(ds.df, limit=limit),
    }


@api.get("/summary")
def summary():
    dsets = list(_all_datasets().values())
    s = AnalyticsEngine().summarise(dsets)
    per_sheet = [{"name": d.name, "rows": d.rows, "cols": d.cols} for d in dsets]
    return {
        "kpis": {
            "files": s.total_files, "sheets": s.total_sheets,
            "total_rows": s.total_rows, "unique_rows": s.unique_rows,
            "duplicate_rows": s.duplicate_rows, "missing_values": s.missing_values,
            "data_quality_score": s.data_quality_score,
            "validation_score": s.validation_score,
            "columns_profiled": s.columns_profiled,
        },
        "per_sheet": per_sheet,
        "quality_composition": [
            {"label": "Unique", "value": s.unique_rows},
            {"label": "Duplicates", "value": s.duplicate_rows},
            {"label": "Missing", "value": s.missing_values},
        ],
    }


@api.get("/duplicates")
def duplicates(
    file: str,
    sheet: str | None = None,
    column: str | None = None,
    threshold: float = Query(88.0, ge=50, le=100),
    algorithm: str = "weighted_ratio",
    clean: bool = True,
    limit: int = 200,
):
    ds = _load(file, sheet)
    if clean:
        ds = CleaningEngine().clean(ds)
    engine = DuplicateEngine(FuzzyEngine(algorithm))
    if column:
        groups = engine.detect_fuzzy(ds, column, threshold=threshold)
    else:
        groups = engine.detect_smart(ds, threshold=threshold)

    payload_groups = []
    for gi, g in enumerate(groups[:80]):
        payload_groups.append({
            "id": gi,
            "size": g.size,
            "confidence": round(g.confidence, 2),
            "method": g.method,
            "reason": g.reason,
            "rows": [{k: (None if v is None else v if isinstance(v, (int, float, str, bool)) else str(v))
                      for k, v in r.items() if not k.startswith("_")}
                     for r in g.rows[:10]],
        })
    return {
        "total_groups": len(groups),
        "total_rows_flagged": sum(g.size for g in groups),
        "threshold": threshold,
        "algorithm": algorithm,
        "groups": payload_groups,
    }


@api.get("/validation")
def validation(file: str, sheet: str | None = None, limit: int = 200):
    ds = _load(file, sheet)
    engine = ValidationEngine()
    issues = engine.validate(ds)
    score = engine.quality_score(ds, issues)
    return {
        "quality_score": score,
        "counts": {
            "error": sum(1 for i in issues if i.severity == "error"),
            "warning": sum(1 for i in issues if i.severity == "warning"),
            "info": sum(1 for i in issues if i.severity == "info"),
        },
        "issues": [{
            "row": i.row_index, "column": i.column,
            "value": None if i.value is None else str(i.value),
            "severity": i.severity, "rule": i.rule, "message": i.message,
        } for i in issues[:limit]],
    }


@api.get("/pivot")
def pivot(
    file: str, sheet: str | None = None,
    rows: str = Query(..., description="Comma-separated row fields"),
    columns: str | None = Query(None, description="Comma-separated column fields"),
    value: str | None = None,
    aggregate: str = "sum",
    limit: int = 200,
):
    ds = _load(file, sheet)
    row_list = [r.strip() for r in rows.split(",") if r.strip()]
    col_list = [c.strip() for c in columns.split(",")] if columns else None
    try:
        result = PivotEngine().pivot(ds, rows=row_list, columns=col_list,
                                     values=value, aggregate=aggregate)
    except Exception as e:
        raise HTTPException(400, str(e))
    return {
        "columns": result.columns,
        "rows": _df_to_records(result, limit=limit),
        "total_rows": result.height,
    }


@api.get("/relationships")
def relationships():
    ds = _all_datasets()
    rels = RelationshipEngine(min_overlap=0.5, min_shared=3).discover(ds)
    return {
        "datasets": list(ds.keys()),
        "relationships": [{
            "left_dataset": r.left_dataset, "left_column": r.left_column,
            "right_dataset": r.right_dataset, "right_column": r.right_column,
            "cardinality": r.cardinality,
            "confidence": r.confidence, "overlap": r.overlap,
            "reverse_overlap": r.reverse_overlap, "shared": r.shared_values,
            "reason": r.reason,
        } for r in rels],
    }


@api.get("/merge")
def merge(
    left_file: str, right_file: str,
    on: str, how: str = "inner",
    left_sheet: str | None = None, right_sheet: str | None = None,
    limit: int = 200,
):
    l = _load(left_file, left_sheet)
    r = _load(right_file, right_sheet)
    try:
        result = MergeEngine().merge(l, r, on=on, how=how)
    except Exception as e:
        raise HTTPException(400, str(e))
    return {
        "rows": result.total, "matched": result.matched,
        "unmatched_left": result.unmatched_left, "unmatched_right": result.unmatched_right,
        "conflicts": len(result.conflicts),
        "columns": result.dataset.columns,
        "preview": _df_to_records(result.dataset.df, limit=limit),
    }


@api.get("/top-values")
def top_values(file: str, column: str, sheet: str | None = None, n: int = 10):
    ds = _load(file, sheet)
    if column not in ds.columns:
        raise HTTPException(400, f"Column '{column}' not found")
    vc = ds.df[column].value_counts(sort=True).head(n).to_dicts()
    if not vc:
        return {"column": column, "top": []}
    label_key = column
    count_key = "count" if "count" in vc[0] else ("counts" if "counts" in vc[0] else None)
    return {
        "column": column,
        "top": [
            {"value": str(row.get(label_key)) if row.get(label_key) is not None else "—",
             "count": int(row.get(count_key, 0)) if count_key else 0}
            for row in vc
        ],
    }


@api.get("/screenshots/{name}")
def screenshot(name: str):
    p = DOCS_DIR / name
    if not p.exists() or not p.name.startswith("screenshot"):
        raise HTTPException(404, "Not found")
    return FileResponse(p, media_type="image/png")


# ---------------------------------------------------------------------------- app
app.include_router(api)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)
