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
        "total_time": get("scene", "total_time", float, 8.0),
        "loop_w": get("scene", "loop_w", float, 9.0),
        "loop_h": get("scene", "loop_h", float, 5.0),
        "loop_center_y": get("scene", "loop_center_y", float, 0.0),
        "wire_stroke": get("scene", "wire_stroke", float, 4.0),
        "src_radius": get("scene", "src_radius", float, 0.4),
        "src_sine_amp": get("scene", "src_sine_amp", float, 0.15),
        "src_sine_width": get("scene", "src_sine_width", float, 0.4),
        "diode_scale": get("scene", "diode_scale", float, 0.25),
        "diode_line_half": get("scene", "diode_line_half", float, 0.25),
        "diode_glow_on": get("scene", "diode_glow_on", float, 0.35),
        "diode_glow_off": get("scene", "diode_glow_off", float, 0.18),
        "n_electrons": get("scene", "n_electrons", int, 40),
        "electron_radius": get("scene", "electron_radius", float, 0.07),
        "speed": get("scene", "speed", float, 0.22),
        "graph_x_length": get("scene", "graph_x_length", float, 5.0),
        "graph_y_length": get("scene", "graph_y_length", float, 2.5),
        "graph_opacity": get("scene", "graph_opacity", float, 0.2),
        "vin_stroke_opacity": get("scene", "vin_stroke_opacity", float, 0.40),
        "i_stroke_opacity": get("scene", "i_stroke_opacity", float, 0.95),
    }

    colors = {
        "wire_col": get("colors", "wire_col", str, "#AEE6AE"),
        "node_col": get("colors", "node_col", str, "#52FF52"),
        "vin_col": get("colors", "vin_col", str, "#8FA0FF"),
        "i_col": get("colors", "i_col", str, "#FFD166"),
    }

    return {"manim": manim_params, "scene": scene, "colors": colors}


CFG = load_cfg("run.cfg")

config.pixel_width = CFG["manim"]["pixel_width"]
config.pixel_height = CFG["manim"]["pixel_height"]
config.frame_width = CFG["manim"]["frame_width"]
config.frame_height = CFG["manim"]["frame_height"]
config.frame_rate = CFG["manim"]["frame_rate"]


class Diode(Scene):
    def construct(self):
        scene = CFG["scene"]
        colors = CFG["colors"]
        self.camera.background_color = CFG["manim"]["background_color"]

        # --- Parameters ---
        T = scene["period"]
        total_time = scene["total_time"]
        omega = 2 * np.pi / T
        tracker = ValueTracker(0.0)

        # Colors
        wire_col, node_col = colors["wire_col"], colors["node_col"]
        vin_col, i_col = colors["vin_col"], colors["i_col"]

        # --- Geometry ---
        loop_w, loop_h = scene["loop_w"], scene["loop_h"]
        loop_center = UP * scene["loop_center_y"]
        p_tl = loop_center + UP * (loop_h / 2) + LEFT * (loop_w / 2)
        p_tr = loop_center + UP * (loop_h / 2) + RIGHT * (loop_w / 2)
        p_br = loop_center + DOWN * (loop_h / 2) + RIGHT * (loop_w / 2)
        p_bl = loop_center + DOWN * (loop_h / 2) + LEFT * (loop_w / 2)

        # Wire path (closed rectangle)
        wire_path = VMobject()
        wire_path.set_points_as_corners([p_tr, p_br, p_bl, p_tl, p_tr])
        wire_visual = wire_path.copy().set_stroke(wire_col, scene["wire_stroke"])

        # Components placement
        diode_pos = loop_center + UP * (loop_h / 2)
        src_pos = loop_center + DOWN * (loop_h / 2)

        # --- AC source symbol ---
        src_circle = Circle(radius=scene["src_radius"], color=WHITE).move_to(src_pos).set_fill("#05050a", 1)
        src_sine = ParametricFunction(
            lambda t: np.array([t, scene["src_sine_amp"] * np.sin(2 * PI * t / scene["src_sine_width"]), 0]),
            t_range=[-scene["src_sine_width"] / 2, scene["src_sine_width"] / 2],
            color=WHITE
        ).move_to(src_pos)
        source = VGroup(src_circle, src_sine)

        # --- Diode symbol ---
        diode_tri = Triangle(color=WHITE, fill_opacity=0).scale(scene["diode_scale"]).rotate(-90 * DEGREES).move_to(diode_pos)
        diode_line = Line(UP * scene["diode_line_half"], DOWN * scene["diode_line_half"], color=WHITE).next_to(diode_tri, RIGHT, buff=0)
        diode_group = VGroup(diode_tri, diode_line)

        # Diode glow (conducting vs blocking)
        diode_glow = diode_tri.copy().set_fill(GREEN, opacity=0)

        def update_diode(m):
            v_in = np.sin(omega * tracker.get_value())
            if v_in > 0:
                m.set_fill(GREEN, opacity=scene["diode_glow_on"]).set_stroke(GREEN, width=2)
            else:
                m.set_fill(RED, opacity=scene["diode_glow_off"]).set_stroke(RED, width=2)

        diode_glow.add_updater(update_diode)

        # --- "Electrons" visualization (current only when diode conducts) ---
        n_electrons = scene["n_electrons"]
        electrons = VGroup(*[Dot(radius=scene["electron_radius"], color=node_col) for _ in range(n_electrons)])

        # fixed base positions along the loop
        props = np.linspace(0, 1, n_electrons, endpoint=False).copy()

        # speed scale (visual only)
        speed = scene["speed"]

        def update_electrons(mob, dt):
            # Ideal diode current: I ~ max(0, Vin)
            v_in = np.sin(omega * tracker.get_value())
            current = max(0.0, float(v_in))

            step = speed * current * dt
            # move only when current > 0, otherwise freeze
            if step > 0:
                for i in range(n_electrons):
                    props[i] = (props[i] + step) % 1.0

            for i, dot in enumerate(mob):
                dot.move_to(wire_path.point_from_proportion(props[i]))

        electrons.add_updater(update_electrons)

        # --- Graphs: Vin and I ---
        ax = Axes(
            x_range=[0, 2, 1],
            y_range=[-1.2, 1.2, 1],
            x_length=scene["graph_x_length"],
            y_length=scene["graph_y_length"],
            tips=False
        ).move_to(ORIGIN).set_stroke(opacity=scene["graph_opacity"])

        # x is in periods: x = t/T, so sin(2πx) matches Vin(t)
        def vin_func(x):
            return np.sin(2 * np.pi * x)

        def i_func(x):
            return max(0.0, np.sin(2 * np.pi * x))

        vin_plot = always_redraw(lambda: ax.plot(
            vin_func,
            x_range=[0, max(0.001, tracker.get_value() / T)],
            color=vin_col,
            stroke_opacity=scene["vin_stroke_opacity"]
        ))

        i_plot = always_redraw(lambda: ax.plot(
            i_func,
            x_range=[0, max(0.001, tracker.get_value() / T)],
            color=i_col,
            stroke_opacity=scene["i_stroke_opacity"]
        ))

        # Labels
        l_in = MathTex(r"V_{in}", color=vin_col).scale(0.8).next_to(ax, UP).shift(LEFT * 1.6)
        l_i  = MathTex(r"I", color=i_col).scale(0.8).next_to(ax, UP).shift(RIGHT * 1.6)

        # --- Assemble ---
        self.add(wire_visual, source, diode_group, diode_glow, electrons, ax, vin_plot, i_plot, l_in, l_i)

        self.play(
            tracker.animate.set_value(total_time),
            run_time=total_time,
            rate_func=linear
        )
        self.wait()
