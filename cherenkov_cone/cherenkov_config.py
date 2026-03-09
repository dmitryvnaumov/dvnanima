import configparser
from pathlib import Path

import numpy as np


def _parse_bool(raw: str) -> bool:
    """Parse a permissive boolean value from config text."""
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _parse_vec3(raw: str, fallback: tuple[float, float, float]) -> np.ndarray:
    """Parse a 3D vector from comma-separated config text."""
    if raw is None:
        return np.asarray(fallback, dtype=float)
    parts = [token.strip() for token in raw.replace(";", ",").split(",") if token.strip()]
    if len(parts) != 3:
        return np.asarray(fallback, dtype=float)
    try:
        return np.asarray([float(parts[0]), float(parts[1]), float(parts[2])], dtype=float)
    except ValueError:
        return np.asarray(fallback, dtype=float)


def load_cfg(path: str | Path | None = None) -> dict:
    """Load the prototype configuration from ``run.cfg``."""
    cfg = configparser.ConfigParser(inline_comment_prefixes=(";",))
    cfg_path = Path(path) if path is not None else Path(__file__).with_name("run.cfg")
    cfg.read(cfg_path)

    def get(section: str, key: str, cast, fallback):
        """Read and cast a single config value with fallback."""
        raw = cfg.get(section, key, fallback=None)
        if raw is None:
            return fallback
        try:
            return cast(raw)
        except (TypeError, ValueError):
            return fallback

    def get_bool(section: str, key: str, fallback: bool) -> bool:
        """Read a boolean config value with fallback."""
        raw = cfg.get(section, key, fallback=None)
        if raw is None:
            return fallback
        return _parse_bool(raw)

    nappe = get("intersection", "nappe", str, "trailing").strip().lower()

    camera_position = _parse_vec3(
        cfg.get("visual", "camera_position", fallback="160.0, -140.0, 120.0"),
        (160.0, -140.0, 120.0),
    )
    camera_focal = _parse_vec3(cfg.get("visual", "camera_focal", fallback="0.0, 0.0, 0.0"), (0.0, 0.0, 0.0))
    camera_view_up = _parse_vec3(cfg.get("visual", "camera_view_up", fallback="0.0, 0.0, 1.0"), (0.0, 0.0, 1.0))
    parallel_projection = get_bool("visual", "parallel_projection", False)

    return {
        "run": {
            "save_movie": get_bool("run", "save_movie", True),
            "movie_path": get("run", "movie_path", str, "cherenkov_cylinder.mp4"),
            "n_frames": get("run", "n_frames", int, 140),
            "show_progress": get_bool("run", "show_progress", True),
            "movie_fps": get("run", "movie_fps", int, 24),
            "movie_format": get("run", "movie_format", str, "pyav"),
            "movie_codec": get("run", "movie_codec", str, "libx264"),
            "movie_is_batch": get_bool("run", "movie_is_batch", False),
            "history_stride": get("run", "history_stride", int, 1),
            "save_history_npz": get_bool("run", "save_history_npz", True),
            "history_npz_path": get("run", "history_npz_path", str, "cherenkov_history.npz"),
            "save_history_vtm": get_bool("run", "save_history_vtm", True),
            "history_vtm_path": get("run", "history_vtm_path", str, "cherenkov_history.vtm"),
            "show_history_viewer": get_bool("run", "show_history_viewer", False),
        },
        "detector": {
            "cluster_radius": get("detector", "cluster_radius", float, 40.0),
            "z_min": get("detector", "z_min", float, -70.0),
            "z_max": get("detector", "z_max", float, 70.0),
            "cylinder_resolution": get("detector", "cylinder_resolution", int, 120),
            "cyl_sample_phi": get("detector", "cyl_sample_phi", int, 280),
            "n_strings": get("detector", "n_strings", int, 10),
            "oms_per_string": get("detector", "oms_per_string", int, 20),
        },
        "optics": {
            "n_refr": get("optics", "n_refr", float, 1.33),
            "beta": get("optics", "beta", float, 1.0),
        },
        "track": {
            "r0": _parse_vec3(cfg.get("track", "r0", fallback="-25.0, -10.0, -80.0"), (-25.0, -10.0, -80.0)),
            "u": _parse_vec3(cfg.get("track", "u", fallback="0.38, 0.18, 0.91"), (0.38, 0.18, 0.91)),
            "s_start": get("track", "s_start", float, 0.0),
            "s_end": get("track", "s_end", float, 170.0),
            "draw_s_min": get("track", "draw_s_min", float, -10.0),
            "draw_s_max": get("track", "draw_s_max", float, 190.0),
            "draw_points": get("track", "draw_points", int, 300),
        },
        "intersection": {
            "analytic_eps": get("intersection", "analytic_eps", float, 1e-12),
            "apex_inside_only": get_bool("intersection", "apex_inside_only", False),
            "nappe": nappe,
            "clip_to_visual_cone": get_bool("intersection", "clip_to_visual_cone", True),
            "max_forward_distance": get("intersection", "max_forward_distance", float, 0.0),
            "min_points": get("intersection", "min_points", int, 5),
            "verify_geometry": get_bool("intersection", "verify_geometry", False),
            "verify_every": get("intersection", "verify_every", int, 20),
            "verify_atol": get("intersection", "verify_atol", float, 1e-8),
            "activation_distance": get("intersection", "activation_distance", float, 2.8),
            "curve_line_width": get("intersection", "curve_line_width", float, 2.0),
            "curve_color": get("intersection", "curve_color", str, "lime"),
        },
        "visual": {
            "plot_theme": get("visual", "plot_theme", str, "document"),
            "window_width": get("visual", "window_width", int, 1400),
            "window_height": get("visual", "window_height", int, 900),
            "show_unwrapped_view": get_bool("visual", "show_unwrapped_view", False),
            "cylinder_line_width": get("visual", "cylinder_line_width", float, 1.5),
            "cylinder_opacity": get("visual", "cylinder_opacity", float, 0.35),
            "track_line_width": get("visual", "track_line_width", float, 4.0),
            "om_point_size": get("visual", "om_point_size", float, 10.0),
            "unwrap_om_point_size": get("visual", "unwrap_om_point_size", float, 7.0),
            "unwrap_curve_line_width": get("visual", "unwrap_curve_line_width", float, 3.0),
            "unwrap_curve_point_size": get("visual", "unwrap_curve_point_size", float, 5.0),
            "unwrap_active_om_point_size": get("visual", "unwrap_active_om_point_size", float, 10.0),
            "apex_radius": get("visual", "apex_radius", float, 1.8),
            "cone_height": get("visual", "cone_height", float, 45.0),
            "cone_resolution": get("visual", "cone_resolution", int, 80),
            "cone_opacity": get("visual", "cone_opacity", float, 0.18),
            "camera_position": camera_position,
            "camera_focal": camera_focal,
            "camera_view_up": camera_view_up,
            "parallel_projection": parallel_projection,
            "movie_camera_position": _parse_vec3(
                cfg.get("visual", "movie_camera_position", fallback=None),
                tuple(camera_position),
            ),
            "movie_camera_focal": _parse_vec3(
                cfg.get("visual", "movie_camera_focal", fallback=None),
                tuple(camera_focal),
            ),
            "movie_camera_view_up": _parse_vec3(
                cfg.get("visual", "movie_camera_view_up", fallback=None),
                tuple(camera_view_up),
            ),
            "movie_parallel_projection": get_bool("visual", "movie_parallel_projection", parallel_projection),
            "title_text": get("visual", "title_text", str, "Cherenkov cone-cylinder intersection prototype"),
        },
    }
