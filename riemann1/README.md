# Riemann zeta spiral

Manim scene that visualizes the Riemann zeta function along the critical line
and marks nontrivial zeros with ticks on a time slider.

---

## Files

- `RiemannZetaSpiral.py`
  Manim scene. Reads parameters from `run.cfg`.

- `run.cfg`
  Portrait (9:16) configuration and scene parameters.

---

## How to run

```bash
manim -pqh RiemannZetaSpiral.py RiemannZetaSpiral -o output_name
```

Edit `run.cfg` to adjust ranges, timing, and root display (list vs auto).
