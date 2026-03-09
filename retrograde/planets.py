from manim import *
import numpy as np
from pathlib import Path
import configparser

try:
    from manim.opengl import OpenGLSurface, OpenGLTexturedSurface
except Exception:
    OpenGLSurface = None
    OpenGLTexturedSurface = None

try:
    from PIL import Image, ImageOps
except Exception:
    Image = None
    ImageOps = None


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
    }

    planets = {
        "renderer": get("planets", "renderer", str, "opengl"),
        "background_color": get("planets", "background_color", str, "#000000"),
        "label_col": get("planets", "label_col", str, "#FFD166"),
        "title_font_size": get("planets", "title_font_size", int, 72),
        "title_buff": get("planets", "title_buff", float, 0.65),
        "planet_radius": get("planets", "planet_radius", float, 1.75),
        "planet_shift_y": get("planets", "planet_shift_y", float, 0.2),
        "sphere_u": get("planets", "sphere_u", int, 64),
        "sphere_v": get("planets", "sphere_v", int, 96),
        "star_count": get("planets", "star_count", int, 120),
        "star_seed": get("planets", "star_seed", int, 7),
        "star_xlim": get("planets", "star_xlim", float, 4.2),
        "star_ylim": get("planets", "star_ylim", float, 7.6),
        "camera_phi_deg": get("planets", "camera_phi_deg", float, 70),
        "camera_theta_deg": get("planets", "camera_theta_deg", float, -35),
        "camera_zoom": get("planets", "camera_zoom", float, 1.15),
        "planet_spin_rate": get("planets", "planet_spin_rate", float, 0.55),
        "ring_spin_rate": get("planets", "ring_spin_rate", float, -0.10),
        "ambient_rate": get("planets", "ambient_rate", float, 0.10),
        "ring_in_scale": get("planets", "ring_in_scale", float, 1.26),
        "ring_out_scale": get("planets", "ring_out_scale", float, 1.86),
        "ring_thickness": get("planets", "ring_thickness", float, 0.08),
        "ring_tilt_x_deg": get("planets", "ring_tilt_x_deg", float, 25),
        "ring_tilt_z_deg": get("planets", "ring_tilt_z_deg", float, 10),
        "ring_fill_col": get("planets", "ring_fill_col", str, "#CFC7B4"),
        "ring_fill_opacity": get("planets", "ring_fill_opacity", float, 0.55),
        "ring_stroke_width": get("planets", "ring_stroke_width", float, 0.8),
        "ring_stroke_opacity": get("planets", "ring_stroke_opacity", float, 0.12),
        "ring_anti_z_fighting_scale": get("planets", "ring_anti_z_fighting_scale", float, 1.001),
        "mesh_u": get("planets", "mesh_u", int, 18),
        "mesh_v": get("planets", "mesh_v", int, 24),
        "mesh_stroke_width": get("planets", "mesh_stroke_width", float, 1.0),
        "mesh_stroke_opacity": get("planets", "mesh_stroke_opacity", float, 0.06),
        "jupiter_band_opacity": get("planets", "jupiter_band_opacity", float, 0.55),
        "jupiter_grs_opacity": get("planets", "jupiter_grs_opacity", float, 0.95),
        "textures_enabled": get("planets", "textures_enabled", int, 1) == 1,
        # Conservative defaults: Mars texture is usually stable in OpenGL,
        # while Jupiter/Saturn may show driver-dependent artifacts.
        "mars_texture_enabled": get("planets", "mars_texture_enabled", int, 1) == 1,
        "jupiter_texture_enabled": get("planets", "jupiter_texture_enabled", int, 0) == 1,
        "saturn_texture_enabled": get("planets", "saturn_texture_enabled", int, 0) == 1,
        "texture_u": get("planets", "texture_u", int, 48),
        "texture_v": get("planets", "texture_v", int, 96),
        "texture_u_min": get("planets", "texture_u_min", int, 24),
        "texture_v_min": get("planets", "texture_v_min", int, 48),
        "texture_u_max": get("planets", "texture_u_max", int, 192),
        "texture_v_max": get("planets", "texture_v_max", int, 384),
        "texture_snap_pow2": get("planets", "texture_snap_pow2", int, 0) == 1,
        "texture_seam_overlap_steps": get("planets", "texture_seam_overlap_steps", float, 1.0),
        "mars_texture_u": get("planets", "mars_texture_u", int, 0),
        "mars_texture_v": get("planets", "mars_texture_v", int, 0),
        "jupiter_texture_u": get("planets", "jupiter_texture_u", int, 0),
        "jupiter_texture_v": get("planets", "jupiter_texture_v", int, 0),
        "saturn_texture_u": get("planets", "saturn_texture_u", int, 0),
        "saturn_texture_v": get("planets", "saturn_texture_v", int, 0),
        "texture_gloss": get("planets", "texture_gloss", float, 0.35),
        "texture_shadow": get("planets", "texture_shadow", float, 0.45),
        "texture_image_mode": get("planets", "texture_image_mode", str, "RGB"),
        "texture_sanitize": get("planets", "texture_sanitize", int, 1) == 1,
        "texture_max_width": get("planets", "texture_max_width", int, 2048),
        "texture_cache_dir": get("planets", "texture_cache_dir", str, "assets/planets/.cache"),
        "texture_pole_eps": get("planets", "texture_pole_eps", float, 1e-5),
        "texture_hide_pole_deg": get("planets", "texture_hide_pole_deg", float, 0.0),
        "texture_hide_pole_x_deg": get("planets", "texture_hide_pole_x_deg", float, 0.0),
        "texture_hide_pole_z_deg": get("planets", "texture_hide_pole_z_deg", float, 0.0),
        "safe_textured_mode": get("planets", "safe_textured_mode", int, 1) == 1,
        "safe_textured_fader": get("planets", "safe_textured_fader", int, 1) == 1,
        "mars_texture": get("planets", "mars_texture", str, "assets/planets/2k_mars.jpg"),
        "jupiter_texture": get("planets", "jupiter_texture", str, "assets/planets/2k_jupiter.jpg"),
        "saturn_texture": get("planets", "saturn_texture", str, "assets/planets/2k_saturn.jpg"),
        "mars_dark_texture": get("planets", "mars_dark_texture", str, ""),
        "jupiter_dark_texture": get("planets", "jupiter_dark_texture", str, ""),
        "saturn_dark_texture": get("planets", "saturn_dark_texture", str, ""),
        "textured_spin_rate": get("planets", "textured_spin_rate", float, 0.0),
        "ambient_rate_textured": get("planets", "ambient_rate_textured", float, 0.06),
        "intro_time": get("planets", "intro_time", float, 0.45),
        "ring_fade_time": get("planets", "ring_fade_time", float, 0.25),
        "extras_fade_time": get("planets", "extras_fade_time", float, 0.25),
        "outro_time": get("planets", "outro_time", float, 0.45),
        "hold_default": get("planets", "hold_default", float, 1.2),
        "hold_mars": get("planets", "hold_mars", float, 1.05),
        "hold_jupiter": get("planets", "hold_jupiter", float, 1.15),
        "hold_saturn": get("planets", "hold_saturn", float, 1.20),
    }

    return {"manim": manim_params, "planets": planets}


