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
        "period": get("scene", "period", float, 6.0),
        "num_cycles": get("scene", "num_cycles", int, 2),
        "vd0": get("scene", "vd0", float, 0.10),
        "tau_charge": get("scene", "tau_charge", float, 0.8),
        "tau_disch": get("scene", "tau_disch", float, 150.0),
        "loop_w": get("scene", "loop_w", float, 10.0),
        "loop_h": get("scene", "loop_h", float, 6.0),
        "loop_center_y": get("scene", "loop_center_y", float, 0.0),
        "graph_width_ratio": get("scene", "graph_width_ratio", float, 0.7),
        "graph_height_ratio": get("scene", "graph_height_ratio", float, 0.7),
        "wire_stroke": get("scene", "wire_stroke", float, 3.0),
        "diode_scale": get("scene", "diode_scale", float, 0.2),
        "diode_line_half": get("scene", "diode_line_half", float, 0.2),
        "diode_offset_x": get("scene", "diode_offset_x", float, 1.5),
        "capacitor_half": get("scene", "capacitor_half", float, 0.5),
        "capacitor_gap": get("scene", "capacitor_gap", float, 0.3),
        "source_radius": get("scene", "source_radius", float, 0.35),
        "arrow_left_offset": get("scene", "arrow_left_offset", float, 2.8),
        "arrow_right_offset": get("scene", "arrow_right_offset", float, 1.8),
        "arrow_stroke": get("scene", "arrow_stroke", float, 6.0),
        "current_font_size": get("scene", "current_font_size", int, 28),
        "ax_y_min": get("scene", "ax_y_min", float, -2.2),
        "ax_y_max": get("scene", "ax_y_max", float, 1.2),
        "ax_y_step": get("scene", "ax_y_step", float, 1.0),
        "ax_opacity": get("scene", "ax_opacity", float, 0.15),
        "vin_opacity": get("scene", "vin_opacity", float, 0.30),
        "vc_opacity": get("scene", "vc_opacity", float, 1.00),
        "vd_opacity": get("scene", "vd_opacity", float, 1.00),
        "plot_width": get("scene", "plot_width", float, 4.0),
        "label_scale": get("scene", "label_scale", float, 0.7),
        "tail_wait": get("scene", "tail_wait", float, 1.0),
    }

    colors = {
        "wire_col": get("colors", "wire_col", str, "#AEE6AE"),
        "vin_col": get("colors", "vin_col", str, "#8FA0FF"),
        "vc_col": get("colors", "vc_col", str, "#6DFF8A"),
        "vd_col": get("colors", "vd_col", str, "#FF8F8F"),
    }

    return {"manim": manim_params, "scene": scene, "colors": colors}


CFG = load_cfg("run.cfg")

config.pixel_width = CFG["manim"]["pixel_width"]
config.pixel_height = CFG["manim"]["pixel_height"]
config.frame_width = CFG["manim"]["frame_width"]
config.frame_height = CFG["manim"]["frame_height"]
config.frame_rate = CFG["manim"]["frame_rate"]


