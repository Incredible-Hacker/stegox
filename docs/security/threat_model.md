# Threat Model

StegoX is designed for analysts. The threat model is therefore the
analyst's local environment, not a remote attacker.

## In scope

- Tampering with cover files during analysis.
- Accidental overwrite of evidence.
- Memory disclosure of passwords or keys.
- Supply chain attacks via dependencies.
- Plugin supply chain attacks.

## Out of scope

- Side-channel attacks on the host OS.
- Hardware keyloggers.
- Coercion of the operator.

## Mitigations

- All writes go to explicit `--out` paths.
- StegoX never overwrites a file in place.
- Symlinks are not followed during analysis.
- Passwords are zeroized after use.
- `pip-audit` and `bandit` run on every PR.
- Lockfiles are committed.
- Plugins must declare permissions; network access requires
  `--allow-network`.