CFG = load_cfg(str(Path(__file__).with_name("run.cfg")))

config.pixel_width = CFG["manim"]["pixel_width"]
config.pixel_height = CFG["manim"]["pixel_height"]
config.frame_width = CFG["manim"]["frame_width"]
config.frame_height = CFG["manim"]["frame_height"]
config.frame_rate = CFG["manim"]["frame_rate"]
if CFG["planets"]["renderer"]:
    config.renderer = CFG["planets"]["renderer"]


def lerp_num(a, b, t):
    return a * (1 - t) + b * t


def resolve_asset_path(path_str: str) -> Path | None:
    if not path_str:
        return None
    p = Path(path_str)
    if not p.is_absolute():
        p = (Path(__file__).parent / p).resolve()
    return p if p.exists() else None


def prepare_texture_path(src: Path | None, cfg: dict) -> Path | None:
    """
    Normalize texture assets for OpenGL stability:
    - apply EXIF orientation
    - strip metadata by re-encoding to PNG
    - optionally cap max width
    """
    if src is None:
        return None
    if not cfg.get("texture_sanitize", True):
        return src
    if Image is None or ImageOps is None:
        return src
    try:
        cache_dir = Path(__file__).parent / cfg.get("texture_cache_dir", "assets/planets/.cache")
        cache_dir.mkdir(parents=True, exist_ok=True)
        max_w = int(cfg.get("texture_max_width", 2048))
        out_name = f"{src.stem}_w{max_w}.png"
        out = cache_dir / out_name

        if out.exists() and out.stat().st_mtime >= src.stat().st_mtime:
            return out

        im = Image.open(src)
        im = ImageOps.exif_transpose(im).convert("RGB")
        if max_w > 0 and im.width > max_w:
            new_h = max(1, int(round(im.height * max_w / im.width)))
            resampling = getattr(Image, "Resampling", Image)
            im = im.resize((max_w, new_h), resampling.LANCZOS)
        im.save(out, format="PNG")
        return out
    except Exception:
        return src


