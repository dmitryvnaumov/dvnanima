from manim import *
import numpy as np
from pathlib import Path
import configparser


def load_cfg(path: str = "run.cfg") -> dict:
    cfg = configparser.ConfigParser(inline_comment_prefixes=(";",))
    cfg.read(Path(path))

    def get(section, key, cast=str, fallback=None):
        if fallback is None:
            return cast(cfg[section][key])
        return cast(cfg.get(section, key, fallback=str(fallback)))

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
        "title_scale": get("scene", "title_scale", float, 0.9),
        "title_shift_down": get("scene", "title_shift_down", float, 0.45),
        "heart_formula_scale": get("scene", "heart_formula_scale", float, 18.0),
        "nu_stroke": get("scene", "nu_stroke", float, 18.0),
        "nu_height": get("scene", "nu_height", float, 8.5),
        "nu_y": get("scene", "nu_y", float, 0.2),
        "heart_stroke": get("scene", "heart_stroke", float, 12.0),
        "heart_height": get("scene", "heart_height", float, 8.0),
        "glow_width": get("scene", "glow_width", float, 24.0),
        "glow_opacity": get("scene", "glow_opacity", float, 0.10),
        "hold_pulses": get("scene", "hold_pulses", float, 3.0),
        "pulse_width_boost": get("scene", "pulse_width_boost", float, 0.35),
        "pulse_opacity_boost": get("scene", "pulse_opacity_boost", float, 1.10),
        "heart_pulse_width_boost": get("scene", "heart_pulse_width_boost", float, 0.22),
        "heart_pulse_color_mix": get("scene", "heart_pulse_color_mix", float, 0.35),
        "morph_points": get("scene", "morph_points", int, 1000),
        "create_time": get("scene", "create_time", float, 1.2),
        "pre_morph_wait": get("scene", "pre_morph_wait", float, 0.6),
        "morph_time": get("scene", "morph_time", float, 1.3),
        "post_wait": get("scene", "post_wait", float, 0.8),
    }

    colors = {
        "col_text": get("colors", "col_text", str, "#FFD166"),
        "col_nu": get("colors", "col_nu", str, "#7AA6FF"),
        "col_heart": get("colors", "col_heart", str, "#FF4D4D"),
    }

    return {"manim": manim_params, "scene": scene, "colors": colors}


CFG = load_cfg(str(Path(__file__).with_name("run.cfg")))

config.pixel_width = CFG["manim"]["pixel_width"]
config.pixel_height = CFG["manim"]["pixel_height"]
config.frame_width = CFG["manim"]["frame_width"]
config.frame_height = CFG["manim"]["frame_height"]
config.frame_rate = CFG["manim"]["frame_rate"]
if CFG["manim"]["renderer"]:
    config.renderer = CFG["manim"]["renderer"]


def resample_vmobject(m: VMobject, n: int = 600) -> VMobject:
    """
    Make a NEW VMobject with exactly n sample points along m.
    Works best for a single continuous path (one VMobject).
    """
    out = VMobject()
    pts = [m.point_from_proportion(i / (n - 1)) for i in range(n)]
    out.set_points_smoothly(pts)
    out.match_style(m)
    return out


def make_nu_curve(color="#7AA6FF", stroke=14) -> VGroup:
    """
    Build a nu outline directly from LaTeX glyph paths.
    Keep all drawable subpaths to preserve the real glyph shape.
    """
    glyph = MathTex(r"\nu").set_color(color)
    parts = [m for m in glyph.family_members_with_points() if len(m.points) >= 2]
    if not parts:
        raise ValueError("Failed to extract points from LaTeX nu glyph.")

    nu = VGroup(*[p.copy() for p in parts])
    nu.set_stroke(color=color, width=stroke, opacity=1.0)
    nu.set_fill(opacity=0.0)
    return nu


def heart_2d(t: float, scale: float = 18.0) -> np.ndarray:
    """
    Classic parametric heart curve used as the stage-2 target.
    """
    x = 16 * (np.sin(t) ** 3)
    y = 13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t)
    return np.array([x / scale, y / scale, 0.0])


def make_heart_half(left=True, color="#FF4D4D", stroke=14) -> VMobject:
    """
    One half of a heart outline as ONE VMobject (open curve).
    left=True -> left half, else right half (mirrored).
    """
    # A nice half-heart from top notch -> left lobe -> bottom tip.
    P = np.array([
        [ 0.0,  1.55, 0.0],   # top notch
        [-0.55, 1.45, 0.0],
        [-1.15, 0.95, 0.0],
        [-1.25, 0.20, 0.0],
        [-0.95,-0.55, 0.0],
        [-0.35,-1.25, 0.0],
        [ 0.0, -1.65, 0.0],   # bottom tip
    ])
    if not left:
        P[:, 0] *= -1

    half = VMobject()
    half.set_points_smoothly(P)
    half.set_stroke(color=color, width=stroke, opacity=1.0)
    half.set_fill(opacity=0.0)
    half.make_smooth()
    return half


