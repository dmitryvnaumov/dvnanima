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


class D_p_to_He3_gamma(Scene):
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

        def soft_bloom(shape, n=3):
            blooms = VGroup()
            for k in range(1, n + 1):
                b = shape.copy().scale(1.06 + 0.06*k)
                b.set_stroke(width=0)
                b.set_fill(opacity=0.18 / (k**1.2))
                blooms.add(b)
            return blooms

        def flash_ring(point, r=0.30, w=7, op=0.75):
            ring = Circle(radius=r).move_to(point)
            ring.set_stroke(WHITE, width=w, opacity=op)
            ring.set_fill(opacity=0)
            return ring

        def decel_not_stop(t):
            return 0.92 * smooth(t) + 0.08 * t

        def gentle_wiggle(mobj, amp=0.02, t=0.7):
            self.play(mobj.animate.shift(amp*UP), rate_func=there_and_back, run_time=t)

        # ----------------- objects -----------------
        center = ORIGIN + 0.15 * DOWN

        # Deuteron
        D_body = particle_body(D_COLOR, r=0.25)
        D_lab  = label(r"{}^{2}\mathrm{D}", scale=0.62)
        D = VGroup(D_body, D_lab)
        D_lab.move_to(D_body)

        # Proton
        p_body = particle_body(P_COLOR, r=0.22)
        p_lab  = label("p", scale=0.75)
        p = VGroup(p_body, p_lab)
        p_lab.move_to(p_body)

        # Helium-3
        He3_body = particle_body(HE3_COLOR, r=0.27)  # светлее D, чтобы различалось
        He3_lab  = label(r"{}^{3}\mathrm{He}", scale=0.60)
        He3 = VGroup(He3_body, He3_lab)
        He3_lab.move_to(He3_body)

        # Gamma as a particle (circle)
        gam_body = particle_body(GAMMA_COLOR, r=0.16, stroke_w=2)
        gam_lab  = MathTex(r"\gamma").scale(0.60)
        gam = VGroup(gam_body, gam_lab)
        gam_lab.move_to(gam_body)

        # Glows
        gD = glow_layers(D_body, n=10, scale=1.06, opacity=0.20).move_to(D_body)
        gp = glow_layers(p_body, n=8,  scale=1.07, opacity=0.20).move_to(p_body)
        gHe3 = glow_layers(He3_body, n=11, scale=1.06, opacity=0.22).move_to(center)
        gGam = glow_layers(gam_body, n=6, scale=1.09, opacity=0.10).move_to(gam_body)

        # initial positions along one axis
        theta = +12 * DEGREES
        axis = np.array([np.cos(theta), np.sin(theta), 0.0])

        left_pos  = center - 3.0 * (axis[0]*RIGHT + axis[1]*UP)
        right_pos = center + 3.0 * (axis[0]*RIGHT + axis[1]*UP)

        D.move_to(left_pos)
        p.move_to(right_pos)
        gD.move_to(left_pos)
        gp.move_to(right_pos)

        self.add(gD, gp, D, p)

        # ----------------- approach (continuous) -----------------
        self.play(
            D.animate.move_to(center),
            p.animate.move_to(center),
            gD.animate.move_to(center),
            gp.animate.move_to(center),
            run_time=4.0,
            rate_func=decel_not_stop
        )

        # ----------------- morph to He3 -----------------
        He3.move_to(center)

        ring = flash_ring(center, r=0.30, w=7, op=0.80)
        blooms = soft_bloom(He3_body, n=3).move_to(center)

        self.play(
            AnimationGroup(
                Create(ring),
                FadeIn(blooms, scale=0.98),
                TransformMatchingShapes(VGroup(D_body, p_body), He3_body),
                TransformMatchingTex(VGroup(D_lab, p_lab), He3_lab),
                FadeOut(VGroup(gD, gp), scale=0.90),
                FadeIn(gHe3, scale=0.92),
                lag_ratio=0.0
            ),
            run_time=1.15,
            rate_func=smooth
        )

        # подчистим
        self.remove(D, p)
        self.add(He3)

        # короткое "волнение" He3
        gentle_wiggle(He3, amp=0.018, t=0.55)

        # ----------------- gamma appears slightly off-center and flies away -----------------
        spawn_shift = 0.22
        # пусть гамма уходит примерно "вверх-вправо" относительно оси, но можно сделать вдоль оси
        # В едином стиле лучше вдоль оси (как импульс), выберем направление +axis
        gam_start = center + spawn_shift * (axis[0]*RIGHT + axis[1]*UP)
        gam_end   = center + 3.4 * (axis[0]*RIGHT + axis[1]*UP)

        gam.move_to(gam_start)
        gGam.move_to(gam_start)

        self.play(
            FadeIn(gGam, scale=0.92),
            FadeIn(gam, scale=0.92),
            ring.animate.scale(3.6).set_stroke(opacity=0.0),
            blooms.animate.scale(1.25).set_opacity(0.0),
            run_time=0.6,
            rate_func=smooth
        )
        self.remove(ring, blooms)

        gam_path = Line(gam.get_center(), gam_end)

        self.play(
            MoveAlongPath(gam, gam_path, rate_func=decel_not_stop),
            MoveAlongPath(gGam, gam_path, rate_func=decel_not_stop),
            run_time=2.8
        )

        # финальная пауза: He3 и gamma остаются
        self.wait(1.2)
