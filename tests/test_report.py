from __future__ import annotations

import unittest

from maintainer_triage.models import Issue
import json

from maintainer_triage.report import render_board_json, render_markdown
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

    def test_board_json_matches_dashboard_shape(self) -> None:
        results = [
            triage_issue(Issue(number=1, title="Token leak", labels=("security",))),
            triage_issue(Issue(number=2, title="README typo", labels=("docs",))),
        ]

        board = json.loads(render_board_json(results, project_name="Demo", repo="owner/demo", release="1.2.3"))

        self.assertEqual(board["project"]["repo"], "owner/demo")
        self.assertEqual(board["project"]["release"], "1.2.3")
        self.assertEqual(len(board["issues"]), 2)
        self.assertIn("release", board)
        self.assertIn("risks", board)


if __name__ == "__main__":
    unittest.main()