class PeakDetector(Scene):
    def construct(self):
        scene = CFG["scene"]
        colors = CFG["colors"]
        self.camera.background_color = CFG["manim"]["background_color"]

        # --- Control parameters ---
        T = scene["period"]
        num_cycles = scene["num_cycles"]
        total_time = T * num_cycles
        omega = 2 * np.pi / T
        tracker = ValueTracker(0.0)

        # Pedagogical offset so V_diode can be > 0 during conduction
        VD0 = scene["vd0"]

        # Charge time (larger -> wider V_diode > 0 window)
        TAU_CHARGE = scene["tau_charge"]
        TAU_DISCH = scene["tau_disch"]  # almost no discharge (no load)

        # Geometry
        loop_w, loop_h = scene["loop_w"], scene["loop_h"]
        loop_center = UP * scene["loop_center_y"]
        graph_width_ratio = scene["graph_width_ratio"]
        graph_height_ratio = scene["graph_height_ratio"]

        # Colors
        wire_col = colors["wire_col"]
        vin_col, vc_col, vd_col = colors["vin_col"], colors["vc_col"], colors["vd_col"]

        # --- Precompute Vc(t) with finite charging rate ---
        dt_sim = 0.005
        ts = np.arange(0.0, total_time + dt_sim, dt_sim)

        vin_arr = np.sin(omega * ts)
        vc_arr = np.zeros_like(ts)

        vc = 0.0
        for i in range(1, len(ts)):
            v_in = vin_arr[i]

            # Diode conducts only if Vin exceeds Vc + VD0
            if v_in - vc > VD0:
                target = v_in - VD0
                vc += (target - vc) * (dt_sim / TAU_CHARGE)
            else:
                # Discharge through load (or self-discharge)
                vc += (0.0 - vc) * (dt_sim / TAU_DISCH)

            vc_arr[i] = vc

        def vc_of_t(t: float) -> float:
            t = float(np.clip(t, 0.0, total_time))
            return float(np.interp(t, ts, vc_arr))

        def vin_of_t(t: float) -> float:
            return float(np.sin(omega * t))

        def vd_of_t(t: float) -> float:
            # The plotted diode voltage: V_diode = Vin - Vc
            return vin_of_t(t) - vc_of_t(t)

        # --- Loop and components ---
        p_tl = loop_center + UP * (loop_h / 2) + LEFT * (loop_w / 2)
        p_tr = loop_center + UP * (loop_h / 2) + RIGHT * (loop_w / 2)
        p_br = loop_center + DOWN * (loop_h / 2) + RIGHT * (loop_w / 2)
        p_bl = loop_center + DOWN * (loop_h / 2) + LEFT * (loop_w / 2)

        wire_path = VMobject().set_points_as_corners([p_tr, p_br, p_bl, p_tl, p_tr])
        wire_visual = wire_path.copy().set_stroke(wire_col, scene["wire_stroke"])

        diode_tri = Triangle(color=WHITE).scale(scene["diode_scale"]).rotate(-90 * DEGREES)
        diode_line = Line(UP * scene["diode_line_half"], DOWN * scene["diode_line_half"], color=WHITE).move_to(diode_tri.get_right())
        diode = VGroup(diode_tri, diode_line).move_to(loop_center + UP * (loop_h / 2) + LEFT * scene["diode_offset_x"])

        diode_glow = diode_tri.copy().set_fill(GREEN, opacity=0).set_stroke(width=0)
        diode_glow.move_to(diode_tri)

        def update_diode_glow(m):
            t = tracker.get_value()
            if vd_of_t(t) > 0:
                m.set_fill(GREEN, opacity=0.35).set_stroke(GREEN, width=2)
            else:
                m.set_fill(RED, opacity=0.18).set_stroke(RED, width=2)

        diode_glow.add_updater(update_diode_glow)

        capacitor = VGroup(
            Line(LEFT * scene["capacitor_half"], RIGHT * scene["capacitor_half"]).shift(UP * scene["capacitor_gap"] / 2),
            Line(LEFT * scene["capacitor_half"], RIGHT * scene["capacitor_half"]).shift(DOWN * scene["capacitor_gap"] / 2),
        ).move_to(loop_center + RIGHT * (loop_w / 2)).set_color(WHITE)

        source = VGroup(Circle(radius=scene["source_radius"], color=WHITE), MathTex(r"\sim")).move_to(loop_center + DOWN * (loop_h / 2))

        # --- Current indicator: strictly on when V_diode > 0 ---
        arrow_start = loop_center + UP * (loop_h / 2) + LEFT * scene["arrow_left_offset"]
        arrow_end = loop_center + UP * (loop_h / 2) + RIGHT * scene["arrow_right_offset"]

        current_arrow = Arrow(
            start=arrow_start, end=arrow_end,
            buff=0.0, stroke_width=scene["arrow_stroke"], max_tip_length_to_length_ratio=0.12
        ).set_color(WHITE)

        current_text = Text("current", font_size=scene["current_font_size"]).set_color(WHITE).next_to(current_arrow, DOWN, buff=0.15)
        current_group = VGroup(current_arrow, current_text)

        def update_current_indicator(m, dt):
            t = tracker.get_value()
            vd = vd_of_t(t)

            if vd > 0:
                # Strict sync: opacity is 0 when vd <= 0.
                # For vd > 0, ease in without violating the condition.
                # Normalize by VD0 so small thresholds still show up.
                s = np.clip(vd / max(VD0, 1e-6), 0.0, 1.0)
                # Smoothstep 0..1
                alpha = s * s * (3 - 2 * s)
                m.set_opacity(0.25 + 0.75 * alpha)
            else:
                m.set_opacity(0.0)

        current_group.add_updater(update_current_indicator)

        # --- Axes and plots ---
        ax = Axes(
            x_range=[0, num_cycles, 1],
            y_range=[scene["ax_y_min"], scene["ax_y_max"], scene["ax_y_step"]],
            x_length=loop_w * graph_width_ratio,
            y_length=loop_h * graph_height_ratio,
            axis_config={"include_tip": False},
        ).move_to(ORIGIN).set_stroke(opacity=scene["ax_opacity"])

        def x_end():
            return float(np.clip(tracker.get_value() / T, 0.0, float(num_cycles)))

        # Plots as functions of x (cycles), t = x*T
        vin_x = lambda x: np.sin(2 * PI * x)
        vc_x = lambda x: vc_of_t(x * T)
        vd_x = lambda x: vin_x(x) - vc_x(x)

        def get_plot(func, color, opacity=1.0, width=4):
            return always_redraw(lambda: ax.plot(
                func,
                x_range=[0, max(0.01, tracker.get_value() / T)],
                color=color,
                stroke_opacity=opacity,
                stroke_width=width,
            ))

        vin_p = get_plot(vin_x, vin_col, opacity=scene["vin_opacity"], width=scene["plot_width"])
        vc_p = get_plot(vc_x, vc_col, opacity=scene["vc_opacity"], width=scene["plot_width"])
        vd_p = get_plot(vd_x, vd_col, opacity=scene["vd_opacity"], width=scene["plot_width"])

        # --- Labels follow curve endpoints ---
        l_vin = MathTex(r"V_{in}", color=vin_col).scale(scene["label_scale"])
        l_vc = MathTex(r"V_C", color=vc_col).scale(scene["label_scale"])
        l_vd = MathTex(r"V_{diode}", color=vd_col).scale(scene["label_scale"])

        def follow(label, func, direction=UR, buff=0.10):
            def _upd(m):
                xe = x_end()
                ye = float(func(xe))
                m.next_to(ax.c2p(xe, ye), direction, buff=buff)
            label.add_updater(_upd)

        follow(l_vin, vin_x, UR, 0.10)
        follow(l_vc, vc_x, UR, 0.10)
        follow(l_vd, vd_x, UR, 0.10)

        # --- Assemble ---
        self.add(
            wire_visual, source, diode, diode_glow, capacitor,
            current_group, ax, vin_p, vc_p, vd_p, l_vin, l_vc, l_vd
        )

        self.play(
            tracker.animate.set_value(total_time),
            run_time=total_time,
            rate_func=linear
        )
        self.wait(scene["tail_wait"])
