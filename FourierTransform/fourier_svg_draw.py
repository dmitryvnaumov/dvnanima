from manim import *
import numpy as np
from pathlib import Path
import configparser
from img2svg import get_fourier_samples


# -----------------------------
# Optional config (run.cfg)
# -----------------------------
def load_cfg(path: str = "run.cfg") -> dict:
    cfg = configparser.ConfigParser(inline_comment_prefixes=(";",))
    if Path(path).exists():
        cfg.read(Path(path))

    def get(section, key, cast=str, fallback=None):
        if cfg.has_option(section, key):
            return cast(cfg.get(section, key))
        if fallback is None:
            raise KeyError(f"Missing [{section}] {key} in {path}")
        return cast(fallback)

    manim_params = {
        "pixel_width": get("manim", "pixel_width", int, 1080),
        "pixel_height": get("manim", "pixel_height", int, 1920),
        "frame_width": get("manim", "frame_width", float, 9.0),
        "frame_height": get("manim", "frame_height", float, 16.0),
        "frame_rate": get("manim", "frame_rate", int, 60),
        "background_color": get("manim", "background_color", str, "#000000"),
    }

    scene = {
        "total_time": get("scene", "total_time", float, 12.0),
        "n_samples": get("scene", "n_samples", int, 2048),
        "n_terms": get("scene", "n_terms", int, 80),
        "slider_length": get("scene", "slider_length", float, 6.5),
        "slider_shift_down": get("scene", "slider_shift_down", float, 4.8),
        "full_path_opacity": get("scene", "full_path_opacity", float, 0.25),
        "full_path_width": get("scene", "full_path_width", float, 2.0),
        "active_path_width": get("scene", "active_path_width", float, 4.0),
        "dot_radius": get("scene", "dot_radius", float, 0.06),
        "circle_width": get("scene", "circle_width", float, 2.0),
        "vector_width": get("scene", "vector_width", float, 3.0),
        "max_draw_scale": get("scene", "max_draw_scale", float, 3.6),
        "title_scale": get("scene", "title_scale", float, 0.85),
        "label_scale": get("scene", "label_scale", float, 0.65),
        "svg_path": get("scene", "svg_path", str, ""),  # empty -> default pi path
    }

    colors = {
        "label_col": get("colors", "label_col", str, "#FFD166"),
        "path_col": get("colors", "path_col", str, "#7AA6FF"),
        "active_path_col": get("colors", "active_path_col", str, "#4D6BFF"),
        "dot_col": get("colors", "dot_col", str, "#FF4D4D"),
        "circle_col": get("colors", "circle_col", str, "#FF4D4D"),
        "vector_col": get("colors", "vector_col", str, "#FF4D4D"),
        "slider_col": get("colors", "slider_col", str, "#FFFFFF"),
        "knob_col": get("colors", "knob_col", str, "#FFD166"),
        "tick_col": get("colors", "tick_col", str, "#FFFFFF"),
    }

    return {"manim": manim_params, "scene": scene, "colors": colors}


CFG = load_cfg("run.cfg")

config.pixel_width = CFG["manim"]["pixel_width"]
config.pixel_height = CFG["manim"]["pixel_height"]
config.frame_width = CFG["manim"]["frame_width"]
config.frame_height = CFG["manim"]["frame_height"]
config.frame_rate = CFG["manim"]["frame_rate"]


# -----------------------------
# Default SVG (pi outline)
# Single-path SVG, normalized-ish viewbox.
# You can replace this path with any other default you like.
# -----------------------------
DEFAULT_PI_SVG = r"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <path d="M35 45
           L165 45
           L165 70
           L140 70
           L140 155
           C140 170 132 178 118 178
           C104 178 96 170 96 155
           L96 70
           L72 70
           L72 155
           C72 170 64 178 50 178
           C36 178 28 170 28 155
           L28 70
           L35 70
           Z"
        fill="none" stroke="black" stroke-width="6"/>
