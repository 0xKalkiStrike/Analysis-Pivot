"""ULTRA-FAST Discovery Engine using multiprocessing + memory mapping."""
from __future__ import annotations

import hashlib
import json
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Any
import duckdb

from ..core.constants import SUPPORTED_ALL
from ..core.logger import get_logger
from .excel_engine import ExcelEngine

log = get_logger(__name__)


def _analyze_file_worker(file_path: str, excel_engine: ExcelEngine | None = None) -> dict[str, Any] | None:
    """Worker function for parallel file analysis."""
    if excel_engine is None:
        from .excel_engine import ExcelEngine
        excel_engine = ExcelEngine()

    try:
        path = Path(file_path)
        sheets = excel_engine.list_sheets(path)
        total_rows = 0
        total_cols = 0
        sheet_info = []

        for sheet in sheets:
            try:
                ds = excel_engine.load_sheet(path, sheet_name=sheet)
                total_rows += ds.rows
                total_cols = max(total_cols, ds.cols)
                sheet_info.append({
                    "name": sheet,
                    "rows": ds.rows,
                    "cols": ds.cols,
                })
            except Exception:
                pass

        return {
            "file_path": str(path),
            "file_name": path.name,
            "file_size": path.stat().st_size,
            "extension": path.suffix.lower(),
            "status": "ok",
            "worksheets_count": len(sheets),
            "total_rows": total_rows,
            "total_columns": total_cols,
            "sheets": sheet_info,
        }
    except Exception as e:
        log.error(f"Failed to analyze {file_path}: {e}")
        return None


class UltraFastDiscoveryEngine:
    """True parallel discovery using multiprocessing."""

    CACHE_FILE = ".discovery_cache.json"

    def __init__(self, excel_engine: ExcelEngine | None = None):
        self.excel_engine = excel_engine or ExcelEngine()
        self._file_cache: dict[str, dict[str, Any]] = {}
        self._results_cache: dict[str, dict[str, Any]] = {}
        self.max_workers = max(2, cpu_count() - 1)  # Use all CPUs

    def _compute_file_hash(self, path: Path) -> str:
        """Quick hash: first 10MB only."""
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            for _ in range(10):  # 10 * 1MB = first 10MB
                data = f.read(1024 * 1024)
                if not data:
                    break
                hasher.update(data)
        return hasher.hexdigest()

    def scan_workspace_instant(self, workspace_path: Path) -> dict[str, Any]:
        """Instant workspace scan using multiprocessing."""
        # Load cache
        cache_file = workspace_path / self.CACHE_FILE
        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    cached = json.load(f)
                    self._file_cache = cached.get("files", {})
                    self._results_cache = cached.get("results", {})
            except Exception as e:
                log.warning(f"Cache load failed: {e}")

        # Discover all files
        file_paths = []
        for ext in SUPPORTED_ALL:
            file_paths.extend(workspace_path.rglob(f"*{ext}"))

        if not file_paths:
            return {"total_files": 0, "files": []}

        # Separate new/changed from cached
        to_analyze = []
        files_data = []
        total_worksheets = 0
        total_records = 0
        total_columns = 0

        for path in file_paths:
            key = str(path)
            current_hash = self._compute_file_hash(path)
            cached_meta = self._file_cache.get(key)

            if not cached_meta or cached_meta.get("hash") != current_hash:
                to_analyze.append(str(path))
            elif key in self._results_cache:
                result = self._results_cache[key]
                files_data.append(result)
                total_worksheets += result.get("worksheets_count", 0)
                total_records += result.get("total_rows", 0)
                total_columns += result.get("total_columns", 0)

        # PARALLEL ANALYSIS using multiprocessing (true parallelism, not threading)
        if to_analyze:
            with Pool(self.max_workers) as pool:
                results = pool.map(lambda p: _analyze_file_worker(p, self.excel_engine), to_analyze)

            for file_path, result in zip(to_analyze, results):
                if result:
                    self._results_cache[file_path] = result
                    self._file_cache[file_path] = {
                        "hash": self._compute_file_hash(Path(file_path)),
                        "size": Path(file_path).stat().st_size,
                    }
                    files_data.append(result)
                    total_worksheets += result.get("worksheets_count", 0)
                    total_records += result.get("total_rows", 0)
                    total_columns += result.get("total_columns", 0)

        # Save cache
        self._save_cache(cache_file)

        return {
            "total_files": len(files_data),
            "total_worksheets": total_worksheets,
            "total_records": total_records,
            "total_columns": total_columns,
            "files": files_data,
        }

    def _save_cache(self, cache_file: Path) -> None:
        """Save analysis cache."""
        try:
            with open(cache_file, "w") as f:
                json.dump({
                    "files": self._file_cache,
                    "results": self._results_cache,
                }, f)
        except Exception as e:
            log.warning(f"Cache save failed: {e}")
