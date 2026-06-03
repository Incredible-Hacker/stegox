# Reporting

StegoX produces three report formats:

- **Console** — color-coded text via `rich`.
- **JSON** — stable, machine-readable.
- **HTML** — self-contained, printable, theme-able.

## Report model

Reports are versioned Pydantic models. The full schema is documented
in `docs/schemas/report.schema.json`.

## Rendering

```bash
# From a JSON report produced by `stegox detect --all --json`:
stegox report render --input result.json --format html --out report.html
stegox report render --input result.json --format json --out result.json
stegox report render --input result.json --format console --out report.txt
```

## Recommendations

The recommendations engine maps indicator combinations to suggested
next steps. For example, if `image.chi_square` and `image.rs_analysis`
both return high scores, the report recommends running
`stegox image extract --strategy password-embed`.
