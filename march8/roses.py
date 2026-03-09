from manim import *
import numpy as np
from pathlib import Path
import configparser
import math


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
        "renderer": get("manim", "renderer", str, ""),
    }

    scene = {
        "random_seed": get("scene", "random_seed", int, 8),
        "total_time": get("scene", "total_time", float, 60.0),
        "formula_tex": get("scene", "formula_tex", str, r"r(\\theta)=a\\cos\\!\\big(k(\\theta+\\phi)\\big)"),
        "formula_scale": get("scene", "formula_scale", float, 0.88),
        "formula_top_buff": get("scene", "formula_top_buff", float, 0.35),
        "formula_in_time": get("scene", "formula_in_time", float, 1.2),
        "formula_hold_time": get("scene", "formula_hold_time", float, 0.8),
        "show_k_label": get("scene", "show_k_label", int, 1) == 1,
        "k_label_tex": get("scene", "k_label_tex", str, r"k=\\frac{n}{d}"),
        "k_label_scale": get("scene", "k_label_scale", float, 0.85),
        "k_label_buff": get("scene", "k_label_buff", float, 0.42),
        "k_label_in_time": get("scene", "k_label_in_time", float, 0.55),
        "show_param_table": get("scene", "show_param_table", int, 1) == 1,
        "table_in_time": get("scene", "table_in_time", float, 0.55),
        "table_top_buff": get("scene", "table_top_buff", float, 0.16),
        "table_text_scale": get("scene", "table_text_scale", float, 0.30),
        "table_row_height": get("scene", "table_row_height", float, 0.30),
        "table_slot_width": get("scene", "table_slot_width", float, 0.23),
        "table_slot_gap": get("scene", "table_slot_gap", float, 0.05),
        "table_n_values": get("scene", "table_n_values", str, "1,2,3,4,5,6,7"),
        "table_d_values": get("scene", "table_d_values", str, "1,2,3,4,5,6,7,8,9"),
        "table_line_opacity": get("scene", "table_line_opacity", float, 0.38),
        "table_fill_opacity": get("scene", "table_fill_opacity", float, 0.05),
        "table_slot_opacity": get("scene", "table_slot_opacity", float, 0.22),
        "table_copy_lag": get("scene", "table_copy_lag", float, 0.22),
        "table_rose_size": get("scene", "table_rose_size", float, 0.10),
        "table_theta_step": get("scene", "table_theta_step", float, 0.05),
        "show_guide_contour": get("scene", "show_guide_contour", int, 1) == 1,
        "guide_fade_time": get("scene", "guide_fade_time", float, 0.7),
        "guide_hold_time": get("scene", "guide_hold_time", float, 0.2),
        "guide_final_opacity": get("scene", "guide_final_opacity", float, 0.08),
        "eight_source": get("scene", "eight_source", str, "text").lower(),
        "eight_text": get("scene", "eight_text", str, "8"),
        "eight_font_candidates": get(
            "scene",
            "eight_font_candidates",
            str,
            "Snell Roundhand, Zapfino, STIX Two Text, Times New Roman, PT Sans",
        ),
        "eight_weight": get("scene", "eight_weight", str, "BOLD"),
        "eight_slant": get("scene", "eight_slant", int, 1) == 1,
        "eight_tex_fallback": get("scene", "eight_tex_fallback", str, r"\\mathit{8}"),
        "eight_height": get("scene", "eight_height", float, 6.8),
        "eight_rotation_deg": get("scene", "eight_rotation_deg", float, -6.0),
        "eight_shear": get("scene", "eight_shear", float, -0.08),
        "eight_offset_x": get("scene", "eight_offset_x", float, 0.0),
        "eight_offset_y": get("scene", "eight_offset_y", float, 0.0),
        "eight_stroke_width": get("scene", "eight_stroke_width", float, 2.0),
        "eight_stroke_opacity": get("scene", "eight_stroke_opacity", float, 0.22),
        "rose_count": get("scene", "rose_count", int, 36),
        "rose_k_values": get("scene", "rose_k_values", str, "2,3,4,5,6,7,8,9"),
        "rose_size_min": get("scene", "rose_size_min", float, 0.26),
        "rose_size_max": get("scene", "rose_size_max", float, 0.52),
        "rose_size_floor": get("scene", "rose_size_floor", float, 0.14),
        "rose_min_gap": get("scene", "rose_min_gap", float, 0.03),
        "rose_anchor_oversample": get("scene", "rose_anchor_oversample", int, 12),
        "rose_stroke_width": get("scene", "rose_stroke_width", float, 2.0),
        "rose_opacity": get("scene", "rose_opacity", float, 0.95),
        "rose_lag_ratio": get("scene", "rose_lag_ratio", float, 0.10),
        "rose_theta_step": get("scene", "rose_theta_step", float, 0.03),
        "anchor_start": get("scene", "anchor_start", float, 0.02),
        "anchor_end": get("scene", "anchor_end", float, 0.98),
        "final_fill_time": get("scene", "final_fill_time", float, 1.0),
        "final_fill_color": get("scene", "final_fill_color", str, "#CC1F2F"),
        "final_fill_opacity": get("scene", "final_fill_opacity", float, 0.92),
        "copy_to_heart_time": get("scene", "copy_to_heart_time", float, 0.9),
        "heart_transform_time": get("scene", "heart_transform_time", float, 1.2),
        "heart_copy_scale": get("scene", "heart_copy_scale", float, 0.40),
        "heart_offset_x": get("scene", "heart_offset_x", float, 1.45),
        "heart_offset_y": get("scene", "heart_offset_y", float, -2.10),
        "heart_height": get("scene", "heart_height", float, 1.35),
        "heart_stroke_width": get("scene", "heart_stroke_width", float, 2.4),
        "min_draw_time": get("scene", "min_draw_time", float, 6.0),
        "final_wait": get("scene", "final_wait", float, 1.5),
    }

    colors = {
        "formula_col": get("colors", "formula_col", str, "#FFD166"),
        "guide_col": get("colors", "guide_col", str, "#FFFFFF"),
        "rose_palette": get("colors", "rose_palette", str, "#FFD6E0,#CDE7FF,#D9FBD0,#FFF1C9,#E7D7FF"),
    }

    return {"manim": manim_params, "scene": scene, "colors": colors}


