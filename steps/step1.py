"""
steps/step1.py
Box placement via grid subdivision and attractor/repeller field.

Workflow:
  1. Subdivide the panel face into an NxN grid of small quads
  2. Use attractor/repeller simulation to pick rectangular cell groups
  3. Extrude each group in -Z to create recessed box cavities
  4. Return box data (top faces of recessed areas) and negative space
     (remaining flat panel faces outside boxes)

INPUT:  obj, bm, face, rng, min_box_size
OUTPUT: box_regions    — list of dicts, each describing a recessed box
        negative_space — dict describing remaining flat panel faces
"""

import bpy
import bmesh
import mathutils
import math

# ---------------------------------------------------------------------------
# TUNING CONSTANTS
# ---------------------------------------------------------------------------

GRID_DIVISIONS     = 10     # NxN grid subdivisions across the panel face
BOX_EXTRUDE_DEPTH  = 0.08   # how deep boxes are recessed in -Z (Blender units)

ATTRACTOR_COUNT    = 4      # attractors scattered across face per panel
ATTRACTOR_STRENGTH = 1.2    # pull strength (inverse-square scale)
REPELLER_STRENGTH  = 1.0    # push strength between box centres
ITERATIONS         = 100    # max simulation steps
CONVERGENCE_DELTA  = 0.0005 # stop early if max movement drops below this
STEP_SIZE          = 0.04   # movement scale per iteration

# Box size in grid cells (min/max span per axis)
BOX_MIN_CELLS = 2           # minimum cells per box side
BOX_MAX_CELLS = 4           # maximum cells per box side

# Face area (Blender units²) → target box count
AREA_BOX_COUNT = [
    (0.0,  2),
    (1.0,  3),
    (2.5,  4),
    (4.5,  5),
]


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
# GRID HELPERS
# ---------------------------------------------------------------------------

def clamp(val, lo, hi):
    return max(lo, min(hi, val))


def build_grid(bm, face, divisions):
    """
    Subdivide a single quad face into a divisions x divisions grid.
    Uses bmesh subdivide_edges to split the face evenly.

    Returns the updated bm — the original face is replaced by grid quads.
    The new grid faces all share the same normal as the original face.
    """
    # We need to work in object mode for subdivide to work cleanly,
    # so we use bmesh operators directly.

    # Select only this face's edges for subdivision
    bm.faces.ensure_lookup_table()
    bm.edges.ensure_lookup_table()

    # Collect the 4 edges of the quad
    edges = list(face.edges)

    # Subdivide edges (divisions-1 cuts = divisions segments)
    cuts = divisions - 1
    if cuts > 0:
        bmesh.ops.subdivide_edges(
            bm,
            edges=edges,
            cuts=cuts,
            use_grid_fill=True,
            use_only_quads=True,
        )

    bm.faces.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    return bm


def get_grid_faces(bm, original_face_normal, original_face_center, divisions):
    """
    After subdivision, collect all the small grid quad faces.
    Identifies them by matching normal direction and proximity to original face plane.

    Returns list of BMFace objects forming the grid, sorted by (row, col).
    """
    normal = original_face_normal.normalized()

    grid_faces = []
    for f in bm.faces:
        if len(f.verts) != 4:
            continue
        # Face must point same direction as original
        if f.normal.dot(normal) < 0.9:
            continue
        # Face centre must be close to original face plane
        to_center = f.calc_center_median() - original_face_center
        dist_from_plane = abs(to_center.dot(normal))
        if dist_from_plane < 0.01:
            grid_faces.append(f)

    return grid_faces


def build_grid_index(grid_faces, u_axis, v_axis, origin):
    """
    Build a 2D dictionary mapping (row, col) → BMFace.
    Uses UV projection to assign grid coordinates.
    """
    # Project all face centres into UV space
    uvs = []
    for f in grid_faces:
        c    = f.calc_center_median()
        delta = c - origin
        u    = delta.dot(u_axis)
        v    = delta.dot(v_axis)
        uvs.append((u, v, f))

    if not uvs:
        return {}, 0, 0

    # Find unique U and V values (grid lines)
    us = sorted(set(round(x[0], 5) for x in uvs))
    vs = sorted(set(round(x[1], 5) for x in uvs))

    u_to_col = {u: i for i, u in enumerate(us)}
    v_to_row = {v: i for i, v in enumerate(vs)}

    grid = {}
    for u, v, f in uvs:
        col = u_to_col[round(u, 5)]
        row = v_to_row[round(v, 5)]
        grid[(row, col)] = f

    return grid, len(vs), len(us)


# ---------------------------------------------------------------------------
# ATTRACTOR / REPELLER — works in grid cell space
# ---------------------------------------------------------------------------

