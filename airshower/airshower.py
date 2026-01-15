from manim import *
import numpy as np
import random

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
        "pixel_width": get("manim", "pixel_width", int),
        "pixel_height": get("manim", "pixel_height", int),
        "frame_width": get("manim", "frame_width", float),
        "frame_height": get("manim", "frame_height", float),
        "frame_rate": get("manim", "frame_rate", int, 60),
        "background_color": get("manim", "background_color", str),
    }

    airshower = {
        "seed": get("airshower", "seed", int, 7),
        "stroke_width": get("airshower", "stroke_width", float, 8.0),
        "generations": get("airshower", "generations", int, 4),
        "n_children": get("airshower", "n_children", int, 4),
        "base_len": get("airshower", "base_len", float, 2.3),
        "shrink": get("airshower", "shrink", float, 0.62),
        "spread_deg": get("airshower", "spread_deg", float, 55.0),
        "root_x": get("airshower", "root_x", float, 0.2),
        "root_y": get("airshower", "root_y", float, 0.2),
        "primary_len": get("airshower", "primary_len", float, 4.2),
        "dash_length": get("airshower", "dash_length", float, 0.18),
        "dashed_ratio": get("airshower", "dashed_ratio", float, 0.55),
        "bg_opacity": get("airshower", "bg_opacity", float, 0.85),
        "primary_time": get("airshower", "primary_time", float, 1.0),
        "generation_time": get("airshower", "generation_time", float, 0.8),
        "generation_decay": get("airshower", "generation_decay", float, 0.85),
        "min_generation_time": get("airshower", "min_generation_time", float, 0.45),
        "lag_ratio": get("airshower", "lag_ratio", float, 0.025),
        "tail_wait": get("airshower", "tail_wait", float, 0.2),
    }

    return {"manim": manim_params, "airshower": airshower}


CFG = load_cfg("run.cfg")

config.pixel_width = CFG["manim"]["pixel_width"]
config.pixel_height = CFG["manim"]["pixel_height"]
config.frame_width = CFG["manim"]["frame_width"]
config.frame_height = CFG["manim"]["frame_height"]
config.frame_rate = CFG["manim"]["frame_rate"]

class AirShower(Scene):
    def construct(self):
        p = CFG["airshower"]
        random.seed(p["seed"])  # Fix the randomness for reproducibility

        # ---------- style ----------
        self.camera.background_color = CFG["manim"]["background_color"]
        stroke_w = p["stroke_width"]

        # ---------- shower parameters ----------
        generations = p["generations"]  # branching generations
        n_children = p["n_children"]    # tracks per node
        base_len = p["base_len"]        # length of the first segment
        shrink = p["shrink"]            # length decay per generation
        spread_deg = p["spread_deg"]    # total fan spread (degrees)

        # ---------- geometry ----------
        # First interaction point
        root = np.array([p["root_x"], p["root_y"], 0.0])

        # Primary track direction: from upper-right into the root
        primary_dir = normalize(np.array([-1.0, -0.55, 0.0]))

        # Start of the primary track (off-frame)
        primary_start = root - primary_dir * p["primary_len"]

        primary = DashedLine(
            primary_start, root,
            dash_length=p["dash_length"], dashed_ratio=p["dashed_ratio"],
            color=WHITE, stroke_width=stroke_w
        )
        bg = ImageMobject("atmosphere.jpg")
        bg.height = config.frame_height  # fit to height
        bg.move_to(ORIGIN)
        bg.set_z_index(-10)
        self.add(bg)
        bg.set_opacity(p["bg_opacity"])

        # ---------- branch generation by generations ----------
        gen_groups = []  # list of VGroup: [gen1, gen2, ...]

        def children_dirs(parent_dir, k):
            """k directions around parent_dir in the XY plane (fan)."""
            # base angle of parent_dir
            ang0 = np.arctan2(parent_dir[1], parent_dir[0])
            # symmetric fan around ang0
            spread = np.deg2rad(spread_deg)
            if k == 1:
                angles = [ang0]
            else:
                angles = np.linspace(ang0 - spread/2, ang0 + spread/2, k)

            dirs = []
            for a in angles:
                # small randomness to avoid perfect symmetry
                a += np.deg2rad(random.uniform(-6, 6))
                d = np.array([np.cos(a), np.sin(a), 0.0])
                # normalize and bias downward so tracks head to the ground
                d = normalize(d + np.array([0.0, -0.18, 0.0]))
                dirs.append(d)
            return dirs

        # Current "leaves" (segment ends) where children grow
        leaves = [(root, primary_dir, base_len)]

        for g in range(generations):
            group = VGroup()
            new_leaves = []
            length = base_len * (shrink ** g)

            for (leaf_pos, parent_dir, _) in leaves:
                dirs = children_dirs(parent_dir, n_children)
                for d in dirs:
                    end = leaf_pos + d * length
                    seg = Line(leaf_pos, end, color=WHITE, stroke_width=stroke_w)
                    group.add(seg)
                    new_leaves.append((end, d, length))

            gen_groups.append(group)
            leaves = new_leaves

        # ---------- animation ----------
        # Primary track first, then branches with smoother timing
        self.play(Create(primary), run_time=p["primary_time"], rate_func=smooth)

        # Generations: grouped with subtle lag inside each group
        for i, grp in enumerate(gen_groups):
            gen_time = max(
                p["min_generation_time"],
                p["generation_time"] * (p["generation_decay"] ** i),
            )
            self.play(
                LaggedStart(
                    *[Create(m, rate_func=smooth) for m in grp],
                    lag_ratio=p["lag_ratio"],
                ),
                run_time=gen_time,
            )

        self.wait(p["tail_wait"])
