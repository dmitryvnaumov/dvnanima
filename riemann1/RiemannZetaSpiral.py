from manim import *
import scipy.special as sp
import numpy as np

from pathlib import Path
import configparser


def load_cfg(path: str = "run.cfg") -> dict:
    # Read visual and timing parameters from a config file.
    cfg = configparser.ConfigParser(inline_comment_prefixes=(";",))
    cfg.read(Path(path))

    def get(section, key, cast=str, fallback=None):
        # Small helper to read + cast values with optional defaults.
        if fallback is None:
            return cast(cfg[section][key])
        return cast(cfg.get(section, key, fallback=str(fallback)))

    manim_params = {
        "pixel_width": get("manim", "pixel_width", int),
        "pixel_height": get("manim", "pixel_height", int),
        "frame_width": get("manim", "frame_width", float),
        "frame_height": get("manim", "frame_height", float),
        "frame_rate": get("manim", "frame_rate", int, 60),
        "background_color": get("manim", "background_color", str),
    }

    scene = {
        "t_min": get("scene", "t_min", float, 0.0),
        "t_max": get("scene", "t_max", float),
        "t_epsilon": get("scene", "t_epsilon", float, 0.001),
        "total_time": get("scene", "total_time", float),
        "slider_shift_down": get("scene", "slider_shift_down", float, 0.0),
        "tick_label_alt_offset": get("scene", "tick_label_alt_offset", float, 0.18),
        "zeta_x_min": get("scene", "zeta_x_min", float),
        "zeta_x_max": get("scene", "zeta_x_max", float),
        "zeta_x_step": get("scene", "zeta_x_step", float),
        "zeta_y_min": get("scene", "zeta_y_min", float),
        "zeta_y_max": get("scene", "zeta_y_max", float),
        "zeta_y_step": get("scene", "zeta_y_step", float),
        "zeta_x_length": get("scene", "zeta_x_length", float),
        "zeta_y_length": get("scene", "zeta_y_length", float),
        "zeta_axis_stroke": get("scene", "zeta_axis_stroke", float, 2.0),
        "zeta_axis_opacity": get("scene", "zeta_axis_opacity", float, 1.0),
        "zeta_axis_labels_scale": get("scene", "zeta_axis_labels_scale", float, 0.7),
        "title_scale": get("scene", "title_scale", float, 0.9),
        "title_buff": get("scene", "title_buff", float, 0.3),
        "def_scale": get("scene", "def_scale", float, 0.7),
        "def_buff": get("scene", "def_buff", float, 0.15),
        "plot_label_scale": get("scene", "plot_label_scale", float, 0.75),
        "plot_label_buff": get("scene", "plot_label_buff", float, 0.25),
        "footer_scale": get("scene", "footer_scale", float, 0.6),
        "footer_buff": get("scene", "footer_buff", float, 0.35),
        "full_path_opacity": get("scene", "full_path_opacity", float, 0.5),
        "full_path_width": get("scene", "full_path_width", float, 2.0),
        "active_path_tail": get("scene", "active_path_tail", float, 2.0),
        "active_path_width": get("scene", "active_path_width", float, 4.0),
        "dot_radius": get("scene", "dot_radius", float, 0.06),
        "origin_mark_radius": get("scene", "origin_mark_radius", float, 0.03),
        "origin_mark_opacity": get("scene", "origin_mark_opacity", float, 0.6),
        "origin_flash_radius": get("scene", "origin_flash_radius", float, 0.14),
        "flash_sigma": get("scene", "flash_sigma", float, 0.06),
        "slider_length": get("scene", "slider_length", float),
        "slider_buff": get("scene", "slider_buff", float, 0.4),
        "slider_tick_height": get("scene", "slider_tick_height", float, 0.2),
        "slider_stroke": get("scene", "slider_stroke", float, 3.0),
        "slider_knob_radius": get("scene", "slider_knob_radius", float, 0.08),
        "slider_inset": get("scene", "slider_inset", float, 0.0),
        "slider_major_tick_height": get("scene", "slider_major_tick_height", float, 0.32),
        "slider_major_tick_stroke": get("scene", "slider_major_tick_stroke", float, 3.5),
        "slider_major_tick_step": get("scene", "slider_major_tick_step", float, 20.0),
        "t_label_scale": get("scene", "t_label_scale", float, 0.8),
        "t_value_scale": get("scene", "t_value_scale", float, 0.6),
        "t_label_buff": get("scene", "t_label_buff", float, 0.25),
        "t_value_buff": get("scene", "t_value_buff", float, 0.25),
        "t_legend_buff": get("scene", "t_legend_buff", float, 0.2),
        "t_legend_value_buff": get("scene", "t_legend_value_buff", float, 0.15),
        "tick_sigma": get("scene", "tick_sigma", float, 0.12),
        "zeros_limit": get("scene", "zeros_limit", int, 0),
        "root_mode": get("scene", "root_mode", str, "list"),
        "root_threshold": get("scene", "root_threshold", float, 0.12),
        "root_min_dt": get("scene", "root_min_dt", float, 0.6),
        "root_max": get("scene", "root_max", int, 0),
        "zeros": get("scene", "zeros", str, ""),
    }

    colors = {
        "axis_col": get("colors", "axis_col", str, "#FFFFFF"),
        "label_col": get("colors", "label_col", str, "#FFD166"),
        "path_col": get("colors", "path_col", str, "#7AA6FF"),
        "active_path_col": get("colors", "active_path_col", str, "#4D6BFF"),
        "dot_col": get("colors", "dot_col", str, "#FF4D4D"),
        "slider_col": get("colors", "slider_col", str, "#FFFFFF"),
        "tick_col": get("colors", "tick_col", str, "#FFFFFF"),
        "knob_col": get("colors", "knob_col", str, "#FFD166"),
    }

    return {"manim": manim_params, "scene": scene, "colors": colors}