def parse_int_list(raw: str, fallback: list[int]) -> list[int]:
    out = []
    for token in raw.replace(";", ",").split(","):
        token = token.strip()
        if not token:
            continue
        try:
            out.append(int(token))
        except ValueError:
            continue
    return out if out else fallback


def parse_str_list(raw: str, fallback: list[str]) -> list[str]:
    out = [token.strip() for token in raw.split(",") if token.strip()]
    return out if out else fallback


def parse_k_ratio_list(raw: str, fallback: list[int]) -> list[tuple[int, int, float]]:
    out = []
    for token in raw.replace(";", ",").split(","):
        token = token.strip()
        if not token:
            continue

        try:
            if "/" in token:
                m_raw, n_raw = token.split("/", maxsplit=1)
                m = int(m_raw.strip())
                n = int(n_raw.strip())
            else:
                m = int(token)
                n = 1
        except ValueError:
            continue

        if n == 0:
            continue
        if n < 0:
            m, n = -m, -n

        gcd = math.gcd(abs(m), abs(n))
        if gcd > 0:
            m //= gcd
            n //= gcd

        out.append((m, n, float(m / n)))

    if out:
        return out
    return [(k, 1, float(k)) for k in fallback]


def ratio_to_tex(m: int, n: int) -> str:
    if n == 1:
        return str(m)
    return rf"\frac{{{m}}}{{{n}}}"


