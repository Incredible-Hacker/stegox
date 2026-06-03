# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 1.x     | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

Report vulnerabilities privately to **security@stegox.dev** (PGP key available on request).

Include:

- A clear description of the vulnerability
- Steps to reproduce
- Impact assessment
- Suggested fix (optional)

We will:

1. Acknowledge within **48 hours**.
2. Provide a triage assessment within **7 days**.
3. Coordinate disclosure with a 90-day deadline by default.
4. Credit reporters in the release notes (unless anonymity is requested).

## Threat Model Summary

StegoX is local-first and explicitly avoids:

- Outbound network calls
- Cloud services
- Telemetry
- Auto-update mechanisms

We audit dependencies via `pip-audit` and `safety` on every PR and weekly via Dependabot.

## Cryptography

StegoX uses:

- AES-256-GCM (authenticated encryption)
- Argon2id (preferred) or scrypt (fallback) for key derivation
- `secrets` module (CSPRNG) for randomness
- `secrets.compare_digest` for all secret comparisons

## Secure I/O

- All writes require an explicit `--out` path.
- StegoX never overwrites a file in place.
- Symlinks are not followed during analysis by default.
