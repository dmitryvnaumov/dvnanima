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
        "period": get("scene", "period", float, 4.0),
        "n_periods": get("scene", "n_periods", int, 2),
        "run_time": get("scene", "run_time", float, 12.0),
        "loop_w": get("scene", "loop_w", float, 10.2),
        "loop_h": get("scene", "loop_h", float, 5.6),
        "loop_center_y": get("scene", "loop_center_y", float, 0.45),
        "cap_offset": get("scene", "cap_offset", float, 1.7),
        "cap_gap": get("scene", "cap_gap", float, 0.55),
        "plate_len": get("scene", "plate_len", float, 0.8),
        "n_electrons": get("scene", "n_electrons", int, 45),
        "electron_size": get("scene", "electron_size", float, 0.08),
        "electron_amp": get("scene", "electron_amp", float, 0.12),
        "graph_x_length": get("scene", "graph_x_length", float, 6.0),
        "graph_y_length": get("scene", "graph_y_length", float, 3.0),
        "graph_opacity": get("scene", "graph_opacity", float, 0.2),
        "vin_scale": get("scene", "vin_scale", float, 1.0),
        "i_scale": get("scene", "i_scale", float, 0.9),
    }

    colors = {
        "wire_col": get("colors", "wire_col", str, "#AEE6AE"),
        "node_col": get("colors", "node_col", str, "#52FF52"),
        "vin_col": get("colors", "vin_col", str, "#8FA0FF"),
        "i_col": get("colors", "i_col", str, "#FFD166"),
        "plate_col": get("colors", "plate_col", str, "#FFFFFF"),
    }

    return {"manim": manim_params, "scene": scene, "colors": colors}


CFG = load_cfg("run.cfg")

config.pixel_width = CFG["manim"]["pixel_width"]
config.pixel_height = CFG["manim"]["pixel_height"]
config.frame_width = CFG["manim"]["frame_width"]
config.frame_height = CFG["manim"]["frame_height"]
config.frame_rate = CFG["manim"]["frame_rate"]


