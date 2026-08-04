<<<<<<< HEAD
"""ExcelIntel Web Preview — FastAPI wrapper around bi_platform engines."""
=======
"""ExcelIntel Web Preview — FastAPI wrapper around bi_platform engines.
Clean compile verified.
"""
>>>>>>> a4386bf (Initial commit)
from __future__ import annotations

import os
import sys
<<<<<<< HEAD
=======
import threading
>>>>>>> a4386bf (Initial commit)
from pathlib import Path
from typing import Any

# Ensure we can import bi_platform from /app
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

<<<<<<< HEAD
from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
=======
import io
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, HTTPException, Query, File, UploadFile, Body, Form, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
>>>>>>> a4386bf (Initial commit)
from starlette.middleware.cors import CORSMiddleware

load_dotenv(Path(__file__).parent / ".env")

# Import the engines lazily so backend boots even if a dependency is missing
from bi_platform import __version__ as bi_version
from bi_platform.engine import (AnalyticsEngine, CleaningEngine, DuplicateEngine,
                                 ExcelEngine, FuzzyEngine, MergeEngine,
                                 PivotEngine, RelationshipEngine,
<<<<<<< HEAD
                                 ValidationEngine)
from bi_platform.models import Dataset
=======
                                 ValidationEngine, DiscoveryEngine, ColumnDetector,
                                 CrossFileAnalyzer, JobController,
                                 MasterConsolidationEngine, PREDEFINED_MATCHING_RULES)
from bi_platform.engine.analytics_engine_fast import FastAnalyticsEngine
from bi_platform.engine.discovery_engine_fast import FastDiscoveryEngine
from bi_platform.export import ExcelExporter
from bi_platform.models import Dataset
from .job_queue import JobQueue, ProgressTracker
>>>>>>> a4386bf (Initial commit)

APP_ROOT = ROOT
SAMPLES_DIR = APP_ROOT / "samples"
DOCS_DIR = APP_ROOT / "docs"

app = FastAPI(title="ExcelIntel Preview API", version=bi_version)
api = APIRouter(prefix="/api")

# ---------------------------------------------------------------------------- state
_engine = ExcelEngine()
<<<<<<< HEAD
_dataset_cache: dict[str, Dataset] = {}
=======
_discovery_engine = DiscoveryEngine(excel_engine=_engine)
_discovery_engine_fast = FastDiscoveryEngine(excel_engine=_engine, max_workers=4)
_analytics_engine_fast = FastAnalyticsEngine(max_workers=4)
_column_detector = ColumnDetector()
_dataset_cache: dict[str, Dataset] = {}
_dataset_mtime_cache: dict[str, float] = {}
_cached_discovery_report: tuple[float, dict] | None = None
_cached_summary_data: tuple[float, dict] | None = None

# Job queue for async analysis
_job_queue = JobQueue()
_executor = ThreadPoolExecutor(max_workers=2)

# Active background analysis job state
_current_job: dict[str, Any] = {
    "status": "idle",  # "idle" | "running" | "paused" | "completed" | "cancelled" | "error"
    "percent": 0.0,
    "stage": "",
    "current_file": "",
    "stats": {},
    "result": None,
    "error": None,
    "controller": None,
}
>>>>>>> a4386bf (Initial commit)


def _ds_key(file: str, sheet: str) -> str:
    return f"{Path(file).name} :: {sheet}"


def _load(file: str, sheet: str | None = None) -> Dataset:
    p = SAMPLES_DIR / file
    if not p.exists():
        raise HTTPException(404, f"Sample file not found: {file}")
    sheet = sheet or _engine.list_sheets(p)[0]
    key = _ds_key(str(p), sheet)
<<<<<<< HEAD
    if key not in _dataset_cache:
        _dataset_cache[key] = _engine.load_sheet(p, sheet_name=sheet)
=======
    mtime = p.stat().st_mtime
    if key not in _dataset_cache or _dataset_mtime_cache.get(key) != mtime:
        _dataset_cache[key] = _engine.load_sheet(p, sheet_name=sheet)
        _dataset_mtime_cache[key] = mtime