def scatter_attractors(rng, n_rows, n_cols, n):
    """Place n attractors at random grid cell positions."""
    return [
        (rng.uniform(0, n_cols - 1), rng.uniform(0, n_rows - 1))
        for _ in range(n)
    ]


def attractor_force(pos, attractors, strength):
    fx, fy = 0.0, 0.0
    for ax, ay in attractors:
        dx      = ax - pos[0]
        dy      = ay - pos[1]
        dist_sq = dx * dx + dy * dy + 1e-6
        scale   = strength / dist_sq
        fx     += dx * scale
        fy     += dy * scale
    return fx, fy


def repeller_force(idx, positions, strength):
    fx, fy = 0.0, 0.0
    px, py = positions[idx]
    for j, (qx, qy) in enumerate(positions):
        if j == idx:
            continue
        dx      = px - qx
        dy      = py - qy
        dist_sq = dx * dx + dy * dy + 1e-6
        scale   = strength / dist_sq
        fx     += dx * scale
        fy     += dy * scale
    return fx, fy


def simulate(positions, attractors, n_rows, n_cols):
    """Run attractor/repeller simulation in grid cell space."""
    for iteration in range(ITERATIONS):
        max_move      = 0.0
        new_positions = []
        for i, pos in enumerate(positions):
            fa  = attractor_force(pos, attractors, ATTRACTOR_STRENGTH)
            fr  = repeller_force(i, positions, REPELLER_STRENGTH)
            nx  = clamp(pos[0] + (fa[0] + fr[0]) * STEP_SIZE, 0, n_cols - 1)
            ny  = clamp(pos[1] + (fa[1] + fr[1]) * STEP_SIZE, 0, n_rows - 1)
            move = math.sqrt((nx - pos[0]) ** 2 + (ny - pos[1]) ** 2)
            max_move = max(max_move, move)
            new_positions.append((nx, ny))
        positions[:] = new_positions
        if max_move < CONVERGENCE_DELTA:
            print(f"    [Step1] Converged at iteration {iteration + 1}")
            break
    return positions


# ---------------------------------------------------------------------------
# BOX RECTANGLE SELECTION
# ---------------------------------------------------------------------------

def pick_box_rect(center, rng, n_rows, n_cols):
    """
    Given a float grid centre position, pick a random rectangle of cells
    (BOX_MIN_CELLS to BOX_MAX_CELLS per side) centred approximately there.
    Returns (row_start, col_start, row_end, col_end) clamped to grid.
    """
    w = rng.randint(BOX_MIN_CELLS, BOX_MAX_CELLS)
    h = rng.randint(BOX_MIN_CELLS, BOX_MAX_CELLS)

    col_start = int(round(center[0] - w / 2.0))
    row_start = int(round(center[1] - h / 2.0))
    col_end   = col_start + w
    row_end   = row_start + h

    col_start = clamp(col_start, 0, n_cols - w)
    row_start = clamp(row_start, 0, n_rows - h)
    col_end   = clamp(col_end,   w, n_cols)
    row_end   = clamp(row_end,   h, n_rows)

    return row_start, col_start, row_end, col_end


def boxes_overlap(a, b):
    """
    Check if two box rectangles overlap.
    a, b are (row_start, col_start, row_end, col_end).
    A 1-cell margin is enforced to keep boxes separated.
    """
    margin = 1
    ar0, ac0, ar1, ac1 = a
    br0, bc0, br1, bc1 = b
    return not (
        ar1 + margin <= br0 or
        br1 + margin <= ar0 or
        ac1 + margin <= bc0 or
        bc1 + margin <= ac0
    )


def resolve_box_rects(positions, rng, n_rows, n_cols, max_attempts=20):
    """
    For each settled position, pick a non-overlapping box rectangle.
    Attempts up to max_attempts times per box before skipping.
    Returns list of (row_start, col_start, row_end, col_end).
    """
    rects = []
    for pos in positions:
        placed = False
        for _ in range(max_attempts):
            rect = pick_box_rect(pos, rng, n_rows, n_cols)
            if not any(boxes_overlap(rect, r) for r in rects):
                rects.append(rect)
                placed = True
                break
        if not placed:
            print(f"    [Step1] Could not place box at {pos} without overlap — skipped.")
    return rects


# ---------------------------------------------------------------------------
# EXTRUSION
# ---------------------------------------------------------------------------

