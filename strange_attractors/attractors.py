from __future__ import annotations

import configparser
from pathlib import Path

import numpy as np
from manim import *
from manim import rate_functions as rf


def load_cfg(path: str = "run.cfg") -> dict:
    cfg = configparser.ConfigParser(inline_comment_prefixes=(";",))
    if Path(path).exists():
        cfg.read(Path(path))

    def get(section, key, cast=str, fallback=None):
        if cfg.has_option(section, key):
            return cast(cfg.get(section, key))
        if fallback is None:
            raise KeyError(f"Missing [{section}] {key} in {path}")
        return cast(fallback)

    manim_params = {
        "pixel_width": get("manim", "pixel_width", int, 1080),
        "pixel_height": get("manim", "pixel_height", int, 1920),
        "frame_width": get("manim", "frame_width", float, 9.0),
        "frame_height": get("manim", "frame_height", float, 16.0),
        "frame_rate": get("manim", "frame_rate", int, 60),
        "background_color": get("manim", "background_color", str, "#000000"),
        "renderer": get("manim", "renderer", str, ""),
    }

    scene = {
        "text_font": get("scene", "text_font", str, "PT Sans"),
        "default_attractor": get("scene", "default_attractor", str, "lorenz").lower(),
        "total_time": get("scene", "total_time", float, 45.0),
        "dt": get("scene", "dt", float, 0.006),
        "warmup_steps": get("scene", "warmup_steps", int, 2500),
        "points_per_sec": get("scene", "points_per_sec", int, 200),
        "tail_seconds": get("scene", "tail_seconds", float, 12.0),
        "target_radius": get("scene", "target_radius", float, 3.1),
        "scene_scale": get("scene", "scene_scale", float, 1.18),
        "center_shift_y": get("scene", "center_shift_y", float, -0.35),
        "axis_min": get("scene", "axis_min", float, -4.0),
        "axis_max": get("scene", "axis_max", float, 4.0),
        "axis_step": get("scene", "axis_step", float, 2.0),
        "axes_length": get("scene", "axes_length", float, 6.6),
        "axis_stroke_width": get("scene", "axis_stroke_width", float, 1.6),
        "axis_stroke_opacity": get("scene", "axis_stroke_opacity", float, 0.10),
        "camera_phi_deg": get("scene", "camera_phi_deg", float, 68.0),
        "camera_theta_deg": get("scene", "camera_theta_deg", float, -42.0),
        "ambient_rotation_rate": get("scene", "ambient_rotation_rate", float, 0.05),
        "title_font_size": get("scene", "title_font_size", int, 56),
        "subtitle_text": get("scene", "subtitle_text", str, "STRANGE ATTRACTOR"),
        "subtitle_font_size": get("scene", "subtitle_font_size", int, 24),
        "title_top_buff": get("scene", "title_top_buff", float, 0.28),
        "title_gap": get("scene", "title_gap", float, 0.03),
        "title_in_time": get("scene", "title_in_time", float, 0.6),
        "show_equations": get("scene", "show_equations", int, 1) == 1,
        "equation_scale": get("scene", "equation_scale", float, 0.62),
        "equation_bottom_buff": get("scene", "equation_bottom_buff", float, 0.55),
        "equation_in_time": get("scene", "equation_in_time", float, 0.6),
        "equation_box_opacity": get("scene", "equation_box_opacity", float, 0.44),
        "equation_box_buff": get("scene", "equation_box_buff", float, 0.20),
        "curve_stroke_width": get("scene", "curve_stroke_width", float, 3.1),
        "curve_opacity": get("scene", "curve_opacity", float, 0.90),
        "head_radius": get("scene", "head_radius", float, 0.052),
        "head_opacity": get("scene", "head_opacity", float, 1.0),
        "path_rate_func": get("scene", "path_rate_func", str, "ease_in_out_sine"),
        "end_wait": get("scene", "end_wait", float, 0.3),
    }

    colors = {
        "text_col": get("colors", "text_col", str, "#FFFFFF"),
        "subtitle_col": get("colors", "subtitle_col", str, "#C9D2DF"),
        "label_col": get("colors", "label_col", str, "#FFD166"),
        "axis_col": get("colors", "axis_col", str, "#FFFFFF"),
        "path_col": get("colors", "path_col", str, "#7AA6FF"),
        "active_path_col": get("colors", "active_path_col", str, "#4D6BFF"),
        "head_col": get("colors", "head_col", str, "#FF4D4D"),
        "equation_col": get("colors", "equation_col", str, "#FFFFFF"),
    }

    return {"manim": manim_params, "scene": scene, "colors": colors}


def resolve_rate_func(name: str):
    table = {
        "linear": linear,
        "smooth": smooth,
        "ease_in_out_sine": rf.ease_in_out_sine,
        "ease_in_sine": rf.ease_in_sine,
        "ease_out_sine": rf.ease_out_sine,
    }
    return table.get(name.lower(), rf.ease_in_out_sine)


