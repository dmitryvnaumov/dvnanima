# Proton-proton cycle

Manim scenes for key reactions in the pp chain.

---

## Files

- `pp-D-e-nu.py`
  Proton-proton fusion to deuteron with positron and neutrino.

- `D-p-He-gamma.py`
  Deuteron + proton to helium-3 with gamma emission.

- `He3_He3_to_He4_2p.py`
  Helium-3 fusion to helium-4 with two protons.

- `run.cfg`
  Shared 16:9 hires configuration.

---

## How to run

```bash
manim -pqh pp-D-e-nu.py PP_to_D_e_nu -o output_name
manim -pqh D-p-He-gamma.py D_p_to_He3_gamma -o output_name
manim -pqh He3_He3_to_He4_2p.py He3_He3_to_He4_2p -o output_name
```
