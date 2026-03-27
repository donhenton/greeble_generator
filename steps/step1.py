"""
steps/step1.py
Box placement via attractor / repeller field.

INPUT:  obj, bm, face, rng, min_box_size
OUTPUT: box_regions    — list of dicts describing each placed box
        negative_space — dict describing remaining face area for Step 4
"""

import mathutils
import math

# ---------------------------------------------------------------------------
# TUNING CONSTANTS
# ---------------------------------------------------------------------------

ATTRACTOR_COUNT    = 4      # attractors scattered across face per panel
ATTRACTOR_STRENGTH = 1.0    # pull strength (inverse-square scale)
REPELLER_STRENGTH  = 0.8    # push strength between box centres
ITERATIONS         = 80     # max simulation steps
CONVERGENCE_DELTA  = 0.001  # stop early if max movement drops below this
STEP_SIZE          = 0.05   # movement scale per iteration

BOX_SIZE_MIN_FRAC  = 0.10   # box size as fraction of face short edge (min)
BOX_SIZE_MAX_FRAC  = 0.28   # box size as fraction of face short edge (max)

# Face area (Blender units²) → target box count
AREA_BOX_COUNT = [
    (0.0,  2),
    (1.0,  3),
    (2.5,  4),
    (4.5,  5),
]


# ---------------------------------------------------------------------------
# COORDINATE SYSTEM
# ---------------------------------------------------------------------------

def build_face_basis(face):
    """
    Build a local 2D coordinate system for the face.
    Returns (origin, u_axis, v_axis, normal).
    origin  — first vertex position
    u_axis  — along first edge, normalised
    v_axis  — perpendicular to u_axis in the face plane
    normal  — face normal
    """
    verts  = [v.co.copy() for v in face.verts]
    origin = verts[0]
    u_axis = (verts[1] - verts[0]).normalized()
    normal = face.normal.copy()
    v_axis = normal.cross(u_axis).normalized()
    return origin, u_axis, v_axis, normal


def world_to_uv(pt, origin, u_axis, v_axis):
    delta = pt - origin
    return (delta.dot(u_axis), delta.dot(v_axis))


def uv_to_world(u, v, origin, u_axis, v_axis):
    return origin + u_axis * u + v_axis * v


def face_uv_bounds(face, origin, u_axis, v_axis):
    """
    Returns (u_min, u_max, v_min, v_max) — bounding box of face in UV space.
    """
    uvs = [world_to_uv(v.co, origin, u_axis, v_axis) for v in face.verts]
    us  = [p[0] for p in uvs]
    vs  = [p[1] for p in uvs]
    return min(us), max(us), min(vs), max(vs)


# ---------------------------------------------------------------------------
# BOX COUNT
# ---------------------------------------------------------------------------

def target_box_count(face_area):
    count = 2
    for threshold, n in AREA_BOX_COUNT:
        if face_area >= threshold:
            count = n
    return count


# ---------------------------------------------------------------------------
# ATTRACTOR / REPELLER SIMULATION
# ---------------------------------------------------------------------------

def scatter_attractors(rng, u_min, u_max, v_min, v_max, n):
    return [
        (rng.uniform(u_min, u_max), rng.uniform(v_min, v_max))
        for _ in range(n)
    ]


def attractor_force(pos, attractors, strength):
    fu, fv = 0.0, 0.0
    for ax, ay in attractors:
        du     = ax - pos[0]
        dv     = ay - pos[1]
        dist_sq = du * du + dv * dv + 1e-6
        scale  = strength / dist_sq
        fu    += du * scale
        fv    += dv * scale
    return fu, fv


def repeller_force(idx, positions, strength):
    fu, fv = 0.0, 0.0
    pu, pv = positions[idx]
    for j, (qu, qv) in enumerate(positions):
        if j == idx:
            continue
        du     = pu - qu
        dv     = pv - qv
        dist_sq = du * du + dv * dv + 1e-6
        scale  = strength / dist_sq
        fu    += du * scale
        fv    += dv * scale
    return fu, fv


def clamp(val, lo, hi):
    return max(lo, min(hi, val))


def simulate(positions, attractors, u_min, u_max, v_min, v_max):
    for iteration in range(ITERATIONS):
        max_move     = 0.0
        new_positions = []
        for i, pos in enumerate(positions):
            fa  = attractor_force(pos, attractors, ATTRACTOR_STRENGTH)
            fr  = repeller_force(i, positions, REPELLER_STRENGTH)
            nu  = clamp(pos[0] + (fa[0] + fr[0]) * STEP_SIZE, u_min, u_max)
            nv  = clamp(pos[1] + (fa[1] + fr[1]) * STEP_SIZE, v_min, v_max)
            move = math.sqrt((nu - pos[0]) ** 2 + (nv - pos[1]) ** 2)
            max_move = max(max_move, move)
            new_positions.append((nu, nv))
        positions[:] = new_positions
        if max_move < CONVERGENCE_DELTA:
            print(f"    [Step1] Converged at iteration {iteration + 1}")
            break
    return positions


# ---------------------------------------------------------------------------
# BOX SIZING
# ---------------------------------------------------------------------------

def assign_sizes(positions, rng, short_edge, min_box_size):
    lo = short_edge * BOX_SIZE_MIN_FRAC
    hi = short_edge * BOX_SIZE_MAX_FRAC
    boxes = []
    for pos in positions:
        size = max(rng.uniform(lo, hi), min_box_size)
        boxes.append({'uv_center': pos, 'uv_size': size})
    return boxes


# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------

def run_step1(obj, bm, face, rng, min_box_size):
    """
    Main entry — called by main.py for each panel.

    Returns:
        box_regions   : list of dicts {center_3d, uv_center, uv_size,
                                       origin, u_axis, v_axis, normal}
        negative_space: dict {face, u_bounds, v_bounds, origin,
                               u_axis, v_axis, normal, boxes}
    """
    origin, u_axis, v_axis, normal = build_face_basis(face)
    u_min, u_max, v_min, v_max     = face_uv_bounds(face, origin, u_axis, v_axis)

    face_area  = face.calc_area()
    u_span     = u_max - u_min
    v_span     = v_max - v_min
    short_edge = min(u_span, v_span)

    n_boxes = target_box_count(face_area)
    print(f"    [Step1] area={face_area:.3f}  short_edge={short_edge:.3f} "
          f" → target {n_boxes} boxes")

    attractors = scatter_attractors(rng, u_min, u_max, v_min, v_max, ATTRACTOR_COUNT)

    positions = [
        (rng.uniform(u_min, u_max), rng.uniform(v_min, v_max))
        for _ in range(n_boxes)
    ]

    positions  = simulate(positions, attractors, u_min, u_max, v_min, v_max)
    raw_boxes  = assign_sizes(positions, rng, short_edge, min_box_size)

    box_regions = []
    for b in raw_boxes:
        uc, vc   = b['uv_center']
        center3d = uv_to_world(uc, vc, origin, u_axis, v_axis)
        box_regions.append({
            'center_3d': center3d,
            'uv_center': b['uv_center'],
            'uv_size'  : b['uv_size'],
            'origin'   : origin,
            'u_axis'   : u_axis,
            'v_axis'   : v_axis,
            'normal'   : normal,
        })

    negative_space = {
        'face'    : face,
        'u_bounds': (u_min, u_max),
        'v_bounds': (v_min, v_max),
        'origin'  : origin,
        'u_axis'  : u_axis,
        'v_axis'  : v_axis,
        'normal'  : normal,
        'boxes'   : box_regions,
    }

    return box_regions, negative_space
