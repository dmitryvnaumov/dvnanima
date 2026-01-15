from __future__ import annotations

from pathlib import Path
import configparser


def _get(cfg, section, key, cast=str, fallback=None):
    if fallback is None:
        return cast(cfg[section][key])
    return cast(cfg.get(section, key, fallback=str(fallback)))


def load_cfg(path: Path) -> dict:
    cfg = configparser.ConfigParser(inline_comment_prefixes=(";",))
    cfg.read(path)

    manim_params = {
        "pixel_width": _get(cfg, "manim", "pixel_width", int),
        "pixel_height": _get(cfg, "manim", "pixel_height", int),
        "frame_width": _get(cfg, "manim", "frame_width", float),
        "frame_height": _get(cfg, "manim", "frame_height", float),
        "frame_rate": _get(cfg, "manim", "frame_rate", int, 60),
        "background_color": _get(cfg, "manim", "background_color", str),
    }

    cw = {
        "n_stages": _get(cfg, "cw", "n_stages", int, 3),
        "v_peak": _get(cfg, "cw", "v_peak", float, 12.0),
        "v_peak_unit": _get(cfg, "cw", "v_peak_unit", str, "V"),
        "freq": _get(cfg, "cw", "freq", float, 1.0),
        "freq_unit": _get(cfg, "cw", "freq_unit", str, "kHz"),
        "cap": _get(cfg, "cw", "cap", float, 100.0),
        "cap_unit": _get(cfg, "cw", "cap_unit", str, "uF"),
        "r_load": _get(cfg, "cw", "r_load", float, 1.0),
        "r_load_unit": _get(cfg, "cw", "r_load_unit", str, "GOhm"),
        "end_time_ms": _get(cfg, "cw", "end_time_ms", float, 150.0),
        "step_time_us": _get(cfg, "cw", "step_time_us", float, 10.0),
        "suppress_ngspice_warning": cfg.getboolean("cw", "suppress_ngspice_warning", fallback=False),
    }

    paths = {
        "svg_raw": _get(cfg, "paths", "svg_raw", str, "cw.svg"),
        "svg_clean": _get(cfg, "paths", "svg_clean", str, "cw_clean.svg"),
        "npz": _get(cfg, "paths", "npz", str, "cw_sim.npz"),
        "auto_generate": cfg.getboolean("paths", "auto_generate", fallback=True),
        "force_regen": cfg.getboolean("paths", "force_regen", fallback=False),
    }

    anim = {
        "run_time": _get(cfg, "animation", "run_time", float, 10.0),
        "tail_wait": _get(cfg, "animation", "tail_wait", float, 0.5),
        "scheme_height": _get(cfg, "animation", "scheme_height", float, 3.6),
        "scheme_shift_y": _get(cfg, "animation", "scheme_shift_y", float, -0.4),
        "ax_x_length": _get(cfg, "animation", "ax_x_length", float, 12.5),
        "ax_y_length": _get(cfg, "animation", "ax_y_length", float, 3.8),
        "ax_bottom_buff": _get(cfg, "animation", "ax_bottom_buff", float, 0.35),
        "ax_label_font_size": _get(cfg, "animation", "ax_label_font_size", int, 22),
        "legend_font_size": _get(cfg, "animation", "legend_font_size", int, 20),
        "legend_line_width": _get(cfg, "animation", "legend_line_width", int, 4),
        "curve_width": _get(cfg, "animation", "curve_width", float, 3.0),
    }

    return {"manim": manim_params, "cw": cw, "paths": paths, "animation": anim}


def resolve_paths(paths: dict, base_dir: Path) -> dict:
    out = dict(paths)
    out["svg_raw"] = base_dir / paths["svg_raw"]
    out["svg_clean"] = base_dir / paths["svg_clean"]
    out["npz"] = base_dir / paths["npz"]
    return out
