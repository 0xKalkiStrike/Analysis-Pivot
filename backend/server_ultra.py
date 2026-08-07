"""ULTRA-FAST ExcelIntel API using DuckDB + multiprocessing — sub-1-second responses."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import io
import zipfile
import orjson
from fastapi import FastAPI, HTTPException, File, UploadFile, Query
from fastapi.responses import ORJSONResponse
from starlette.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from bi_platform import __version__ as bi_version
from bi_platform.engine.excel_engine import ExcelEngine
from bi_platform.engine.analytics_engine_ultra import UltraFastAnalyticsEngine
from bi_platform.engine.discovery_engine_ultra import UltraFastDiscoveryEngine
from bi_platform.core.logger import get_logger

log = get_logger(__name__)

APP_ROOT = ROOT
SAMPLES_DIR = APP_ROOT / "samples"
SAMPLES_DIR.mkdir(exist_ok=True)

app = FastAPI(title="ExcelIntel Ultra-Fast API", version=bi_version)

# Ultra-fast engines
_excel_engine = ExcelEngine()
_discovery_ultra = UltraFastDiscoveryEngine(excel_engine=_excel_engine)
_analytics_ultra = UltraFastAnalyticsEngine()

# Cache (in-memory)
_dataset_cache: dict[str, Any] = {}
_discovery_cache: dict[str, Any] = None
_discovery_cache_time: float = 0


def _ds_key(file: str, sheet: str) -> str:
    return f"{Path(file).name}::{sheet}"


def _load_cached(file: str, sheet: str | None = None) -> Any:
    """Load dataset with caching."""
    p = SAMPLES_DIR / file
    if not p.exists():
        raise HTTPException(404, f"File not found: {file}")

    sheet = sheet or _excel_engine.list_sheets(p)[0]
    key = _ds_key(str(p), sheet)

    if key not in _dataset_cache:
        _dataset_cache[key] = _excel_engine.load_sheet(p, sheet_name=sheet)

    return _dataset_cache[key]


def _df_to_records(df, limit: int = 100) -> list[dict[str, Any]]:
    """Convert DF to JSON records."""
    rows = df.head(limit).to_dicts()
    for r in rows:
        for k, v in list(r.items()):
            if v is None or isinstance(v, (int, float, str, bool)):
                pass
            else:
                r[k] = str(v)
    return rows


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/", response_class=ORJSONResponse)
async def root():
    return {"app": "ExcelIntel Ultra", "version": bi_version, "status": "ready"}


@app.post("/api/upload", response_class=ORJSONResponse)
async def upload_file(file: UploadFile = File(...)):
    """Ultra-fast single file upload."""
    if not file.filename:
        raise HTTPException(400, "Invalid filename")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in (".xlsx", ".csv", ".xls", ".xlsm", ".xlsb", ".tsv", ".zip"):
        raise HTTPException(400, f"Unsupported: {suffix}")

    content = await file.read()

    # Save file instantly
    if suffix == ".zip":
        target_dir = SAMPLES_DIR / Path(file.filename).stem
        target_dir.mkdir(exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            zf.extractall(target_dir)

        extracted = [str(p.relative_to(SAMPLES_DIR)).replace("\\", "/")
                    for p in target_dir.rglob("*")
                    if p.is_file() and p.suffix.lower() in (".xlsx", ".csv", ".xls", ".xlsm", ".xlsb", ".tsv")]

        _dataset_cache.clear()
        return ORJSONResponse({
            "status": "uploaded",
            "filename": file.filename,
            "type": "archive",
            "files": len(extracted),
            "extracted": extracted,
        })
    else:
        target_path = SAMPLES_DIR / file.filename
        with open(target_path, "wb") as f:
            f.write(content)

        # Clear cache only for this file
        for k in list(_dataset_cache.keys()):
            if file.filename in k:
                del _dataset_cache[k]

        sheets = _excel_engine.list_sheets(target_path)

        return ORJSONResponse({
            "status": "uploaded",
            "filename": file.filename,
            "size": len(content),
            "sheets": sheets,
        })


@app.post("/api/upload-batch", response_class=ORJSONResponse)
async def upload_batch(files: list[UploadFile] = File(default=[])):
    """Ultra-fast batch upload."""
    if not files:
        raise HTTPException(400, "No files")

    saved = []
    for file in files:
        if not file.filename:
            continue

        content = await file.read()
        target = SAMPLES_DIR / file.filename
        target.parent.mkdir(exist_ok=True)

        with open(target, "wb") as f:
            f.write(content)

        saved.append(file.filename)

    _dataset_cache.clear()

    return ORJSONResponse({
        "status": "uploaded",
        "files": len(saved),
        "saved": saved,
    })


@app.get("/api/files", response_class=ORJSONResponse)
async def list_files():
    """List all files (cached, instant)."""
    files = []
    for p in SAMPLES_DIR.rglob("*"):
        if p.is_file() and p.suffix.lower() in (".xlsx", ".csv", ".xls", ".xlsm", ".xlsb", ".tsv"):
            rel = str(p.relative_to(SAMPLES_DIR)).replace("\\", "/")
            try:
                sheets = _excel_engine.list_sheets(p)
                files.append({
                    "name": rel,
                    "size": p.stat().st_size,
                    "sheets": sheets,
                })
            except Exception:
                pass

    return {"files": files, "count": len(files)}


@app.get("/api/discover", response_class=ORJSONResponse)
async def discover():
    """Ultra-fast discovery (multiprocessing parallel)."""
    global _discovery_cache, _discovery_cache_time

    import time
    now = time.time()

    # Cache for 30 seconds
    if _discovery_cache and (now - _discovery_cache_time) < 30:
        return _discovery_cache

    report = _discovery_ultra.scan_workspace_instant(SAMPLES_DIR)
    _discovery_cache = report
    _discovery_cache_time = now

    return report


@app.get("/api/dataset", response_class=ORJSONResponse)
async def get_dataset(file: str, sheet: str | None = None, limit: int = 100):
    """Get dataset preview (instant)."""
    ds = _load_cached(file, sheet)

    return {
        "name": ds.name,
        "rows": ds.rows,
        "cols": ds.cols,
        "columns": ds.columns,
        "dtypes": {c: str(ds.df.schema[c]) for c in ds.columns},
        "preview": _df_to_records(ds.df, limit),
    }


@app.get("/api/summary", response_class=ORJSONResponse)
async def summary():
    """Get full analysis summary (ultra-fast DuckDB)."""
    import time
    start = time.time()

    files = []
    datasets = []

    for p in SAMPLES_DIR.rglob("*"):
        if p.is_file() and p.suffix.lower() in (".xlsx", ".csv", ".xls", ".xlsm", ".xlsb", ".tsv"):
            rel = str(p.relative_to(SAMPLES_DIR)).replace("\\", "/")
            try:
                sheets = _excel_engine.list_sheets(p)
                for sheet in sheets:
                    try:
                        ds = _load_cached(rel, sheet)
                        datasets.append(ds)
                        files.append({
                            "name": rel,
                            "sheet": sheet,
                            "rows": ds.rows,
                            "cols": ds.cols,
                        })
                    except Exception:
                        pass
            except Exception:
                pass

    # Ultra-fast analysis using DuckDB
    s = _analytics_ultra.summarise(datasets)

    elapsed = time.time() - start

    return ORJSONResponse({
        "kpis": {
            "files": s.total_files,
            "sheets": s.total_sheets,
            "total_rows": s.total_rows,
            "unique_rows": s.unique_rows,
            "duplicate_rows": s.duplicate_rows,
            "missing_values": s.missing_values,
            "data_quality_score": s.data_quality_score,
            "validation_score": s.validation_score,
            "columns_profiled": s.columns_profiled,
        },
        "per_file": files,
        "analysis_time_ms": round(elapsed * 1000),
    })


@app.get("/api/profile/{file}/{column}", response_class=ORJSONResponse)
async def profile_column(file: str, column: str):
    """Profile single column (ultra-fast DuckDB)."""
    ds = _load_cached(file)
    prof = _analytics_ultra.profile_column_ultra_fast(ds, column)
    return prof


@app.get("/api/duplicates", response_class=ORJSONResponse)
async def find_duplicates(
    file: str,
    sheet: str | None = None,
    column: str | None = None,
    threshold: float = Query(90.0, ge=50, le=100),
):
    """Fast duplicate detection (optimized)."""
    ds = _load_cached(file, sheet)

    # Quick fuzzy duplicate detection
    try:
        from bi_platform.engine.duplicate_engine import DuplicateEngine
        from bi_platform.engine.fuzzy_engine import FuzzyEngine

        engine = DuplicateEngine(FuzzyEngine("weighted_ratio"))

        if column:
            groups = engine.detect_fuzzy(ds, column, threshold=threshold)
        else:
            groups = engine.detect_smart(ds, threshold=threshold)

        return ORJSONResponse({
            "total_groups": len(groups),
            "total_rows_flagged": sum(g.size for g in groups),
            "threshold": threshold,
            "groups": [
                {
                    "id": gi,
                    "size": g.size,
                    "confidence": round(g.confidence, 2),
                }
                for gi, g in enumerate(groups[:50])  # Limit to 50
            ],
        })
    except Exception as e:
        return ORJSONResponse({
            "status": "error",
            "message": str(e),
        }, status_code=500)


# ============================================================================
# MIDDLEWARE
# ============================================================================

raw_origins_ultra = os.environ.get("CORS_ORIGINS", "")
parsed_origins_ultra = [o.strip() for o in raw_origins_ultra.split(",") if o.strip() and o.strip() != "*"]

default_origins_ultra = [
    "https://analysis-pivot.vercel.app",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8000",
]
for orig in default_origins_ultra:
    if orig not in parsed_origins_ultra:
        parsed_origins_ultra.append(orig)

app.add_middleware(
    CORSMiddleware,
    allow_origins=parsed_origins_ultra,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=4)