def build_param_table(
    row_keys: list[tuple[int, int]],
    row_counts: dict[tuple[int, int], int],
    scene: dict,
    colors: dict,
) -> tuple[VGroup, dict[tuple[int, int], list[VMobject]]]:
    row_h = scene["table_row_height"]
    text_scale = scene["table_text_scale"]
    slot_w = scene["table_slot_width"]
    slot_gap = scene["table_slot_gap"]
    slot_h = 0.62 * row_h

    max_slots = max(row_counts.values()) if row_counts else 1
    slot_padding = 0.16
    col_m_w = 0.52
    col_n_w = 0.52
    col_k_w = 1.30
    col_slots_w = slot_padding * 2 + max_slots * slot_w + max(0, max_slots - 1) * slot_gap

    n_rows_total = 1 + len(row_keys)
    total_w = col_m_w + col_n_w + col_k_w + col_slots_w
    total_h = n_rows_total * row_h

    left = -0.5 * total_w
    top = 0.5 * total_h
    x_sep_1 = left + col_m_w
    x_sep_2 = x_sep_1 + col_n_w
    x_sep_3 = x_sep_2 + col_k_w

    frame = RoundedRectangle(
        corner_radius=0.05,
        width=total_w,
        height=total_h,
    )
    frame.set_stroke(
        color=colors["guide_col"],
        width=1.0,
        opacity=scene["table_line_opacity"],
    )
    frame.set_fill(
        color=BLACK,
        opacity=scene["table_fill_opacity"],
    )

    table_parts = VGroup(frame)

    for x in (x_sep_1, x_sep_2, x_sep_3):
        line = Line(
            np.array([x, -0.5 * total_h, 0.0]),
            np.array([x, 0.5 * total_h, 0.0]),
        )
        line.set_stroke(
            color=colors["guide_col"],
            width=1.0,
            opacity=scene["table_line_opacity"],
        )
        table_parts.add(line)

    for row_idx in range(1, n_rows_total):
        y = top - row_idx * row_h
        line = Line(
            np.array([left, y, 0.0]),
            np.array([left + total_w, y, 0.0]),
        )
        line.set_stroke(
            color=colors["guide_col"],
            width=1.0,
            opacity=scene["table_line_opacity"],
        )
        table_parts.add(line)

    header_y = top - 0.5 * row_h
    headers = [
        MathTex("m"),
        MathTex("n"),
        MathTex(r"k=\frac{m}{n}"),
        MathTex(r"\mathrm{roses}"),
    ]
    header_x = [
        left + 0.5 * col_m_w,
        x_sep_1 + 0.5 * col_n_w,
        x_sep_2 + 0.5 * col_k_w,
        x_sep_3 + 0.5 * col_slots_w,
    ]
    for mob, x in zip(headers, header_x):
        mob.scale(text_scale)
        mob.move_to(np.array([x, header_y, 0.0]))
        mob.set_color(colors["guide_col"])
        table_parts.add(mob)

    slot_map = {}
    for row_idx, key in enumerate(row_keys):
        m, n = key
        y = top - (row_idx + 1.5) * row_h

        entry_m = MathTex(str(m)).scale(text_scale).move_to(np.array([left + 0.5 * col_m_w, y, 0.0]))
        entry_n = MathTex(str(n)).scale(text_scale).move_to(np.array([x_sep_1 + 0.5 * col_n_w, y, 0.0]))
        entry_k = MathTex(ratio_to_tex(m, n)).scale(text_scale).move_to(np.array([x_sep_2 + 0.5 * col_k_w, y, 0.0]))
        for entry in (entry_m, entry_n, entry_k):
            entry.set_color(colors["guide_col"])
            table_parts.add(entry)

        row_slots = []
        row_slot_count = row_counts[key]
        x_start = x_sep_3 + slot_padding + 0.5 * slot_w
        for slot_idx in range(row_slot_count):
            x = x_start + slot_idx * (slot_w + slot_gap)
            slot = RoundedRectangle(
                corner_radius=0.04,
                width=slot_w,
                height=slot_h,
            )
            slot.set_stroke(
                color=colors["guide_col"],
                width=0.9,
                opacity=scene["table_slot_opacity"],
            )
            slot.set_fill(opacity=0.0)
            slot.move_to(np.array([x, y, 0.0]))
            row_slots.append(slot)
            table_parts.add(slot)
        slot_map[key] = row_slots

    return table_parts, slot_map