CFG = load_cfg("run.cfg")

# Apply render settings from config (resolution, frame rate, etc.).
config.pixel_width = CFG["manim"]["pixel_width"]
config.pixel_height = CFG["manim"]["pixel_height"]
config.frame_width = CFG["manim"]["frame_width"]
config.frame_height = CFG["manim"]["frame_height"]
config.frame_rate = CFG["manim"]["frame_rate"]


class RiemannZetaSpiral(Scene):
    def construct(self):
        # Pull frequently used config sections for readability.
        scene = CFG["scene"]
        colors = CFG["colors"]
        self.camera.background_color = CFG["manim"]["background_color"]

        # Animation time range.
        t_min = scene["t_min"]
        t_max = scene["t_max"]
        t_eps = scene["t_epsilon"]

        # Axes for the complex plane of ζ values (Re/Im).
        z_plane = Axes(
            x_range=[scene["zeta_x_min"], scene["zeta_x_max"], scene["zeta_x_step"]],
            y_range=[scene["zeta_y_min"], scene["zeta_y_max"], scene["zeta_y_step"]],
            x_length=scene["zeta_x_length"],
            y_length=scene["zeta_y_length"],
            tips=False,
            axis_config={"stroke_width": scene["zeta_axis_stroke"], "stroke_opacity": scene["zeta_axis_opacity"]},
        )
        z_plane.set_color(colors["axis_col"])

        axis_labels = z_plane.get_axis_labels(
            x_label=MathTex(r"\mathrm{Re}(\zeta)").scale(scene["zeta_axis_labels_scale"]),
            y_label=MathTex(r"\mathrm{Im}(\zeta)").scale(scene["zeta_axis_labels_scale"]),
        )
        self.add(z_plane, axis_labels)

        # Title and explanatory text (top center).
        title = MathTex(r"\mathrm{Riemann}\ \zeta\ \mathrm{function}", color=colors["label_col"])\
            .scale(scene["title_scale"]).to_edge(UP, buff=scene["title_buff"])
        zeta_def = MathTex(r"\zeta(s)=\sum_{n=1}^{\infty}\frac{1}{n^s}", color=colors["label_col"])\
            .scale(scene["def_scale"]).next_to(title, DOWN, buff=scene["def_buff"])
        plot_label = MathTex(r"\mathrm{Plot\ of}\ \zeta(\tfrac{1}{2}+it)", color=colors["label_col"])\
            .scale(scene["plot_label_scale"]).next_to(zeta_def, DOWN, buff=scene["plot_label_buff"])
        watch_label = MathTex(r"\mathrm{Watch\ for}\ t\ \mathrm{when}\ \zeta(\tfrac{1}{2}+it)=0", color=colors["label_col"])\
            .scale(scene["plot_label_scale"]).next_to(plot_label, DOWN, buff=scene["plot_label_buff"] * 0.7)
        t_legend = MathTex(r"t=", color=colors["label_col"])\
            .scale(scene["plot_label_scale"] * 0.9).next_to(watch_label, DOWN, buff=scene["plot_label_buff"] * 0.6)
        footer = MathTex(
            r"\begin{array}{c}"
            r"\mathrm{Zeros\ of}\ \zeta\ \mathrm{control\ the\ error}\\"
            r"\mathrm{in\ the\ distribution}\\"
            r"\mathrm{of\ prime\ numbers}"
            r"\end{array}",
            color=colors["label_col"],
        ).scale(scene["footer_scale"]).to_edge(DOWN, buff=scene["footer_buff"]).set_x(0)
        self.add(title, zeta_def, plot_label, watch_label, footer)

        # -------- Precompute trajectory (critical for speed) --------
        # We compute ζ(1/2 + it) once on a time grid and reuse it each frame.
        fps = config.frame_rate
        oversample = 1.0
        n_pts = int(scene["total_time"] * fps * oversample) + 1

        t_grid = np.linspace(t_min, t_max, n_pts)
        z_grid = np.array([sp.zeta(0.5 + 1j * t) for t in t_grid], dtype=np.complex128)
        abs_grid = np.abs(z_grid)
        pts = np.array([z_plane.c2p(z.real, z.imag) for z in z_grid])

        # Helpers to map current time t to precomputed samples.
        def t_to_idx(t: float) -> int:
            if t_max == t_min:
                return 0
            alpha = (t - t_min) / (t_max - t_min)
            return int(np.clip(alpha, 0.0, 1.0) * (n_pts - 1))

        # Linear interpolation between samples for smooth motion.
        def interp_point(t: float) -> np.ndarray:
            if t_max == t_min:
                return pts[0]
            u = (t - t_min) / (t_max - t_min) * (n_pts - 1)
            i0 = int(np.clip(np.floor(u), 0, n_pts - 2))
            f = u - i0
            return (1 - f) * pts[i0] + f * pts[i0 + 1]

        # Interpolated |ζ| used for the origin flash.
        def interp_abs(t: float) -> float:
            if t_max == t_min:
                return float(abs_grid[0])
            u = (t - t_min) / (t_max - t_min) * (n_pts - 1)
            i0 = int(np.clip(np.floor(u), 0, n_pts - 2))
            f = u - i0
            return float((1 - f) * abs_grid[i0] + f * abs_grid[i0 + 1])

        # ValueTracker drives the animation time.
        t_tracker = ValueTracker(t_min)

        # Full history path of ζ(t).
        full_path = VMobject()
        full_path.set_stroke(
            colors["path_col"],
            width=scene["full_path_width"],
            opacity=scene["full_path_opacity"],
        )

        # Bright tail to emphasize the most recent segment.
        active_path = VMobject()
        active_path.set_stroke(
            colors["active_path_col"],
            width=scene["active_path_width"],
            opacity=1.0,
        )

        # Tail length in samples (converted from time length).
        tail_pts = 2
        if t_max > t_min:
            tail_pts = max(2, int(scene["active_path_tail"] / (t_max - t_min) * (n_pts - 1)))

        # Update both paths based on the current t.
        def update_paths():
            k = max(2, t_to_idx(t_tracker.get_value()) + 1)
            full_path.set_points_as_corners(pts[:k])
            k0 = max(0, k - tail_pts)
            active_path.set_points_as_corners(pts[k0:k])

        full_path.add_updater(lambda m: (update_paths(), m)[1])
        active_path.add_updater(lambda m: (update_paths(), m)[1])

        # Moving dot for the current ζ value.
        z_dot = Dot(radius=scene["dot_radius"], color=colors["dot_col"])
        z_dot.add_updater(lambda m: m.move_to(interp_point(t_tracker.get_value())))

        # Origin marker + flash to highlight near-zeros.
        origin = z_plane.c2p(0.0, 0.0)
        origin_mark = Dot(origin, radius=scene["origin_mark_radius"], color=colors["axis_col"])\
            .set_opacity(scene["origin_mark_opacity"])

        origin_flash = Dot(origin, radius=scene["origin_flash_radius"], color=colors["dot_col"])
        origin_flash.add_updater(
            lambda m: m.set_opacity(np.exp(-(interp_abs(t_tracker.get_value()) / scene["flash_sigma"]) ** 2))
        )

        self.add(full_path, active_path, z_dot, origin_mark, origin_flash)

        # Slider for t with ticks for roots and major time marks.
        slider_half = max(0.1, scene["slider_length"] / 2 - scene["slider_inset"])
        slider_line = Line(
            LEFT * slider_half,
            RIGHT * slider_half,
            color=colors["slider_col"],
            stroke_width=scene["slider_stroke"],
        ).next_to(z_plane, DOWN, buff=scene["slider_buff"]).shift(DOWN * scene["slider_shift_down"])

        # Caption under the slider axis.
        t_label = MathTex("t", color=colors["label_col"]).scale(scene["t_label_scale"])\
            .next_to(slider_line, DOWN, buff=scene["t_label_buff"] + 0.60).set_x(slider_line.get_center()[0])

        # Map any t to a point on the slider line.
        def slider_point(t: float) -> np.ndarray:
            alpha = 0.0 if t_max == t_min else (t - t_min) / (t_max - t_min)
            alpha = np.clip(alpha, 0.0, 1.0)
            return interpolate(slider_line.get_start(), slider_line.get_end(), alpha)

        # Optional: detect roots by local minima in |ζ| if auto mode is enabled.
        def detect_roots(t_vals: np.ndarray, abs_vals: np.ndarray) -> list[float]:
            roots = []
            last_t = -1e9
            for i in range(1, len(abs_vals) - 1):
                if abs_vals[i] < abs_vals[i - 1] and abs_vals[i] < abs_vals[i + 1]:
                    if abs_vals[i] <= scene["root_threshold"]:
                        t = float(t_vals[i])
                        if t - last_t >= scene["root_min_dt"]:
                            roots.append(t)
                            last_t = t
                            if scene["root_max"] > 0 and len(roots) >= scene["root_max"]:
                                break
            return roots

        if scene["root_mode"].lower() == "auto":
            zeros = detect_roots(t_grid, abs_grid)
        else:
            zeros_raw = [s.strip() for s in scene["zeros"].split(",") if s.strip()]
            zeros = [float(v) for v in zeros_raw]
            if scene["zeros_limit"] > 0:
                zeros = zeros[:scene["zeros_limit"]]
        zeros = sorted(zeros)

        # Show the last root reached in the top legend (t = ...).
        t_value = DecimalNumber(
            t_min,
            num_decimal_places=2,
            color=colors["label_col"],
        ).scale(scene["plot_label_scale"] * 0.9).next_to(t_legend, RIGHT, buff=scene["plot_label_buff"] * 0.2)

        def update_root_value(m):
            t = t_tracker.get_value()
            root = None
            for z in zeros:
                if z <= t:
                    root = z
                else:
                    break
            if root is None:
                m.set_opacity(0.0)
            else:
                m.set_value(root)
                m.set_opacity(1.0)

        t_value.add_updater(update_root_value)
        self.add(t_legend, t_value)

        # Root ticks appear once their t value is reached.
        zero_ticks = VGroup()
        for z in zeros:
            if t_min <= z <= t_max:
                tick = Line(
                    UP * (scene["slider_tick_height"] / 2),
                    DOWN * (scene["slider_tick_height"] / 2),
                    color=colors["tick_col"],
                    stroke_width=scene["slider_stroke"],
                ).move_to(slider_point(z))
                tick.add_updater(lambda m, dt, z=z: m.set_opacity(1.0 if t_tracker.get_value() >= z else 0.0))
                zero_ticks.add(tick)

        # Major ticks (fixed spacing) with numeric labels.
        major_ticks = VGroup()
        major_tick_labels = VGroup()
        if scene["slider_major_tick_step"] > 0:
            t0 = np.ceil(t_min / scene["slider_major_tick_step"]) * scene["slider_major_tick_step"]
            for tv in np.arange(t0, t_max + 1e-9, scene["slider_major_tick_step"]):
                tick = Line(
                    UP * (scene["slider_major_tick_height"] / 2),
                    DOWN * (scene["slider_major_tick_height"] / 2),
                    color=colors["tick_col"],
                    stroke_width=scene["slider_major_tick_stroke"],
                ).move_to(slider_point(tv))
                lbl = DecimalNumber(
                    tv,
                    num_decimal_places=0,
                    color=colors["label_col"],
                ).scale(scene["t_value_scale"]).next_to(tick, DOWN, buff=scene["t_value_buff"])
                if abs(tv - t_max) < 1e-6:
                    lbl.shift(LEFT * (lbl.width * 0.6))
                elif abs(tv - t_min) < 1e-6:
                    lbl.shift(RIGHT * (lbl.width * 0.6))
                major_ticks.add(tick)
                major_tick_labels.add(lbl)

        # Highlight the current root tick briefly as we pass it.
        highlight_ticks = VGroup()
        for z in zeros:
            if t_min <= z <= t_max:
                ht = Line(
                    UP * (scene["slider_tick_height"] / 2),
                    DOWN * (scene["slider_tick_height"] / 2),
                    color=colors["dot_col"],
                    stroke_width=scene["slider_stroke"] * 1.8,
                ).move_to(slider_point(z))
                ht.add_updater(
                    lambda m, dt, z=z: m.set_opacity(
                        np.exp(-((t_tracker.get_value() - z) / scene["tick_sigma"]) ** 2)
                    )
                )
                highlight_ticks.add(ht)

        # Slider knob follows the current t.
        slider_knob = Dot(radius=scene["slider_knob_radius"], color=colors["knob_col"])
        slider_knob.add_updater(lambda m: m.move_to(slider_point(t_tracker.get_value())))

        self.add(
            slider_line,
            major_ticks,
            major_tick_labels,
            zero_ticks,
            highlight_ticks,
            slider_knob,
            t_label,
            t_value,
        )

        # Run the animation from t_min to t_max in the configured duration.
        self.play(
            t_tracker.animate.set_value(t_max),
            run_time=scene["total_time"],
            rate_func=linear,
        )
        self.wait()
