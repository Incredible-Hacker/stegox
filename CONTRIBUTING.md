# Contributing to StegoX

Thank you for your interest in StegoX. This document explains how to contribute effectively.

## Code of Conduct

All participants are expected to follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## How to Contribute

1. **Search existing issues** before opening a new one.
2. **Open an issue** to discuss non-trivial changes.
3. **Write an RFC** under `rfcs/` for changes to the CLI, plugin protocol, or report schema.
4. **Open a pull request** against `main`.
5. **Pass CI** — lint, type check, tests, and security scans.

## Development Setup

```bash
git clone https://github.com/Incredible-Hacker/stegox.git
cd stegox
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,extras]"
pre-commit install
pytest
```

## Coding Standards

- Python 3.10+ minimum.
- `ruff` for formatting and linting.
- `mypy --strict` for `stegox.core`, `stegox.engine`, `stegox.security`.
- Google-style docstrings on all public APIs.
- No `print` in library code.
- No bare `except:`.
- No mutable default arguments.

## Commit Messages

We use [Conventional Commits](https://www.conventionalcommits.org/).

```
feat(image): add F5-style JPEG embedder
fix(audio): correct bitplane indexing
docs(spec): clarify detector weight table
```

## Pull Request Process

- One focused change per PR.
- Include tests with a non-trivial change.
- Update documentation when behavior changes.
- Reference the issue or RFC in the PR body.
- PRs require one code-owner approval.

## Plugin Contributions

Plugins that add new detectors or embedders are first-class contributions. See [docs/plugins/writing_a_plugin.md](docs/plugins/writing_a_plugin.md).

## Reporting Security Issues

**Do not open a public issue.** Follow the process in [SECURITY.md](SECURITY.md).
