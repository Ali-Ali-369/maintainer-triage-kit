from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict

from .models import TriageResult


def render_markdown(results: list[TriageResult]) -> str:
    ordered = sorted(results, key=lambda item: (-item.score, item.issue.number))
    counts = Counter(item.category for item in ordered)
    lines = [
        "# Maintainer Triage Report",
        "",
        "## Summary",
        "",
    ]
    for category, count in sorted(counts.items()):
        lines.append(f"- {category}: {count}")

    lines.extend(["", "## Queue", ""])
    for item in ordered:
        issue_ref = f"#{item.issue.number}" if item.issue.number else "(untracked)"
        title = item.issue.title or "Untitled issue"
        lines.append(f"### {item.priority} {issue_ref} - {title}")
        lines.append("")
        lines.append(f"- Category: {item.category}")
        lines.append(f"- Score: {item.score}")
        lines.append(f"- Reasons: {', '.join(item.reasons)}")
        lines.append(f"- Next action: {item.next_action}")
        if item.issue.url:
            lines.append(f"- URL: {item.issue.url}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_json(results: list[TriageResult]) -> str:
    payload = []
    for result in sorted(results, key=lambda item: (-item.score, item.issue.number)):
        item = asdict(result)
        created_at = result.issue.created_at.isoformat() if result.issue.created_at else None
        item["issue"]["created_at"] = created_at
        payload.append(item)
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"