def extrude_box(bm, grid, rect, normal, depth):
    """
    Extrude the rectangle of grid faces as a single region into the panel (-Z),
    then delete the original top faces to leave an open tray.

    Result: four clean walls + one flat floor, open at the top —
    a recessed tray ready for Step 2 greeble fill.

    Returns the floor faces (bottom of the tray).
    """
    row_start, col_start, row_end, col_end = rect

    faces_to_extrude = []
    for row in range(row_start, row_end):
        for col in range(col_start, col_end):
            f = grid.get((row, col))
            if f is not None:
                faces_to_extrude.append(f)

    if not faces_to_extrude:
        return []

    extrude_vec = -normal.normalized() * depth

    # Extrude as a single connected region — one floor, four walls
    ret      = bmesh.ops.extrude_face_region(bm, geom=faces_to_extrude)
    new_geom = ret['geom']

    new_faces = [g for g in new_geom if isinstance(g, bmesh.types.BMFace)]
    new_verts = [g for g in new_geom if isinstance(g, bmesh.types.BMVert)]

    # Push new geometry down into the panel
    bmesh.ops.translate(bm, vec=extrude_vec, verts=new_verts)

    # Delete the original top faces — they cap the tray and must be removed
    # so the recess is open at the panel surface level
    bmesh.ops.delete(bm, geom=faces_to_extrude, context='FACES')

    # Floor faces: new faces whose normal matches the panel normal
    # (wall faces point sideways, floor points same way as panel)
    floor_faces = [
        f for f in new_faces
        if f.normal.dot(normal) > 0.9
    ]

    return floor_faces


# ---------------------------------------------------------------------------
# COORDINATE SYSTEM
# ---------------------------------------------------------------------------

def build_face_basis(face):
    verts  = [v.co.copy() for v in face.verts]
    origin = verts[0]
    u_axis = (verts[1] - verts[0]).normalized()
    normal = face.normal.copy()
    v_axis = normal.cross(u_axis).normalized()
    return origin, u_axis, v_axis, normal


# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------

def run_step1(obj, bm, face, rng, min_box_size):
    """
    Main entry — called by main.py for each panel.

    Returns:
        box_regions   : list of dicts {
                            'floor_faces' : [BMFace, ...],  # bottom of recess
                            'rect'        : (r0,c0,r1,c1),
                            'normal'      : Vector,
                            'depth'       : float,
                        }
        negative_space: dict {
                            'faces'  : [BMFace, ...],  # flat panel faces outside boxes
                            'normal' : Vector,
                        }
    """
    origin, u_axis, v_axis, normal = build_face_basis(face)
    face_center = face.calc_center_median().copy()
    face_area   = face.calc_area()

    n_boxes = target_box_count(face_area)
    print(f"    [Step1] area={face_area:.3f} → target {n_boxes} boxes  "
          f"grid={GRID_DIVISIONS}x{GRID_DIVISIONS}")

    # --- Subdivide panel into grid ---
    bm = build_grid(bm, face, GRID_DIVISIONS)
    bmesh.update_edit_mesh(obj.data)

    # --- Collect grid faces ---
    grid_faces = get_grid_faces(bm, normal, face_center, GRID_DIVISIONS)
    if not grid_faces:
        print("    [Step1] ERROR: no grid faces found after subdivision.")
        return [], {'faces': [], 'normal': normal}

    grid, n_rows, n_cols = build_grid_index(grid_faces, u_axis, v_axis, origin)
    print(f"    [Step1] Grid built: {n_rows} rows x {n_cols} cols  "
          f"({len(grid_faces)} faces)")

    # --- Attractor/repeller in grid cell space ---
    attractors = scatter_attractors(rng, n_rows, n_cols, ATTRACTOR_COUNT)
    positions  = [
        (rng.uniform(0, n_cols - 1), rng.uniform(0, n_rows - 1))
        for _ in range(n_boxes)
    ]
    positions = simulate(positions, attractors, n_rows, n_cols)

    # --- Resolve non-overlapping box rectangles ---
    rects = resolve_box_rects(positions, rng, n_rows, n_cols)
    print(f"    [Step1] {len(rects)} non-overlapping box rects resolved.")

    # --- Extrude each box rect into the panel ---
    box_cell_set = set()
    box_regions  = []

    for rect in rects:
        floor_faces = extrude_box(bm, grid, rect, normal, BOX_EXTRUDE_DEPTH)
        if floor_faces:
            # Track which grid cells are consumed by this box
            row_start, col_start, row_end, col_end = rect
            for row in range(row_start, row_end):
                for col in range(col_start, col_end):
                    box_cell_set.add((row, col))

            box_regions.append({
                'floor_faces': floor_faces,
                'rect'       : rect,
                'normal'     : normal.copy(),
                'depth'      : BOX_EXTRUDE_DEPTH,
            })

    # --- Collect remaining flat faces as negative space ---
    # Refresh after extrusion
    bm.faces.ensure_lookup_table()
    neg_faces = [
        grid[key] for key in grid
        if key not in box_cell_set
    ]

    negative_space = {
        'faces' : neg_faces,
        'normal': normal.copy(),
    }

    bmesh.update_edit_mesh(obj.data)

    print(f"    [Step1] {len(box_regions)} boxes extruded. "
          f"{len(neg_faces)} negative space faces.")
    return box_regions, negative_space
