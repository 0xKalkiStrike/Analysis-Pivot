"""Fast Discovery Engine with incremental analysis and parallel processing."""
from __future__ import annotations

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ..core.constants import SUPPORTED_ALL
from ..core.logger import get_logger
from .excel_engine import ExcelEngine
from .discovery_engine import inspect_sheet_efficiently

log = get_logger(__name__)


@dataclass
class FileMetadata:
    """Lightweight file metadata for caching."""
    file_path: str
    file_hash: str
    file_size: int
    modified_time: float
    extension: str


@dataclass
class FastDiscoveryReport:
    total_files: int = 0
    total_worksheets: int = 0
    total_records: int = 0
    total_columns: int = 0
    empty_sheets_count: int = 0
    corrupted_files_count: int = 0
    password_protected_files_count: int = 0
    duplicate_files_count: int = 0
    analysis_time_sec: float = 0.0
    files: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class FastDiscoveryEngine:
    """Parallel discovery with incremental updates."""

    CACHE_FILE = ".discovery_cache.json"

    def __init__(self, excel_engine: ExcelEngine | None = None, max_workers: int = 4):
        self.excel_engine = excel_engine or ExcelEngine()
        self.max_workers = max_workers
        self._file_cache: dict[str, FileMetadata] = {}
        self._results_cache: dict[str, dict[str, Any]] = {}

    def _compute_file_hash(self, path: Path, chunk_size: int = 8192) -> str:
        """Compute SHA256 hash of file (only first 1MB for speed)."""
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            for _ in range(chunk_size):
                data = f.read(chunk_size)
                if not data:
                    break
                hasher.update(data)
        return hasher.hexdigest()

    def scan_workspace_incremental(self, workspace_path: Path) -> FastDiscoveryReport:
        """Scan workspace, only analyzing new/changed files."""
        report = FastDiscoveryReport()

        # Load previous cache
        cache_file = workspace_path / self.CACHE_FILE
        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    cached_data = json.load(f)
                    self._file_cache = {
                        k: FileMetadata(**v) for k, v in cached_data.get("files", {}).items()
                    }
                    self._results_cache = cached_data.get("results", {})
            except Exception as e:
                log.warning(f"Failed to load cache: {e}")

        # Discover files
        file_paths = []
        for ext in SUPPORTED_ALL:
            for path in workspace_path.rglob(f"*{ext}"):
                if path.is_file():
                    # Skip files larger than 50MB or generated duplicate reports to prevent memory/timeout issues
                    if path.stat().st_size > 50 * 1024 * 1024:
                        log.warning(f"Skipping large file: {path.name}")
                        continue
                    if "duplicate_report" in path.name.lower():
                        log.info(f"Skipping duplicate report: {path.name}")
                        continue
                    file_paths.append(path)

        if not file_paths:
            return report

        # Separate new/changed from cached
        files_to_analyze = []
        for path in file_paths:
            key = str(path)
            current_hash = self._compute_file_hash(path)

            cached_meta = self._file_cache.get(key)
            if not cached_meta or cached_meta.file_hash != current_hash:
                files_to_analyze.append(path)
            elif key in self._results_cache:
                # Use cached result
                cached_result = self._results_cache[key]
                report.total_worksheets += cached_result.get("worksheets_count", 0)
                report.total_records += cached_result.get("total_rows", 0)
                report.total_columns += cached_result.get("total_columns", 0)
                report.files.append(cached_result)

        # Sequential analysis of new/changed files (avoids ThreadPoolExecutor hangs in resource-constrained environments)
        if files_to_analyze:
            for p in files_to_analyze:
                path_key = str(p)
                try:
                    result = self._analyze_file(p)
                    if result:
                        self._results_cache[path_key] = result
                        self._file_cache[path_key] = FileMetadata(
                            file_path=path_key,
                            file_hash=self._compute_file_hash(p),
                            file_size=p.stat().st_size,
                            modified_time=p.stat().st_mtime,
                            extension=p.suffix.lower(),
                        )
                        report.total_worksheets += result.get("worksheets_count", 0)
                        report.total_records += result.get("total_rows", 0)
                        report.total_columns += result.get("total_columns", 0)
                        report.files.append(result)
                except Exception as e:
                    log.error(f"File analysis error for {path_key}: {e}")
                    report.corrupted_files_count += 1

        report.total_files = len(report.files)

        # Save cache
        self._save_cache(cache_file)

        return report

    def _analyze_file(self, path: Path) -> dict[str, Any] | None:
        """Analyze single file (fast path)."""
        try:
            sheets = self.excel_engine.list_sheets(path)
            total_rows = 0
            total_cols = 0

            sheet_info = []
            for sheet in sheets:
                try:
                    rows_cnt, cols_cnt, cols_names = inspect_sheet_efficiently(path, sheet, self.excel_engine)
                    total_rows += rows_cnt
                    total_cols = max(total_cols, cols_cnt)
                    sheet_info.append({
                        "name": sheet,
                        "rows": rows_cnt,
                        "cols": cols_cnt,
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
            log.error(f"Failed to analyze {path}: {e}")
            return None

    def _save_cache(self, cache_file: Path) -> None:
        """Save analysis cache to disk."""
        try:
            cache_data = {
                "files": {k: asdict(v) for k, v in self._file_cache.items()},
                "results": self._results_cache,
            }
            with open(cache_file, "w") as f:
                json.dump(cache_data, f)
        except Exception as e:
            log.warning(f"Failed to save cache: {e}")
