"""Application configuration — offline, file-based, no external services."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AppConfig:
    """Persistent user + application configuration."""

    # Paths
    home_dir: str = str(Path.home() / ".excelintel")
    projects_dir: str = str(Path.home() / ".excelintel" / "projects")
    cache_dir: str = str(Path.home() / ".excelintel" / "cache")
    logs_dir: str = str(Path.home() / ".excelintel" / "logs")
    exports_dir: str = str(Path.home() / ".excelintel" / "exports")

    # UI
    theme: str = "dark"  # dark | light | auto
    accent_color: str = "#7c5cff"
    font_family: str = "Inter"
    font_size: int = 10
    high_dpi: bool = True

    # Engine
    chunk_size: int = 100_000
    max_workers: int = max(2, (os.cpu_count() or 4) - 1)
    similarity_threshold: float = 0.88
    fuzzy_algorithm: str = "weighted_ratio"  # weighted_ratio | token_sort | token_set | partial | ratio
    use_duckdb: bool = True

    # Behaviour
    auto_backup: bool = True
    autosave_interval_sec: int = 60
    recent_projects: list[str] = field(default_factory=list)

    @property
    def config_file(self) -> Path:
        return Path(self.home_dir) / "config.json"

    def ensure_dirs(self) -> None:
        for p in (self.home_dir, self.projects_dir, self.cache_dir, self.logs_dir, self.exports_dir):
            Path(p).mkdir(parents=True, exist_ok=True)

    def save(self) -> None:
        self.ensure_dirs()
        self.config_file.write_text(json.dumps(asdict(self), indent=2, default=str))

    @classmethod
    def load(cls) -> "AppConfig":
        cfg = cls()
        cfg.ensure_dirs()
        if cfg.config_file.exists():
            try:
                data: dict[str, Any] = json.loads(cfg.config_file.read_text())
                for k, v in data.items():
                    if hasattr(cfg, k):
                        setattr(cfg, k, v)
            except (json.JSONDecodeError, OSError):
                pass
        return cfg


_config: AppConfig | None = None


def get_config() -> AppConfig:
    global _config
    if _config is None:
        _config = AppConfig.load()
    return _config
