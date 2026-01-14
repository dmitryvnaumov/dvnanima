from manim import *
import numpy as np
from osc_prob import prob_row_x 

from pathlib import Path
import configparser

def load_cfg(path: str = "run.cfg") -> dict:
    cfg = configparser.ConfigParser(inline_comment_prefixes=(";",))
    cfg.read(Path(path))
    # helpers
    def get(section, key, cast=str, fallback=None):
        if fallback is None:
            return cast(cfg[section][key])
        return cast(cfg.get(section, key, fallback=str(fallback)))

    # Manim params (set early)
    manim_params = {
        "pixel_width":  get("manim", "pixel_width", int),
        "pixel_height": get("manim", "pixel_height", int),
        "frame_width":  get("manim", "frame_width", float),
        "frame_height": get("manim", "frame_height", float),
        "background_color": get("manim", "background_color", str),
    }

    # Oscillation params
    osc = {
        "initial_flavor": get("osc", "initial_flavor", str),
        "ordering":       get("osc", "ordering", str),
        "theta12_deg":    get("osc", "theta12_deg", float),
        "theta23_deg":    get("osc", "theta23_deg", float),
        "theta13_deg":    get("osc", "theta13_deg", float),
        "delta_cp_deg":   get("osc", "delta_cp_deg", float),
        "dm21":           get("osc", "dm21", float),
        "dm31abs":        get("osc", "dm31abs", float),
        "n_periods":      get("osc", "n_periods", float),
        "run_time":       get("osc", "run_time", float),
        "n_grid":         get("osc", "n_grid", int),
    }

    ui = {
        "triangle_scale":    get("ui", "triangle_scale", float, 1.15),
        "triangle_shift_up": get("ui", "triangle_shift_up", float, 0.4),
        "trace_time":        get("ui", "trace_time", float, 3.0),
        "ghost_time":        get("ui", "ghost_time", float, 8.0),
        "trace_width":       get("ui", "trace_width", float, 5.0),
        "ghost_width":       get("ui", "ghost_width", float, 12.0),
        "ghost_opacity":     get("ui", "ghost_opacity", float, 0.10),
        "dot_radius":        get("ui", "dot_radius", float, 0.12),
    }

    return {"manim": manim_params, "osc": osc, "ui": ui}

CFG = load_cfg("run.cfg")

config.pixel_width  = CFG["manim"]["pixel_width"]
config.pixel_height = CFG["manim"]["pixel_height"]
config.frame_width  = CFG["manim"]["frame_width"]
config.frame_height = CFG["manim"]["frame_height"]


