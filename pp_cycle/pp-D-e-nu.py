from manim import *
import numpy as np
from colors import *

from pathlib import Path
from pp_config import load_cfg

BASE_DIR = Path(__file__).resolve().parent
CFG = load_cfg(BASE_DIR / "run.cfg")

config.pixel_width = CFG["manim"]["pixel_width"]
config.pixel_height = CFG["manim"]["pixel_height"]
config.frame_width = CFG["manim"]["frame_width"]
config.frame_height = CFG["manim"]["frame_height"]
config.frame_rate = CFG["manim"]["frame_rate"]


class PP_to_D_e_nu(Scene):
    def construct(self):
        self.camera.background_color = CFG["manim"]["background_color"]

        # ----------------- helpers -----------------
        def particle_body(color, r=0.22, stroke_w=3):
            c = Circle(radius=r).set_stroke(width=stroke_w)
            c.set_fill(color, opacity=1.0)
            c.set_stroke(WHITE, opacity=0.9)
            return c

        def label(tex, scale=0.7):
            return MathTex(tex).scale(scale)

        def glow_layers(shape, n=7, scale=1.08, opacity=0.18):
            layers = VGroup()
            for k in range(1, n + 1):
                layer = shape.copy().scale(scale**k)
                layer.set_stroke(width=0)
                layer.set_fill(opacity=opacity / (k**0.75))
                layers.add(layer)
            return layers

        def flash_ring(point, r=0.30, w=7, op=0.85):
            ring = Circle(radius=r).move_to(point)
            ring.set_stroke(WHITE, width=w, opacity=op)
            ring.set_fill(opacity=0)
            return ring

        def soft_bloom(shape, n=3):
            # короткий "bloom" как у 3b1b: пару полупрозрачных заливок
            blooms = VGroup()
            for k in range(1, n + 1):
                b = shape.copy().scale(1.06 + 0.06*k)
                b.set_stroke(width=0)
                b.set_fill(opacity=0.20 / (k**1.2))
                blooms.add(b)
            return blooms

        # скорость замедляется, но НЕ до нуля в конце:
        # smooth дает нулевую скорость на конце, поэтому добавляем чуть-чуть линейной компоненты
        def decel_not_stop(t):
            return 0.92 * smooth(t) + 0.08 * t  # остаточный "ход" в конце



        def gentle_wiggle(mobj, amp=0.028, t=0.75):
            self.play(mobj.animate.shift(amp*UP), rate_func=there_and_back, run_time=t)

        # ----------------- objects: geometry separated from labels -----------------
        center = ORIGIN + 0.15 * DOWN

        # Protons
        p_r = 0.22
        pL_body = particle_body(P_COLOR, r=p_r)
        pR_body = particle_body(P_COLOR, r=p_r)
        pL_lab  = label("p", scale=0.75)
        pR_lab  = label("p", scale=0.75)
        pL = VGroup(pL_body, pL_lab)
        pR = VGroup(pR_body, pR_lab)
        pL_lab.move_to(pL_body)
        pR_lab.move_to(pR_body)

        # Deuteron
        D_body = particle_body(D_COLOR, r=0.25)
        D_lab  = label(r"{}^{2}\mathrm{D}", scale=0.62)
        D = VGroup(D_body, D_lab)
        D_lab.move_to(D_body)

        # Positron 
        e_body = particle_body(EP_COLOR, r=0.24)
        e_plus = MathTex(r"e^+").scale(0.55)
        e = VGroup(e_body, e_plus)

        # Neutrino: simple circle + label
        nu_body = particle_body(NU_COLOR, r=0.22, stroke_w=2)
        nu_lab  = MathTex(r"\nu_e").scale(0.55)
        nu = VGroup(nu_body, nu_lab)
        nu_lab.move_to(nu_body)

        # positions
        pL.move_to(center + 3.1 * LEFT)
        pR.move_to(center + 3.1 * RIGHT)

        gL = glow_layers(pL_body, n=8, scale=1.07, opacity=0.20).move_to(pL_body)
        gR = glow_layers(pR_body, n=8, scale=1.07, opacity=0.20).move_to(pR_body)

        self.add(gL, gR, pL, pR)

        # ----------------- ONE continuous approach to overlap (no pauses) -----------------
        self.play(
            pL.animate.move_to(center),
            pR.animate.move_to(center),
            gL.animate.move_to(center),
            gR.animate.move_to(center),
            run_time=4.2,
            rate_func=decel_not_stop
        )

        # ----------------- instant morph at full overlap -----------------
        D.move_to(center)
        gD = glow_layers(D_body, n=11, scale=1.065, opacity=0.22).move_to(center)

        ring = flash_ring(center, r=0.30, w=7, op=0.85)
        blooms = soft_bloom(D_body, n=3).move_to(center)

        # главная "3b1b" магия: shape-match + tex-match
        self.play(
            AnimationGroup(
                Create(ring),
                FadeIn(blooms, scale=0.98),
                TransformMatchingShapes(VGroup(pL_body, pR_body), D_body),
                TransformMatchingTex(VGroup(pL_lab, pR_lab), D_lab),
                FadeOut(VGroup(gL, gR), scale=0.90),
                FadeIn(gD, scale=0.92),
                lag_ratio=0.0
            ),
            run_time=1.15,
            rate_func=smooth
        )

        # подчистим: убираем pL,pR и лишний bloom
        self.remove(pL, pR)
        self.add(D)
        self.play(
            ring.animate.scale(3.6).set_stroke(opacity=0.0),
            blooms.animate.scale(1.25).set_opacity(0.0),
            run_time=0.55,
            rate_func=smooth
        )
        self.remove(ring, blooms)

        # ----------------- deuteron "wobble" (then products appear) -----------------
        gentle_wiggle(D, amp=0.03, t=0.85)

        # ----------------- emission (momentum conservation, appear slightly off-center) -----------------
        theta = -18 * DEGREES  # можно менять вручную
        axis = np.array([np.cos(theta), np.sin(theta), 0.0])

        # продукты появляются уже чуть разнесёнными вдоль оси
        spawn_shift = 0.22
        e_start  = center + spawn_shift * (axis[0] * RIGHT + axis[1] * UP)
        nu_start = center - spawn_shift * (axis[0] * RIGHT + axis[1] * UP)

        e.move_to(e_start)
        nu.move_to(nu_start)

        self.play(
            FadeIn(e, scale=0.92),
            FadeIn(nu, scale=0.92),
            run_time=0.45,
            rate_func=smooth
        )

        # траектории строго по одной оси в разные стороны
        d = 3.25
        e_end  = center + d * (axis[0] * RIGHT + axis[1] * UP)
        nu_end = center - d * (axis[0] * RIGHT + axis[1] * UP)

        e_path  = Line(e.get_center(),  e_end)
        nu_path = Line(nu.get_center(), nu_end)


        def flap_updater(mob, dt):
            t = self.renderer.time
            ang = 0.16 * np.sin(5.0 * t)  # медленнее/мягче
            wL.rotate( ang * dt, about_point=ball.get_center())
            wR.rotate(-ang * dt, about_point=ball.get_center())


        # полёт медленнее, чтобы успеть увидеть
        self.play(
            MoveAlongPath(e, e_path, rate_func=decel_not_stop),
            MoveAlongPath(nu, nu_path, rate_func=decel_not_stop),
            run_time=3.6
        )

        # финальная пауза: всё остается на экране
        self.wait(1.2)