>>>>>>> a4386bf (Initial commit)
    return _dataset_cache[key]


def _all_datasets() -> dict[str, Dataset]:
    result: dict[str, Dataset] = {}
    for f in _engine.scan_folder(SAMPLES_DIR):
        if f.suffix.lower() == ".csv":
            continue
        try:
<<<<<<< HEAD
            for sh in _engine.list_sheets(f):
                key = _ds_key(str(f), sh)
                if key not in _dataset_cache:
                    _dataset_cache[key] = _engine.load_sheet(f, sheet_name=sh)
=======
            mtime = f.stat().st_mtime
            for sh in _engine.list_sheets(f):
                key = _ds_key(str(f), sh)
                if key not in _dataset_cache or _dataset_mtime_cache.get(key) != mtime:
                    _dataset_cache[key] = _engine.load_sheet(f, sheet_name=sh)
                    _dataset_mtime_cache[key] = mtime
>>>>>>> a4386bf (Initial commit)
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
<<<<<<< HEAD
    for f in sorted(SAMPLES_DIR.glob("*")):
        if f.suffix.lower() not in (".xlsx", ".csv", ".xls", ".xlsm", ".xlsb", ".tsv"):
=======
    for f in sorted(SAMPLES_DIR.rglob("*")):
        if not f.is_file() or f.suffix.lower() not in (".xlsx", ".csv", ".xls", ".xlsm", ".xlsb", ".tsv"):
>>>>>>> a4386bf (Initial commit)
            continue
        try:
            sheets = _engine.list_sheets(f)
        except Exception:
            sheets = []