CFG = load_cfg(str(Path(__file__).with_name("run.cfg")))
config.pixel_width = CFG["manim"]["pixel_width"]
config.pixel_height = CFG["manim"]["pixel_height"]
config.frame_width = CFG["manim"]["frame_width"]
config.frame_height = CFG["manim"]["frame_height"]
config.frame_rate = CFG["manim"]["frame_rate"]
config.background_color = CFG["manim"]["background_color"]
if CFG["manim"]["renderer"]:
    config.renderer = CFG["manim"]["renderer"]


# ----------------------------
# Attractor definitions
# ----------------------------
def lorenz(state, sigma=10.0, rho=28.0, beta=8 / 3):
    x, y, z = state
    return np.array([sigma * (y - x), x * (rho - z) - y, x * y - beta * z], dtype=float)


def rossler(state, a=0.2, b=0.2, c=5.7):
    x, y, z = state
    return np.array([-y - z, x + a * y, b + z * (x - c)], dtype=float)


def aizawa(state, a=0.95, b=0.7, c=0.6, d=3.5, e=0.25, f=0.1):
    x, y, z = state
    dx = (z - b) * x - d * y
    dy = d * x + (z - b) * y
    dz = c + a * z - (z**3) / 3 - (x**2 + y**2) * (1 + e * z) + f * z * (x**3)
    return np.array([dx, dy, dz], dtype=float)


def thomas(state, b=0.208186):
    x, y, z = state
    return np.array([np.sin(y) - b * x, np.sin(z) - b * y, np.sin(x) - b * z], dtype=float)


def dadras(state, a=3.0, b=2.7, c=1.7, d=2.0, e=9.0):
    x, y, z = state
    dx = y - a * x + b * y * z
    dy = c * y - x * z + z
    dz = d * x * y - e * z
    return np.array([dx, dy, dz], dtype=float)


ATTRACTORS = {
    "lorenz": (lorenz, dict(), np.array([0.1, 0.0, 0.0])),
    "rossler": (rossler, dict(), np.array([0.1, 0.0, 0.0])),
    "aizawa": (aizawa, dict(), np.array([0.1, 0.0, 0.0])),
    "thomas": (thomas, dict(), np.array([0.1, 0.0, 0.0])),
    "dadras": (dadras, dict(), np.array([1.1, 2.2, 3.3])),
}

EQUATION_SYSTEMS = {
    "lorenz": [
        r"\dot{x} &= \sigma (y-x)",
        r"\dot{y} &= x(\rho-z)-y",
        r"\dot{z} &= xy-\beta z",
    ],
    "rossler": [
        r"\dot{x} &= -y-z",
        r"\dot{y} &= x+a y",
        r"\dot{z} &= b+z(x-c)",
    ],
    "aizawa": [
        r"\dot{x} &= (z-b)x-dy",
        r"\dot{y} &= dx+(z-b)y",
        r"\dot{z} &= c+az-\frac{z^3}{3}-(x^2+y^2)(1+ez)+f z x^3",
    ],
    "thomas": [
        r"\dot{x} &= \sin(y)-bx",
        r"\dot{y} &= \sin(z)-by",
        r"\dot{z} &= \sin(x)-bz",
    ],
    "dadras": [
        r"\dot{x} &= y-a x+b y z",
        r"\dot{y} &= c y-x z+z",
        r"\dot{z} &= d x y-e z",
    ],
}


def build_equation_panel(attractor_name: str, scene: dict, colors: dict) -> VGroup | None:
    lines = EQUATION_SYSTEMS.get(attractor_name)
    if not lines:
        return None

    system_tex = r"\left\{\begin{aligned}" + r"\\ ".join(lines) + r"\end{aligned}\right."
    eq = MathTex(system_tex, color=colors["equation_col"]).scale(scene["equation_scale"])
    eq.to_edge(DOWN, buff=scene["equation_bottom_buff"])

    bg = BackgroundRectangle(
        eq,
        color=BLACK,
        fill_opacity=scene["equation_box_opacity"],
        buff=scene["equation_box_buff"],
    )
    bg.set_stroke(opacity=0.0)
    return VGroup(bg, eq)


# ----------------------------
# Numerical integration (RK4)
# ----------------------------
def rk4_step(f, x, dt, **params):
    k1 = f(x, **params)
    k2 = f(x + 0.5 * dt * k1, **params)
    k3 = f(x + 0.5 * dt * k2, **params)
    k4 = f(x + dt * k3, **params)
    return x + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)


def integrate(f, x0, dt, n_steps, warmup=2000, **params):
    x = np.array(x0, dtype=float)
    for _ in range(warmup):
        x = rk4_step(f, x, dt, **params)
    pts = np.zeros((n_steps, 3), dtype=float)
    for i in range(n_steps):
        x = rk4_step(f, x, dt, **params)
        pts[i] = x
    return pts


def normalize_points(pts, target_radius=3.2):
    r = np.linalg.norm(pts, axis=1)
    s = np.percentile(r, 95)
    if s <= 1e-9:
        s = 1.0
    return pts / s * target_radius


