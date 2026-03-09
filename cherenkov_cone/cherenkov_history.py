from pathlib import Path

import numpy as np
import pyvista as pv


def save_history_npz(
    npz_path: str | Path,
    apex_points: np.ndarray,
    apex_frames: np.ndarray,
    intersection_points: np.ndarray,
    intersection_frames: np.ndarray,
    intersection_segments: np.ndarray,
    r0: np.ndarray,
    u: np.ndarray,
    theta_c_rad: float,
    radius: float,
    z_min: float,
    z_max: float,
) -> None:
    """Save sampled history arrays to an ``.npz`` bundle."""
    path = Path(npz_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        path,
        apex_points=apex_points,
        apex_frames=apex_frames,
        intersection_points=intersection_points,
        intersection_frames=intersection_frames,
        intersection_segments=intersection_segments,
        track_r0=np.asarray(r0, dtype=float),
        track_u=np.asarray(u, dtype=float),
        theta_c_rad=float(theta_c_rad),
        cylinder_radius=float(radius),
        z_min=float(z_min),
        z_max=float(z_max),
    )



def save_history_vtm(
    vtm_path: str | Path,
    apex_points: np.ndarray,
    apex_frames: np.ndarray,
    intersection_points: np.ndarray,
    intersection_frames: np.ndarray,
    intersection_segments: np.ndarray,
) -> None:
    """Save sampled history geometry to a ``.vtm`` scene."""
    path = Path(vtm_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if len(apex_points) >= 2:
        apex_poly = pv.lines_from_points(apex_points, close=False)
    else:
        apex_poly = pv.PolyData(apex_points)
    if len(apex_points) > 0:
        apex_poly["sample_idx"] = np.arange(len(apex_points), dtype=np.int32)
        apex_poly["frame_idx"] = np.asarray(apex_frames, dtype=np.int32)

    inter_poly = pv.PolyData(intersection_points)
    if len(intersection_points) > 0:
        inter_poly["frame_idx"] = np.asarray(intersection_frames, dtype=np.int32)
        inter_poly["segment_id"] = np.asarray(intersection_segments, dtype=np.int32)

    scene_blocks = pv.MultiBlock({"apex_path": apex_poly, "intersection_points": inter_poly})
    scene_blocks.save(path)



def build_multiline_polydata(points: np.ndarray, segment_ids: np.ndarray) -> pv.PolyData:
    """Build a multi-segment polyline dataset from point chunks."""
    if len(points) == 0:
        return pv.PolyData(np.empty((0, 3), dtype=float))

    points = np.asarray(points, dtype=float)
    segment_ids = np.asarray(segment_ids, dtype=np.int32)
    ordered_segments = list(dict.fromkeys(segment_ids.tolist()))
    point_chunks = []
    line_chunks = []
    offset = 0

    for seg in ordered_segments:
        seg_pts = points[segment_ids == seg]
        if len(seg_pts) < 2:
            continue
        point_chunks.append(seg_pts)
        line = np.hstack([[len(seg_pts)], np.arange(offset, offset + len(seg_pts), dtype=np.int32)])
        line_chunks.append(line)
        offset += len(seg_pts)

    if not point_chunks:
        return pv.PolyData(points)

    out_points = np.vstack(point_chunks)
    out_lines = np.hstack(line_chunks).astype(np.int32)
    poly = pv.PolyData(out_points)
    poly.lines = out_lines
    return poly
