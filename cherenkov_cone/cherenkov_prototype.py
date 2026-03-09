from pathlib import Path

import numpy as np
import pyvista as pv

try:
    from .cherenkov_config import load_cfg
    from .cherenkov_geometry import (
        analytic_intersection_curve_on_cylinder,
        build_unwrapped_multiline_polydata,
        make_oms_on_cylinder,
        make_track_points,
        make_unwrapped_outline,
        make_unwrapped_string_guides,
        nearest_distance_to_polylines,
        normalize,
        polylines_to_segmented_points,
        unwrap_cylinder_points,
        verify_intersection,
    )
    from .cherenkov_history import save_history_npz, save_history_vtm
    from .cherenkov_viewer import apply_camera, apply_unwrapped_camera, show_history_viewer
except ImportError:
    from cherenkov_config import load_cfg
    from cherenkov_geometry import (
        analytic_intersection_curve_on_cylinder,
        build_unwrapped_multiline_polydata,
        make_oms_on_cylinder,
        make_track_points,
        make_unwrapped_outline,
        make_unwrapped_string_guides,
        nearest_distance_to_polylines,
        normalize,
        polylines_to_segmented_points,
        unwrap_cylinder_points,
        verify_intersection,
    )
    from cherenkov_history import save_history_npz, save_history_vtm
    from cherenkov_viewer import apply_camera, apply_unwrapped_camera, show_history_viewer


# ============================================================
# Main prototype
# ============================================================

