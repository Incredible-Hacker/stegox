# CLI Reference

StegoX exposes a single `stegox` command with a stable grammar.

## Top-level commands

```
stegox image ...
stegox audio ...
stegox video ...
stegox text ...
stegox metadata ...
stegox detect ...
stegox case ...
stegox plugin ...
stegox config ...
stegox report ...
stegox doctor
stegox version
```

## Global flags

| Flag | Description |
|---|---|
| `--config PATH` | Path to YAML config file |
| `--log-level LEVEL` | `debug`, `info`, `warning`, `error`, `critical` |
| `--log-file PATH` | Write logs to file |
| `--json-logs` | Emit logs as JSON |
| `--json` | Emit machine-readable JSON on stdout |
| `--no-color` | Disable ANSI colors |
| `--quiet, -q` | Suppress non-error output |
| `--allow-network` | Permit network-requiring plugins |
| `--jobs, -j N` | Parallel jobs |
| `--no-cache` | Disable detector cache |
| `--version` | Show version |

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success, no findings |
| 1 | Generic failure |
| 2 | Usage error |
| 3 | File not found |
| 4 | Unsupported format |
| 5 | Integrity error (decryption failure) |
| 6 | Permission denied |
| 7 | Plugin error |
| 8 | Timeout |
| 9 | Cancelled |
| 10 | Detection completed with findings |

See the per-command pages for details.
