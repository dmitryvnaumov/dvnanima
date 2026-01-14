# Neutrino oscillations

Manim scenes for visualizing **3-flavor neutrino oscillations** using a
barycentric (ternary) probability triangle: the point position encodes
($P_e$, $P_\mu$, $P_\tau$).

---

## Files

- `neutrino3d.py`  
  Manim scene (vertical 1080×1920). Shows the evolving flavor composition
  as a moving point inside the probability triangle.

- `osc_prob.py`  
  Pure numerical backend: PMNS matrix, phase evolution in
  $x = L / L_{osc}^{21}$, and probability computation.

- `plot_probabilities.py`  
  (Optional) test the probabilities with matplotlib (required) visualization.

- `run.cfg`
   List of parameters
---

## How to run

```bash
manim -pqh neutrino3d.py NeutrinoOscillationShorts -o output_name
```

