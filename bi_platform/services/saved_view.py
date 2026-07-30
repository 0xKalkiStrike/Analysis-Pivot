"""Saved View — capture and restore workspace state per project."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class SavedView:
    """A named workspace snapshot."""
    name: str
    tab: str = "dashboard"              # dashboard | data | duplicates | validation | sql | charts | pivot | relationships
    dataset: str | None = None
    search_text: str = ""
    search_column: str = ""             # empty = All columns
    duplicate_column: str = "Smart (auto)"
    duplicate_algo: str = "weighted_ratio"
    duplicate_threshold: float = 88.0
    duplicate_clean: bool = True
    pivot_rows: list[str] = field(default_factory=list)
    pivot_cols: list[str] = field(default_factory=list)
    pivot_value: str = ""
    pivot_agg: str = "sum"
    sql_query: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SavedView":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})