class NuMorphToHeart(ThreeDScene):
    def construct(self):
        scene = CFG["scene"]
        colors = CFG["colors"]
        col_text = colors["col_text"]
        col_nu = colors["col_nu"]
        col_heart = colors["col_heart"]

        self.camera.background_color = CFG["manim"]["background_color"]

        title_l = MathTex(
            r"U(t)\,\lvert \nu \rangle = \lvert",
            color=col_text,
        ).scale(scene["title_scale"])
#        title_h = Text("♥", color=col_text, weight=BOLD, font_size=40 * scene["title_scale"])
        title_h = MathTex(r"\heartsuit", color=col_text).scale(scene["title_scale"])
        title_r = MathTex(
            r"\rangle",
            color=col_text,
        ).scale(scene["title_scale"])
        title = VGroup(title_l, title_h, title_r).arrange(RIGHT, buff=0.08)
        title.to_edge(UP, buff=0.35).shift(DOWN * scene["title_shift_down"])
        self.add(title)

        nu = make_nu_curve(color=col_nu, stroke=scene["nu_stroke"])
        nu.set(height=scene["nu_height"])
        nu.move_to(DOWN * scene["nu_y"])

        heart_curve = ParametricFunction(
            lambda t: heart_2d(t, scale=scene["heart_formula_scale"]),
            t_range=[0, TAU],
        ).set_stroke(col_heart, width=scene["heart_stroke"], opacity=1.0).set_fill(opacity=0.0)
        heart_curve.set(height=scene["heart_height"])
        heart_curve.move_to(nu.get_center())

        heart_glow = heart_curve.copy().set_stroke(
            col_heart, width=scene["glow_width"], opacity=scene["glow_opacity"]
        )
        pulse_phase = ValueTracker(-PI / 2)
        base_rgb = color_to_rgb(col_heart)
        hi_rgb = color_to_rgb(WHITE)

        def pulse_strength() -> float:
            return 0.5 + 0.5 * np.sin(pulse_phase.get_value())

        def update_heart_glow(m):
            s = pulse_strength()
            width = scene["glow_width"] * (1.0 + scene["pulse_width_boost"] * s)
            opacity = scene["glow_opacity"] * (0.35 + scene["pulse_opacity_boost"] * s)
            m.set_stroke(width=width, opacity=float(np.clip(opacity, 0.0, 1.0)))

        heart_glow.add_updater(update_heart_glow)

        # Step 1: show a clearly visible latex-derived nu glyph.
        self.play(Create(nu), run_time=scene["create_time"])
        self.wait(scene["pre_morph_wait"])

        # Step 2: smooth morph nu -> heart by matching sampled point counts.
        # nu is built from glyph paths; use the primary path for stable single-curve transform.
        nu_path = nu[0].copy() if isinstance(nu, VGroup) and len(nu) > 0 else nu.copy()
        nu_path.set_stroke(col_nu, width=scene["nu_stroke"], opacity=1.0).set_fill(opacity=0.0)
        nu_path.move_to(nu.get_center())

        N = scene["morph_points"]
        nu_morph = resample_vmobject(nu_path, N)
        heart_morph = resample_vmobject(heart_curve, N)
        nu_morph.match_style(nu_path)
        heart_morph.match_style(heart_curve)

        self.remove(nu)
        self.add(nu_morph)
        self.play(
            FadeIn(heart_glow),
            Transform(nu_morph, heart_morph, rate_func=smooth),
            run_time=scene["morph_time"],
        )

        def update_heart_line(m):
            s = pulse_strength()
            width = scene["heart_stroke"] * (1.0 + scene["heart_pulse_width_boost"] * s)
            mix = float(np.clip(scene["heart_pulse_color_mix"] * s, 0.0, 1.0))
            col = rgb_to_color((1.0 - mix) * base_rgb + mix * hi_rgb)
            m.set_stroke(color=col, width=width, opacity=1.0)

        nu_morph.add_updater(update_heart_line)
        if scene["post_wait"] > 0:
            self.play(
                pulse_phase.animate.set_value(-PI / 2 + TAU * scene["hold_pulses"]),
                run_time=scene["post_wait"],
                rate_func=linear,
            )
        nu_morph.clear_updaters()
        heart_glow.clear_updaters()
