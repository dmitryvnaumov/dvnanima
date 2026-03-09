from manim import *
import numpy as np
from dataclasses import dataclass
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
        "pixel_width": get("manim", "pixel_width", int, 1080),
        "pixel_height": get("manim", "pixel_height", int, 1920),
        "frame_width": get("manim", "frame_width", float, 9.0),
        "frame_height": get("manim", "frame_height", float, 16.0),
        "frame_rate": get("manim", "frame_rate", int, 60),
        "background_color": get("manim", "background_color", str, "#000000"),
    }

    scene = {
        "planet_name": get("scene", "planet_name", str, "Mars"),
        "do_fourier": get("scene", "do_fourier", int, 0) == 1,
        "t_min": get("scene", "t_min", float, 0.0),
        "t_max": get("scene", "t_max", float, 4.0),
        "segment_time": get("scene", "segment_time", float, 7.0),
        "pause_end_geo": get("scene", "pause_end_geo", float, 0.80),
        "total_time_epicycles": get("scene", "total_time_epicycles", float, 7.5),
        "pause_end_fourier": get("scene", "pause_end_fourier", float, 0.50),
    }

    colors = {
        "axis_col": get("colors", "axis_col", str, "#FFFFFF"),
        "label_col": get("colors", "label_col", str, "#FFD166"),
        "path_col": get("colors", "path_col", str, "#7AA6FF"),
        "active_path_col": get("colors", "active_path_col", str, "#4D6BFF"),
        "earth_col": get("colors", "earth_col", str, "#4D6BFF"),
        "planet_col": get("colors", "planet_col", str, "#FF4D4D"),
        "slider_col": get("colors", "slider_col", str, "#FFFFFF"),
        "knob_col": get("colors", "knob_col", str, "#FFD166"),
    }

    return {"manim": manim_params, "scene": scene, "colors": colors}


CFG = load_cfg("run.cfg")

# Apply render settings from config (resolution, frame rate, etc.).
config.pixel_width = CFG["manim"]["pixel_width"]
config.pixel_height = CFG["manim"]["pixel_height"]
config.frame_width = CFG["manim"]["frame_width"]
config.frame_height = CFG["manim"]["frame_height"]
config.frame_rate = CFG["manim"]["frame_rate"]


@dataclass(frozen=True)
class Orbit:
    name: str
    a: float          # AU (semi-major axis)
    e: float          # eccentricity
    P: float          # years (sidereal period)
    M0: float         # mean anomaly at t=0 (rad)
    i: float          # inclination (rad)
    Omega: float      # longitude of ascending node (rad)
    omega: float      # argument of periapsis (rad)
    color: str


def solve_kepler(M, e, iters=10):
    """Solve Kepler: E - e sin E = M. Vectorized Newton."""
    M = np.asarray(M)
    E = M.copy()
    for _ in range(iters):
        f = E - e * np.sin(E) - M
        fp = 1 - e * np.cos(E)
        E = E - f / fp
    return E


def rot_z(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0],
                     [s,  c, 0],
                     [0,  0, 1]], dtype=float)


def rot_x(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0,  0],
                     [0, c, -s],
                     [0, s,  c]], dtype=float)


def kepler_r_eci(t, orb: Orbit):
    """
    Heliocentric 3D position in a fixed ecliptic-like frame.
    Standard rotation: Rz(Omega) Rx(i) Rz(omega) * r_orbital_plane
    """
    n = 2 * np.pi / orb.P
    M = n * t + orb.M0
    M = (M + np.pi) % (2 * np.pi) - np.pi

    E = solve_kepler(M, orb.e)
    cosE, sinE = np.cos(E), np.sin(E)
    r = orb.a * (1 - orb.e * cosE)

    nu = np.arctan2(np.sqrt(1 - orb.e**2) * sinE, cosE - orb.e)

    x_op = r * np.cos(nu)
    y_op = r * np.sin(nu)
    z_op = 0.0 * x_op
    r_op = np.stack([x_op, y_op, z_op], axis=0)  # (3, N)

    R = rot_z(orb.Omega) @ rot_x(orb.i) @ rot_z(orb.omega)
    return R @ r_op  # (3, N)


