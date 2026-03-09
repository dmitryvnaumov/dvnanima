import numpy as np
import pyvista as pv

try:
    from .cherenkov_geometry import (
        build_unwrapped_multiline_polydata,
        make_unwrapped_outline,
        make_unwrapped_string_guides,
        nearest_distance_to_polylines,
        normalize,
        segmented_points_to_polylines,
        unwrap_cylinder_points,
    )
    from .cherenkov_history import build_multiline_polydata
except ImportError:
    from cherenkov_geometry import (
        build_unwrapped_multiline_polydata,
        make_unwrapped_outline,
        make_unwrapped_string_guides,
        nearest_distance_to_polylines,
        normalize,
        segmented_points_to_polylines,
        unwrap_cylinder_points,
    )
    from cherenkov_history import build_multiline_polydata


def apply_camera(
    pl: pv.Plotter,
    position: np.ndarray,
    focal: np.ndarray,
    view_up: np.ndarray,
    parallel_projection: bool,
) -> None:
    """Apply a 3D camera pose to a plotter."""
    pl.camera_position = [
        tuple(position),
        tuple(focal),
        tuple(view_up),
    ]
    if parallel_projection:
        pl.enable_parallel_projection()



def apply_unwrapped_camera(pl: pv.Plotter, radius: float, z_min: float, z_max: float) -> None:
    """Set a camera that looks straight onto the unwrap plane."""
    s_max = 2.0 * np.pi * radius
    center_s = 0.5 * s_max
    center_z = 0.5 * (z_min + z_max)
    distance = max(s_max, z_max - z_min, 1.0)
    pl.camera_position = [
        (center_s, center_z, 2.5 * distance),
        (center_s, center_z, 0.0),
        (0.0, 1.0, 0.0),
    ]
    pl.enable_parallel_projection()



