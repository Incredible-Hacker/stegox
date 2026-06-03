# Contributing

StegoX welcomes contributions. This page summarizes the workflow;
details are in `CONTRIBUTING.md` and the RFC process.

## Process

1. Open or claim an issue.
2. Discuss the design.
3. Write an RFC under `rfcs/` for non-trivial changes.
4. Open a pull request.
5. Pass CI (lint, type-check, tests, security).
6. Get a code-owner review.
7. Merge via squash.

## Standards

- Python 3.10+.
- `ruff` for lint and format.
- `mypy --strict` for `core/`, `engine/`, `security/`.
- Google-style docstrings on public APIs.
- No `print` in library code.
- No bare `except`.
- Conventional Commits.