def build_param_grid_table(
    n_values: list[int],
    d_values: list[int],
    scene: dict,
    colors: dict,
) -> tuple[VGroup, dict[tuple[int, int], np.ndarray]]:
    text_scale = scene["table_text_scale"]
    row_h = scene["table_row_height"]
    cell_w = scene["table_slot_width"]
    pad_x = 0.13
    pad_y = 0.10
    label_w = 0.46
    header_h = row_h

    cols = len(n_values)
    rows = len(d_values)
    total_w = 2 * pad_x + label_w + cols * cell_w
    total_h = 2 * pad_y + header_h + rows * row_h

    left = -0.5 * total_w
    right = 0.5 * total_w
    top = 0.5 * total_h
    bottom = -0.5 * total_h
    x0 = left + pad_x
    y0 = top - pad_y

    panel = VGroup()
    frame = Rectangle(width=total_w, height=total_h)
    frame.set_stroke(color=colors["guide_col"], width=1.0, opacity=scene["table_line_opacity"])
    frame.set_fill(color=BLACK, opacity=scene["table_fill_opacity"])
    panel.add(frame)

    x_label_sep = x0 + label_w
    for x in [x_label_sep] + [x_label_sep + idx * cell_w for idx in range(cols + 1)]:
        line = Line(np.array([x, bottom, 0.0]), np.array([x, top, 0.0]))
        line.set_stroke(color=colors["guide_col"], width=0.95, opacity=scene["table_line_opacity"])
        panel.add(line)

    y_header_sep = y0 - header_h
    for y in [y_header_sep] + [y_header_sep - idx * row_h for idx in range(rows + 1)]:
        line = Line(np.array([left, y, 0.0]), np.array([right, y, 0.0]))
        line.set_stroke(color=colors["guide_col"], width=0.95, opacity=scene["table_line_opacity"])
        panel.add(line)

    diag = Line(
        np.array([x0 + 0.12 * label_w, y0 - 0.88 * header_h, 0.0]),
        np.array([x0 + 0.88 * label_w, y0 - 0.12 * header_h, 0.0]),
    )
    diag.set_stroke(color=colors["guide_col"], width=0.95, opacity=scene["table_line_opacity"])
    panel.add(diag)

    n_label = MathTex("n").scale(text_scale)
    d_label = MathTex("d").scale(text_scale)
    n_label.set_color(colors["guide_col"])
    d_label.set_color(colors["guide_col"])
    n_label.move_to(np.array([x0 + 0.70 * label_w, y0 - 0.30 * header_h, 0.0]))
    d_label.move_to(np.array([x0 + 0.30 * label_w, y0 - 0.72 * header_h, 0.0]))
    panel.add(n_label, d_label)

    for col_idx, n in enumerate(n_values):
        x = x_label_sep + (col_idx + 0.5) * cell_w
        label = MathTex(str(n)).scale(text_scale)
        label.set_color(colors["guide_col"])
        label.move_to(np.array([x, y0 - 0.5 * header_h, 0.0]))
        panel.add(label)

    for row_idx, d in enumerate(d_values):
        y = y_header_sep - (row_idx + 0.5) * row_h
        label = MathTex(str(d)).scale(text_scale)
        label.set_color(colors["guide_col"])
        label.move_to(np.array([x0 + 0.5 * label_w, y, 0.0]))
        panel.add(label)

    cell_centers = {}
    for row_idx, d in enumerate(d_values):
        y = y_header_sep - (row_idx + 0.5) * row_h
        for col_idx, n in enumerate(n_values):
            x = x_label_sep + (col_idx + 0.5) * cell_w
            cell_centers[(n, d)] = np.array([x, y, 0.0])

    return panel, cell_centers


