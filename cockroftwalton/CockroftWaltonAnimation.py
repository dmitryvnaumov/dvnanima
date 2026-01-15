from manim import *
import numpy as np

from pathlib import Path

from cw_config import load_cfg, resolve_paths
from cw_pipeline import build_assets


def partial_curve(full_curve: VMobject, alpha: float) -> VMobject:
    """Return a copy of full_curve clipped to [0, alpha] along its parameter."""
    alpha = float(np.clip(alpha, 0.0, 1.0))
    mob = full_curve.copy()
    mob.pointwise_become_partial(full_curve, 0.0, alpha)
    return mob


def lerp(a, b, t):
    return a + (b - a) * t


def bbox_uv_to_point(mob, u, v):
    left = mob.get_left()[0]
    right = mob.get_right()[0]
    bottom = mob.get_bottom()[1]
    top = mob.get_top()[1]
    x = left + u * (right - left)
    y = bottom + v * (top - bottom)
    return np.array([x, y, 0.0])


# --- for cw_clean.svg, n_stages=3 ---
NODE_UV = {
    "vin":   (0.11, 0.91),   # top rail near source (vin)
    "bot_1": (0.38, 0.43),   # bottom rail: end of C2 (bot_1)
    "bot_2": (0.655, 0.43),  # bottom rail: end of C4 (bot_2)
    "bot_3": (0.925, 0.43),  # bottom rail: end of C6 / output (bot_3)
}


def pretty_name(name: str) -> str:
    if name == "vin":
        return r"V_{\mathrm{in}}"
    if name.startswith("bot_"):
        i = int(name.split("_")[1])
        return rf"V_{{{i}}}"
    return name


def remove_svg_frame(svg: SVGMobject):
    """Remove the outer frame in cw_clean.svg by dropping the largest submobject."""
    if not svg.submobjects:
        return

    def area(m):
        return float(m.width * m.height)

    frame = max(svg.submobjects, key=area)
    svg.remove(frame)


BASE_DIR = Path(__file__).resolve().parent
CFG = load_cfg(BASE_DIR / "run.cfg")
PATHS = resolve_paths(CFG["paths"], BASE_DIR)

config.pixel_width = CFG["manim"]["pixel_width"]
config.pixel_height = CFG["manim"]["pixel_height"]
config.frame_width = CFG["manim"]["frame_width"]
config.frame_height = CFG["manim"]["frame_height"]
config.frame_rate = CFG["manim"]["frame_rate"]


