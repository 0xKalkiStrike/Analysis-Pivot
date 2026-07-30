"""Project workspace persistence — save/load/import/export .eip files (JSON)."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from ..core.config import get_config
from ..core.logger import get_logger

log = get_logger(__name__)


@dataclass
class Project:
    name: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    files: list[str] = field(default_factory=list)
    sheets: list[dict[str, Any]] = field(default_factory=list)
    settings: dict[str, Any] = field(default_factory=dict)
    bookmarks: list[dict[str, Any]] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)


class ProjectService:
    EXT = ".eip"  # ExcelIntel Project

    def __init__(self) -> None:
        self.cfg = get_config()

    def new(self, name: str) -> Project:
        return Project(name=name)

    def path_for(self, name: str) -> Path:
        return Path(self.cfg.projects_dir) / f"{name}{self.EXT}"

    def save(self, project: Project, path: str | Path | None = None) -> str:
        p = Path(path) if path else self.path_for(project.name)
        p.parent.mkdir(parents=True, exist_ok=True)
        project.updated_at = datetime.utcnow().isoformat()
        p.write_text(json.dumps(asdict(project), indent=2))
        self._touch_recent(str(p))
        return str(p)

    def load(self, path: str | Path) -> Project:
        p = Path(path)
        data = json.loads(p.read_text())
        proj = Project(**data)
        self._touch_recent(str(p))
        return proj

    def list_projects(self) -> list[Path]:
        return sorted(Path(self.cfg.projects_dir).glob(f"*{self.EXT}"))

    def _touch_recent(self, path: str) -> None:
        recent = [path] + [r for r in self.cfg.recent_projects if r != path]
        self.cfg.recent_projects = recent[:10]
        self.cfg.save()