def build_eight(scene: dict) -> VMobject:
    source = scene["eight_source"]
    if source == "mathtex":
        eight = MathTex(scene["eight_tex_fallback"])
    else:
        fonts = parse_str_list(scene["eight_font_candidates"], ["PT Sans"])
        slant = ITALIC if scene["eight_slant"] else NORMAL
        last_error = None
        eight = None
        for font_name in fonts:
            try:
                candidate = Text(
                    scene["eight_text"],
                    font=font_name,
                    slant=slant,
                    weight=scene["eight_weight"],
                )
                if len(candidate.family_members_with_points()) > 0:
                    eight = candidate
                    break
            except Exception as exc:
                last_error = exc

        if eight is None:
            if last_error is not None:
                print(f"[RoseEight] Text font fallback: {last_error}")
            eight = MathTex(scene["eight_tex_fallback"])

    eight.set_fill(opacity=0.0)
    eight.scale_to_fit_height(scene["eight_height"])
    eight.move_to(ORIGIN)

    if abs(scene["eight_rotation_deg"]) > 1e-9:
        eight.rotate(scene["eight_rotation_deg"] * DEGREES)
    if abs(scene["eight_shear"]) > 1e-9:
        eight.apply_matrix(
            np.array(
                [
                    [1.0, scene["eight_shear"], 0.0],
                    [0.0, 1.0, 0.0],
                    [0.0, 0.0, 1.0],
                ]
            )
        )
    return eight


def contour_paths(vmobj: VMobject) -> list[VMobject]:
    paths = []
    for m in vmobj.family_members_with_points():
        if isinstance(m, VMobject) and m.get_num_points() >= 4 and m.get_arc_length() > 1e-9:
            paths.append(m)
    return paths


def sample_anchor_candidates(
    paths: list[VMobject], count: int, t0: float, t1: float
) -> list[tuple[float, np.ndarray]]:
    if not paths:
        raise ValueError("No contour paths found for the digit 8.")

    lengths = np.array([p.get_arc_length() for p in paths], dtype=float)
    total = float(lengths.sum())
    if total <= 0:
        raise ValueError("Total contour length is zero for the digit 8.")

    cdf = np.cumsum(lengths) / total
    props = np.linspace(t0, t1, count, endpoint=True)

    candidates = []
    for prop in props:
        idx = int(np.searchsorted(cdf, prop, side="left"))
        idx = max(0, min(idx, len(paths) - 1))

        prev = 0.0 if idx == 0 else float(cdf[idx - 1])
        span = max(float(cdf[idx] - prev), 1e-9)
        local = (float(prop) - prev) / span
        local = float(np.clip(local, 0.0, 1.0))

        candidates.append((float(prop), paths[idx].point_from_proportion(local)))
    return candidates


def max_allowed_radius(
    point: np.ndarray,
    placed: list[dict],
    max_radius: float,
    min_gap: float,
) -> float:
    allowed = float(max_radius)
    for item in placed:
        dist = float(np.linalg.norm(point - item["point"]))
        allowed = min(allowed, dist - item["radius"] - min_gap)
    return allowed


def select_rose_layout(
    paths: list[VMobject],
    desired_count: int,
    t0: float,
    t1: float,
    size_min: float,
    size_max: float,
    size_floor: float,
    min_gap: float,
    oversample: int,
    rng: np.random.Generator,
) -> list[dict]:
    if desired_count <= 0:
        return []

    candidate_count = max(desired_count * max(1, oversample), desired_count)
    candidates = sample_anchor_candidates(paths, candidate_count, t0, t1)
    used = np.zeros(len(candidates), dtype=bool)
    placed = []

    # First pass keeps larger flowers, fallback passes allow smaller ones to hit count.
    floors = [size_floor, size_floor * 0.8, size_floor * 0.6]
    for floor in floors:
        floor = max(0.02, float(floor))
        while len(placed) < desired_count:
            best_idx = -1
            best_allowed = -1e9
            for idx, (_, point) in enumerate(candidates):
                if used[idx]:
                    continue
                allowed = max_allowed_radius(point, placed, size_max, min_gap)
                if allowed > best_allowed:
                    best_allowed = allowed
                    best_idx = idx

            if best_idx < 0 or best_allowed < floor:
                break

            target = float(rng.uniform(size_min, size_max))
            radius = min(target, best_allowed, size_max)
            radius = max(radius, floor)

            prop, point = candidates[best_idx]
            placed.append({"prop": prop, "point": point, "radius": radius})
            used[best_idx] = True

    placed.sort(key=lambda item: item["prop"])
    return placed


