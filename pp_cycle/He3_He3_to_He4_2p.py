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


class He3_He3_to_He4_2p(Scene):
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
                b.set_fill(opacity=0.20 / (k**1.2))
                blooms.add(b)
            return blooms

        def flash_ring(point, r=0.32, w=7, op=0.85):
            ring = Circle(radius=r).move_to(point)
            ring.set_stroke(WHITE, width=w, opacity=op)
            ring.set_fill(opacity=0)
            return ring

        def decel_not_stop(t):
            return 0.92 * smooth(t) + 0.08 * t

        def gentle_wiggle(mobj, amp=0.025, t=0.8):
            self.play(mobj.animate.shift(amp*UP), rate_func=there_and_back, run_time=t)

        # ----------------- objects -----------------
        center = ORIGIN + 0.15 * DOWN

        # He-3 (left & right)
        He3L_body = particle_body(HE3_COLOR, r=0.27)
        He3L_lab  = label(r"{}^{3}\mathrm{He}", scale=0.60)
        He3L = VGroup(He3L_body, He3L_lab)
        He3L_lab.move_to(He3L_body)

        He3R_body = particle_body(HE3_COLOR, r=0.27)
        He3R_lab  = label(r"{}^{3}\mathrm{He}", scale=0.60)
        He3R = VGroup(He3R_body, He3R_lab)
        He3R_lab.move_to(He3R_body)

        # He-4 (final)
        He4_body = particle_body(HE4_COLOR, r=0.30)
        He4_lab  = label(r"{}^{4}\mathrm{He}", scale=0.62)
        He4 = VGroup(He4_body, He4_lab)
        He4_lab.move_to(He4_body)

        # outgoing protons
        def make_proton():
            body = particle_body(P_COLOR, r=0.22)
            lab  = label("p", scale=0.75)
            lab.move_to(body)
            return VGroup(body, lab)

        p1 = make_proton()
        p2 = make_proton()

        # glows
        gL = glow_layers(He3L_body, n=10, scale=1.06, opacity=0.22)
        gR = glow_layers(He3R_body, n=10, scale=1.06, opacity=0.22)

        # approach axis
        theta = 0 * DEGREES
        axis = np.array([np.cos(theta), np.sin(theta), 0.0])

        left_pos  = center - 3.2 * (axis[0]*RIGHT + axis[1]*UP)
        right_pos = center + 3.2 * (axis[0]*RIGHT + axis[1]*UP)

        He3L.move_to(left_pos)
        He3R.move_to(right_pos)
        gL.move_to(left_pos)
        gR.move_to(right_pos)

        self.add(gL, gR, He3L, He3R)

        # ----------------- continuous approach -----------------
        self.play(
            He3L.animate.move_to(center),
            He3R.animate.move_to(center),
            gL.animate.move_to(center),
            gR.animate.move_to(center),
            run_time=4.5,
            rate_func=decel_not_stop
        )

        # ----------------- fusion to He-4 -----------------
        He4.move_to(center)
        gHe4 = glow_layers(He4_body, n=12, scale=1.06, opacity=0.25).move_to(center)

        ring   = flash_ring(center)
        blooms = soft_bloom(He4_body, n=3).move_to(center)

        self.play(
            AnimationGroup(
                Create(ring),
                FadeIn(blooms, scale=0.98),
                TransformMatchingShapes(VGroup(He3L_body, He3R_body), He4_body),
                TransformMatchingTex(VGroup(He3L_lab, He3R_lab), He4_lab),
                FadeOut(VGroup(gL, gR), scale=0.90),
                FadeIn(gHe4, scale=0.92),
                lag_ratio=0.0
            ),
            run_time=1.25,
            rate_func=smooth
        )

        self.remove(He3L, He3R)
        self.add(He4)

        gentle_wiggle(He4, amp=0.03, t=0.9)

        # ----------------- emit two protons (momentum conservation) -----------------
        perp = np.array([-axis[1], axis[0], 0.0])  # orthogonal direction

        spawn_shift = 0.25
        p1.move_to(center + spawn_shift * (perp[0]*RIGHT + perp[1]*UP))
        p2.move_to(center - spawn_shift * (perp[0]*RIGHT + perp[1]*UP))

        self.play(
            FadeIn(p1, scale=0.92),
            FadeIn(p2, scale=0.92),
            ring.animate.scale(3.6).set_stroke(opacity=0.0),
            blooms.animate.scale(1.25).set_opacity(0.0),
            run_time=0.6,
            rate_func=smooth
        )
        self.remove(ring, blooms)

        d = 3.5
        p1_end = center + d * (perp[0]*RIGHT + perp[1]*UP)
        p2_end = center - d * (perp[0]*RIGHT + perp[1]*UP)

        p1_path = Line(p1.get_center(), p1_end)
        p2_path = Line(p2.get_center(), p2_end)

        self.play(
            MoveAlongPath(p1, p1_path, rate_func=decel_not_stop),
            MoveAlongPath(p2, p2_path, rate_func=decel_not_stop),
            run_time=3.2
        )

        # финал: He-4 в центре, два протона разлетелись
        self.wait(1.4)
