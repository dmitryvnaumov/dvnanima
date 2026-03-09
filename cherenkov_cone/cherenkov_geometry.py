import numpy as np
import pyvista as pv


def normalize(v: np.ndarray) -> np.ndarray:
    """Return a normalized copy of a 3D vector."""
    n = np.linalg.norm(v)
    if n == 0:
        raise ValueError("Zero-length vector cannot be normalized.")
    return v / n


def make_track_points(r0: np.ndarray, u: np.ndarray, s_min: float, s_max: float, n: int = 200) -> np.ndarray:
    """Sample evenly spaced points along the muon track."""
    s = np.linspace(s_min, s_max, n)
    return r0[None, :] + s[:, None] * u[None, :]


def _nappe_mask(proj: np.ndarray, nappe: str, max_proj: float | None = None) -> np.ndarray:
    """Select the requested cone nappe and optional axial cutoff."""
    if nappe == "trailing":
        mask = proj < 0.0
    elif nappe == "leading":
        mask = proj > 0.0
    elif nappe == "both":
        mask = np.ones_like(proj, dtype=bool)
    else:
        raise ValueError("intersection.nappe must be 'trailing', 'leading', or 'both'")

    if max_proj is not None and max_proj > 0.0:
        mask &= np.abs(proj) <= max_proj
    return mask


def _branches_from_masked_curve(points: np.ndarray, mask: np.ndarray, min_points: int = 5) -> list[pv.PolyData]:
    """Split a sampled periodic curve into contiguous valid branches."""
    idx = np.flatnonzero(mask)
    if len(idx) == 0:
        return []

    split_idx = np.where(np.diff(idx) > 1)[0] + 1
    chunks = np.split(idx, split_idx)

    if len(chunks) > 1 and chunks[0][0] == 0 and chunks[-1][-1] == len(mask) - 1:
        merged = np.concatenate([chunks[-1], chunks[0]])
        chunks = [merged] + chunks[1:-1]

    polylines = []
    for chunk in chunks:
        if len(chunk) < min_points:
            continue
        polylines.append(pv.lines_from_points(points[chunk], close=False))
    return polylines


def analytic_intersection_curve_on_cylinder(
    radius: float,
    z_min: float,
    z_max: float,
    apex: np.ndarray,
    axis: np.ndarray,
    theta_c_rad: float,
    n_phi: int = 720,
    nappe: str = "trailing",
    min_points: int = 5,
    eps: float = 1e-12,
    max_proj: float | None = None,
) -> list[pv.PolyData]:
    """Compute the exact cone-cylinder intersection on the side surface."""
    axis = normalize(np.asarray(axis, dtype=float))
    apex = np.asarray(apex, dtype=float)

    ux, uy, uz = axis
    ax, ay, az = apex
    c2 = np.cos(theta_c_rad) ** 2

    phi = np.linspace(0.0, 2.0 * np.pi, n_phi, endpoint=False)
    cp = np.cos(phi)
    sp = np.sin(phi)

    x = radius * cp
    y = radius * sp

    beta = ux * (x - ax) + uy * (y - ay)
    rho2 = (x - ax) ** 2 + (y - ay) ** 2

    A = uz**2 - c2
    B = 2.0 * beta * uz
    C = beta**2 - c2 * rho2

    branches: list[pv.PolyData] = []

    if abs(A) < eps:
        valid = np.abs(B) > eps
        w = np.full_like(phi, np.nan, dtype=float)
        w[valid] = -C[valid] / B[valid]
        z = az + w
        pts = np.column_stack([x, y, z])

        mask = valid & np.isfinite(z) & (z >= z_min) & (z <= z_max)
        d = pts - apex[None, :]
        proj = d @ axis
        mask &= _nappe_mask(proj, nappe=nappe, max_proj=max_proj)
        return _branches_from_masked_curve(pts, mask, min_points=min_points)

    D = B**2 - 4.0 * A * C
    D = np.where(D < -eps, np.nan, np.clip(D, 0.0, None))
    sqrtD = np.sqrt(D)

    for sign in (+1.0, -1.0):
        w = (-B + sign * sqrtD) / (2.0 * A)
        z = az + w
        pts = np.column_stack([x, y, z])

        mask = np.isfinite(z) & (z >= z_min) & (z <= z_max)
        d = pts - apex[None, :]
        proj = d @ axis
        mask &= _nappe_mask(proj, nappe=nappe, max_proj=max_proj)
        branches.extend(_branches_from_masked_curve(pts, mask, min_points=min_points))

    return branches