<<<<<<< HEAD
        files.append({
            "name": f.name,
            "size": f.stat().st_size,
=======
        rel_path = str(f.relative_to(SAMPLES_DIR)).replace("\\", "/")
        folder = str(f.parent.relative_to(SAMPLES_DIR)).replace("\\", "/")
        files.append({
            "name": rel_path,
            "basename": f.name,
            "size": f.stat().st_size,
            "folder": "Root" if folder == "." else folder,
>>>>>>> a4386bf (Initial commit)
            "sheets": sheets,
        })
    return {"files": files, "count": len(files)}


<<<<<<< HEAD
=======
@api.get("/discovery")
def get_discovery_report():
    """Run pre-analysis file discovery across workspace."""
    global _cached_discovery_report
    now = time.time()
    if _cached_discovery_report and (now - _cached_discovery_report[0]) < 10.0:
        return _cached_discovery_report[1]
    report = _discovery_engine.scan_workspace(SAMPLES_DIR)
    rep_dict = report.to_dict()
    _cached_discovery_report = (now, rep_dict)
    return rep_dict


>>>>>>> a4386bf (Initial commit)
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
<<<<<<< HEAD
    dsets = list(_all_datasets().values())
    s = AnalyticsEngine().summarise(dsets)
    per_sheet = [{"name": d.name, "rows": d.rows, "cols": d.cols} for d in dsets]
    return {
=======
    global _cached_summary_data
    now = time.time()
    if _cached_summary_data and (now - _cached_summary_data[0]) < 10.0:
        return _cached_summary_data[1]
    dsets = list(_all_datasets().values())
    s = AnalyticsEngine().summarise(dsets)
    per_sheet = [{"name": d.name, "rows": d.rows, "cols": d.cols} for d in dsets]
    res_dict = {
>>>>>>> a4386bf (Initial commit)
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
<<<<<<< HEAD
=======
    _cached_summary_data = (now, res_dict)
    return res_dict
>>>>>>> a4386bf (Initial commit)


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


<<<<<<< HEAD
=======
# ---------------------------------------------------------------- Advanced Duplicate Engine Job API

# Cached active MDM consolidation result
_active_mdm_result: Any = None

def _run_cross_file_job(controller: JobController, rule_id: str = "rule_1", custom_fields: list[str] | None = None):
    global _current_job, _active_mdm_result
    try:
        datasets = list(_all_datasets().values())
        mdm_engine = MasterConsolidationEngine(column_detector=_column_detector)

        def progress_cb(pct, stage, cur_file, stats):
            _current_job["percent"] = round(pct, 1)
            _current_job["stage"] = stage
            _current_job["current_file"] = cur_file
            _current_job["stats"].update(stats)
            if controller.is_paused:
                _current_job["status"] = "paused"
            else:
                _current_job["status"] = "running"

        mdm_res = mdm_engine.process_mdm(
            datasets=datasets,
            rule_id=rule_id,
            custom_fields=custom_fields,
            controller=controller,
            progress_callback=progress_cb,
        )
        _active_mdm_result = mdm_res

        # Generate 8-sheet Master_Data.xlsx workbook
        master_wb_path = SAMPLES_DIR / "Master_Data.xlsx"
        ExcelExporter().generate_master_workbook(mdm_res, master_wb_path)

        # Format result payload for UI instantly
        exact_dup_groups = []
        for g_idx, m in enumerate(mdm_res.master_records):
            if m.duplicate_count > 0:
                exact_dup_groups.append({
                    "group_id": f"GRP_{g_idx + 1:04d}",
                    "master_id": m.master_id,
                    "confidence_score": 100.0,
                    "match_level": "Exact Match",
                })

        _current_job["status"] = "completed"
        _current_job["percent"] = 100.0
        _current_job["stage"] = "Consolidation Completed"
        _current_job["result"] = {
            "mdm_summary": mdm_res.to_summary_dict(),
            "master_records": [m.to_dict() for m in mdm_res.master_records[:500]],
            "duplicate_references": [r.to_dict() for r in mdm_res.duplicate_references[:1000]],
            "unique_records": [u.to_dict() for u in mdm_res.unique_records[:500]],
            "conflicts": [c.to_dict() for c in mdm_res.conflicts[:200]],
            "missing_data": mdm_res.missing_data[:200],
            "processing_logs": mdm_res.processing_logs,
            "summary": {
                "total_files": mdm_res.total_files,
                "total_worksheets": mdm_res.total_worksheets,
                "total_records": mdm_res.total_records,
                "exact_duplicates": mdm_res.duplicate_records_count,
                "unique_records": mdm_res.unique_records_count,
            },
            "exact_duplicates": exact_dup_groups[:200],
            "similar_records": [],
        }
    except Exception as e:
        if controller.is_cancelled:
            _current_job["status"] = "cancelled"
            _current_job["stage"] = "Cancelled by user"
        else:
            _current_job["status"] = "error"
            _current_job["error"] = str(e)


@api.post("/analyze-duplicates-advanced")
def start_advanced_analysis():
    global _current_job
    if _current_job["status"] == "running":
        return {"status": "already_running", "job": _current_job}

    controller = JobController()
    _current_job = {
        "status": "running",
        "percent": 0.0,
        "stage": "Scanning Files...",
        "current_file": "",
        "stats": {},
        "result": None,
        "error": None,
        "controller": controller,
    }

    thread = threading.Thread(target=_run_cross_file_job, args=(controller,), daemon=True)
    thread.start()
    return {"status": "started", "job": {"status": "running", "percent": 0.0}}


@api.post("/mdm/analyze")
def start_mdm_analysis(rule_id: str = Body("rule_1"), custom_fields: list[str] | None = Body(None)):
    global _current_job
    if _current_job["status"] == "running":
        return {"status": "already_running", "job": _current_job}

    controller = JobController()
    _current_job = {
        "status": "running",
        "percent": 0.0,
        "stage": "Scanning Files...",
        "current_file": "",
        "stats": {},
        "result": None,
        "error": None,
        "controller": controller,
    }

    thread = threading.Thread(
        target=_run_cross_file_job,
        args=(controller, rule_id, custom_fields),
        daemon=True
    )
    thread.start()
    return {"status": "started", "job": {"status": "running", "percent": 0.0}}


@api.get("/mdm/matching-rules")
def get_matching_rules():
    return {
        "rules": [
            {
                "rule_id": r.rule_id,
                "rule_name": r.rule_name,
                "fields": r.fields,
                "description": r.description,
            } for r in PREDEFINED_MATCHING_RULES
        ]
    }


@api.get("/job/status")
def get_job_status():
    global _current_job
    return {
        "status": _current_job["status"],
        "percent": _current_job["percent"],
        "stage": _current_job["stage"],
        "current_file": _current_job["current_file"],
        "stats": _current_job["stats"],
        "result": _current_job["result"],
        "error": _current_job["error"],
    }


@api.post("/job/control")
def control_job(action: str = Body(..., embed=True)):
    global _current_job
    controller: JobController | None = _current_job.get("controller")
    if not controller:
        raise HTTPException(400, "No active job controller found")

    if action == "pause":
        controller.pause()
        _current_job["status"] = "paused"
    elif action == "resume":
        controller.resume()
        _current_job["status"] = "running"
    elif action == "cancel":
        controller.cancel()
        _current_job["status"] = "cancelled"
    else:
        raise HTTPException(400, f"Unknown action: {action}")

    return {"status": "ok", "action": action, "job_status": _current_job["status"]}


@api.get("/download-duplicate-report")
def download_duplicate_report():
    report_path = SAMPLES_DIR / "Duplicate_Report.xlsx"
    if not report_path.exists():
        datasets = list(_all_datasets().values())
        analysis_res = CrossFileAnalyzer(column_detector=_column_detector).analyze(datasets)
        ExcelExporter().generate_duplicate_report(analysis_res, report_path)

    return FileResponse(
        report_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="Duplicate_Report.xlsx"'},
    )


@api.get("/download-master-workbook")
def download_master_workbook():
    report_path = SAMPLES_DIR / "Master_Data.xlsx"
    if not report_path.exists():
        datasets = list(_all_datasets().values())
        mdm_res = MasterConsolidationEngine(column_detector=_column_detector).process_mdm(datasets)
        ExcelExporter().generate_master_workbook(mdm_res, report_path)

    return FileResponse(
        report_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="Master_Data.xlsx"'},
    )


from pydantic import BaseModel

class ConflictResolvePayload(BaseModel):
    conflict_id: str
    action: str

@api.post("/mdm/resolve-conflict")
def resolve_conflict(payload: ConflictResolvePayload):
    global _current_job, _active_mdm_result
    conflict_id = payload.conflict_id
    action = payload.action
    if not _current_job.get("result") or not _current_job["result"].get("conflicts"):
        raise HTTPException(400, "No active analysis conflicts found")

    conflicts = _current_job["result"]["conflicts"]
    matched = None
    for c in conflicts:
        if c.get("conflict_id") == conflict_id:
            c["status"] = f"resolved_{action}" if not action.startswith("resolved_") else action
            matched = c
            break

    if action == "apply_all":
        for c in conflicts:
            c["status"] = "resolved_keep_first"

    return {"status": "success", "resolved_conflict": matched, "total_conflicts": len(conflicts)}


@api.get("/aliases")
def get_column_aliases():
    return {"aliases": _column_detector.get_aliases_config()}


@api.post("/aliases")
def add_column_alias(canonical: str = Body(...), alias: str = Body(...)):
    _column_detector.add_alias(canonical, alias)
    return {"status": "ok", "aliases": _column_detector.get_aliases_config()}


>>>>>>> a4386bf (Initial commit)
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


<<<<<<< HEAD
=======
@api.post("/clear-workspace")
def clear_workspace(keep_samples: bool = Query(False)):
    """Clear all uploaded files, extracted folders, dataset caches, and job results."""
    global _dataset_cache, _current_job

    _dataset_cache.clear()
    _current_job = {
        "status": "idle",
        "percent": 0.0,
        "stage": "",
        "current_file": "",
        "stats": {},
        "result": None,
        "error": None,
        "controller": None,
    }

    import shutil
    default_sample_names = {"customers_region_a.xlsx", "customers_region_b.xlsx", "invoices_2024.xlsx", "products_catalog.xlsx", "customers.csv"}

    removed_count = 0
    if SAMPLES_DIR.exists():
        for item in list(SAMPLES_DIR.glob("*")):
            if keep_samples and item.name in default_sample_names:
                continue
            try:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
                removed_count += 1
            except Exception:
                pass

    report = _discovery_engine.scan_workspace(SAMPLES_DIR)
    return {
        "status": "success",
        "message": f"Cleared {removed_count} workspace item(s).",
        "discovery": report.to_dict(),
    }


@api.post("/upload-batch")
async def upload_batch(
    request: Request,
    files: list[UploadFile] = File(default=[]),
    paths: list[str] = Form(default=[]),
):
    """Batch upload endpoint — fast return with async analysis via job queue."""
    global _job_queue, _dataset_cache
    form = await request.form()
    if not files:
        files = [v for k, v in form.multi_items() if hasattr(v, "filename") and v.filename]
        if not paths:
            paths = [str(v) for k, v in form.multi_items() if k in ("paths", "paths[]") and isinstance(v, str)]

    if not files:
        raise HTTPException(400, "No files uploaded")

    # STEP 1: Save files quickly (sync, but fast)
    saved_files = []
    for i, file in enumerate(files):
        if not file.filename:
            continue

        rel_p = paths[i] if (paths and i < len(paths) and paths[i]) else file.filename
        rel_p = rel_p.replace("\\", "/").lstrip("/")

        target_path = SAMPLES_DIR / rel_p
        target_path.parent.mkdir(parents=True, exist_ok=True)

        content = await file.read()
        with open(target_path, "wb") as f:
            f.write(content)

        suffix = target_path.suffix.lower()
        if suffix == ".zip":
            extract_dir = target_path.parent / f"_extracted_{target_path.stem}"
            extract_dir.mkdir(parents=True, exist_ok=True)
            try:
                with zipfile.ZipFile(io.BytesIO(content)) as zf:
                    zf.extractall(extract_dir)
            except Exception as e:
                pass

        saved_files.append(str(target_path.relative_to(SAMPLES_DIR)).replace("\\", "/"))

    # STEP 2: Invalidate cache and queue analysis job
    _dataset_cache.clear()
    job_id = _job_queue.enqueue()

    # STEP 3: Queue background analysis (runs independently)
    _executor.submit(
        _run_batch_analysis_job,
        job_id=job_id,
        saved_files=saved_files,
    )

    # STEP 4: Return immediately with job ID (user can poll for results)
    return {
        "status": "accepted",
        "type": "batch",
        "job_id": job_id,
        "files_uploaded": len(saved_files),
        "saved_files": saved_files,
        "message": "Files uploaded. Analysis started in background. Check /api/job/{job_id} for progress.",
    }


def _run_batch_analysis_job(job_id: str, saved_files: list[str]) -> None:
    """Background job: analyze uploaded files."""
    global _job_queue, _dataset_cache, _cached_discovery_report, _cached_summary_data
    try:
        tracker = ProgressTracker(
            _job_queue, job_id,
            stages=["Scanning Files", "Loading Datasets", "Profiling Data", "Generating Report"],
        )

        # Stage 1: Fast incremental discovery
        tracker.advance_stage("Scanning Files")
        report = _discovery_engine_fast.scan_workspace_incremental(SAMPLES_DIR)

        # Stage 2: Load first dataset for preview
        tracker.advance_stage("Loading Datasets")
        valid_spreadsheets = [f for f in saved_files if Path(f).suffix.lower() in (".xlsx", ".csv", ".xls", ".xlsm", ".xlsb", ".tsv")]
        first_file = valid_spreadsheets[0] if valid_spreadsheets else None
        ds = None
        if first_file:
            try:
                ds = _load(first_file)
            except Exception as e:
                log.warning(f"Failed to load {first_file}: {e}")

        # Stage 3: Profile datasets
        tracker.advance_stage("Profiling Data")
        datasets = list(_all_datasets().values())
        summary = _analytics_engine_fast.summarise(datasets)

        # Stage 4: Compile results
        tracker.advance_stage("Generating Report")

        result = {
            "files_uploaded": len(saved_files),
            "saved_files": saved_files,
            "discovery": report.to_dict(),
            "active_sheet": ds.source.sheet_name if (ds and ds.source) else None,
            "dataset": {
                "name": ds.name if ds else (first_file or "Batch Upload"),
                "rows": ds.rows if ds else 0,
                "cols": ds.cols if ds else 0,
                "columns": ds.columns if ds else [],
                "dtypes": {c: str(ds.df.schema[c]) for c in ds.columns} if ds else {},
                "preview": _df_to_records(ds.df, limit=100) if ds else [],
            } if ds else None,
            "summary": {
                "total_files": summary.total_files,
                "total_sheets": summary.total_sheets,
                "total_rows": summary.total_rows,
                "unique_rows": summary.unique_rows,
                "duplicate_rows": summary.duplicate_rows,
                "data_quality_score": summary.data_quality_score,
                "validation_score": summary.validation_score,
            }
        }

        # Invalidate caches
        _cached_discovery_report = None
        _cached_summary_data = None

        _job_queue.complete_job(job_id, result)
        log.info(f"Analysis complete for job {job_id}")

    except Exception as e:
        log.error(f"Analysis failed for job {job_id}: {e}", exc_info=True)
        _job_queue.fail_job(job_id, str(e))


@api.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Single file upload — fast return with async analysis."""
    global _job_queue, _dataset_cache

    if not file.filename:
        raise HTTPException(400, "Invalid file name")
    suffix = Path(file.filename).suffix.lower()
    if suffix not in (".xlsx", ".csv", ".xls", ".xlsm", ".xlsb", ".tsv", ".zip"):
        raise HTTPException(400, f"Unsupported file extension: {suffix}")

    content = await file.read()

    # Save file
    if suffix == ".zip":
        subfolder_name = Path(file.filename).stem
        target_subfolder = SAMPLES_DIR / subfolder_name
        target_subfolder.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            zf.extractall(target_subfolder)
        extracted_files = [str(p.relative_to(SAMPLES_DIR)).replace("\\", "/")
                          for p in sorted(target_subfolder.rglob("*"))
                          if p.is_file() and p.suffix.lower() in (".xlsx", ".csv", ".xls", ".xlsm", ".xlsb", ".tsv")]
        saved_files = extracted_files
    else:
        target_path = SAMPLES_DIR / file.filename
        with open(target_path, "wb") as f:
            f.write(content)
        saved_files = [file.filename]

    # Invalidate cache and queue analysis
    _dataset_cache.clear()
    job_id = _job_queue.enqueue()

    # Queue background analysis
    _executor.submit(
        _run_single_file_analysis_job,
        job_id=job_id,
        filename=file.filename,
        saved_files=saved_files,
    )

    return {
        "status": "accepted",
        "filename": file.filename,
        "job_id": job_id,
        "files_saved": len(saved_files),
        "message": "File uploaded. Analysis started in background. Check /api/job/{job_id} for progress.",
    }


def _run_single_file_analysis_job(job_id: str, filename: str, saved_files: list[str]) -> None:
    """Background job: analyze uploaded file."""
    global _job_queue, _dataset_cache, _cached_discovery_report, _cached_summary_data
    try:
        tracker = ProgressTracker(
            _job_queue, job_id,
            stages=["Scanning Files", "Loading Datasets", "Profiling Data"],
        )

        # Stage 1: Discovery
        tracker.advance_stage("Scanning Files")
        report = _discovery_engine_fast.scan_workspace_incremental(SAMPLES_DIR)

        # Stage 2: Load dataset
        tracker.advance_stage("Loading Datasets")
        first_file = saved_files[0] if saved_files else None
        ds = None
        sheets = []
        if first_file:
            try:
                sheets = _engine.list_sheets(SAMPLES_DIR / first_file)
                ds = _load(first_file, sheets[0] if sheets else None)
            except Exception as e:
                log.warning(f"Failed to load {first_file}: {e}")

        # Stage 3: Profile
        tracker.advance_stage("Profiling Data")

        result = {
            "filename": filename,
            "files_saved": len(saved_files),
            "saved_files": saved_files,
            "sheets": sheets,
            "active_sheet": ds.source.sheet_name if (ds and ds.source) else None,
            "dataset": {
                "name": ds.name if ds else filename,
                "rows": ds.rows if ds else 0,
                "cols": ds.cols if ds else 0,
                "columns": ds.columns if ds else [],
                "dtypes": {c: str(ds.df.schema[c]) for c in ds.columns} if ds else {},
                "preview": _df_to_records(ds.df, limit=100) if ds else [],
            } if ds else None,
        }

        # Invalidate caches
        _cached_discovery_report = None
        _cached_summary_data = None

        _job_queue.complete_job(job_id, result)
        log.info(f"Upload analysis complete for job {job_id}")

    except Exception as e:
        log.error(f"Upload analysis failed for job {job_id}: {e}", exc_info=True)
        _job_queue.fail_job(job_id, str(e))


@api.get("/download-desktop")
def download_desktop():
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_name in ["run.py", "requirements.txt", "README.md"]:
            p = APP_ROOT / file_name
            if p.exists():
                zf.write(p, arcname=file_name)
        
        bi_dir = APP_ROOT / "bi_platform"
        if bi_dir.exists():
            for root_path, dirs, files in os.walk(bi_dir):
                if "__pycache__" in root_path:
                    continue
                for f in files:
                    if f.endswith(".pyc"):
                        continue
                    full_p = Path(root_path) / f
                    rel_p = full_p.relative_to(APP_ROOT)
                    zf.write(full_p, arcname=str(rel_p))
                    
        run_bat = "@echo off\r\necho Starting ExcelIntel Desktop App...\r\npip install -r requirements.txt\r\npython run.py\r\npause\r\n"
        zf.writestr("start_app.bat", run_bat)

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="ExcelIntel-Desktop-App.zip"'}
    )


>>>>>>> a4386bf (Initial commit)
@api.get("/screenshots/{name}")
def screenshot(name: str):
    p = DOCS_DIR / name
    if not p.exists() or not p.name.startswith("screenshot"):
        raise HTTPException(404, "Not found")
    return FileResponse(p, media_type="image/png")


<<<<<<< HEAD
=======
# ---------------------------------------------------------------------------- job queue
@api.get("/job/{job_id}")
def get_job_status(job_id: str):
    """Get status of background analysis job."""
    job = _job_queue.get_job(job_id)
    if not job:
        raise HTTPException(404, f"Job not found: {job_id}")
    return job.to_dict()


@api.post("/job/{job_id}/cancel")
def cancel_job(job_id: str):
    """Cancel a queued analysis job."""
    _job_queue.cancel_job(job_id)
    job = _job_queue.get_job(job_id)
    if not job:
        raise HTTPException(404, f"Job not found: {job_id}")
    return {"status": "cancelled", "job": job.to_dict()}


@api.post("/job/{job_id}/result")
def get_job_result(job_id: str):
    """Get result of completed analysis job."""
    job = _job_queue.get_job(job_id)
    if not job:
        raise HTTPException(404, f"Job not found: {job_id}")
    if job.status.value != "completed":
        return {
            "status": "not_ready",
            "job_id": job_id,
            "current_status": job.status.value,
            "progress": job.progress,
            "stage": job.stage,
        }
    return {
        "status": "ready",
        "job_id": job_id,
        "result": job.result,
    }


>>>>>>> a4386bf (Initial commit)
# ---------------------------------------------------------------------------- app
app.include_router(api)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)