def clamp_texture_resolution(u: int, v: int, cfg: dict) -> tuple[int, int]:
    def nearest_pow2(n: int) -> int:
        n = max(1, int(n))
        return 1 << int(round(np.log2(n)))

    u_min = int(cfg.get("texture_u_min", 24))
    v_min = int(cfg.get("texture_v_min", 48))
    u_max = int(cfg.get("texture_u_max", 192))
    v_max = int(cfg.get("texture_v_max", 384))
    if cfg.get("texture_snap_pow2", False):
        u = nearest_pow2(u)
        v = nearest_pow2(v)
    u = max(u_min, min(u_max, int(u)))
    v = max(v_min, min(v_max, int(v)))
    return u, v


def resolve_texture_resolution(planet_name: str, cfg: dict) -> tuple[int, int]:
    # Planet-specific values override global when > 0.
    u_key = f"{planet_name}_texture_u"
    v_key = f"{planet_name}_texture_v"
    u = int(cfg.get(u_key, 0))
    v = int(cfg.get(v_key, 0))
    if u <= 0:
        u = int(cfg["texture_u"])
    if v <= 0:
        v = int(cfg["texture_v"])
    return clamp_texture_resolution(u, v, cfg)


def make_textured_planet(radius: float, tex_path: Path, dark_tex_path: Path | None, cfg: dict):
    if not tex_path or OpenGLSurface is None or OpenGLTexturedSurface is None:
        return None

    eps = max(1e-7, float(cfg.get("texture_pole_eps", 1e-5)))

    def sphere_uv(u, v):
        # Standard spherical parameterization.
        x = radius * np.sin(u) * np.cos(v)
        y = radius * np.cos(u)
        z = radius * np.sin(u) * np.sin(v)
        return np.array([x, y, z])

    surf = OpenGLSurface(
        uv_func=sphere_uv,
        u_range=[eps, PI - eps],
        # Keep canonical azimuth range for OpenGLTexturedSurface stability.
        v_range=[0, TAU],
        resolution=(cfg["texture_u"], cfg["texture_v"]),
        gloss=cfg["texture_gloss"],
        shadow=cfg["texture_shadow"],
    )

    try:
        if dark_tex_path is not None:
            return OpenGLTexturedSurface(
                surf,
                str(tex_path),
                str(dark_tex_path),
                image_mode=cfg["texture_image_mode"],
            )
        return OpenGLTexturedSurface(
            surf,
            str(tex_path),
            image_mode=cfg["texture_image_mode"],
        )
    except Exception:
        return None

