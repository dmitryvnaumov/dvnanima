from manim import *
import numpy as np

# 9:16
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9.0
config.frame_height = 16.0
config.frame_rate = 60


def hex_to_rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i+2], 16) for i in (0, 2, 4)]) / 255.0


def rgb_to_color(rgb):
    rgb = np.clip(rgb, 0, 1)
    return Color(rgb=tuple(rgb))


def lerp(a, b, t):
    return a*(1-t) + b*t


def make_shaded_sphere(radius=2.2, base="#C9A27E", light_dir=np.array([-1.0, 1.0]), n_layers=80):
    """
    Fake 3D sphere for Cairo: many concentric circles with varying color/opacity,
    plus a specular highlight and a soft terminator shadow.
    """
    base_rgb = hex_to_rgb(base)
    light_dir = light_dir / (np.linalg.norm(light_dir) + 1e-9)

    layers = VGroup()
    # radial shading: center is slightly brighter, rim slightly darker
    for k in range(n_layers, 0, -1):
        r = radius * (k / n_layers)
        t = k / n_layers  # 0..1
        # brighten toward center
        col_rgb = lerp(base_rgb * 0.55, base_rgb * 1.10, t**1.6)
        c = Circle(r).set_fill(rgb_to_color(col_rgb), opacity=1.0).set_stroke(opacity=0)
        layers.add(c)

    # soft shadow (terminator) as big translucent circle offset opposite to light
    shadow = Circle(radius*1.02).set_fill(BLACK, opacity=0.25).set_stroke(opacity=0)
    shadow.shift(np.array([+0.35, -0.25, 0.0]))  # opposite to light_dir (tuned by hand)

    # highlight spot
    highlight = Circle(radius*0.35).set_fill(WHITE, opacity=0.18).set_stroke(opacity=0)
    highlight.shift(np.array([-0.55, +0.60, 0.0]))  # along light_dir

    planet = VGroup(layers, shadow, highlight)
    return planet


def make_jupiter_bands(radius=2.2, n_bands=11):
    """
    Fake Jupiter texture: ellipses inside sphere, clipped by being smaller than diameter.
    """
    # Warm Jupiter palette (hand-tuned)
    palette = [
        "#E8D5B7", "#D8B48A", "#CBA27A", "#E2C09E",
        "#B88C6B", "#E6D2B5", "#C49A73", "#EADAC3",
    ]
    bands = VGroup()
    for i in range(n_bands):
        y = lerp(+0.95*radius, -0.95*radius, i/(n_bands-1))
        w = 2.00*radius * np.sqrt(max(0.0, 1 - (y/(radius*1.03))**2))  # shrink near poles
        h = 0.28 + 0.06*np.sin(3*i)  # slight variation
        band = Ellipse(width=w, height=h).set_stroke(opacity=0).set_fill(
            rgb_to_color(hex_to_rgb(palette[i % len(palette)])), opacity=0.55
        )
        band.shift(UP * y)
        bands.add(band)

    # Great Red Spot (stylized)
    grs = Ellipse(width=0.95, height=0.55).set_fill("#C44A3D", opacity=0.75).set_stroke(opacity=0)
    grs.shift(RIGHT*0.85 + DOWN*0.10)

    return VGroup(bands, grs)


def make_ring(radius=2.2):
    """
    Saturn ring in Cairo: two ellipses (outer filled, inner cut by black overlay).
    """
    outer = Ellipse(width=2*radius*2.15, height=2*radius*0.85).set_fill("#CFC7B4", opacity=0.45).set_stroke(opacity=0)
    inner = Ellipse(width=2*radius*1.40, height=2*radius*0.55).set_fill(BLACK, opacity=1.0).set_stroke(opacity=0)
    ring = VGroup(outer, inner)
    ring.rotate(18*DEGREES)
    return ring


def make_starfield(n=80, xlim=4.2, ylim=7.6, seed=1):
    rng = np.random.default_rng(seed)
    stars = VGroup()
    for _ in range(n):
        x = rng.uniform(-xlim, xlim)
        y = rng.uniform(-ylim, ylim)
        r = rng.uniform(0.01, 0.03)
        o = rng.uniform(0.12, 0.45)
        stars.add(Dot([x, y, 0], radius=r, color=WHITE).set_opacity(o))
    return stars


class PlanetCardCairo(Scene):
    PLANET_NAME = "Planet"
    BASE = "#C9A27E"     # base color
    TYPE = "plain"       # plain/jupiter/saturn
    HOLD = 1.2

    def construct(self):
        bg = "#000000"
        label_col = "#FFD166"
        self.camera.background_color = bg

        stars = make_starfield(seed=7)
        self.add(stars)

        title = Text(self.PLANET_NAME, font_size=72, color=label_col).to_edge(UP, buff=0.7)

        radius = 2.15
        planet = make_shaded_sphere(radius=radius, base=self.BASE, n_layers=90)
        planet.move_to(DOWN*0.2)

        # Add textures per planet type
        texture = VGroup()
        ring = None
        if self.TYPE == "jupiter":
            texture = make_jupiter_bands(radius=radius)
            texture.move_to(planet.get_center())
        elif self.TYPE == "saturn":
            ring = make_ring(radius=radius)
            ring.move_to(planet.get_center())

        # A simple limb darkening edge (thin rim)
        rim = Circle(radius*1.01).set_stroke(WHITE, width=2.0, opacity=0.08).set_fill(opacity=0)
        rim.move_to(planet.get_center())

        self.play(FadeIn(title, shift=DOWN*0.2), run_time=0.45)
        self.play(FadeIn(planet, shift=UP*0.15), run_time=0.55)

        if ring:
            # ring behind + in front illusion: split by overlaying a "front" copy with higher opacity
            ring_back = ring.copy().set_opacity(0.35)
            ring_front = ring.copy().set_opacity(0.55)

            # put back ring first
            self.add(ring_back)
            self.add(texture)  # usually empty here
            self.add(rim)
            self.add(planet)

            # front ring: simple cheat (works fine visually)
            self.add(ring_front)
        else:
            self.add(texture, rim)

        # Spin illusion (Cairo): rotate texture/ring slightly over time
        def spin_tex(m, dt):
            m.rotate(0.35*dt, about_point=planet.get_center())
        if len(texture) > 0:
            texture.add_updater(spin_tex)

        if ring:
            ring.add_updater(lambda m, dt: m.rotate(-0.10*dt, about_point=planet.get_center()))

        self.wait(self.HOLD)

        # cleanup
        if len(texture) > 0:
            texture.clear_updaters()
        if ring:
            ring.clear_updaters()

        self.play(FadeOut(title, shift=UP*0.2), FadeOut(planet, shift=DOWN*0.15),
                  FadeOut(texture), FadeOut(rim),
                  *( [FadeOut(ring)] if ring else [] ),
                  run_time=0.5)
        self.wait(0.05)


class MarsCard(PlanetCardCairo):
    PLANET_NAME = "Mars"
    BASE = "#C1440E"
    TYPE = "plain"
    HOLD = 1.1


class JupiterCard(PlanetCardCairo):
    PLANET_NAME = "Jupiter"
    BASE = "#D2B48C"
    TYPE = "jupiter"
    HOLD = 1.2


class SaturnCard(PlanetCardCairo):
    PLANET_NAME = "Saturn"
    BASE = "#D8C8A0"
    TYPE = "saturn"
    HOLD = 1.25