def run_prototype(
    save_movie: bool | None = None,
    movie_path: str | None = None,
    n_frames: int | None = None,
    show_progress: bool | None = None,
    cfg_path: str | Path | None = None,
):
    """Run the Cherenkov cone prototype from config and overrides."""
    cfg = load_cfg(cfg_path)
    run_cfg = cfg["run"]
    detector_cfg = cfg["detector"]
    optics_cfg = cfg["optics"]
    track_cfg = cfg["track"]
    intersection_cfg = cfg["intersection"]
    visual_cfg = cfg["visual"]

    if save_movie is not None:
        run_cfg["save_movie"] = save_movie
    if movie_path is not None:
        run_cfg["movie_path"] = movie_path
    if n_frames is not None:
        run_cfg["n_frames"] = n_frames
    if show_progress is not None:
        run_cfg["show_progress"] = show_progress

    save_movie = run_cfg["save_movie"]
    movie_path = run_cfg["movie_path"]
    n_frames = max(1, int(run_cfg["n_frames"]))
    show_progress = run_cfg["show_progress"]
    history_stride = max(1, int(run_cfg["history_stride"]))
    save_history_npz_enabled = run_cfg["save_history_npz"]
    history_npz_path = run_cfg["history_npz_path"]
    save_history_vtm_enabled = run_cfg["save_history_vtm"]
    history_vtm_path = run_cfg["history_vtm_path"]
    show_history_viewer_enabled = run_cfg["show_history_viewer"]
    verify_every = max(1, int(intersection_cfg["verify_every"]))
    verify_atol = float(intersection_cfg["verify_atol"])

    cluster_radius = detector_cfg["cluster_radius"]
    z_min = detector_cfg["z_min"]
    z_max = detector_cfg["z_max"]
    cylinder_height = z_max - z_min

    n_refr = optics_cfg["n_refr"]
    beta = optics_cfg["beta"]
    if beta * n_refr <= 1.0:
        raise ValueError("Cherenkov angle is undefined: beta * n_refr must be > 1.")
    theta_c = np.arccos(1.0 / (beta * n_refr))

    r0 = np.asarray(track_cfg["r0"], dtype=float)
    u = normalize(np.asarray(track_cfg["u"], dtype=float))
    s_values = np.linspace(track_cfg["s_start"], track_cfg["s_end"], n_frames)

    om_points = make_oms_on_cylinder(
        radius=cluster_radius,
        z_min=z_min,
        z_max=z_max,
        n_strings=detector_cfg["n_strings"],
        oms_per_string=detector_cfg["oms_per_string"],
    )

    pv.set_plot_theme(visual_cfg["plot_theme"])
    show_unwrapped = visual_cfg["show_unwrapped_view"]
    plotter_kwargs = {
        "window_size": (visual_cfg["window_width"], visual_cfg["window_height"]),
        "off_screen": save_movie,
    }
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
        height=cylinder_height,
        resolution=detector_cfg["cylinder_resolution"],
        capping=False,
    )
    pl.add_mesh(
        cylinder,
        style="wireframe",
        line_width=visual_cfg["cylinder_line_width"],
        opacity=visual_cfg["cylinder_opacity"],
        color="white",
    )

    track_pts = make_track_points(
        r0,
        u,
        s_min=track_cfg["draw_s_min"],
        s_max=track_cfg["draw_s_max"],
        n=track_cfg["draw_points"],
    )
    track_poly = pv.lines_from_points(track_pts)
    pl.add_mesh(track_poly, color="yellow", line_width=visual_cfg["track_line_width"])

    oms_poly = pv.PolyData(om_points)
    oms_poly["active"] = np.zeros(len(om_points), dtype=float)
    om_actor = pl.add_mesh(
        oms_poly,
        render_points_as_spheres=True,
        point_size=visual_cfg["om_point_size"],
        scalars="active",
        clim=[0.0, 1.0],
        cmap="coolwarm",
        show_scalar_bar=False,
    )

    apex_actor = pl.add_mesh(pv.Sphere(radius=visual_cfg["apex_radius"], center=r0), color="orange", smooth_shading=True)

    cone_height = visual_cfg["cone_height"]
    cone_radius = cone_height * np.tan(theta_c)
    cone_mesh = pv.Cone(
        center=r0 - 0.5 * cone_height * u,
        direction=u,
        height=cone_height,
        radius=cone_radius,
        resolution=visual_cfg["cone_resolution"],
        capping=False,
    )
    cone_actor = pl.add_mesh(cone_mesh, color="deepskyblue", opacity=visual_cfg["cone_opacity"])

    curve_actors = []
    unwrap_line_actor = None
    unwrap_points_actor = None
    unwrap_active_oms_actor = None

    if show_unwrapped:
        unwrap_om_points = unwrap_cylinder_points(om_points, cluster_radius)
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
        pl.add_text("Cylinder unwrap (s = R*phi, z)", font_size=12, name="unwrap_title")

    use_3d()
    pl.add_text(visual_cfg["title_text"], font_size=12)
    pl.show_axes()
    if save_movie:
        camera_position = visual_cfg["movie_camera_position"]
        camera_focal = visual_cfg["movie_camera_focal"]
        camera_view_up = visual_cfg["movie_camera_view_up"]
        parallel_projection = visual_cfg["movie_parallel_projection"]
    else:
        camera_position = visual_cfg["camera_position"]
        camera_focal = visual_cfg["camera_focal"]
        camera_view_up = visual_cfg["camera_view_up"]
        parallel_projection = visual_cfg["parallel_projection"]

    apply_camera(pl, camera_position, camera_focal, camera_view_up, parallel_projection)
    if show_unwrapped:
        use_2d()
        apply_unwrapped_camera(pl, cluster_radius, z_min, z_max)
        use_3d()

    movie_writer = None
    if save_movie:
        import imageio.v2 as iio

        writer_kwargs = {
            "fps": run_cfg["movie_fps"],
            "codec": run_cfg["movie_codec"],
            "is_batch": run_cfg["movie_is_batch"],
        }
        if run_cfg["movie_format"]:
            writer_kwargs["format"] = run_cfg["movie_format"]
        movie_writer = iio.get_writer(movie_path, **writer_kwargs)
        pl.show(auto_close=False)
    else:
        pl.show(auto_close=False, interactive_update=True)

    activation_distance = intersection_cfg["activation_distance"]
    max_proj: float | None = None
    if intersection_cfg["clip_to_visual_cone"]:
        max_proj = float(cone_height)
    user_max_proj = float(intersection_cfg["max_forward_distance"])
    if user_max_proj > 0.0:
        max_proj = user_max_proj if max_proj is None else min(max_proj, user_max_proj)

    apex_history: list[np.ndarray] = []
    apex_history_frames: list[int] = []
    intersection_history_pts: list[np.ndarray] = []
    intersection_history_frames: list[np.ndarray] = []
    intersection_history_segments: list[np.ndarray] = []
    segment_counter = 0
    progress_every = max(1, len(s_values) // 10)

    try:
        for frame_idx, s in enumerate(s_values, start=1):
            apex = r0 + s * u
            apex_actor.mapper.dataset.copy_from(pv.Sphere(radius=visual_cfg["apex_radius"], center=apex))
            cone_actor.mapper.dataset.copy_from(
                pv.Cone(
                    center=apex - 0.5 * cone_height * u,
                    direction=u,
                    height=cone_height,
                    radius=cone_radius,
                    resolution=visual_cfg["cone_resolution"],
                    capping=False,
                )
            )

            use_3d()
            for actor in curve_actors:
                pl.remove_actor(actor)
            curve_actors = []
            if show_unwrapped:
                use_2d()
                if unwrap_line_actor is not None:
                    pl.remove_actor(unwrap_line_actor)
                    unwrap_line_actor = None
                if unwrap_points_actor is not None:
                    pl.remove_actor(unwrap_points_actor)
                    unwrap_points_actor = None
                if unwrap_active_oms_actor is not None:
                    pl.remove_actor(unwrap_active_oms_actor)
                    unwrap_active_oms_actor = None

            apex_inside_detector = (
                (apex[0] ** 2 + apex[1] ** 2) <= cluster_radius**2
                and (z_min <= apex[2] <= z_max)
            )
            if intersection_cfg["apex_inside_only"] and not apex_inside_detector:
                polylines = []
            else:
                polylines = analytic_intersection_curve_on_cylinder(
                    radius=cluster_radius,
                    z_min=z_min,
                    z_max=z_max,
                    apex=apex,
                    axis=u,
                    theta_c_rad=theta_c,
                    n_phi=detector_cfg["cyl_sample_phi"],
                    nappe=intersection_cfg["nappe"],
                    min_points=intersection_cfg["min_points"],
                    eps=intersection_cfg["analytic_eps"],
                    max_proj=max_proj,
                )

            use_3d()
            for poly in polylines:
                curve_actors.append(
                    pl.add_mesh(
                        poly,
                        color=intersection_cfg["curve_color"],
                        line_width=intersection_cfg["curve_line_width"],
                        render_lines_as_tubes=True,
                    )
                )

            active = (nearest_distance_to_polylines(om_points, polylines) < activation_distance).astype(float)
            oms_poly["active"] = active
            om_actor.mapper.dataset["active"] = active

            if show_unwrapped:
                inter_pts_frame, inter_seg_frame = polylines_to_segmented_points(polylines)
                use_2d()
                unwrap_line_poly = build_unwrapped_multiline_polydata(
                    inter_pts_frame,
                    inter_seg_frame,
                    radius=cluster_radius,
                    min_points=max(2, int(intersection_cfg["min_points"])),
                )
                if unwrap_line_poly.n_points > 0:
                    unwrap_line_actor = pl.add_mesh(
                        unwrap_line_poly,
                        color=intersection_cfg["curve_color"],
                        line_width=visual_cfg["unwrap_curve_line_width"],
                        opacity=0.95,
                    )
                unwrap_pts_frame = unwrap_cylinder_points(inter_pts_frame, cluster_radius)
                if len(unwrap_pts_frame) > 0:
                    unwrap_points_actor = pl.add_mesh(
                        pv.PolyData(unwrap_pts_frame),
                        color=intersection_cfg["curve_color"],
                        point_size=visual_cfg["unwrap_curve_point_size"],
                        render_points_as_spheres=True,
                        opacity=0.30,
                    )
                active_mask = active > 0.0
                if np.any(active_mask):
                    unwrap_active_oms_actor = pl.add_mesh(
                        pv.PolyData(unwrap_om_points[active_mask]),
                        color="crimson",
                        point_size=visual_cfg["unwrap_active_om_point_size"],
                        render_points_as_spheres=True,
                        opacity=0.95,
                    )

            if ((frame_idx - 1) % history_stride == 0) or frame_idx == len(s_values):
                apex_history.append(apex.copy())
                apex_history_frames.append(frame_idx)
                for poly in polylines:
                    pts = np.asarray(poly.points)
                    if len(pts) == 0:
                        continue
                    intersection_history_pts.append(pts.copy())
                    intersection_history_frames.append(np.full(len(pts), frame_idx, dtype=np.int32))
                    intersection_history_segments.append(np.full(len(pts), segment_counter, dtype=np.int32))
                    segment_counter += 1

            if (
                intersection_cfg["verify_geometry"]
                and (frame_idx == 1 or frame_idx % verify_every == 0 or frame_idx == len(s_values))
            ):
                cyl_err, cone_err, n_verify_pts = verify_intersection(
                    polylines=polylines,
                    apex=apex,
                    axis=u,
                    theta_c_rad=theta_c,
                    radius=cluster_radius,
                )
                if n_verify_pts > 0:
                    status = "OK" if max(cyl_err, cone_err) <= verify_atol else "WARN"
                    print(
                        f"[check:{status}] pts={n_verify_pts} cyl_err={cyl_err:.3e} cone_err={cone_err:.3e} atol={verify_atol:.1e}",
                        flush=True,
                    )

            use_3d()
            if save_movie:
                pl.render()
                movie_writer.append_data(pl.image)
            else:
                pl.render()
                pl.update()

            if show_progress and (frame_idx == 1 or frame_idx % progress_every == 0 or frame_idx == len(s_values)):
                print(f"[cherenkov] frame {frame_idx}/{len(s_values)}", flush=True)
    finally:
        if save_movie and movie_writer is not None:
            movie_writer.close()

    apex_points = np.asarray(apex_history, dtype=float) if apex_history else np.empty((0, 3), dtype=float)
    apex_frames = np.asarray(apex_history_frames, dtype=np.int32) if apex_history_frames else np.empty((0,), dtype=np.int32)
    if intersection_history_pts:
        intersection_points = np.vstack(intersection_history_pts)
        intersection_frames = np.concatenate(intersection_history_frames).astype(np.int32, copy=False)
        intersection_segments = np.concatenate(intersection_history_segments).astype(np.int32, copy=False)
    else:
        intersection_points = np.empty((0, 3), dtype=float)
        intersection_frames = np.empty((0,), dtype=np.int32)
        intersection_segments = np.empty((0,), dtype=np.int32)

    if save_history_npz_enabled:
        save_history_npz(
            npz_path=history_npz_path,
            apex_points=apex_points,
            apex_frames=apex_frames,
            intersection_points=intersection_points,
            intersection_frames=intersection_frames,
            intersection_segments=intersection_segments,
            r0=r0,
            u=u,
            theta_c_rad=theta_c,
            radius=cluster_radius,
            z_min=z_min,
            z_max=z_max,
        )
        if show_progress:
            print(f"[history] wrote npz: {history_npz_path}", flush=True)

    if save_history_vtm_enabled:
        save_history_vtm(
            vtm_path=history_vtm_path,
            apex_points=apex_points,
            apex_frames=apex_frames,
            intersection_points=intersection_points,
            intersection_frames=intersection_frames,
            intersection_segments=intersection_segments,
        )
        if show_progress:
            print(f"[history] wrote vtm: {history_vtm_path}", flush=True)

    if save_movie:
        pl.close()
        if show_history_viewer_enabled:
            show_history_viewer(
                apex_points=apex_points,
                apex_frames=apex_frames,
                intersection_points=intersection_points,
                intersection_frames=intersection_frames,
                intersection_segments=intersection_segments,
                cluster_radius=cluster_radius,
                z_min=z_min,
                z_max=z_max,
                om_points=om_points,
                track_pts=track_pts,
                track_axis=u,
                theta_c_rad=theta_c,
                visual_cfg=visual_cfg,
                intersection_cfg=intersection_cfg,
            )
        return

    if show_history_viewer_enabled:
        pl.close()
        show_history_viewer(
            apex_points=apex_points,
            apex_frames=apex_frames,
            intersection_points=intersection_points,
            intersection_frames=intersection_frames,
            intersection_segments=intersection_segments,
            cluster_radius=cluster_radius,
            z_min=z_min,
            z_max=z_max,
            om_points=om_points,
            track_pts=track_pts,
            track_axis=u,
            theta_c_rad=theta_c,
            visual_cfg=visual_cfg,
            intersection_cfg=intersection_cfg,
        )
        return

    pl.show()


if __name__ == "__main__":
    run_prototype()
