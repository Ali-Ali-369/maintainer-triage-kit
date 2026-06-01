from __future__ import annotations

import unittest
from datetime import datetime, timezone

from maintainer_triage.models import Issue
from maintainer_triage.rules import triage_issue


class TriageRuleTests(unittest.TestCase):
    def test_security_issue_is_highest_priority(self) -> None:
        issue = Issue(
            number=7,
            title="Secret token leak in logs",
            labels=("bug",),
            reactions={"+1": 10},
        )

        result = triage_issue(issue)

        self.assertEqual(result.category, "security")
        self.assertEqual(result.priority, "P0")
        self.assertIn("security-sensitive language", result.reasons)

    def test_bug_with_activity_becomes_p1(self) -> None:
        issue = Issue(
            number=8,
            title="Regression: command crashes on macOS",
            labels=("bug",),
            comments=9,
            reactions={"+1": 4},
        )

        result = triage_issue(issue)

        self.assertEqual(result.category, "bug")
        self.assertEqual(result.priority, "P1")

    def test_stale_docs_issue_stays_lower_priority(self) -> None:
        issue = Issue(
            number=9,
            title="README typo",
            labels=("documentation",),
            created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )

        result = triage_issue(issue, now=datetime(2026, 1, 1, tzinfo=timezone.utc))

        self.assertEqual(result.category, "docs")
        self.assertEqual(result.priority, "P3")
        self.assertIn("stale but unresolved", result.reasons)


if __name__ == "__main__":
    unittest.main()