def verify_intersection(
    polylines: list[pv.PolyData],
    apex: np.ndarray,
    axis: np.ndarray,
    theta_c_rad: float,
    radius: float,
) -> tuple[float, float, int]:
    """Return residuals for the cylinder and cone constraints."""
    axis = normalize(np.asarray(axis, dtype=float))
    apex = np.asarray(apex, dtype=float)
    c2 = np.cos(theta_c_rad) ** 2

    max_cyl_err = 0.0
    max_cone_err = 0.0
    n_pts = 0

    for poly in polylines:
        pts = np.asarray(poly.points)
        if len(pts) == 0:
            continue

        n_pts += len(pts)
        cyl_err = np.max(np.abs(pts[:, 0] ** 2 + pts[:, 1] ** 2 - radius**2))

        d = pts - apex[None, :]
        lhs = (d @ axis) ** 2
        rhs = np.sum(d * d, axis=1) * c2
        cone_err = np.max(np.abs(lhs - rhs))

        max_cyl_err = max(max_cyl_err, float(cyl_err))
        max_cone_err = max(max_cone_err, float(cone_err))

    return max_cyl_err, max_cone_err, n_pts


def make_oms_on_cylinder(radius: float, z_min: float, z_max: float,
                         n_strings: int = 8, oms_per_string: int = 18) -> np.ndarray:
    """Place optical modules on evenly spaced vertical strings."""
    phis = np.linspace(0.0, 2.0 * np.pi, n_strings, endpoint=False)
    zs = np.linspace(z_min + 0.08 * (z_max - z_min), z_max - 0.08 * (z_max - z_min), oms_per_string)

    pts = []
    for ph in phis:
        x = radius * np.cos(ph)
        y = radius * np.sin(ph)
        for z in zs:
            pts.append([x, y, z])
    return np.asarray(pts, dtype=float)


def unwrap_cylinder_points(points: np.ndarray, radius: float) -> np.ndarray:
    """Map cylinder surface points to unwrapped ``(s, z)`` coordinates."""
    pts = np.asarray(points, dtype=float)
    if len(pts) == 0:
        return np.empty((0, 3), dtype=float)

    phi = np.mod(np.arctan2(pts[:, 1], pts[:, 0]), 2.0 * np.pi)
    s = radius * phi
    return np.column_stack([s, pts[:, 2], np.zeros(len(pts), dtype=float)])


def _ordered_segment_point_chunks(
    points: np.ndarray,
    segment_ids: np.ndarray,
    min_points: int = 2,
) -> list[np.ndarray]:
    """Group points by segment id while preserving segment order."""
    if len(points) == 0:
        return []

    pts = np.asarray(points, dtype=float)
    seg = np.asarray(segment_ids, dtype=np.int32)
    ordered_segments = list(dict.fromkeys(seg.tolist()))

    chunks: list[np.ndarray] = []
    for segment_id in ordered_segments:
        seg_pts = pts[seg == segment_id]
        if len(seg_pts) >= min_points:
            chunks.append(seg_pts)
    return chunks


def segmented_points_to_polylines(
    points: np.ndarray,
    segment_ids: np.ndarray,
    min_points: int = 2,
) -> list[pv.PolyData]:
    """Convert segmented point arrays back to individual polylines."""
    polylines: list[pv.PolyData] = []
    for seg_pts in _ordered_segment_point_chunks(points, segment_ids, min_points=min_points):
        polylines.append(pv.lines_from_points(seg_pts, close=False))
    return polylines


