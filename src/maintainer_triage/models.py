from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class Issue:
    number: int
    title: str
    body: str = ""
    labels: tuple[str, ...] = ()
    created_at: datetime | None = None
    comments: int = 0
    reactions: dict[str, int] = field(default_factory=dict)
    url: str | None = None

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "Issue":
        labels = data.get("labels", ())
        if labels and isinstance(labels[0], dict):
            labels = [item.get("name", "") for item in labels]

        reactions = data.get("reactions") or {}
        if not isinstance(reactions, dict):
            reactions = {}

        return cls(
            number=int(data.get("number", 0)),
            title=str(data.get("title", "")).strip(),
            body=str(data.get("body", "") or "").strip(),
            labels=tuple(str(label).strip().lower() for label in labels if str(label).strip()),
            created_at=_parse_datetime(data.get("created_at")),
            comments=int(data.get("comments", 0) or 0),
            reactions={str(key): int(value or 0) for key, value in reactions.items()},
            url=data.get("html_url") or data.get("url"),
        )

    @property
    def searchable_text(self) -> str:
        return " ".join((self.title, self.body, " ".join(self.labels))).lower()


@dataclass(frozen=True)
class TriageResult:
    issue: Issue
    category: str
    priority: str
    score: int
    reasons: tuple[str, ...]
    next_action: str