def make_rose(
    a: float,
    k: float,
    phase: float,
    rotation: float,
    stroke_w: float,
    theta_turns: int = 1,
    theta_step: float = 0.03,
) -> VMobject:
    def polar_rose(theta):
        r = a * np.cos(k * (theta + phase))
        return np.array([r * np.cos(theta), r * np.sin(theta), 0.0])

    turns = max(1, int(theta_turns))
    step = max(0.002, float(theta_step))
    curve = ParametricFunction(
        polar_rose,
        t_range=[0, TAU * turns, step],
        use_smoothing=False,
    )
    curve.set_stroke(width=stroke_w)
    curve.rotate(rotation)
    return curve


def make_heart(stroke_w: float) -> VMobject:
    t_vals = np.linspace(0.0, TAU, 240, endpoint=True)
    pts = []
    for t in t_vals:
        x = 16.0 * (np.sin(t) ** 3)
        y = (
            13.0 * np.cos(t)
            - 5.0 * np.cos(2.0 * t)
            - 2.0 * np.cos(3.0 * t)
            - np.cos(4.0 * t)
        )
        pts.append(np.array([x / 18.0, y / 18.0, 0.0]))

    heart = VMobject()
    heart.set_points_smoothly(pts)
    heart.close_path()
    heart.set_stroke(width=stroke_w)
    return heart


CFG = load_cfg(str(Path(__file__).with_name("run.cfg")))
config.pixel_width = CFG["manim"]["pixel_width"]
config.pixel_height = CFG["manim"]["pixel_height"]
config.frame_width = CFG["manim"]["frame_width"]
config.frame_height = CFG["manim"]["frame_height"]
config.frame_rate = CFG["manim"]["frame_rate"]
config.background_color = CFG["manim"]["background_color"]
if CFG["manim"]["renderer"]:
    config.renderer = CFG["manim"]["renderer"]


