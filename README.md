# Maintainer Triage Kit

Maintainer Triage Kit is a small local-first CLI for turning exported GitHub
issues into a review queue. It is designed for maintainers who need a fast,
repeatable first pass before deciding what deserves human attention.

The first version is intentionally deterministic and offline:

- Classifies issues into security, bug, dependency, docs, enhancement, question,
  and maintenance buckets.
- Estimates priority from labels, title/body signals, reactions, and age.
- Produces Markdown or JSON reports that can be pasted into release planning,
  weekly triage notes, or maintainer handoff docs.
- Keeps network and token handling out of the runtime path.

## Install

```bash
python -m pip install -e .
```

No runtime dependencies are required beyond Python 3.11+.

## Usage

```bash
python -m maintainer_triage examples/issues.sample.json --format markdown
python -m maintainer_triage examples/issues.sample.json --format json
```

Input is a JSON array of issue-like objects:

```json
[
  {
    "number": 42,
    "title": "Crash when config file is missing",
    "body": "The CLI exits with a traceback.",
    "labels": ["bug"],
    "created_at": "2026-05-18T12:00:00Z",
    "comments": 3,
    "reactions": { "+1": 8 }
  }
]
```

## Roadmap

- GitHub export adapter that reads from the API without storing tokens.
- LLM-assisted summaries for long issue threads.
- Duplicate detection across issues and pull requests.
- Maintainer policy packs for project-specific labels and release criteria.

## Development

```bash
python -m unittest discover -s tests
python -m maintainer_triage examples/issues.sample.json --format markdown
```

## License

MIT