# ----------------------------
# Scene engine
# ----------------------------
class StrangeAttractor3D(ThreeDScene):
    """
    Set:
      name = "lorenz" | "rossler" | "aizawa" | "thomas" | "dadras"
      T_TOTAL = duration in seconds (None -> run.cfg total_time)
    """

    name = None
    T_TOTAL = None

    def construct(self):
        scene = CFG["scene"]
        colors = CFG["colors"]

        self.camera.background_color = CFG["manim"]["background_color"]
        Text.set_default(font=scene["text_font"], color=colors["text_col"])

        attractor_name = (self.name or scene["default_attractor"]).lower()
        if attractor_name not in ATTRACTORS:
            raise ValueError(f"Unknown attractor: {attractor_name}")

        total_time = float(scene["total_time"] if self.T_TOTAL is None else self.T_TOTAL)
        f, params, x0 = ATTRACTORS[attractor_name]

        n_steps = max(2, int(scene["points_per_sec"] * total_time))
        pts = integrate(
            f,
            x0,
            dt=scene["dt"],
            n_steps=n_steps,
            warmup=scene["warmup_steps"],
            **params,
        )
        pts = normalize_points(pts, target_radius=scene["target_radius"])
        pts *= scene["scene_scale"]
        pts += np.array([0.0, scene["center_shift_y"], 0.0])

        axes = ThreeDAxes(
            x_range=[scene["axis_min"], scene["axis_max"], scene["axis_step"]],
            y_range=[scene["axis_min"], scene["axis_max"], scene["axis_step"]],
            z_range=[scene["axis_min"], scene["axis_max"], scene["axis_step"]],
            x_length=scene["axes_length"],
            y_length=scene["axes_length"],
            z_length=scene["axes_length"],
        )
        axes.scale(scene["scene_scale"])
        axes.shift(UP * scene["center_shift_y"])
        axes.set_stroke(
            color=colors["axis_col"],
            width=scene["axis_stroke_width"],
            opacity=scene["axis_stroke_opacity"],
        )
        self.add(axes)

        self.set_camera_orientation(
            phi=scene["camera_phi_deg"] * DEGREES,
            theta=scene["camera_theta_deg"] * DEGREES,
        )
        self.begin_ambient_camera_rotation(rate=scene["ambient_rotation_rate"])

        title = Text(
            attractor_name.upper(),
            font_size=scene["title_font_size"],
            color=colors["label_col"],
            weight=BOLD,
        )
        subtitle = Text(
            scene["subtitle_text"],
            font_size=scene["subtitle_font_size"],
            color=colors["subtitle_col"],
        )
        title_group = VGroup(title, subtitle).arrange(DOWN, buff=scene["title_gap"])
        title_group.to_edge(UP, buff=scene["title_top_buff"])
        self.add_fixed_in_frame_mobjects(title_group)
        self.play(FadeIn(title_group, shift=0.18 * DOWN), run_time=scene["title_in_time"])

        if scene["show_equations"]:
            equation_panel = build_equation_panel(attractor_name, scene, colors)
            if equation_panel is not None:
                self.add_fixed_in_frame_mobjects(equation_panel)
                self.play(FadeIn(equation_panel, shift=0.15 * UP), run_time=scene["equation_in_time"])

        progress = ValueTracker(0.0)
        tail_pts = max(6, int(scene["points_per_sec"] * scene["tail_seconds"]))

        def make_curve():
            i = int(progress.get_value() * (len(pts) - 1))
            i0 = max(0, i - tail_pts)
            seg = pts[i0 : i + 1]
            if len(seg) < 2:
                seg = np.vstack([seg, seg + np.array([1e-4, 0.0, 0.0])])

            curve = VMobject()
            curve.set_points_smoothly(seg)
            curve.set_stroke(
                width=scene["curve_stroke_width"],
                opacity=scene["curve_opacity"],
            )
            curve.set_color_by_gradient(colors["path_col"], colors["active_path_col"])
            return curve

        def make_head():
            i = int(progress.get_value() * (len(pts) - 1))
            head = Dot3D(point=pts[i], radius=scene["head_radius"], color=colors["head_col"])
            head.set_fill(color=colors["head_col"], opacity=scene["head_opacity"])
            return head

        curve = always_redraw(make_curve)
        head = always_redraw(make_head)
        self.add(curve, head)

        self.play(
            progress.animate.set_value(1.0),
            run_time=total_time,
            rate_func=resolve_rate_func(scene["path_rate_func"]),
        )
        self.wait(scene["end_wait"])


# ----------------------------
# Ready-made variants
# ----------------------------
class LorenzScene(StrangeAttractor3D):
    name = "lorenz"


class RosslerScene(StrangeAttractor3D):
    name = "rossler"


class AizawaScene(StrangeAttractor3D):
    name = "aizawa"


class ThomasScene(StrangeAttractor3D):
    name = "thomas"


class DadrasScene(StrangeAttractor3D):
    name = "dadras"
