# mp4gainpy

Minimal Python + Rust library for **static gain adjustment of AAC/M4A audio** —
no analysis, no undo tags, no metadata. Just locate the `global_gain` fields in
the AAC bitstream and add/subtract a fixed number of steps.

## Usage

```python
import mp4gainpy

# Bytes in, bytes out
with open("track.m4a", "rb") as f:
    data = f.read()
louder = mp4gainpy.aac_apply_gain(data, 2)   # +2 steps  (~+3.0 dB)
softer = mp4gainpy.aac_apply_gain(data, -2)  # -2 steps  (~-3.0 dB)

# File in-place
mp4gainpy.aac_apply_gain_file("track.m4a", 2)

# Step size is 1.5 dB by AAC spec
mp4gainpy.GAIN_STEP_DB  # 1.5
```

## Units

`gain_steps` is the native AAC `global_gain` unit (an 8-bit integer in the
bitstream). One step is 1.5 dB. If you want to think in dB, just divide:
`steps = round(db / mp4gainpy.GAIN_STEP_DB)`.

Zero steps is a no-op; gain locations are saturating-clamped to `0..=255`;
locations with `global_gain == 0` are skipped (silence).

## Build

```bash
uv venv
uv pip install maturin
uv run maturin develop --features python
uv run python -m unittest tests/test_python_bindings.py -v
```
