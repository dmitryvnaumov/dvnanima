# Air shower

Manim scene for a stylized atmospheric particle shower with a primary track
and cascading secondary branches.

---

## Files

- `airshower.py`
  Manim scene. Reads parameters from `run.cfg`.

- `run.cfg`
  16:9 hires configuration and animation parameters.

---

## How to run

```bash
manim -pqh airshower.py AirShower -o output_name
```

Edit `run.cfg` to adjust geometry, timing, and output resolution.
