# `stegox metadata`

Hide, extract, detect, and audit metadata fields.

## Examples

```bash
# Hide in a JPEG's UserComment field
stegox metadata hide \
    --cover photo.jpg --payload secret.bin --out photo_stego.jpg \
    --field UserComment

# Extract
stegox metadata extract --target photo_stego.jpg --out recovered.bin --field UserComment

# Audit every metadata field
stegox metadata audit --target photo.jpg
```

## Supported fields

Run `stegox metadata list-fields` to see the full table.
