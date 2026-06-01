from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone

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


def render_board_json(
    results: list[TriageResult],
    *,
    project_name: str = "Maintainer Triage Board",
    repo: str = "local/maintainer-triage",
    release: str = "0.1.0",
) -> str:
    ordered = sorted(results, key=lambda item: (-item.score, item.issue.number))
    board = {
        "project": {
            "name": project_name,
            "repo": repo,
            "release": release,
            "window": datetime.now(timezone.utc).strftime("%B %Y"),
        },
        "metrics": _board_metrics(ordered),
        "activity": _board_activity(ordered),
        "issues": [_board_issue(item) for item in ordered],
        "release": _board_release(ordered),
        "risks": _board_risks(ordered),
    }
    return json.dumps(board, indent=2, sort_keys=True) + "\n"


def _board_metrics(results: list[TriageResult]) -> list[dict[str, str | int]]:
    high_priority = sum(1 for item in results if item.priority in {"P0", "P1"})
    blockers = sum(1 for item in results if item.category in {"security", "bug", "dependency"})
    return [
        {"label": "Open issues", "value": len(results), "delta": "imported"},
        {"label": "PRs awaiting review", "value": high_priority, "delta": "needs owner"},
        {"label": "Release blockers", "value": blockers, "delta": "triage"},
        {"label": "Median response", "value": "n/a", "delta": "local export"},
    ]


def _board_activity(results: list[TriageResult]) -> list[dict[str, int | str]]:
    counts: Counter[str] = Counter()
    for item in results:
        if item.issue.created_at:
            label = item.issue.created_at.strftime("%a")
        else:
            label = "New"
        counts[label] += 1
    labels = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun", "New")
    return [{"day": label, "issues": counts[label], "prs": 0} for label in labels if counts[label] or label != "New"]


def _board_issue(result: TriageResult) -> dict[str, str | int]:
    return {
        "id": result.issue.number,
        "title": result.issue.title or "Untitled issue",
        "priority": result.priority,
        "type": result.category,
        "owner": "Unassigned",
        "status": _status_for(result),
        "age": _age_for(result),
        "risk": min(result.score, 100),
    }


def _status_for(result: TriageResult) -> str:
    if result.category == "security":
        return "Review"
    if result.priority in {"P0", "P1"}:
        return "Needs repro"
    if result.category in {"docs", "question"}:
        return "Open"
    return "Ready"


def _age_for(result: TriageResult) -> str:
    if not result.issue.created_at:
        return "new"
    days = max((datetime.now(timezone.utc) - result.issue.created_at).days, 0)
    return f"{days}d"


def _board_release(results: list[TriageResult]) -> list[dict[str, bool | str]]:
    categories = {item.category for item in results}
    high_priority_bugs = any(item.category == "bug" and item.priority in {"P0", "P1"} for item in results)
    return [
        {"label": "Security review", "done": "security" not in categories},
        {"label": "Regression tests", "done": not high_priority_bugs},
        {"label": "Docs updated", "done": "docs" not in categories},
        {"label": "Changelog drafted", "done": False},
        {"label": "Dependency scan", "done": "dependency" not in categories},
    ]


def _board_risks(results: list[TriageResult]) -> list[dict[str, int | str]]:
    return [
        {
            "label": "Security-sensitive issues",
            "count": sum(1 for item in results if item.category == "security"),
            "severity": "high",
        },
        {
            "label": "High-priority queue",
            "count": sum(1 for item in results if item.priority in {"P0", "P1"}),
            "severity": "medium",
        },
        {
            "label": "Dependency maintenance",
            "count": sum(1 for item in results if item.category == "dependency"),
            "severity": "medium",
        },
        {
            "label": "Docs and support drift",
            "count": sum(1 for item in results if item.category in {"docs", "question"}),
            "severity": "low",
        },
    ]
