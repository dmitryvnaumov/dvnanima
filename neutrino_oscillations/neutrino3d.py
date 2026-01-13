from manim import *
import numpy as np
from osc_prob import prob_row_x 

# Настройки для вертикального формата Shorts
config.frame_width = 9
config.frame_height = 16
config.pixel_width = 1080
config.pixel_height = 1920

class NeutrinoOscillationShorts_e(Scene):
    def construct(self):
        self.camera.background_color = "#05050a"

        # -------------------- user parameters --------------------
        initial_flavor = "e"          # "e", "mu", "tau"
        ordering = "NO"               # "NO" or "IO"

        th12 = np.deg2rad(33.0)
        th23 = np.deg2rad(45.0)
        th13 = np.deg2rad(8.6)
        dcp  = np.deg2rad(180.0)

        dm21    = 7.5e-5
        dm31abs = 2.5e-3

        n_periods = 3.0
        run_time = 58.0 

        # Словарь для правильного отображения флэйворов в LaTeX
        flavor_latex = {
            "e": "e",
            "mu": r"\mu",
            "tau": r"\tau"
        }
        tex_flavor = flavor_latex.get(initial_flavor, initial_flavor)

        # -------------------- calculation logic --------------------
        n_grid = 20000
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

        tri.scale(1.15).move_to(ORIGIN).shift(UP * 0.4)
        v = tri.get_vertices()

        lab_e = MathTex(r"\nu_e", color=YELLOW).scale(1.3).move_to(v[0] + DOWN*0.6 + LEFT*0.2)
        lab_m = MathTex(r"\nu_\mu", color=BLUE).scale(1.3).move_to(v[1] + DOWN*0.6 + RIGHT*0.2)
        lab_t = MathTex(r"\nu_\tau", color=PURPLE).scale(1.3).move_to(v[2] + UP*0.7)

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

        dot = always_redraw(lambda: Dot(get_pos(), radius=0.12, color=WHITE))
        trace = TracedPath(dot.get_center, dissipating_time=3.0, stroke_width=5, stroke_color=WHITE)
        ghost = TracedPath(dot.get_center, dissipating_time=8.0, stroke_width=12, stroke_opacity=0.1, stroke_color=WHITE)
        
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