def starfield(n=120, seed=3, xlim=4.2, ylim=7.6):
    rng = np.random.default_rng(seed)
    stars = VGroup()
    for _ in range(n):
        x = rng.uniform(-xlim, xlim)
        y = rng.uniform(-ylim, ylim)
        r = rng.uniform(0.008, 0.020)
        o = rng.uniform(0.12, 0.55)
        stars.add(Dot([x, y, 0], radius=r, color=WHITE).set_opacity(o))
    return stars


def make_ring_surface(r_in=2.25, r_out=3.25, thickness=0.06):
    """
    Thick 3D ring surface for Saturn.
    """

    def ring(u, v):
        r = lerp_num(r_in, r_out, u)
        x = r * np.cos(v)
        z = r * np.sin(v)
        y = (thickness / 2) * np.sin(2 * v) * 0.15
        return np.array([x, y, z])

    return Surface(
        ring,
        u_range=[0, 1],
        v_range=[0, TAU],
        resolution=(14, 96),
    )


def make_jupiter_bands(r=1.75, band_opacity=0.55, grs_opacity=0.95):
    """
    Jupiter-like latitudinal patches plus a stylized Great Red Spot.
    """
    cols = ["#EAD9C3", "#D9B894", "#CBA27A", "#E2C09E", "#B88C6B", "#E6D2B5", "#C49A73"]
    bands = VGroup()

    thetas = np.linspace(0.20 * np.pi, 0.80 * np.pi, 12)
    for i in range(len(thetas) - 1):
        t0, t1 = thetas[i], thetas[i + 1]
        col = cols[i % len(cols)]

        def patch(u, v, t0=t0, t1=t1):
            theta = lerp_num(t0, t1, u)
            phi = v
            x = (r * 1.002) * np.sin(theta) * np.cos(phi)
            y = (r * 1.002) * np.cos(theta)
            z = (r * 1.002) * np.sin(theta) * np.sin(phi)
            return np.array([x, y, z])

        s = Surface(
            patch,
            u_range=[0, 1],
            v_range=[0, TAU],
            resolution=(6, 72),
        )
        s.set_fill(col, opacity=band_opacity)
        s.set_stroke(opacity=0.0)
        bands.add(s)

    grs = Sphere(radius=0.18, resolution=(18, 24))
    grs.set_fill("#C44A3D", opacity=grs_opacity).set_stroke(opacity=0)
    theta0, phi0 = 0.56 * np.pi, 0.20 * np.pi
    grs.move_to(
        np.array(
            [
                r * np.sin(theta0) * np.cos(phi0),
                r * np.cos(theta0),
                r * np.sin(theta0) * np.sin(phi0),
            ]
        )
        * 1.005
    )
    return bands, grs


