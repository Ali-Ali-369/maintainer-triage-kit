from __future__ import annotations

import unittest

from maintainer_triage.models import Issue
from maintainer_triage.report import render_markdown
from maintainer_triage.rules import triage_issue


class ReportTests(unittest.TestCase):
    def test_markdown_report_orders_by_score(self) -> None:
        results = [
            triage_issue(Issue(number=2, title="README typo", labels=("docs",))),
            triage_issue(Issue(number=1, title="Vulnerability in parser")),
        ]

        report = render_markdown(results)

        self.assertLess(report.index("#1 - Vulnerability"), report.index("#2 - README"))
        self.assertIn("- security: 1", report)
        self.assertIn("- docs: 1", report)


if __name__ == "__main__":
    unittest.main()
