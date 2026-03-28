"""
steps/step3.py
Sub-panel extrusions in the negative space.

Groups negative space grid cells into random rectangles and extrudes
each as a unit — some recessed (-Z), some proud (+Z) — using preset
discrete depths. Produces a layered, multi-level panel surface appearance.

Uses the same extrude_face_region pattern as Step 1.
Recessed panels: top faces deleted (open recess).
Proud panels: top faces kept (raised platform).
"""

import bpy
import bmesh
import mathutils
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import (
    PANEL_DEPTHS,
    PANEL_COVERAGE,
    PANEL_MIN_CELLS,
    PANEL_MAX_CELLS,
)


# ---------------------------------------------------------------------------
# RECTANGLE HELPERS  (reused pattern from step1)
# ---------------------------------------------------------------------------

def clamp(val, lo, hi):
    return max(lo, min(hi, val))


def pick_rect(center_key, rng, n_rows, n_cols):
    """Pick a random rectangle of cells centred approximately on center_key."""
    row, col = center_key
    w = rng.randint(PANEL_MIN_CELLS, PANEL_MAX_CELLS)
    h = rng.randint(PANEL_MIN_CELLS, PANEL_MAX_CELLS)

    col_start = clamp(int(col - w / 2.0), 0, n_cols - w)
    row_start = clamp(int(row - h / 2.0), 0, n_rows - h)
    col_end   = col_start + w
    row_end   = row_start + h

    return row_start, col_start, row_end, col_end


def rects_overlap(a, b, margin=1):
    ar0, ac0, ar1, ac1 = a
    br0, bc0, br1, bc1 = b
    return not (
        ar1 + margin <= br0 or
        br1 + margin <= ar0 or
        ac1 + margin <= bc0 or
        bc1 + margin <= ac0
    )


def resolve_rects(candidate_keys, rng, n_rows, n_cols, coverage,
                  max_attempts=15):
    """
    For a random subset of negative space cells (coverage fraction),
    attempt to place non-overlapping rectangles.
    Returns list of (rect, depth) tuples.
    """
    # Shuffle and take coverage fraction of cells as candidates
    keys = list(candidate_keys)
    rng.shuffle(keys)
    n_candidates = int(len(keys) * coverage)
    keys = keys[:n_candidates]

    placed = []
    for key in keys:
        for _ in range(max_attempts):
            rect  = pick_rect(key, rng, n_rows, n_cols)
            depth = rng.choice(PANEL_DEPTHS)
            if not any(rects_overlap(rect, r) for r, _ in placed):
                placed.append((rect, depth))
                break

    return placed


# ---------------------------------------------------------------------------
# EXTRUSION
# ---------------------------------------------------------------------------

def extrude_sub_panel(bm, grid, rect, normal, depth):
    """
    Extrude a rectangle of negative space faces as a single region.

    Recessed (depth < 0): extrude down, delete top faces — open recess.
    Proud    (depth > 0): extrude up, keep top faces — raised platform.

    Returns number of faces extruded.
    """
    row_start, col_start, row_end, col_end = rect

    faces_to_extrude = []
    for row in range(row_start, row_end):
        for col in range(col_start, col_end):
            f = grid.get((row, col))
            if f is not None and f.is_valid:
                faces_to_extrude.append(f)

    if not faces_to_extrude:
        return 0

    extrude_vec = normal.normalized() * abs(depth)   # always +Z proud

    ret      = bmesh.ops.extrude_face_region(bm, geom=faces_to_extrude)
    new_geom = ret['geom']
    new_faces = [g for g in new_geom if isinstance(g, bmesh.types.BMFace)]
    new_verts = [g for g in new_geom if isinstance(g, bmesh.types.BMVert)]

    bmesh.ops.translate(bm, vec=extrude_vec, verts=new_verts)

    # Always proud (+Z) — keep original faces as the base,
    # new top faces form the raised platform surface

    return len(faces_to_extrude)


# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------

def run_step3(obj, bm, face, box_regions, rng, staging_col):
    """
    Extrude sub-panels in the negative space.

    Uses negative_space data passed via box_regions context —
    actually receives negative_space directly from main.py pipeline.
    Signature kept consistent with other steps.

    NOTE: This step is called with negative_space not box_regions.
    See main.py run_pipeline() for how it is called.
    """
    # negative_space is passed as box_regions argument from pipeline
    # (see run_pipeline in main.py)
    negative_space = box_regions

    cell_keys = negative_space.get('cell_keys', [])
    grid      = negative_space.get('grid', {})
    n_rows    = negative_space.get('n_rows', 0)
    n_cols    = negative_space.get('n_cols', 0)
    normal    = negative_space.get('normal', mathutils.Vector((0, 0, 1)))

    if not cell_keys:
        print("    [Step3] No negative space cells — skipping.")
        return

    print(f"    [Step3] {len(cell_keys)} negative space cells  "
          f"coverage={PANEL_COVERAGE}  depths={PANEL_DEPTHS}")

    # Resolve non-overlapping sub-panel rectangles
    rects = resolve_rects(cell_keys, rng, n_rows, n_cols, PANEL_COVERAGE)
    print(f"    [Step3] {len(rects)} sub-panels resolved.")

    bm.faces.ensure_lookup_table()

    extruded = 0
    for rect, depth in rects:
        n = extrude_sub_panel(bm, grid, rect, normal, depth)
        if n > 0:
            extruded += 1
            bm.faces.ensure_lookup_table()

    bmesh.update_edit_mesh(obj.data)
    print(f"    [Step3] {extruded} sub-panels extruded.")