</svg>
"""


def ensure_default_svg_file() -> Path:
    # Writes default SVG to local file if user didn't provide a path.
    p = Path("default_pi.svg")
    if not p.exists():
        p.write_text(DEFAULT_PI_SVG, encoding="utf-8")
    return p


def sample_svg_points(svg_path: str, n_samples: int) -> np.ndarray:
    """
    Returns complex samples z[k] = x + i y, k=0..n_samples-1
    from (possibly multi-path) SVG. We sample each subpath uniformly
    in its own parameter and then concatenate proportionally to length
    (approximated by point distances).
    """
    svg = SVGMobject(svg_path, fill_opacity=0.0, stroke_opacity=0.0)
    # Extract submobjects that actually have geometry points.
    parts = [m for m in svg.family_members_with_points() if len(m.get_points()) >= 2]
    if len(parts) == 0:
        raise ValueError(f"No drawable paths found in SVG: {svg_path}")

    # For each part, make a coarse polyline to estimate its length,
    # then allocate samples proportional to that length.
    def approx_length(m: VMobject, coarse: int = 200) -> float:
        pts = np.array([m.point_from_proportion(a) for a in np.linspace(0, 1, coarse)])
        d = np.linalg.norm(pts[1:] - pts[:-1], axis=1)
        return float(d.sum())

    lengths = np.array([approx_length(m) for m in parts], dtype=float)
    total = float(lengths.sum())
    if total <= 0:
        raise ValueError("SVG total length is zero or invalid")

    # Allocate samples; ensure at least 2 per part if it has length.
    alloc = np.maximum(2, np.floor(n_samples * lengths / total).astype(int))
    # Fix rounding to get exactly n_samples.
    diff = int(n_samples - alloc.sum())
    # Distribute the remainder deterministically.
    order = np.argsort(-lengths)
    for i in range(abs(diff)):
        j = order[i % len(order)]
        alloc[j] += 1 if diff > 0 else -1
        alloc[j] = max(2, alloc[j])

    # Now sample each part and concatenate.
    pts_all = []
    for m, k in zip(parts, alloc):
        alphas = np.linspace(0, 1, k, endpoint=False)
        pts = np.array([m.point_from_proportion(a) for a in alphas])
        pts_all.append(pts)

    pts = np.concatenate(pts_all, axis=0)

    # Close the curve by rotating so it starts near the first point (optional),
    # and enforce zero-mean + scale later.
    z = pts[:, 0] + 1j * pts[:, 1]
    return z


def sample_path_points(path: str, n_samples: int) -> np.ndarray:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Path not found: {path}")

    ext = p.suffix.lower()
    if ext in {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}:
        z = get_fourier_samples(str(p), num_points=n_samples)
        if len(z) == 0:
            raise ValueError(f"No contour points found in image: {path}")
        return np.asarray(z, dtype=np.complex128)

    return sample_svg_points(str(p), n_samples)


def normalize_complex_path(z: np.ndarray, max_scale: float = 3.6) -> np.ndarray:
    # Center.
    z0 = z - np.mean(z)
    # Scale to fit roughly inside frame.
    max_abs = np.max(np.abs(z0))
    if max_abs <= 0:
        return z0
    z0 = z0 / max_abs * max_scale
    return z0


def fourier_coeffs_fft(z: np.ndarray):
    """
    For samples z[k], k=0..N-1 representing z(t) with t=k/N,
    compute coefficients c[n] for exp(2π i n t).
    """
    N = len(z)
    c = np.fft.fft(z) / N
    freqs = np.fft.fftfreq(N, d=1.0 / N).astype(int)
    return freqs, c


class FourierSVGEpicycles(Scene):
    def construct(self):
        scene = CFG["scene"]
        colors = CFG["colors"]
        self.camera.background_color = CFG["manim"]["background_color"]

        # Choose SVG path.
        svg_path = scene["svg_path"].strip()
        if svg_path == "":
            svg_file = ensure_default_svg_file()
            svg_path = str(svg_file)

        # Preview original input at the top.
        def make_preview(path: str) -> Mobject:
            ext = Path(path).suffix.lower()
            if ext in {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}:
                m = ImageMobject(path)
            else:
                m = SVGMobject(path, fill_opacity=0.0, stroke_opacity=1.0, stroke_color=colors["label_col"])
                m.set_stroke(width=3)
            return m

        preview = make_preview(svg_path)
        preview.scale_to_fit_height(2.8)
        preview.to_edge(UP, buff=0.35)
        self.add(preview)

        # Sample and normalize path.
        N = int(scene["n_samples"])
        z_samples = sample_path_points(svg_path, N)
        z_samples = normalize_complex_path(z_samples, max_scale=scene["max_draw_scale"])
        path_pts = np.column_stack((z_samples.real, z_samples.imag, np.zeros(len(z_samples))))

        # Fourier decomposition.
        freqs, coeffs = fourier_coeffs_fft(z_samples)

        # Sort terms by amplitude (dominant first).
        amps = np.abs(coeffs)
        order = np.argsort(-amps)
        n_terms = min(int(scene["n_terms"]), N)

        # Keep DC term early (helps anchor).
        # We'll take top n_terms by amplitude, but ensure freq=0 included.
        top = list(order[:n_terms])
        if 0 not in top:
            idx0 = int(np.where(freqs == 0)[0][0])
            top[-1] = idx0
        # Re-sort selected by amplitude.
        top = sorted(top, key=lambda i: -amps[i])

        sel_freqs = freqs[top]
        sel_coeffs = coeffs[top]

        # Time parameter t in [0,1]
        t = ValueTracker(0.0)

        # Title / formula (style similar to your zeta scene).
        title = MathTex(r"\mathrm{Fourier\ Transform}", color=colors["label_col"]).scale(scene["title_scale"])
        title.next_to(preview, DOWN, buff=0.20)

        formula = MathTex(
            r"z(t)=\sum_{n} c_n e^{2\pi i n t}",
            color=colors["label_col"]
        ).scale(scene["label_scale"]).next_to(title, DOWN, buff=0.18)

        self.add(title, formula)

        # Full path (faint), active path (bright) using traced point.
        def z_of_t(tt: float) -> complex:
            # Reconstruction using selected terms.
            phase = np.exp(2j * np.pi * sel_freqs * tt)
            return complex(np.sum(sel_coeffs * phase))

        draw_shift = np.array([0.0, -0.55, 0.0])

        # Moving point (initialize at correct position BEFORE any TracedPath)
        z0 = z_of_t(t.get_value())
        dot = Dot(
            [z0.real, z0.imag, 0] + draw_shift,
            radius=scene["dot_radius"],
            color=colors["dot_col"],
        )

        dot.add_updater(lambda m: m.move_to([z_of_t(t.get_value()).real,
                                            z_of_t(t.get_value()).imag, 0] + draw_shift))

        self.add(dot)
        # Give updaters one frame to run; Manim requires a positive wait time.
        self.wait(1.0 / CFG["manim"]["frame_rate"])

        # Now traces won't connect from origin
        full_trace = TracedPath(
            dot.get_center,
            stroke_color=colors["path_col"],
            stroke_width=scene["full_path_width"],
            stroke_opacity=scene["full_path_opacity"],
            dissipating_time=None,
        )
        active_trace = TracedPath(
            dot.get_center,
            stroke_color=colors["active_path_col"],
            stroke_width=scene["active_path_width"],
            stroke_opacity=1.0,
            dissipating_time=None,
        )

        self.add(full_trace, active_trace)

        # Epicycle group (circles + vectors + intermediate dots).
        epi_group = VGroup()
        epi_fade = ValueTracker(1.0)

        def rebuild_epicycles():
            epi_group.submobjects = []
            origin = np.array([0.0, 0.0, 0.0]) + draw_shift
            pos = origin.copy()

            # Build chain in the chosen order.
            tt = t.get_value()
            fade = epi_fade.get_value()
            for n, c in zip(sel_freqs, sel_coeffs):
                r = abs(c)
                ang = 2 * np.pi * n * tt + np.angle(c)

                # Circle at current center.
                circ = Circle(radius=r, color=colors["circle_col"], stroke_width=scene["circle_width"])
                circ.set_stroke(opacity=0.25 * fade)
                circ.move_to(pos)

                # Vector to next point.
                nxt = pos + np.array([r * np.cos(ang), r * np.sin(ang), 0.0])
                vec = Line(pos, nxt, color=colors["vector_col"], stroke_width=scene["vector_width"])
                vec.set_stroke(opacity=0.75 * fade)

                epi_group.add(circ, vec)
                pos = nxt

        epi_group.add_updater(lambda m: rebuild_epicycles())
        self.add(epi_group, dot)

        # Slider for t (0..1).
        slider_half = scene["slider_length"] / 2
        slider = Line(LEFT * slider_half, RIGHT * slider_half, color=colors["slider_col"], stroke_width=3)
        slider.shift(DOWN * (scene["slider_shift_down"] + 0.6))

        knob = Dot(radius=0.09, color=colors["knob_col"])
        knob.add_updater(
            lambda m: m.move_to(interpolate(slider.get_start(), slider.get_end(), np.clip(t.get_value(), 0, 1)))
        )

        t_label = MathTex(r"t=", color=colors["label_col"]).scale(0.75)
        t_label.next_to(slider, UP, buff=0.18).set_x(slider.get_left()[0] + 0.8)

        t_val = DecimalNumber(0.0, num_decimal_places=2, color=colors["label_col"]).scale(0.65)
        t_val.next_to(t_label, RIGHT, buff=0.15)

        def update_t(m):
            m.set_value(t.get_value())

        t_val.add_updater(update_t)

        self.add(slider, knob, t_label, t_val)

        # Run animation: t=0 -> 1
        self.play(t.animate.set_value(1.0), run_time=scene["total_time"], rate_func=linear)
        # Ensure final blue path stays visible even if traced path is cleared.
        final_path = VMobject().set_points_as_corners(path_pts + draw_shift)\
            .set_stroke(colors["active_path_col"], width=scene["active_path_width"], opacity=1.0)
        self.add(final_path)
        # Fade epicycles at the end; keep blue traces visible.
        self.play(epi_fade.animate.set_value(0.12), run_time=0.6)
        self.wait()
