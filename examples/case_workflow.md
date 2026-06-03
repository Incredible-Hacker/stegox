# Case Workflow Example

This example walks through a full StegoX DFIR case from acquisition
to sealing.

## Inputs

- A suspicious `photo.jpg` in `/evidence/`.
- A candidate password `hunter2`.

## Steps

```bash
# 1. Initialize a case
stegox case init ./case_42 --operator "Alice" --description "Suspicious photo"

# 2. Copy and add the evidence
cp /evidence/photo.jpg ./case_42/inputs/
stegox case add ./case_42 --file ./case_42/inputs/photo.jpg

# 3. Triage
stegox detect --all ./case_42/inputs/photo.jpg
stegox detect --all ./case_42/inputs/photo.jpg --json > ./case_42/reports/photo.json
stegox report render --input ./case_42/reports/photo.json \
    --format html --out ./case_42/reports/photo.html

# 4. Attempt extraction
stegox image extract \
    --stego ./case_42/inputs/photo.jpg --out ./case_42/work/recovered.bin \
    --strategy password-embed --password "hunter2"

# 5. Seal the case
stegox case seal ./case_42
```

## Outputs

```
case_42/
├── manifest.yaml
├── files.yaml
├── inputs/photo.jpg
├── reports/photo.json
├── reports/photo.html
├── work/recovered.bin
└── logs/custody.jsonl
```
