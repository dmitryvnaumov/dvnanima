from __future__ import annotations

from pathlib import Path
import logging

from PySpice.Unit import u_V, u_kHz, u_uF, u_GOhm, u_ms, u_us

from CockroftWaltonSystem import CockroftWaltonSystem
from sanitize_svg import sanitize_svg


UNIT_MAP = {
    "V": u_V,
    "kHz": u_kHz,
    "uF": u_uF,
    "GOhm": u_GOhm,
    "ms": u_ms,
    "us": u_us,
}


def _unit(name: str):
    try:
        return UNIT_MAP[name]
    except KeyError as exc:
        raise ValueError(f"Unknown unit: {name}") from exc


def _with_unit(value: float, unit_name: str):
    return value @ _unit(unit_name)


def build_assets(cfg: dict, paths: dict) -> dict:
    if cfg["cw"].get("suppress_ngspice_warning", False):
        logging.getLogger("PySpice").setLevel(logging.ERROR)

    cw = cfg["cw"]
    n_stages = cw["n_stages"]
    v_peak = _with_unit(cw["v_peak"], cw["v_peak_unit"])
    freq = _with_unit(cw["freq"], cw["freq_unit"])
    cap = _with_unit(cw["cap"], cw["cap_unit"])
    r_load = _with_unit(cw["r_load"], cw["r_load_unit"])
    end_time = _with_unit(cw["end_time_ms"], "ms")
    step_time = _with_unit(cw["step_time_us"], "us")

    system = CockroftWaltonSystem(
        n_stages=n_stages,
        v_peak=v_peak,
        freq=freq,
        cap=cap,
        r_load=r_load,
    )
    system.create_circuit(draw=True)
    system.run_simulation(end_time=end_time, step_time=step_time)
    npz_path = system.export_npz(path=str(paths["npz"]))
    svg_path = system.export_svg(path=str(paths["svg_raw"]))
    clean_path = sanitize_svg(inp=svg_path, out=str(paths["svg_clean"]))

    return {"npz": Path(npz_path), "svg_raw": Path(svg_path), "svg_clean": Path(clean_path)}