class NeutrinoOscillationShorts(Scene):
    def construct(self):
        self.camera.background_color = CFG["manim"]["background_color"]

        p = CFG["osc"]
        ui = CFG["ui"]

        initial_flavor = p["initial_flavor"]
        ordering = p["ordering"]

        th12 = np.deg2rad(p["theta12_deg"])
        th23 = np.deg2rad(p["theta23_deg"])
        th13 = np.deg2rad(p["theta13_deg"])
        dcp  = np.deg2rad(p["delta_cp_deg"])

        dm21    = p["dm21"]
        dm31abs = p["dm31abs"]

        n_periods = p["n_periods"]
        run_time  = p["run_time"]
        n_grid    = p["n_grid"]

        # Словарь для правильного отображения флэйворов в LaTeX
        flavor_latex = {
            "e": "e",
            "mu": r"\mu",
            "tau": r"\tau"
        }
        tex_flavor = flavor_latex.get(initial_flavor, initial_flavor)

        # -------------------- calculation logic --------------------
        x_grid = np.linspace(0.0, n_periods, n_grid)
        P_grid = prob_row_x(
            initial_flavor, x_grid,
            th12, th23, th13, dcp,
            dm21, dm31abs,
            ordering=ordering
        )
        P_grid = np.clip(P_grid, 0.0, 1.0)

        def P_of_x(val: float) -> np.ndarray:
            pe = np.interp(val, x_grid, P_grid[:, 0])
            pm = np.interp(val, x_grid, P_grid[:, 1])
            pt = np.interp(val, x_grid, P_grid[:, 2])
            s = pe + pm + pt
            return np.array([pe, pm, pt]) / (s if s > 0 else 1.0)

        # -------------------- geometry (centered) --------------------
        tri = Polygon(
            np.array([0.0, 0.0, 0.0]),
            np.array([5.8, 0.0, 0.0]),
            np.array([2.9, 5.02, 0.0]),
        ).set_stroke(color=GRAY_B, width=3, opacity=0.9)

        tri.scale(ui["triangle_scale"]).move_to(ORIGIN).shift(UP * ui["triangle_shift_up"])
        v = tri.get_vertices()
        center = tri.get_center()

        def label_on_radius(tex, color, vertex, offset=0.5, scale=1.3):
            direction = vertex - center
            direction /= np.linalg.norm(direction)
            return MathTex(tex, color=color).scale(scale).move_to(vertex + direction * offset)

        lab_e = label_on_radius(r"\nu_e", YELLOW, v[0], offset=0.5)
        lab_m = label_on_radius(r"\nu_\mu", BLUE, v[1], offset=0.5)
        lab_t = label_on_radius(r"\nu_\tau", PURPLE, v[2], offset=0.6)

        levels = [0.2, 0.4, 0.6, 0.8]
        iso_lines = VGroup()
        for p in levels:
            iso_lines.add(Line(p*v[0]+(1-p)*v[1], p*v[0]+(1-p)*v[2]).set_stroke(YELLOW, 1, 0.15))
            iso_lines.add(Line(p*v[1]+(1-p)*v[0], p*v[1]+(1-p)*v[2]).set_stroke(BLUE, 1, 0.15))
            iso_lines.add(Line(p*v[2]+(1-p)*v[0], p*v[2]+(1-p)*v[1]).set_stroke(PURPLE, 1, 0.15))

        self.add(tri, iso_lines, lab_e, lab_m, lab_t)

        # -------------------- moving point & trace --------------------
        x_tracker = ValueTracker(0.0)

        def get_pos():
            pe, pm, pt = P_of_x(x_tracker.get_value())
            return pe*v[0] + pm*v[1] + pt*v[2]

        dot = always_redraw(lambda: Dot(get_pos(), radius=ui["dot_radius"], color=WHITE))
        trace = TracedPath(dot.get_center, dissipating_time=ui["trace_time"],
                        stroke_width=ui["trace_width"], stroke_color=WHITE)
        ghost = TracedPath(dot.get_center, dissipating_time=ui["ghost_time"],
                        stroke_width=ui["ghost_width"], stroke_opacity=ui["ghost_opacity"],
                        stroke_color=WHITE)
        
        self.add(ghost, trace, dot)

        # -------------------- UI Elements (Shorts Layout) --------------------
        title = MathTex(r"x = L / L^{\mathrm{osc}}_{21}", color=GRAY_A).scale(1.4)
        # Теперь здесь используется переменная с правильным LaTeX кодом
        flavor_info = MathTex(rf"\text{{Initial flavor: }} \nu_{{{tex_flavor}}}", color=WHITE).scale(1.1)
        header = VGroup(title, flavor_info).arrange(DOWN, buff=0.4).to_edge(UP, buff=1.0)

        bar = Line(LEFT*2, RIGHT*2).set_stroke(GRAY_B, 4, 0.5).next_to(header, DOWN, buff=0.6)
        knob = always_redraw(lambda: Dot(bar.point_from_proportion(x_tracker.get_value()/n_periods), radius=0.08, color=WHITE))
        x_text = always_redraw(lambda: MathTex(rf"x={x_tracker.get_value():.2f}").scale(0.9).next_to(bar, RIGHT))
        
        self.add(header, bar, knob, x_text)

        # Нижний блок параметров
        def sci_tex(val):
            exp = int(np.floor(np.log10(val)))
            mant = val / 10**exp
            return rf"{mant:.1f}\cdot 10^{{{exp}}}"
        
        params_box = VGroup(
            Text(f"Ordering: {ordering}", color=GRAY_B).scale(0.45),
            MathTex(rf"\theta_{{12}}={np.rad2deg(th12):.1f}^\circ, \theta_{{23}}={np.rad2deg(th23):.1f}^\circ, \theta_{{13}}={np.rad2deg(th13):.1f}^\circ", color=GRAY_A).scale(0.75),
            MathTex(rf"\delta_{{CP}}={np.rad2deg(dcp):.0f}^\circ", color=GRAY_A).scale(0.75),
            MathTex(rf"\Delta m^2_{{21}}={sci_tex(dm21)}, |\Delta m^2_{{31}}|={sci_tex(dm31abs)}", color=GRAY_A).scale(0.75)
        ).arrange(DOWN, buff=0.25).to_edge(DOWN, buff=0.8)
        
        frame = SurroundingRectangle(params_box, color=GRAY_B, buff=0.3, stroke_width=1).set_opacity(0.3)
        self.add(frame, params_box)

        # -------------------- execution --------------------
        self.play(x_tracker.animate.set_value(n_periods), run_time=run_time, rate_func=linear)
        self.wait(2)