def polylines_to_segmented_points(polylines: list[pv.PolyData]) -> tuple[np.ndarray, np.ndarray]:
    """Flatten polyline branches into points plus segment ids."""
    point_chunks: list[np.ndarray] = []
    segment_chunks: list[np.ndarray] = []

    for segment_id, poly in enumerate(polylines):
        pts = np.asarray(poly.points, dtype=float)
        if len(pts) == 0:
            continue
        point_chunks.append(pts)
        segment_chunks.append(np.full(len(pts), segment_id, dtype=np.int32))

    if not point_chunks:
        return np.empty((0, 3), dtype=float), np.empty((0,), dtype=np.int32)

    return np.vstack(point_chunks), np.concatenate(segment_chunks)


def build_unwrapped_multiline_polydata(
    points: np.ndarray,
    segment_ids: np.ndarray,
    radius: float,
    min_points: int = 2,
) -> pv.PolyData:
    """Build an unwrapped multiline dataset and split across the seam."""
    period = 2.0 * np.pi * radius
    point_chunks: list[np.ndarray] = []
    line_chunks: list[np.ndarray] = []
    offset = 0

    for seg_pts in _ordered_segment_point_chunks(points, segment_ids, min_points=min_points):
        unwrap_pts = unwrap_cylinder_points(seg_pts, radius)
        if len(unwrap_pts) < min_points:
            continue

        jump_idx = np.where(np.abs(np.diff(unwrap_pts[:, 0])) > 0.5 * period)[0]
        idx_chunks = np.split(np.arange(len(unwrap_pts), dtype=np.int32), jump_idx + 1)

        for idx_chunk in idx_chunks:
            if len(idx_chunk) < min_points:
                continue
            chunk = unwrap_pts[idx_chunk]
            point_chunks.append(chunk)
            line = np.hstack([[len(chunk)], np.arange(offset, offset + len(chunk), dtype=np.int32)])
            line_chunks.append(line)
            offset += len(chunk)

    if not point_chunks:
        return pv.PolyData(np.empty((0, 3), dtype=float))

    poly = pv.PolyData(np.vstack(point_chunks))
    poly.lines = np.hstack(line_chunks).astype(np.int32)
    return poly


def make_unwrapped_outline(radius: float, z_min: float, z_max: float) -> pv.PolyData:
    """Create a rectangular outline for the cylinder unwrap view."""
    s_max = 2.0 * np.pi * radius
    pts = np.asarray(
        [
            [0.0, z_min, 0.0],
            [s_max, z_min, 0.0],
            [s_max, z_max, 0.0],
            [0.0, z_max, 0.0],
            [0.0, z_min, 0.0],
        ],
        dtype=float,
    )
    return pv.lines_from_points(pts, close=False)


def make_unwrapped_string_guides(om_points: np.ndarray, radius: float, z_min: float, z_max: float) -> pv.PolyData:
    """Create vertical guide lines for OM strings in the unwrap view."""
    unwrap_pts = unwrap_cylinder_points(om_points, radius)
    if len(unwrap_pts) == 0:
        return pv.PolyData(np.empty((0, 3), dtype=float))

    s_values = np.unique(np.round(unwrap_pts[:, 0], decimals=6))
    point_chunks: list[np.ndarray] = []
    line_chunks: list[np.ndarray] = []
    offset = 0

    for s in s_values:
        pts = np.asarray([[s, z_min, 0.0], [s, z_max, 0.0]], dtype=float)
        point_chunks.append(pts)
        line = np.hstack([[2], np.arange(offset, offset + 2, dtype=np.int32)])
        line_chunks.append(line)
        offset += 2

    poly = pv.PolyData(np.vstack(point_chunks))
    poly.lines = np.hstack(line_chunks).astype(np.int32)
    return poly


def nearest_distance_to_polylines(points: np.ndarray, polylines: list[pv.PolyData]) -> np.ndarray:
    """Approximate point-to-curve distance using polyline vertices."""
    if not polylines:
        return np.full(len(points), np.inf)

    curve_pts = np.vstack([np.asarray(poly.points) for poly in polylines if poly.n_points > 0])
    if len(curve_pts) == 0:
        return np.full(len(points), np.inf)

    d2 = ((points[:, None, :] - curve_pts[None, :, :]) ** 2).sum(axis=2)
    return np.sqrt(np.min(d2, axis=1))