def show_history_viewer(
    apex_points: np.ndarray,
    apex_frames: np.ndarray,
    intersection_points: np.ndarray,
    intersection_frames: np.ndarray,
    intersection_segments: np.ndarray,
    cluster_radius: float,
    z_min: float,
    z_max: float,
    om_points: np.ndarray,
    track_pts: np.ndarray,
    track_axis: np.ndarray,
    theta_c_rad: float,
    visual_cfg: dict,
    intersection_cfg: dict,
) -> None:
    """Open an interactive history viewer with frame controls."""
    old_allow_empty = pv.global_theme.allow_empty_mesh
    pv.global_theme.allow_empty_mesh = True
    show_unwrapped = visual_cfg["show_unwrapped_view"]
    plotter_kwargs = {"window_size": (visual_cfg["window_width"], visual_cfg["window_height"])}
    if show_unwrapped:
        plotter_kwargs["shape"] = (1, 2)
        plotter_kwargs["border"] = False
    pl = pv.Plotter(**plotter_kwargs)

    def use_3d() -> None:
        """Activate the 3D subplot when split view is enabled."""
        if show_unwrapped:
            pl.subplot(0, 0)

    def use_2d() -> None:
        """Activate the unwrapped subplot when split view is enabled."""
        if show_unwrapped:
            pl.subplot(0, 1)

    use_3d()
    cylinder = pv.Cylinder(
        center=(0.0, 0.0, 0.5 * (z_min + z_max)),
        direction=(0.0, 0.0, 1.0),
        radius=cluster_radius,
        height=(z_max - z_min),
        resolution=140,
        capping=False,
    )
    pl.add_mesh(
        cylinder,
        style="wireframe",
        line_width=visual_cfg["cylinder_line_width"],
        opacity=visual_cfg["cylinder_opacity"],
        color="white",
    )

    pl.add_mesh(
        pv.lines_from_points(track_pts, close=False),
        color="yellow",
        line_width=visual_cfg["track_line_width"],
    )

    if len(apex_points) == 0:
        pl.add_text("No saved history points", font_size=12)
        pl.show_axes()
        if show_unwrapped:
            use_2d()
            pl.add_mesh(make_unwrapped_outline(cluster_radius, z_min, z_max), color="black", line_width=2.0)
            pl.add_mesh(
                make_unwrapped_string_guides(om_points, cluster_radius, z_min, z_max),
                color="gray",
                line_width=1.0,
                opacity=0.18,
            )
            pl.add_mesh(
                pv.PolyData(unwrap_cylinder_points(om_points, cluster_radius)),
                color="midnightblue",
                point_size=visual_cfg["unwrap_om_point_size"],
                render_points_as_spheres=True,
                opacity=0.45,
            )
            pl.add_text("Cylinder unwrap (s = R*phi, z)", font_size=12, name="unwrap_title")
            apply_unwrapped_camera(pl, cluster_radius, z_min, z_max)
        try:
            pl.show()
        finally:
            pv.global_theme.allow_empty_mesh = old_allow_empty
        return

    if len(apex_points) >= 2:
        pl.add_mesh(pv.lines_from_points(apex_points, close=False), color="orange", line_width=2, opacity=0.25)

    unique_frames = np.unique(np.asarray(apex_frames, dtype=np.int32))
    if len(unique_frames) == 0:
        unique_frames = np.array([0], dtype=np.int32)

    inter_frames = np.asarray(intersection_frames, dtype=np.int32)
    inter_segments = np.asarray(intersection_segments, dtype=np.int32)
    inter_points = np.asarray(intersection_points, dtype=float)
    apex_frames_arr = np.asarray(apex_frames, dtype=np.int32)
    track_axis = normalize(np.asarray(track_axis, dtype=float))
    om_points = np.asarray(om_points, dtype=float)
    unwrap_om_points = unwrap_cylinder_points(om_points, cluster_radius)
    cone_height = visual_cfg["cone_height"]
    cone_radius = cone_height * np.tan(theta_c_rad)
    activation_distance = float(intersection_cfg["activation_distance"])

    first_frame = int(unique_frames[0])
    first_apex_idx = int(np.argmin(np.abs(apex_frames_arr - first_frame)))
    apex_actor = pl.add_mesh(
        pv.PolyData(apex_points[[first_apex_idx]]),
        color="orange",
        point_size=14,
        render_points_as_spheres=True,
    )

    first_apex = apex_points[first_apex_idx]
    first_cone = pv.Cone(
        center=first_apex - 0.5 * cone_height * track_axis,
        direction=track_axis,
        height=cone_height,
        radius=cone_radius,
        resolution=visual_cfg["cone_resolution"],
        capping=False,
    )
    cone_actor = pl.add_mesh(first_cone, color="deepskyblue", opacity=visual_cfg["cone_opacity"])

    frame_mask = inter_frames == first_frame
    first_inter_pts = inter_points[frame_mask]
    first_inter_seg = inter_segments[frame_mask]
    first_frame_polylines = segmented_points_to_polylines(
        first_inter_pts,
        first_inter_seg,
        min_points=max(2, int(intersection_cfg["min_points"])),
    )
    inter_line_actor = pl.add_mesh(
        build_multiline_polydata(first_inter_pts, first_inter_seg),
        color=intersection_cfg["curve_color"],
        line_width=intersection_cfg["curve_line_width"],
        render_lines_as_tubes=True,
        opacity=0.95,
    )
    inter_points_actor = pl.add_mesh(
        pv.PolyData(first_inter_pts),
        color=intersection_cfg["curve_color"],
        point_size=max(2.0, intersection_cfg["curve_line_width"] * 2.0),
        render_points_as_spheres=True,
        opacity=0.45,
    )

    unwrap_line_actor = None
    unwrap_points_actor = None
    unwrap_active_oms_actor = None
    if show_unwrapped:
        use_2d()
        pl.add_mesh(make_unwrapped_outline(cluster_radius, z_min, z_max), color="black", line_width=2.0)
        pl.add_mesh(
            make_unwrapped_string_guides(om_points, cluster_radius, z_min, z_max),
            color="gray",
            line_width=1.0,
            opacity=0.18,
        )
        pl.add_mesh(
            pv.PolyData(unwrap_om_points),
            color="midnightblue",
            point_size=visual_cfg["unwrap_om_point_size"],
            render_points_as_spheres=True,
            opacity=0.45,
        )
        first_active = nearest_distance_to_polylines(om_points, first_frame_polylines) < activation_distance
        unwrap_line_actor = pl.add_mesh(
            build_unwrapped_multiline_polydata(
                first_inter_pts,
                first_inter_seg,
                radius=cluster_radius,
                min_points=max(2, int(intersection_cfg["min_points"])),
            ),
            color=intersection_cfg["curve_color"],
            line_width=visual_cfg["unwrap_curve_line_width"],
            opacity=0.95,
        )
        unwrap_points_actor = pl.add_mesh(
            pv.PolyData(unwrap_cylinder_points(first_inter_pts, cluster_radius)),
            color=intersection_cfg["curve_color"],
            point_size=visual_cfg["unwrap_curve_point_size"],
            render_points_as_spheres=True,
            opacity=0.30,
        )
        unwrap_active_oms_actor = pl.add_mesh(
            pv.PolyData(unwrap_om_points[first_active]),
            color="crimson",
            point_size=visual_cfg["unwrap_active_om_point_size"],
            render_points_as_spheres=True,
            opacity=0.95,
        )
        pl.add_text("Cylinder unwrap (s = R*phi, z)", font_size=12, name="unwrap_title")
        apply_unwrapped_camera(pl, cluster_radius, z_min, z_max)

    state = {"frame_pos": 0}

    def _set_frame_by_pos(pos: int) -> None:
        """Update all actors to the selected saved frame."""
        pos = int(np.clip(pos, 0, len(unique_frames) - 1))
        state["frame_pos"] = pos
        frame = int(unique_frames[pos])

        apex_idx = int(np.argmin(np.abs(apex_frames_arr - frame)))
        apex_current = apex_points[apex_idx]
        apex_actor.mapper.dataset.copy_from(pv.PolyData(apex_points[[apex_idx]]))

        cone_actor.mapper.dataset.copy_from(
            pv.Cone(
                center=apex_current - 0.5 * cone_height * track_axis,
                direction=track_axis,
                height=cone_height,
                radius=cone_radius,
                resolution=visual_cfg["cone_resolution"],
                capping=False,
            )
        )

        frame_mask = inter_frames == frame
        inter_pts = inter_points[frame_mask]
        inter_seg = inter_segments[frame_mask]
        inter_line_actor.mapper.dataset.copy_from(build_multiline_polydata(inter_pts, inter_seg))
        inter_points_actor.mapper.dataset.copy_from(pv.PolyData(inter_pts))
        frame_polylines = segmented_points_to_polylines(
            inter_pts,
            inter_seg,
            min_points=max(2, int(intersection_cfg["min_points"])),
        )

        if show_unwrapped:
            unwrap_line_actor.mapper.dataset.copy_from(
                build_unwrapped_multiline_polydata(
                    inter_pts,
                    inter_seg,
                    radius=cluster_radius,
                    min_points=max(2, int(intersection_cfg["min_points"])),
                )
            )
            unwrap_points_actor.mapper.dataset.copy_from(
                pv.PolyData(unwrap_cylinder_points(inter_pts, cluster_radius))
            )
            active_mask = nearest_distance_to_polylines(om_points, frame_polylines) < activation_distance
            unwrap_active_oms_actor.mapper.dataset.copy_from(pv.PolyData(unwrap_om_points[active_mask]))

        use_3d()
        pl.add_text(
            f"History viewer: frame {frame} / {int(unique_frames[-1])} (j/k, a/d, <-/->)",
            font_size=12,
            name="history_label",
        )
        pl.render()

    def _slider_cb(value: float) -> None:
        """Map slider values to the nearest stored frame index."""
        target = int(round(value))
        pos = int(np.argmin(np.abs(unique_frames - target)))
        _set_frame_by_pos(pos)

    def _prev_frame() -> None:
        """Step to the previous saved frame."""
        _set_frame_by_pos(state["frame_pos"] - 1)

    def _next_frame() -> None:
        """Step to the next saved frame."""
        _set_frame_by_pos(state["frame_pos"] + 1)

    pl.add_slider_widget(
        callback=_slider_cb,
        rng=[int(unique_frames.min()), int(unique_frames.max())],
        value=float(first_frame),
        title="Frame",
        pointa=(0.2, 0.08),
        pointb=(0.8, 0.08),
    )
    pl.add_key_event("j", _prev_frame)
    pl.add_key_event("k", _next_frame)
    pl.add_key_event("a", _prev_frame)
    pl.add_key_event("d", _next_frame)
    pl.add_key_event("Left", _prev_frame)
    pl.add_key_event("Right", _next_frame)
    _set_frame_by_pos(0)

    use_3d()
    pl.show_axes()
    apply_camera(
        pl,
        visual_cfg["camera_position"],
        visual_cfg["camera_focal"],
        visual_cfg["camera_view_up"],
        visual_cfg["parallel_projection"],
    )
    if show_unwrapped:
        use_2d()
        apply_unwrapped_camera(pl, cluster_radius, z_min, z_max)
    try:
        pl.show()
    finally:
        pv.global_theme.allow_empty_mesh = old_allow_empty
