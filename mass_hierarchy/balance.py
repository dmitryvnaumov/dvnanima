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
        "pixel_width": get("manim", "pixel_width", int),
        "pixel_height": get("manim", "pixel_height", int),
        "frame_width": get("manim", "frame_width", float),
        "frame_height": get("manim", "frame_height", float),
        "frame_rate": get("manim", "frame_rate", int, 60),
        "background_color": get("manim", "background_color", str),
    }

    scene = {
        "pivot_y": get("scene", "pivot_y", float, 0.9),
        "beam_half": get("scene", "beam_half", float, 3.2),
        "drop": get("scene", "drop", float, 1.55),
        "ball_r": get("scene", "ball_r", float, 0.38),
        "amp_deg": get("scene", "amp_deg", float, 9.0),
        "omega": get("scene", "omega", float, 1.1),
        "sag_amp": get("scene", "sag_amp", float, 0.06),
        "periods": get("scene", "periods", float, 2.0),
    }

    colors = {
        "beam_col": get("colors", "beam_col", str, "#b7c4d6"),
        "rope_col": get("colors", "rope_col", str, "#8ea0b8"),
        "stand_col": get("colors", "stand_col", str, "#2b394a"),
        "base_col": get("colors", "base_col", str, "#202a36"),
        "ball_fill": get("colors", "ball_fill", str, "#2a3a4c"),
        "ball_stroke": get("colors", "ball_stroke", str, "#aab7c9"),
    }

    return {"manim": manim_params, "scene": scene, "colors": colors}


CFG = load_cfg("run.cfg")

config.pixel_width = CFG["manim"]["pixel_width"]
config.pixel_height = CFG["manim"]["pixel_height"]
config.frame_width = CFG["manim"]["frame_width"]
config.frame_height = CFG["manim"]["frame_height"]
config.frame_rate = CFG["manim"]["frame_rate"]

class NeutrinoHierarchyScales(Scene):
    def construct(self):
        scene = CFG["scene"]
        colors = CFG["colors"]
        self.camera.background_color = CFG["manim"]["background_color"]

        # -------- Parameters --------
        pivot = ORIGIN + UP * scene["pivot_y"]

        beam_half = scene["beam_half"]  # half-length of the beam
        drop = scene["drop"]            # rope length
        ball_r = scene["ball_r"]        # ball radius

        amp = scene["amp_deg"] * DEGREES  # swing amplitude
        omega = scene["omega"]            # angular frequency
        sag_amp = scene["sag_amp"]        # slight sag

        # Colors
        beam_col = colors["beam_col"]
        rope_col = colors["rope_col"]
        stand_col = colors["stand_col"]
        base_col = colors["base_col"]
        ball_fill = colors["ball_fill"]  # matte dark blue
        ball_stroke = colors["ball_stroke"]

        # -------- Static base/stand --------
        base = RoundedRectangle(width=6.2, height=0.55, corner_radius=0.18)\
            .set_stroke(width=0).set_fill(base_col, opacity=1).shift(DOWN * 2.55)

        stand = Rectangle(width=0.32, height=3.6)\
            .set_stroke(width=0).set_fill(stand_col, opacity=1)\
            .move_to(np.array([0, -0.65, 0]))

        self.add(base, stand)

        # -------- Rotating part: beam + cap --------
        beam = RoundedRectangle(width=2 * beam_half, height=0.20, corner_radius=0.10)\
            .set_stroke(width=0).set_fill(beam_col, opacity=1)\
            .move_to(pivot)

        cap = Circle(radius=0.09).set_stroke(width=0).set_fill(beam_col, 1).move_to(pivot)

        rocker = VGroup(beam, cap)
        self.add(rocker)

        # -------- Left & right: rope + ball (not in rocker) --------
        left_rope = Line(ORIGIN, ORIGIN + DOWN * drop).set_stroke(rope_col, width=3)
        right_rope = Line(ORIGIN, ORIGIN + DOWN * drop).set_stroke(rope_col, width=3)

        left_ball = Circle(radius=ball_r).set_fill(ball_fill, opacity=1).set_stroke(ball_stroke, width=3)
        right_ball = Circle(radius=ball_r).set_fill(ball_fill, opacity=1).set_stroke(ball_stroke, width=3)

        # Labels on balls
        nu1 = MathTex(r"\nu_1").set_color(WHITE).scale(1.25)
        nu3 = MathTex(r"\nu_3").set_color(WHITE).scale(1.25)

        self.add(left_rope, right_rope, left_ball, right_ball, nu1, nu3)

        # -------- Rotation tracker --------
        theta = ValueTracker(0.0)

        def rocker_updater(mob, dt):
            t = self.time
            ang = amp * np.sin(omega * t)
            dtheta = ang - theta.get_value()
            mob.rotate(dtheta, about_point=pivot)
            theta.set_value(ang)

        rocker.add_updater(rocker_updater)

        # Anchors that rotate with the beam (the key to sync)
        def left_anchor():
            return pivot + rotate_vector(beam_half * LEFT, theta.get_value())

        def right_anchor():
            return pivot + rotate_vector(beam_half * RIGHT, theta.get_value())

        # Rope+ball positioning
        def left_group_updater(_mob, dt):
            t = self.time
            sag = sag_amp * abs(np.sin(omega * t))
            a = left_anchor() + DOWN * sag

            left_rope.put_start_and_end_on(a, a + DOWN * drop)
            left_ball.move_to(a + DOWN * (drop + ball_r))
            nu1.move_to(left_ball.get_center())
            nu1.set_rotation(0)

        def right_group_updater(_mob, dt):
            t = self.time
            sag = sag_amp * abs(np.sin(omega * t))
            a = right_anchor() + DOWN * sag

            right_rope.put_start_and_end_on(a, a + DOWN * drop)
            right_ball.move_to(a + DOWN * (drop + ball_r))
            nu3.move_to(right_ball.get_center())
            nu3.set_rotation(0)

        # Attach updaters to some stable mobject (e.g., ropes)
        left_rope.add_updater(left_group_updater)
        right_rope.add_updater(right_group_updater)

        # -------- Run time (integer number of periods for seamless loop) --------
        period = 2 * np.pi / omega
        self.wait(scene["periods"] * period)

        # Cleanup (optional)
        rocker.clear_updaters()
        left_rope.clear_updaters()
        right_rope.clear_updaters()
