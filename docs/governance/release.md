# Release Process

StegoX follows Semantic Versioning. Releases are cut from `main`.

1. Cut a `release/vX.Y.Z` branch.
2. Update `CHANGELOG.md`.
3. Bump version in `pyproject.toml` and `src/stegox/version.py`.
4. Tag the commit.
5. GitHub Actions builds wheels for Linux, macOS, and Windows.
6. Sign artifacts with a maintainer GPG key.
7. Generate `SHA256SUMS`.
8. Publish to PyPI.
9. Publish a GitHub Release with notes.
10. Announce on the discussion forum.

## Cadence

- Minor release: every 8 weeks.
- Patch release: as needed.
- LTS branches: maintained for 12 months.
