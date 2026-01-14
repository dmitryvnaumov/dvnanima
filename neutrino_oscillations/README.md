# Neutrino oscillations

Manim scenes for visualizing **3-flavor neutrino oscillations** using a
barycentric (ternary) probability triangle: the point position encodes
(Pe, Pμ, Pτ).

---

## Files

- `neutrino3d.py`  
  Manim scene (vertical 1080×1920). Shows the evolving flavor composition
  as a moving point inside the probability triangle.

- `osc_prob.py`  
  Pure numerical backend: PMNS matrix, phase evolution in
  x = L / Losc(21), and probability computation.

- `plot_probabilities.py`  
  (Optional) test the probabilities with matplotlib (required) visualization.
---

## How to run

Render the Shorts-style scene:

Higher quality:
```bash
manim -pqh neutrino3d.py NeutrinoOscillationShorts -o output_name

Lower quality:
```bash
manim -pql neutrino3d.py NeutrinoOscillationShorts -o output_name
