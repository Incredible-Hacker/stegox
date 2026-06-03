# Case Workflow

A worked example using StegoX end to end.

## 1. Initialize a case

```bash
stegox case init ./case_42 --operator "Alice" --description "Suspicious photo"
```

## 2. Acquire the artifact

```bash
cp /evidence/photo.jpg ./case_42/
stegox case add ./case_42 --file photo.jpg
```

## 3. Run detection

```bash
stegox detect --all ./case_42/inputs/photo.jpg
```

## 4. Generate a report

```bash
stegox detect --all ./case_42/inputs/photo.jpg --json > photo.json
stegox report render --input photo.json --format html --out photo.html
```

## 5. Attempt extraction

```bash
stegox image extract \
    --stego ./case_42/inputs/photo.jpg --out recovered.bin \
    --strategy password-embed --password "candidate"
```

## 6. Seal the case

```bash
stegox case seal ./case_42
```

After sealing, the manifest hash is committed to the custody log and
any subsequent modification to `inputs/` or `reports/` is detectable
by re-running the seal.
