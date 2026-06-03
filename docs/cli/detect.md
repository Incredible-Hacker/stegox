# `stegox detect`

Run the universal detection pipeline.

## Examples

```bash
# Run every applicable detector
stegox detect --all suspicious.png

# List available detectors
stegox detect list-detectors

# Run a specific subset
stegox detect --all suspicious.png \
    --detectors image.chi_square,image.rs_analysis
```