class Capacitor(Scene):
    def construct(self):
        scene = CFG["scene"]
        colors = CFG["colors"]
        self.camera.background_color = CFG["manim"]["background_color"]

        # -----------------
        # Timing
        # -----------------
        T = scene["period"]      # seconds per period in animation-time
        n_periods = scene["n_periods"]
        total_time = n_periods * T
        omega = 2 * np.pi / T
        tracker = ValueTracker(0.0)

        # -----------------
        # Colors
        # -----------------
        wire_col = colors["wire_col"]
        node_col = colors["node_col"]
        vin_col = colors["vin_col"]
        i_col = colors["i_col"]     # current color (warm)
        plate_col = colors["plate_col"]

        # -----------------
        # Geometry (loop + capacitor)
        # -----------------
        loop_w, loop_h = scene["loop_w"], scene["loop_h"]
        loop_center = UP * scene["loop_center_y"]

        p_tl = loop_center + LEFT * loop_w / 2 + UP * loop_h / 2
        p_tr = loop_center + RIGHT * loop_w / 2 + UP * loop_h / 2
        p_br = loop_center + RIGHT * loop_w / 2 + DOWN * loop_h / 2
        p_bl = loop_center + LEFT * loop_w / 2 + DOWN * loop_h / 2

        cap_center = p_tr + LEFT * scene["cap_offset"]
        cap_gap = scene["cap_gap"]
        p_cap_L = cap_center + LEFT * (cap_gap / 2)
        p_cap_R = cap_center + RIGHT * (cap_gap / 2)

        # Path of the wire: start at right capacitor plate, go around, end at left plate
        wire_path = VMobject()
        wire_path.set_points_as_corners([p_cap_R, p_tr, p_br, p_bl, p_tl, p_cap_L])
        wire_visual = wire_path.copy().set_stroke(wire_col, 4)

        # Capacitor plates
        plate_half = scene["plate_len"] / 2
        plate_l = Line(p_cap_L + UP * plate_half, p_cap_L + DOWN * plate_half, stroke_width=4).set_color(plate_col)
        plate_r = Line(p_cap_R + UP * plate_half, p_cap_R + DOWN * plate_half, stroke_width=4).set_color(plate_col)
        cap_plates = VGroup(plate_l, plate_r)

        # -----------------
        # Electrons: small oscillation ALONG local tangent (no circulation!)
        # -----------------
        n_electrons = scene["n_electrons"]
        base_props = np.linspace(0, 1, n_electrons, endpoint=False)

        electrons = VGroup(*[
            Square(side_length=scene["electron_size"], fill_opacity=1, fill_color=node_col, stroke_width=0)
            for _ in range(n_electrons)
        ])

        eps = 1e-3
        amp = scene["electron_amp"]  # visual amplitude of drift (small, but visible)

        def tangent_at(p: float) -> np.ndarray:
            p1 = (p + eps) % 1.0
            p0 = (p - eps) % 1.0
            v = wire_path.point_from_proportion(p1) - wire_path.point_from_proportion(p0)
            n = np.linalg.norm(v)
            if n < 1e-9:
                return RIGHT
            return v / n

        def update_electrons(mob: VGroup):
            t = tracker.get_value()
            # current ~ cos(omega t): oscillatory drift
            drift = amp * np.cos(omega * t)
            for i in range(n_electrons):
                p = float(base_props[i])
                pos = wire_path.point_from_proportion(p)
                tan = tangent_at(p)
                mob[i].move_to(pos + drift * tan)

        electrons.add_updater(update_electrons)

        # -----------------
        # Charge labels near plates: sign follows Vin ~ sin(omega t)
        # -----------------
        def get_charge_label(sign, color):
            return Text(sign, font="Arial", weight=BOLD).set_color(color).scale(0.5)

        charges_l = VGroup(*[get_charge_label("+", RED) for _ in range(3)]).arrange(DOWN, buff=0.1).next_to(plate_l, LEFT, buff=0.1)
        charges_r = VGroup(*[get_charge_label("-", BLUE) for _ in range(3)]).arrange(DOWN, buff=0.1).next_to(plate_r, RIGHT, buff=0.1)
        charge_group = VGroup(charges_l, charges_r)

        def update_charges(m: VGroup):
            # Vin ~ sin(omega t)
            val = np.sin(omega * tracker.get_value())
            opacity = float(np.clip(abs(val), 0.0, 1.0))

            if val >= 0:
                # Left plate positive, right negative
                for c in charges_l:
                    c.set_color(RED)
                    c.become(get_charge_label("+", RED))  # keeps font/weight consistent
                for c in charges_r:
                    c.set_color(BLUE)
                    c.become(get_charge_label("-", BLUE))
            else:
                # Polarity flips
                for c in charges_l:
                    c.set_color(BLUE)
                    c.become(get_charge_label("-", BLUE))
                for c in charges_r:
                    c.set_color(RED)
                    c.become(get_charge_label("+", RED))

            m.set_opacity(opacity)
            # reposition after become()
            charges_l.arrange(DOWN, buff=0.1).next_to(plate_l, LEFT, buff=0.1)
            charges_r.arrange(DOWN, buff=0.1).next_to(plate_r, RIGHT, buff=0.1)

        charge_group.add_updater(update_charges)

        # -----------------
        # Graph: Vin and I (I ∝ dVin/dt)
        # x axis in periods: x = t/T
        # Vin(x)=sin(2πx), I(x)=cos(2πx)
        # -----------------
        ax = Axes(
            x_range=[0, n_periods, 1],
            y_range=[-1.2, 1.2, 1],
            x_length=scene["graph_x_length"],
            y_length=scene["graph_y_length"],
            tips=False
        ).move_to(loop_center).set_stroke(opacity=scene["graph_opacity"])

        vin_func = lambda x: scene["vin_scale"] * np.sin(2 * np.pi * x)
        i_func = lambda x: scene["i_scale"] * np.cos(2 * np.pi * x)  # scaled a bit for aesthetics

        vin_line = always_redraw(lambda: ax.plot(
            vin_func,
            x_range=[0, tracker.get_value() / T],
            color=vin_col
        ))

        i_line = always_redraw(lambda: ax.plot(
            i_func,
            x_range=[0, tracker.get_value() / T],
            color=i_col
        ))

        label_vin = MathTex(r"V_{in}", color=vin_col).scale(0.8)
        label_i   = MathTex(r"I", color=i_col).scale(0.8)

        def safe_x():
            return float(np.clip(tracker.get_value() / T, 0.0, float(n_periods)))

        label_vin.add_updater(lambda m: m.next_to(
            ax.c2p(safe_x(), vin_func(safe_x())),
            UR, buff=0.10
        ))

        label_i.add_updater(lambda m: m.next_to(
            ax.c2p(safe_x(), i_func(safe_x())),
            DR, buff=0.10
        ))

        # -----------------
        # Source symbol
        # -----------------
        src = VGroup(
            Circle(radius=0.35, color=WHITE),
            MathTex(r"\sim").scale(1.2)
        ).move_to((p_bl + p_br) / 2)

        # -----------------
        # Render
        # -----------------
        self.add(wire_visual, cap_plates, electrons, charge_group)
        self.add(ax, vin_line, i_line, label_vin, label_i, src)

        self.play(
            tracker.animate.set_value(total_time),
            run_time=scene["run_time"],
            rate_func=linear
        )
        self.wait()