def fourier_coeffs(z_samples: np.ndarray):
    """z[k] for k=0..N-1 at tau=k/N. Returns freqs, coeffs for exp(2π i n tau)."""
    N = len(z_samples)
    c = np.fft.fft(z_samples) / N
    freqs = np.fft.fftfreq(N, d=1.0 / N).astype(int)
    return freqs, c


class Retrograde(Scene):
    def construct(self):
        # ---------- Style ----------
        scene = CFG["scene"]
        colors = CFG["colors"]
        axis_col = colors["axis_col"]
        label_col = colors["label_col"]
        path_col = colors["path_col"]
        active_path_col = colors["active_path_col"]
        slider_col = colors["slider_col"]
        knob_col = colors["knob_col"]

        self.camera.background_color = CFG["manim"]["background_color"]

        # ---------- Orbits ----------
        deg = np.pi / 180
        earth = Orbit("Earth", a=1.000, e=0.0167, P=1.000,  M0=0.8,
                      i=0.0*deg, Omega=0.0*deg, omega=102.9*deg, color=colors["earth_col"])

        planet_db = {
            "Mars": Orbit("Mars", a=1.524, e=0.0934, P=1.8808, M0=0.1,
                          i=1.85*deg, Omega=49.6*deg, omega=286.5*deg, color=colors["planet_col"]),
            "Jupiter": Orbit("Jupiter", a=5.203, e=0.0489, P=11.862, M0=1.7,
                             i=1.30*deg, Omega=100.5*deg, omega=273.9*deg, color=colors["planet_col"]),
            "Saturn": Orbit("Saturn", a=9.537, e=0.0565, P=29.457, M0=2.2,
                            i=2.49*deg, Omega=113.7*deg, omega=339.4*deg, color=colors["planet_col"]),
        }
        planet_name = scene["planet_name"]
        if planet_name not in planet_db:
            raise ValueError(f"Unknown planet_name={planet_name}. Use Mars/Jupiter/Saturn.")
        pl = planet_db[planet_name]

        # ---------- Timing ----------
        t_min = scene["t_min"]
        t_max = scene["t_max"]
        segment_time = scene["segment_time"]
        pause_end_geo = scene["pause_end_geo"]
        total_time_epicycles = scene["total_time_epicycles"]
        pause_end_fourier = scene["pause_end_fourier"]

        fps = config.frame_rate
        n_pts = int(segment_time * fps * 1.25) + 1
        t_grid = np.linspace(t_min, t_max, n_pts)

        # ---------- Precompute ephemerides ----------
        rE = kepler_r_eci(t_grid, earth)  # (3,N)
        rP = kepler_r_eci(t_grid, pl)     # (3,N)
        rG = rP - rE                      # (3,N)

        # Geocentric in orbital plane (x,y) (good pedagogically; not "sky")
        xg, yg = rG[0], rG[1]
        rmax = float(np.max(np.sqrt(xg**2 + yg**2)))
        geo_target = 2.85
        scale_geo = (geo_target / rmax) if rmax > 0 else 1.0
        X = xg * scale_geo
        Y = yg * scale_geo

        # "Sky" path = ecliptic lon/lat of geocentric vector
        lon = np.unwrap(np.arctan2(rG[1], rG[0]))  # rad
        lat = np.arctan2(rG[2], np.sqrt(rG[0]**2 + rG[1]**2))  # rad
        lon_deg = lon * 180 / np.pi
        lat_deg = lat * 180 / np.pi

        # Center the track for a clean small inset view (this is view-only, not physics)
        lonc = lon_deg - float(np.mean(lon_deg))
        latc = lat_deg - float(np.mean(lat_deg))

        # autoscale sky inset ranges
        sky_margin = 1.15
        sky_xmax = max(5.0, float(np.max(np.abs(lonc))) * sky_margin)
        sky_ymax = max(2.0, float(np.max(np.abs(latc))) * sky_margin)

        # Scaled "sky" path for Fourier (so it can replace geo curve when enabled)
        # Use independent scaling so small latitudes don't flatten the curve.
        sky_x_abs = float(np.max(np.abs(lonc)))
        sky_y_abs = float(np.max(np.abs(latc)))
        sky_sx = (geo_target / sky_x_abs) if sky_x_abs > 0 else 1.0
        sky_sy = (geo_target / sky_y_abs) if sky_y_abs > 0 else 1.0
        sky_X = lonc * sky_sx
        sky_Y = latc * sky_sy

        # ---------- Layout ----------
        # Three stacked panels of equal size (sky, heliocentric, geocentric)
        top_y = 4.55
        mid_y = 0.65
        bottom_y = -3.35
        panel_w = 7.2
        panel_h = 3.4

        # Title (planet name only)
        title = MathTex(rf"\mathbf{{{pl.name}}}", color=label_col)\
            .scale(1.00).to_edge(UP, buff=0.25)
        self.add(title)

        # ---------- Top-left: "what observer sees" ----------
        sky_axes = Axes(
            x_range=[-sky_xmax, sky_xmax, sky_xmax/2],
            y_range=[-sky_ymax, sky_ymax, sky_ymax/2],
            x_length=panel_w,
            y_length=panel_h,
            tips=False,
            axis_config={"stroke_width": 2.6, "stroke_opacity": 0.95},
        ).set_color(axis_col).move_to(np.array([0.0, mid_y, 0.0]))

        sky_label = MathTex(r"\mathbf{Sky\ (ecl.\ lon/lat)}", color=label_col).scale(0.65)\
            .next_to(sky_axes, UP, buff=0.12).set_x(sky_axes.get_center()[0])

        self.add(sky_axes, sky_label)

        # ---------- Top-right: heliocentric system (Sun, Earth, planet) ----------
        helio_axes = Axes(
            x_range=[-1, 1, 1],
            y_range=[-1, 1, 1],
            x_length=panel_w,
            y_length=panel_h,
            tips=False,
            axis_config={"stroke_width": 2.6, "stroke_opacity": 0.95},
        ).set_color(axis_col).move_to(np.array([0.0, top_y, 0.0]))

        helio_label = MathTex(r"\mathbf{Heliocentric}", color=label_col).scale(0.65)\
            .next_to(helio_axes, UP, buff=0.12).set_x(helio_axes.get_center()[0])

        self.add(helio_axes, helio_label)

        # Helio scaling: map AU -> axes coords
        helio_margin = 1.15
        helio_rmax = float(np.max(np.sqrt(rP[0]**2 + rP[1]**2))) * helio_margin
        helio_scale = 0.92 / helio_rmax  # keep inside [-1,1] nicely

        def helio_point(x_au, y_au):
            return helio_axes.c2p(x_au * helio_scale, y_au * helio_scale)

        sun_dot = Dot(helio_point(0, 0), radius=0.045, color=axis_col)

        # Orbits (faint)
        # Earth orbit: sample from precomputed rE
        earth_orbit_pts = [helio_point(rE[0, k], rE[1, k]) for k in range(n_pts)]
        earth_orbit = VMobject().set_points_smoothly(earth_orbit_pts)\
            .set_stroke(earth.color, width=2.6, opacity=0.45)

        planet_orbit_pts = [helio_point(rP[0, k], rP[1, k]) for k in range(n_pts)]
        planet_orbit = VMobject().set_points_smoothly(planet_orbit_pts)\
            .set_stroke(pl.color, width=2.6, opacity=0.40)

        e_dot = Dot(earth_orbit_pts[0], radius=0.045, color=earth.color)
        p_dot = Dot(planet_orbit_pts[0], radius=0.045, color=pl.color)

        self.add(earth_orbit, planet_orbit, sun_dot, e_dot, p_dot)

        # ---------- Bottom: geocentric plane (full width) ----------
        geo_lim = 3.0
        geo_plane = Axes(
            x_range=[-geo_lim, geo_lim, 1],
            y_range=[-geo_lim, geo_lim, 1],
            x_length=panel_w,
            y_length=panel_h,
            tips=False,
            axis_config={"stroke_width": 2.8, "stroke_opacity": 1.0},
        ).set_color(axis_col).move_to(np.array([0.0, bottom_y, 0.0]))

        geo_title = MathTex(r"\mathbf{Geocentric}", color=label_col).scale(0.65)\
            .next_to(geo_plane, UP, buff=0.18).set_x(geo_plane.get_center()[0])
        ptolemy_title = MathTex(r"\mathbf{Ptolemy\ epicycles}", color=label_col).scale(0.65)\
            .next_to(geo_plane, UP, buff=0.18).set_x(geo_plane.get_center()[0])

        self.add(geo_plane, geo_title)

        # Build point arrays for geo and sky
        geo_pts = np.array([geo_plane.c2p(xx, yy) for xx, yy in np.stack([X, Y], axis=1)])
        sky_geo_pts = np.array([geo_plane.c2p(xx, yy) for xx, yy in np.stack([sky_X, sky_Y], axis=1)])
        sky_pts = np.array([sky_axes.c2p(xx, yy) for xx, yy in np.stack([lonc, latc], axis=1)])

        # ---------- Helpers: time -> interpolation ----------
        def t_to_u(tt):
            return (tt - t_min) / (t_max - t_min) * (n_pts - 1) if t_max != t_min else 0.0

        def interp(arr_pts, tt):
            u = np.clip(t_to_u(tt), 0.0, n_pts - 1)
            i0 = int(np.floor(u))
            if i0 >= n_pts - 1:
                return arr_pts[-1]
            f = u - i0
            return (1 - f) * arr_pts[i0] + f * arr_pts[i0 + 1]

        def idx(tt):
            return int(np.clip(round(t_to_u(tt)), 0, n_pts - 1))

        # heliocentric dots (direct updaters for reliability)
        e_dot.add_updater(lambda m: m.move_to(earth_orbit_pts[idx(t.get_value())]))
        p_dot.add_updater(lambda m: m.move_to(planet_orbit_pts[idx(t.get_value())]))

        # ---------- Slider under geocentric plane ----------
        slider_len = 7.8
        slider = Line(LEFT * slider_len / 2, RIGHT * slider_len / 2,
                      color=slider_col, stroke_width=3)
        slider.next_to(geo_plane, DOWN, buff=0.85)

        t_label = MathTex(r"\mathbf{t\ (years)}", color=label_col).scale(0.65)\
            .next_to(slider, DOWN, buff=0.22)

        self.add(slider, t_label)

        def slider_point(tt):
            a = 0.0 if t_max == t_min else (tt - t_min) / (t_max - t_min)
            a = np.clip(a, 0.0, 1.0)
            return interpolate(slider.get_start(), slider.get_end(), a)

        # ---------- Anim objects driven by ValueTracker ----------
        t = ValueTracker(t_min)

        # dots
        geo_dot = Dot(interp(geo_pts, t_min), radius=0.06, color=pl.color)
        sky_dot = Dot(interp(sky_pts, t_min), radius=0.045, color=pl.color)
        knob = Dot(slider_point(t_min), radius=0.085, color=knob_col)

        # number
        t_val = DecimalNumber(t_min, num_decimal_places=2, color=label_col).scale(0.65)\
            .next_to(slider, UP, buff=0.22).set_x(slider.get_center()[0])

        # paths (geo: full+active tail). sky: same style but smaller
        geo_full = VMobject().set_stroke(path_col, width=3.0, opacity=0.55)
        geo_tail = VMobject().set_stroke(active_path_col, width=5.6, opacity=1.0)
        sky_full = VMobject().set_stroke(path_col, width=2.8, opacity=0.55)
        sky_tail = VMobject().set_stroke(active_path_col, width=4.8, opacity=1.0)

        tail_time = 0.35  # years
        tail_pts = max(2, int(tail_time / (t_max - t_min) * (n_pts - 1)))

        def update_all():
            k = max(2, idx(t.get_value()) + 1)
            k0 = max(0, k - tail_pts)

            geo_full.set_points_as_corners(geo_pts[:k])
            geo_tail.set_points_as_corners(geo_pts[k0:k])

            sky_full.set_points_as_corners(sky_pts[:k])
            sky_tail.set_points_as_corners(sky_pts[k0:k])

            geo_dot.move_to(interp(geo_pts, t.get_value()))
            sky_dot.move_to(interp(sky_pts, t.get_value()))
            knob.move_to(slider_point(t.get_value()))
            t_val.set_value(t.get_value())


        # attach a single updater to one on-screen mobject to drive all updates
        geo_full.add_updater(lambda m, dt: update_all())

        self.add(geo_full, geo_tail, sky_full, sky_tail, geo_dot, sky_dot, knob, t_val)

        # ---------- Run ----------
        self.wait(0.02)  # settle
        self.play(t.animate.set_value(t_max), run_time=segment_time, rate_func=linear)
        self.wait(pause_end_geo)

        # freeze and keep faint references
        geo_full.clear_updaters()

        sky_ref = VMobject().set_points_smoothly(list(sky_pts)).set_stroke(path_col, width=2.4, opacity=0.32)
        if not scene["do_fourier"]:
            geo_ref = VMobject().set_points_smoothly(list(geo_pts))\
                .set_stroke(path_col, width=2.6, opacity=0.28)
            self.add(geo_ref, sky_ref)
        else:
            self.add(sky_ref)
        self.play(FadeOut(geo_full), FadeOut(geo_tail), FadeOut(geo_dot),
                  FadeOut(sky_full), FadeOut(sky_tail), FadeOut(sky_dot),
                  run_time=0.30)

        # ---------- Fourier transition (optional) ----------
        if scene["do_fourier"]:
            # Remove geo reference curve and switch label so epicycles are visible
            self.play(FadeOut(geo_title), FadeIn(ptolemy_title), run_time=0.25)
            # Use complex samples from the SKY curve (lon/lat) scaled into geo_plane
            z = (sky_X + 1j * sky_Y).astype(np.complex128)
            z = z - np.mean(z)
            z = z / np.max(np.abs(z)) * 2.85  # keep comparable scale

            freqs, coeffs = fourier_coeffs(z)
            amps = np.abs(coeffs)
            order = np.argsort(-amps)

            n_terms = 10
            top = list(order[:n_terms])
            idx0 = int(np.where(freqs == 0)[0][0])
            if idx0 not in top:
                top[-1] = idx0
            top = sorted(top, key=lambda i: -amps[i])

            sel_freqs = freqs[top]
            sel_coeffs = coeffs[top]

            tau = ValueTracker(0.0)

            def z_of_tau(tt):
                phase = np.exp(2j * np.pi * sel_freqs * tt)
                return complex(np.sum(sel_coeffs * phase))

            # Pre-allocate epicycles (fast)
            unit = geo_plane.get_x_unit_size()
            circles = VGroup(*[
                Circle(radius=0.01, color=pl.color, stroke_width=2.6)
                .set_stroke(opacity=0.22)
                .set_fill(opacity=0)
                for _ in range(n_terms)
            ])
            lines = VGroup(*[
                Line(ORIGIN, RIGHT * 0.01, color=pl.color, stroke_width=3.4)
                .set_stroke(opacity=0.80)
                for _ in range(n_terms)
            ])
            epi = VGroup(circles, lines)

            def update_epicycles():
                pos = np.array([0.0, 0.0, 0.0])
                tt = tau.get_value()
                for i, (n, c) in enumerate(zip(sel_freqs, sel_coeffs)):
                    r = abs(c)
                    ang = 2*np.pi*n*tt + np.angle(c)
                    center = geo_plane.c2p(pos[0], pos[1])

                    circles[i].set(width=2 * r * unit)
                    circles[i].move_to(center)

                    nxt = pos + np.array([r*np.cos(ang), r*np.sin(ang), 0.0])
                    end = geo_plane.c2p(nxt[0], nxt[1])
                    lines[i].set_points_as_corners([center, end])

                    pos = nxt

            update_epicycles()
            epi.add_updater(lambda m: (update_epicycles(), m)[1])

            z0 = z_of_tau(0.0)
            tip = Dot(geo_plane.c2p(z0.real, z0.imag), radius=0.06, color=pl.color)
            tip.add_updater(lambda m: m.move_to(geo_plane.c2p(z_of_tau(tau.get_value()).real,
                                                             z_of_tau(tau.get_value()).imag)))

            self.add(epi, tip)
            self.wait(0.02)  # prevents initial stray segment for traced path

            fourier_trace = TracedPath(
                tip.get_center,
                stroke_color=active_path_col,
                stroke_width=5.0,
                stroke_opacity=1.0,
            )
            self.add(fourier_trace)

            tag = MathTex(r"\mathrm{Same\ curve\ =\ sum\ of\ rotations\ (Fourier)}", color=label_col)\
                .scale(0.55).next_to(geo_title, UP, buff=0.12).set_x(geo_plane.get_center()[0])
            self.play(FadeIn(tag), run_time=0.20)

            tau.set_value(0.0)
            self.play(tau.animate.set_value(1.0), run_time=total_time_epicycles, rate_func=linear)
            self.wait(pause_end_fourier)

            self.play(FadeOut(epi), FadeOut(tip), FadeOut(fourier_trace), FadeOut(tag), run_time=0.35)

        self.wait(0.3)
