# Forensic Workflow

A typical StegoX session follows five steps:

1. **Acquire** — copy the file to a case directory.
2. **Identify** — `stegox detect --all` lists media type, format, signatures.
3. **Triage** — review the score and indicators.
4. **Deep analyze** — `stegox <media> analyze`.
5. **Attempt extraction** — `stegox <media> extract`.

## Case directory

A case is a directory the analyst creates. StegoX never stores a
separate database. The directory layout is:

```
my_case/
├── manifest.yaml
├── inputs/
├── work/
├── reports/
├── logs/
│   └── custody.jsonl
├── files.yaml
└── chain_of_custody.md
```

## Chain of custody

Every command appends an entry to `logs/custody.jsonl`. Entries are
JSON-Lines with timestamps, the operator, the action, the target
file's SHA-256, the command arguments, and the exit code. The log is
append-only; rotation is manual.

## Sealing a case

`stegox case seal` computes a final SHA-256 over the manifest and
appends a sealing event to the custody log. Sealing makes tampering
detectable.
