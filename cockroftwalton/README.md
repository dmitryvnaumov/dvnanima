# Cockcroft-Walton

Manim scene for a Cockcroft-Walton multiplier with simulation-driven
voltage curves and an annotated schematic.

---

## Files

- `CockroftWaltonAnimation.py`
  Manim scene. Auto-generates simulation assets if enabled in `run.cfg`.

- `CockroftWaltonRun.py`
  One-shot asset generator (SVG + NPZ) using `run.cfg`.

- `CockroftWaltonSystem.py`
  PySpice + schemdraw system builder and simulator.

- `sanitize_svg.py`
  Cleans the generated SVG.

- `plot_cw.py`
  Optional matplotlib plots for testing.

- `run.cfg`
  16:9 hires configuration and simulation/animation parameters.

---

## How to run

Generate assets (one-shot):

```bash
python CockroftWaltonRun.py
```

Render animation (auto-generates assets if missing):

```bash
manim -pqh CockroftWaltonAnimation.py CockcroftWaltonAnimation -o output_name
```

Optional plot (test):

```bash
python plot_cw.py
```
