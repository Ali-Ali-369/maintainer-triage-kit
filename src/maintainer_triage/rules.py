from __future__ import annotations

from datetime import datetime, timezone

from .models import Issue, TriageResult

SECURITY_TERMS = ("cve", "vulnerability", "exploit", "secret", "token leak", "rce")
BUG_TERMS = ("crash", "traceback", "regression", "broken", "exception", "fails")
DEPENDENCY_TERMS = ("dependency", "dependencies", "upgrade", "lockfile", "supply chain")
DOCS_TERMS = ("readme", "docs", "documentation", "typo", "example")
QUESTION_TERMS = ("how do i", "question", "usage", "support")
ENHANCEMENT_TERMS = ("feature", "enhancement", "add support", "proposal")


def triage_issue(issue: Issue, *, now: datetime | None = None) -> TriageResult:
    now = now or datetime.now(timezone.utc)
    text = issue.searchable_text
    reasons: list[str] = []

    category = _category_for(text, issue.labels, reasons)
    score = _base_score(category)

    if any(label in issue.labels for label in ("priority: high", "p0", "p1", "urgent")):
        score += 35
        reasons.append("high-priority label")

    thumbs_up = issue.reactions.get("+1", 0) + issue.reactions.get("thumbs_up", 0)
    if thumbs_up >= 10:
        score += 15
        reasons.append("strong community signal")
    elif thumbs_up >= 3:
        score += 8
        reasons.append("moderate community signal")

    if issue.comments >= 8:
        score += 8
        reasons.append("active discussion")

    if issue.created_at:
        age_days = max((now - issue.created_at).days, 0)
        if age_days >= 90:
            score += 10
            reasons.append("stale but unresolved")
        elif age_days <= 7:
            score += 5
            reasons.append("new report")

    priority = _priority_for(score)
    return TriageResult(
        issue=issue,
        category=category,
        priority=priority,
        score=score,
        reasons=tuple(reasons or ("no strong signal",)),
        next_action=_next_action(category, priority),
    )


def _category_for(text: str, labels: tuple[str, ...], reasons: list[str]) -> str:
    label_text = " ".join(labels)

    if "security" in labels or _contains_any(text, SECURITY_TERMS):
        reasons.append("security-sensitive language")
        return "security"
    if "bug" in labels or _contains_any(text, BUG_TERMS):
        reasons.append("bug or regression signal")
        return "bug"
    if "dependencies" in labels or "dependency" in labels or _contains_any(text, DEPENDENCY_TERMS):
        reasons.append("dependency maintenance signal")
        return "dependency"
    if "documentation" in label_text or "docs" in labels or _contains_any(text, DOCS_TERMS):
        reasons.append("documentation signal")
        return "docs"
    if "question" in labels or _contains_any(text, QUESTION_TERMS):
        reasons.append("support or usage signal")
        return "question"
    if "enhancement" in labels or _contains_any(text, ENHANCEMENT_TERMS):
        reasons.append("feature request signal")
        return "enhancement"

    reasons.append("general maintenance item")
    return "maintenance"


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def _base_score(category: str) -> int:
    return {
        "security": 90,
        "bug": 60,
        "dependency": 45,
        "docs": 25,
        "question": 20,
        "enhancement": 30,
        "maintenance": 20,
    }[category]


def _priority_for(score: int) -> str:
    if score >= 85:
        return "P0"
    if score >= 65:
        return "P1"
    if score >= 40:
        return "P2"
    return "P3"


def _next_action(category: str, priority: str) -> str:
    if category == "security":
        return "move to private security review before public triage"
    if priority in {"P0", "P1"}:
        return "assign maintainer owner and request a reproduction or patch"
    if category == "question":
        return "answer or convert into documentation work"
    if category == "docs":
        return "confirm scope and invite a small documentation PR"
    if category == "dependency":
        return "verify compatibility, changelog, and lockfile impact"
    return "label, deduplicate, and schedule in the next triage batch"