class RoseEight(Scene):
    def construct(self):
        scene = CFG["scene"]
        colors = CFG["colors"]

        rng = np.random.default_rng(scene["random_seed"])
        self.camera.background_color = CFG["manim"]["background_color"]

        Text.set_default(color=WHITE)
        MathTex.set_default(color=WHITE)

        formula = MathTex(scene["formula_tex"], color=colors["formula_col"]).scale(scene["formula_scale"])
        formula.to_edge(UP, buff=scene["formula_top_buff"])

        eight = build_eight(scene)
        eight.set_stroke(
            color=colors["guide_col"],
            width=scene["eight_stroke_width"],
            opacity=scene["eight_stroke_opacity"],
        )
        eight.shift(RIGHT * scene["eight_offset_x"] + UP * scene["eight_offset_y"])

        k_label = MathTex(scene["k_label_tex"], color=colors["formula_col"]).scale(scene["k_label_scale"])
        k_label.next_to(eight, DOWN, buff=scene["k_label_buff"])

        paths = contour_paths(eight)
        rose_layout = select_rose_layout(
            paths,
            desired_count=scene["rose_count"],
            t0=scene["anchor_start"],
            t1=scene["anchor_end"],
            size_min=scene["rose_size_min"],
            size_max=scene["rose_size_max"],
            size_floor=scene["rose_size_floor"],
            min_gap=scene["rose_min_gap"],
            oversample=scene["rose_anchor_oversample"],
            rng=rng,
        )
        if len(rose_layout) < scene["rose_count"]:
            print(
                f"[RoseEight] Packed {len(rose_layout)} roses out of requested "
                f"{scene['rose_count']}. Lower rose_size_floor/rose_min_gap or rose_count."
            )

        palette = parse_str_list(colors["rose_palette"], ["#FFD6E0", "#CDE7FF", "#D9FBD0", "#FFF1C9", "#E7D7FF"])
        n_values = [v for v in parse_int_list(scene["table_n_values"], [1, 2, 3, 4, 5, 6, 7]) if v > 0]
        d_values = [v for v in parse_int_list(scene["table_d_values"], [1, 2, 3, 4, 5, 6, 7, 8, 9]) if v > 0]
        if not n_values:
            n_values = [1, 2, 3, 4, 5, 6, 7]
        if not d_values:
            d_values = [1, 2, 3, 4, 5, 6, 7, 8, 9]

        grid_ratio_pool = []
        for d in d_values:
            for n in n_values:
                gcd = max(1, math.gcd(abs(n), abs(d)))
                num = n // gcd
                den = d // gcd
                grid_ratio_pool.append(
                    {
                        "cell_key": (n, d),
                        "num": num,
                        "den": den,
                        "k": float(num / den),
                    }
                )

        assigned_ratios = []
        if scene["show_param_table"] and grid_ratio_pool:
            if len(rose_layout) <= len(grid_ratio_pool):
                order = rng.permutation(len(grid_ratio_pool))
                assigned_ratios = [grid_ratio_pool[int(i)] for i in order[: len(rose_layout)]]
            else:
                assigned_ratios = list(grid_ratio_pool)
                extra = len(rose_layout) - len(grid_ratio_pool)
                for _ in range(extra):
                    assigned_ratios.append(grid_ratio_pool[int(rng.integers(0, len(grid_ratio_pool)))])
        else:
            ratio_pool = parse_k_ratio_list(scene["rose_k_values"], [2, 3, 4, 5, 6, 7, 8, 9])
            for _ in rose_layout:
                m, n, k = ratio_pool[int(rng.integers(0, len(ratio_pool)))]
                assigned_ratios.append(
                    {
                        "cell_key": None,
                        "num": m,
                        "den": n,
                        "k": k,
                    }
                )

        rose_specs = []
        for idx, (spec, ratio_data) in enumerate(zip(rose_layout, assigned_ratios)):
            m = int(ratio_data["num"])
            n = int(ratio_data["den"])
            k = float(ratio_data["k"])
            phase = float(rng.uniform(0.0, TAU))
            rot = float(rng.uniform(0.0, TAU))
            color = palette[idx % len(palette)]

            rose = make_rose(
                a=spec["radius"],
                k=k,
                phase=phase,
                rotation=rot,
                stroke_w=scene["rose_stroke_width"],
                theta_turns=n,
                theta_step=scene["rose_theta_step"],
            )
            rose.set_stroke(
                color=color,
                opacity=scene["rose_opacity"],
            )
            rose.move_to(spec["point"])
            rose_specs.append(
                {
                    "mob": rose,
                    "m": m,
                    "n": n,
                    "k": k,
                    "phase": phase,
                    "rot": rot,
                    "color": color,
                    "cell_key": ratio_data["cell_key"],
                }
            )

        table_overhead = scene["table_in_time"] if scene["show_param_table"] else 0.0
        table_panel = None
        cell_center_map = {}
        if scene["show_param_table"]:
            table_panel, cell_center_map = build_param_grid_table(
                n_values=n_values,
                d_values=d_values,
                scene=scene,
                colors=colors,
            )
            table_panel.next_to(formula, DOWN, buff=scene["table_top_buff"])
            table_panel.set_x(0.0)
            panel_shift = table_panel.get_center()
            cell_center_map = {
                key: center + panel_shift
                for key, center in cell_center_map.items()
            }

        guide_overhead = 0.0
        if scene["show_guide_contour"]:
            guide_overhead = scene["guide_fade_time"] + scene["guide_hold_time"]

        overhead = (
            scene["formula_in_time"]
            + scene["formula_hold_time"]
            + (scene["k_label_in_time"] if scene["show_k_label"] else 0.0)
            + table_overhead
            + guide_overhead
            + scene["final_fill_time"]
            + scene["copy_to_heart_time"]
            + scene["heart_transform_time"]
            + scene["final_wait"]
        )
        draw_time = max(scene["min_draw_time"], scene["total_time"] - overhead)

        self.play(Write(formula), run_time=scene["formula_in_time"])
        if scene["formula_hold_time"] > 0:
            self.wait(scene["formula_hold_time"])
        if scene["show_k_label"]:
            self.play(Write(k_label), run_time=scene["k_label_in_time"])

        if scene["show_param_table"] and table_panel is not None:
            self.play(
                FadeIn(table_panel, shift=0.15 * DOWN),
                run_time=scene["table_in_time"],
            )

        if scene["show_guide_contour"]:
            self.play(FadeIn(eight), run_time=scene["guide_fade_time"])
            if scene["guide_hold_time"] > 0:
                self.wait(scene["guide_hold_time"])

        rose_animations = []
        if scene["show_param_table"] and cell_center_map:
            filled_cells = set()
            table_stroke_w = max(1.0, 0.8 * scene["rose_stroke_width"])
            table_rose_radius = min(
                scene["table_rose_size"],
                0.46 * min(scene["table_slot_width"], scene["table_row_height"]),
            )
            for item in rose_specs:
                cell_key = item["cell_key"]
                center = cell_center_map.get(cell_key)
                if cell_key is None or center is None or cell_key in filled_cells:
                    rose_animations.append(Create(item["mob"]))
                    continue

                filled_cells.add(cell_key)
                table_rose = make_rose(
                    a=table_rose_radius,
                    k=item["k"],
                    phase=0.0,
                    rotation=0.0,
                    stroke_w=table_stroke_w,
                    theta_turns=item["n"],
                    theta_step=scene["table_theta_step"],
                )
                table_rose.set_stroke(color=item["color"], opacity=scene["rose_opacity"])
                table_rose.move_to(center)

                rose_animations.append(
                    AnimationGroup(
                        Create(item["mob"]),
                        TransformFromCopy(item["mob"], table_rose),
                        lag_ratio=scene["table_copy_lag"],
                    )
                )
        else:
            rose_animations = [Create(item["mob"]) for item in rose_specs]

        self.play(
            LaggedStart(
                *rose_animations,
                lag_ratio=scene["rose_lag_ratio"],
            ),
            run_time=draw_time,
        )

        self.play(
            eight.animate.set_fill(
                color=scene["final_fill_color"],
                opacity=scene["final_fill_opacity"],
            ).set_stroke(
                color=scene["final_fill_color"],
                opacity=1.0,
                width=max(1.0, scene["eight_stroke_width"]),
            ),
            run_time=scene["final_fill_time"],
        )

        eight_copy = (
            eight.copy()
            .scale(scene["heart_copy_scale"])
            .move_to(
                eight.get_center()
                + RIGHT * scene["heart_offset_x"]
                + UP * scene["heart_offset_y"]
            )
        )
        eight_copy.set_fill(
            color=scene["final_fill_color"],
            opacity=scene["final_fill_opacity"],
        )
        eight_copy.set_stroke(
            color=scene["final_fill_color"],
            opacity=1.0,
            width=max(1.0, scene["eight_stroke_width"]),
        )

        self.play(
            TransformFromCopy(eight, eight_copy),
            run_time=scene["copy_to_heart_time"],
        )

        heart = make_heart(scene["heart_stroke_width"])
        heart.scale_to_fit_height(scene["heart_height"])
        heart.move_to(eight_copy.get_center())
        heart.set_fill(
            color=scene["final_fill_color"],
            opacity=scene["final_fill_opacity"],
        )
        heart.set_stroke(
            color=scene["final_fill_color"],
            opacity=1.0,
            width=scene["heart_stroke_width"],
        )

        self.play(
            Transform(eight_copy, heart),
            run_time=scene["heart_transform_time"],
        )

        self.wait(scene["final_wait"])