class PlanetCardBase(ThreeDScene):
    PLANET_NAME = "Planet"
    BASE_COLOR = "#C9A27E"
    TYPE = "plain"  # plain / jupiter / saturn

    def construct(self):
        p = CFG["planets"]
        self.camera.background_color = p["background_color"]

        stars = starfield(
            n=p["star_count"],
            seed=p["star_seed"],
            xlim=p["star_xlim"],
            ylim=p["star_ylim"],
        )
        self.add(stars)

        title = Text(self.PLANET_NAME, font_size=p["title_font_size"], color=p["label_col"])
        title.to_edge(UP, buff=p["title_buff"])
        self.add_fixed_in_frame_mobjects(title)

        zoom = p["camera_zoom"]
        # OpenGL camera in some Manim builds does not support zoom kwarg.
        self.set_camera_orientation(
            phi=p["camera_phi_deg"] * DEGREES,
            theta=p["camera_theta_deg"] * DEGREES,
        )
        try:
            self.camera.frame.scale(1 / zoom)
        except Exception:
            pass

        r = p["planet_radius"]
        tex_key = f"{self.PLANET_NAME.lower()}_texture"
        dark_key = f"{self.PLANET_NAME.lower()}_dark_texture"
        tex_enabled_key = f"{self.PLANET_NAME.lower()}_texture_enabled"
        tex_u, tex_v = resolve_texture_resolution(self.PLANET_NAME.lower(), p)
        tex_cfg = dict(p)
        tex_cfg["texture_u"] = tex_u
        tex_cfg["texture_v"] = tex_v
        tex_path = resolve_asset_path(p.get(tex_key, ""))
        dark_tex_path = resolve_asset_path(p.get(dark_key, ""))
        tex_path = prepare_texture_path(tex_path, tex_cfg)
        dark_tex_path = prepare_texture_path(dark_tex_path, tex_cfg)
        planet_tex_enabled = p.get(tex_enabled_key, True)

        planet = None
        textured = False
        if p["textures_enabled"] and planet_tex_enabled:
            planet = make_textured_planet(r, tex_path, dark_tex_path, tex_cfg)
            textured = planet is not None

        if planet is None:
            planet = Sphere(radius=r, resolution=(p["sphere_u"], p["sphere_v"]))
            planet.set_fill(self.BASE_COLOR, opacity=1.0)
            planet.set_stroke(opacity=0.0)

        planet.move_to(DOWN * p["planet_shift_y"])
        hide_pole_x_deg = float(p.get("texture_hide_pole_x_deg", 0.0))
        hide_pole_z_deg = float(p.get("texture_hide_pole_z_deg", 0.0))
        if abs(hide_pole_x_deg) <= 1e-9:
            hide_pole_x_deg = float(p.get("texture_hide_pole_deg", 0.0))
        if textured:
            if abs(hide_pole_x_deg) > 1e-9:
                planet.rotate(hide_pole_x_deg * DEGREES, axis=RIGHT, about_point=planet.get_center())
            if abs(hide_pole_z_deg) > 1e-9:
                planet.rotate(hide_pole_z_deg * DEGREES, axis=OUT, about_point=planet.get_center())

        extras = Group()
        if self.TYPE == "jupiter" and not textured:
            bands, grs = make_jupiter_bands(
                r=r,
                band_opacity=p["jupiter_band_opacity"],
                grs_opacity=p["jupiter_grs_opacity"],
            )
            extras.add(bands, grs)
            extras.move_to(planet.get_center())

        ring = None
        if self.TYPE == "saturn":
            ring = make_ring_surface(
                r_in=r * p["ring_in_scale"],
                r_out=r * p["ring_out_scale"],
                thickness=p["ring_thickness"],
            )
            ring.set_fill(p["ring_fill_col"], opacity=p["ring_fill_opacity"])
            ring.set_stroke(p["ring_fill_col"], width=p["ring_stroke_width"], opacity=p["ring_stroke_opacity"])
            ring.rotate(p["ring_tilt_x_deg"] * DEGREES, axis=RIGHT)
            ring.rotate(p["ring_tilt_z_deg"] * DEGREES, axis=OUT)
            if textured:
                if abs(hide_pole_x_deg) > 1e-9:
                    ring.rotate(hide_pole_x_deg * DEGREES, axis=RIGHT)
                if abs(hide_pole_z_deg) > 1e-9:
                    ring.rotate(hide_pole_z_deg * DEGREES, axis=OUT)
            ring.move_to(planet.get_center())
            ring.scale(float(p.get("ring_anti_z_fighting_scale", 1.001)), about_point=planet.get_center())

        mesh = Group()
        mesh_cls = globals().get("SurfaceMesh")
        if mesh_cls is not None and not textured:
            try:
                mesh = mesh_cls(planet, resolution=(p["mesh_u"], p["mesh_v"]))
                mesh.set_stroke(WHITE, opacity=p["mesh_stroke_opacity"], width=p["mesh_stroke_width"])
            except Exception:
                mesh = Group()

        safe_textured = textured and p.get("safe_textured_mode", True)
        if safe_textured:
            # Avoid Transform/Fade interpolation on OpenGLTexturedSurface:
            # it can produce geometry artifacts on some drivers.
            self.add(planet)
            if p.get("safe_textured_fader", True):
                fader = FullScreenRectangle(fill_color=p["background_color"], fill_opacity=1.0)
                if hasattr(fader, "set_z_index"):
                    fader.set_z_index(100)
                self.add(fader)
                try:
                    self.bring_to_front(fader)
                except Exception:
                    pass
                self.play(FadeIn(title, shift=DOWN * 0.12), fader.animate.set_opacity(0), run_time=p["intro_time"])
                self.remove(fader)
            else:
                self.play(FadeIn(title, shift=DOWN * 0.12), run_time=p["intro_time"])
        elif textured:
            self.play(FadeIn(title, shift=DOWN * 0.12), FadeIn(planet), run_time=p["intro_time"])
        else:
            self.play(FadeIn(title, shift=DOWN * 0.12), FadeIn(planet, shift=UP * 0.12), run_time=p["intro_time"])
        if ring:
            self.play(FadeIn(ring), run_time=p["ring_fade_time"])
        if len(extras) > 0:
            self.play(FadeIn(extras), run_time=p["extras_fade_time"])
        if len(mesh) > 0:
            self.add(mesh)

        spin_rate = p["textured_spin_rate"] if textured else p["planet_spin_rate"]

        def spin_about_center(m, dt):
            m.rotate(spin_rate * dt, axis=UP, about_point=planet.get_center())

        # Apply rotations per-object to avoid OpenGLTexturedSurface group-transform artifacts.
        if abs(spin_rate) > 1e-9:
            planet.add_updater(spin_about_center)
            if len(mesh) > 0:
                mesh.add_updater(spin_about_center)
            if len(extras) > 0:
                extras.add_updater(spin_about_center)
        if ring:
            ring.add_updater(lambda m, dt: m.rotate(p["ring_spin_rate"] * dt, axis=UP, about_point=planet.get_center()))

        ambient_rate = p["ambient_rate_textured"] if textured else p["ambient_rate"]
        self.begin_ambient_camera_rotation(rate=ambient_rate)

        hold_key = f"hold_{self.PLANET_NAME.lower()}"
        hold_time = p[hold_key] if hold_key in p else p["hold_default"]
        self.wait(hold_time)

        self.stop_ambient_camera_rotation()
        planet.clear_updaters()
        if len(mesh) > 0:
            mesh.clear_updaters()
        if len(extras) > 0:
            extras.clear_updaters()
        if ring:
            ring.clear_updaters()

        if safe_textured:
            self.play(
                *( [FadeOut(mesh)] if len(mesh) > 0 else [] ),
                *( [FadeOut(extras)] if len(extras) > 0 else [] ),
                *( [FadeOut(ring)] if ring else [] ),
                FadeOut(title, shift=UP * 0.12),
                run_time=p["outro_time"],
            )
            self.remove(planet)
        else:
            self.play(
                *( [FadeOut(planet)] if textured else [FadeOut(planet, shift=DOWN * 0.12)] ),
                *( [FadeOut(mesh)] if len(mesh) > 0 else [] ),
                *( [FadeOut(extras)] if len(extras) > 0 else [] ),
                *( [FadeOut(ring)] if ring else [] ),
                FadeOut(title, shift=UP * 0.12),
                run_time=p["outro_time"],
            )
        self.wait(0.05)


class MarsCard(PlanetCardBase):
    PLANET_NAME = "Mars"
    BASE_COLOR = "#C1440E"
    TYPE = "plain"


class JupiterCard(PlanetCardBase):
    PLANET_NAME = "Jupiter"
    BASE_COLOR = "#D2B48C"
    TYPE = "jupiter"


class SaturnCard(PlanetCardBase):
    PLANET_NAME = "Saturn"
    BASE_COLOR = "#D8C8A0"
    TYPE = "saturn"