class CockcroftWaltonAnimation(Scene):
    def construct(self):
        anim = CFG["animation"]
        self.camera.background_color = CFG["manim"]["background_color"]

        if CFG["paths"]["auto_generate"]:
            needs_build = CFG["paths"]["force_regen"] or (
                not PATHS["npz"].exists()
                or not PATHS["svg_raw"].exists()
                or not PATHS["svg_clean"].exists()
            )
            if needs_build:
                build_assets(CFG, PATHS)

        # ---------- load assets ----------
        scheme = SVGMobject(str(PATHS["svg_clean"]))
        scheme.set_stroke(WHITE, width=2)
        scheme.set_fill(opacity=0)
        remove_svg_frame(scheme)

        data = np.load(str(PATHS["npz"]))
        t = data["t"]       # seconds
        t_ms = t * 1000.0

        # infer stages from saved arrays
        bot_nodes = sorted(
            [k for k in data.files if k.startswith("bot_")],
            key=lambda s: int(s.split("_")[1])
        )

        curves = {"vin": data["vin"]}
        for bn in bot_nodes:
            curves[bn] = data[bn]

        vmin = min(float(np.min(v)) for v in curves.values())
        vmax = max(float(np.max(v)) for v in curves.values())
        pad = 0.08 * (vmax - vmin) if vmax > vmin else 1.0
        y0, y1 = vmin - pad, vmax + pad
        # ---------- layout ----------
        ax = Axes(
            x_range=[float(t_ms[0]), float(t_ms[-1]), float(t_ms[-1] - t_ms[0]) / 4],
            y_range=[y0, y1, (y1 - y0) / 4],
            x_length=anim["ax_x_length"],
            y_length=anim["ax_y_length"],
            tips=False,
        ).to_edge(DOWN, buff=anim["ax_bottom_buff"])

        ax_labels = ax.get_axis_labels(
            Text("t, ms", font_size=anim["ax_label_font_size"]),
            Text("V", font_size=anim["ax_label_font_size"]),
        )

        self.add(scheme, ax, ax_labels)
        scheme.height = anim["scheme_height"]
        scheme.next_to(ax, UP, buff=0.05).align_to(ax, ORIGIN)
        scheme.shift(UP * anim["scheme_shift_y"])

        # ---------- colors ----------
        stage_colors = [BLUE, ORANGE, GREEN, PURPLE, TEAL, MAROON, GOLD]

        def col(i):
            return stage_colors[(i - 1) % len(stage_colors)]

        line_specs = [("vin", GREY_B)]
        for i, bn in enumerate(bot_nodes, start=1):
            line_specs.append((bn, col(i)))

        color_map = dict(line_specs)

        # ---------- animate-all parameter (0..1) ----------
        draw_alpha = ValueTracker(0.0)

        # ---------- plot curves + legend ----------
        plotted = VGroup()
        legend_items = VGroup()

        for name, c in line_specs:
            v = curves[name]
            pts = [ax.c2p(tt, vv) for tt, vv in zip(t_ms, v)]
            full_curve = VMobject().set_points_as_corners(pts)

            curve_vis = always_redraw(
                lambda fc=full_curve, colr=c:
                    partial_curve(fc, draw_alpha.get_value()).set_stroke(colr, anim["curve_width"])
            )
            plotted.add(curve_vis)

            sw = Line(ORIGIN, RIGHT * 0.6).set_stroke(c, anim["legend_line_width"])
            txt = MathTex(pretty_name(name), font_size=anim["legend_font_size"]).set_color(WHITE)
            legend_items.add(VGroup(sw, txt).arrange(RIGHT, buff=0.15))

        legend = legend_items.arrange(RIGHT, buff=0.6).next_to(ax, UP, buff=0.2).scale(0.9)

        self.add(plotted, legend)

        # ---------- probes on scheme ----------
        node_pos = {k: bbox_uv_to_point(scheme, *uv) for k, uv in NODE_UV.items()}
        probe_nodes = ["vin", "bot_1", "bot_2", "bot_3"]

        probes = VGroup()
        labels = VGroup()

        for name in probe_nodes:
            p = node_pos[name]
            c = color_map.get(name, WHITE)

            dot = Dot(p, radius=0.06, color=c).set_stroke(WHITE, 1, 0.6)
            probes.add(dot)

            if name.startswith("bot_"):
                lab = MathTex(pretty_name(name), font_size=18).next_to(dot, DOWN, buff=0.10)
                labels.add(lab)

        self.add(probes, labels)

        # ---------- readout tied to draw_alpha ----------
        out_node = bot_nodes[-1] if bot_nodes else "vin"
        out_color = color_map.get(out_node, GREY_B)

        def v_at(node, tt_ms):
            return float(np.interp(tt_ms, t_ms, curves[node]))

        def current_t_ms():
            return lerp(float(t_ms[0]), float(t_ms[-1]), draw_alpha.get_value())

        readout = always_redraw(lambda: MathTex(
            rf"{pretty_name(out_node)} = {v_at(out_node, current_t_ms()):.2f}\,\mathrm{{V}}",
            font_size=26
        ).set_color(out_color).next_to(legend, UP, buff=0.15))
        self.add(readout)

        # ---------- animate ----------
        self.play(draw_alpha.animate.set_value(1.0), run_time=anim["run_time"], rate_func=linear)
        self.wait(anim["tail_wait"])
