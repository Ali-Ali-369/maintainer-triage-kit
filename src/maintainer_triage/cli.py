from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TextIO

from .models import Issue
from .report import render_board_json, render_json, render_markdown
from .rules import triage_issue


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="maintainer-triage",
        description="Create a maintainer triage report from exported issues.",
    )
    parser.add_argument("issues_json", type=Path, help="Path to a JSON array of issue objects.")
    parser.add_argument(
        "--format",
        choices=("markdown", "json", "board"),
        default="markdown",
        help="Report format.",
    )
    parser.add_argument("--project", default="Maintainer Triage Board", help="Project name for board exports.")
    parser.add_argument("--repo", default="local/maintainer-triage", help="Repository label for board exports.")
    parser.add_argument("--release", default="0.1.0", help="Release label for board exports.")
    return parser


def main(argv: list[str] | None = None, stdout: TextIO | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    out = stdout or sys.stdout

    try:
        raw = json.loads(args.issues_json.read_text(encoding="utf-8"))
    except OSError as exc:
        parser.error(f"could not read {args.issues_json}: {exc}")
    except json.JSONDecodeError as exc:
        parser.error(f"invalid JSON in {args.issues_json}: {exc}")

    if not isinstance(raw, list):
        parser.error("input must be a JSON array")

    issues = [Issue.from_mapping(item) for item in raw if isinstance(item, dict)]
    results = [triage_issue(issue) for issue in issues]
    if args.format == "json":
        rendered = render_json(results)
    elif args.format == "board":
        rendered = render_board_json(results, project_name=args.project, repo=args.repo, release=args.release)
    else:
        rendered = render_markdown(results)
    out.write(rendered)
    return 0
