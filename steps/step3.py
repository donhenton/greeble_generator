"""
steps/step3.py
Scoring marks — shallow grooves cut across the negative space of the panel.

Approach:
  - Generate non-uniform cut line pairs in both X and Y directions
    across the full panel bounds (edge-to-edge)
  - Use bmesh.ops.bisect_plane to slice negative space faces along each line
  - Each scoring mark is a paired bisect (two parallel cuts = thin strip)
  - Extrude the thin strip faces in -Z to create a visible groove
  - Box faces are untouched — recesses interrupt grooves naturally

All cut positions are seeded per-panel for variety across the library.
Panel is always XY-parallel so no normal alignment needed.
"""

import bpy
import bmesh
import mathutils
import random
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import (
    SCORE_CUTS_X,
    SCORE_CUTS_Y,
    SCORE_IRREGULARITY,
    SCORE_DEPTH,
    SCORE_WIDTH,
)


# ---------------------------------------------------------------------------
# CUT LINE GENERATION  (adapted from geometry.py)
# ---------------------------------------------------------------------------

def generate_cut_positions(total, n_cuts, irregularity, rng):
    """
    Generate n_cuts non-uniform cut positions across a span of `total` units.
    Returns list of floats, each representing one cut line position.
    Adapted from generate_cuts() in the reference geometry.py.
    """
    base_step = total / (n_cuts + 1)
    positions = []
    for i in range(1, n_cuts + 1):
        base   = i * base_step
        offset = rng.uniform(
            -irregularity * base_step,
             irregularity * base_step
        )
        pos = base + offset
        # Keep within bounds with margin
        pos = max(base_step * 0.2, min(total - base_step * 0.2, pos))
        positions.append(pos)
    return positions


def make_groove_pairs(positions, origin, half_width):
    """
    Convert cut positions to paired cut lines (each groove = two parallel cuts).
    Returns list of (cut_a, cut_b) pairs in world space, offset from origin.
    """
    pairs = []
    for pos in positions:
        cut_a = origin + pos - half_width
        cut_b = origin + pos + half_width
        pairs.append((cut_a, cut_b))
    return pairs


# ---------------------------------------------------------------------------
# PANEL BOUNDS
# ---------------------------------------------------------------------------

def get_panel_bounds(neg_faces):
    """
    Return (x_min, x_max, y_min, y_max) world bounds across all negative
    space faces. Used as the scoring grid extent.
    """
    xs = [v.co.x for f in neg_faces for v in f.verts]
    ys = [v.co.y for f in neg_faces for v in f.verts]
    return min(xs), max(xs), min(ys), max(ys)


def get_floor_z(neg_faces):
    """Return Z level of the negative space (panel surface Z=0)."""
    if not neg_faces:
        return 0.0
    zs = [v.co.z for f in neg_faces for v in f.verts]
    return sum(zs) / len(zs)


# ---------------------------------------------------------------------------
# BISECT + GROOVE
# ---------------------------------------------------------------------------

def bisect_faces(bm, faces, point, normal):
    """
    Slice a set of faces along a plane defined by point and normal.
    Returns updated face list after bisect.
    Uses bmesh.ops.bisect_plane — cuts cleanly through existing topology.
    """
    if not faces:
        return faces

    geom = faces[:]
    ret  = bmesh.ops.bisect_plane(
        bm,
        geom        = geom,
        plane_co    = point,
        plane_no    = normal,
        clear_inner = False,
        clear_outer = False,
    )
    bm.faces.ensure_lookup_table()
    return ret


def collect_strip_faces(bm, normal, cut_a_pos, cut_b_pos, panel_z):
    """
    After two parallel bisects, collect the thin face strip between them.
    Identifies strip faces by their centre position falling between the two cuts.
    normal is either X or Y axis vector.
    """
    strip = []
    for f in bm.faces:
        if abs(f.normal.z - 1.0) > 0.1:   # only panel surface faces
            continue
        centre = f.calc_center_median()
        # Project centre onto the cut axis
        proj = centre.dot(normal)
        if cut_a_pos <= proj <= cut_b_pos:
            strip.append(f)
    return strip


def extrude_groove(bm, strip_faces, depth, normal_vec):
    """
    Extrude strip faces in -Z to create a visible groove.
    """
    if not strip_faces:
        return

    extrude_vec = mathutils.Vector((0.0, 0.0, -abs(depth)))
    ret         = bmesh.ops.extrude_face_region(bm, geom=strip_faces)
    new_geom    = ret['geom']
    new_verts   = [g for g in new_geom if isinstance(g, bmesh.types.BMVert)]
    new_faces   = [g for g in new_geom if isinstance(g, bmesh.types.BMFace)]

    bmesh.ops.translate(bm, vec=extrude_vec, verts=new_verts)

    # Delete original strip top faces — open the groove
    bmesh.ops.delete(bm, geom=strip_faces, context='FACES')


# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------

def run_step3(obj, bm, face, box_regions, rng, staging_col):
    """
    Cut scoring grooves across the negative space of the panel.

    Args:
        obj         : Blender mesh object (panel)
        bm          : BMesh in edit mode
        face        : original panel BMFace (used for reference)
        box_regions : list of box dicts from Step 1
        rng         : seeded Random instance
        staging_col : per-panel staging collection (not used — grooves
                      are cut directly into the panel mesh)
    """
    # Refresh bmesh
    bm.faces.ensure_lookup_table()
    bm.verts.ensure_lookup_table()

    # Collect negative space faces — flat panel faces not part of box floors/walls
    # Identify by normal pointing +Z and at panel surface level (Z ~ 0)
    neg_faces = [
        f for f in bm.faces
        if f.normal.z > 0.9 and abs(f.calc_center_median().z) < 0.01
    ]

    if not neg_faces:
        print("    [Step3] No negative space faces found — skipping.")
        return

    x_min, x_max, y_min, y_max = get_panel_bounds(neg_faces)
    panel_z = get_floor_z(neg_faces)

    x_span = x_max - x_min
    y_span = y_max - y_min

    print(f"    [Step3] Panel bounds: X={x_min:.3f}→{x_max:.3f}  "
          f"Y={y_min:.3f}→{y_max:.3f}  neg_faces={len(neg_faces)}")

    half_w = SCORE_WIDTH / 2.0

    # --- X-direction grooves (cut planes face Y normal) ---
    x_positions = generate_cut_positions(x_span, SCORE_CUTS_X,
                                         SCORE_IRREGULARITY, rng)
    x_pairs     = make_groove_pairs(x_positions, x_min, half_w)

    x_axis = mathutils.Vector((1.0, 0.0, 0.0))
    y_axis = mathutils.Vector((0.0, 1.0, 0.0))

    x_grooves = 0
    for cut_a, cut_b in x_pairs:
        # Two parallel bisects along X
        pt_a = mathutils.Vector((cut_a, 0.0, panel_z))
        pt_b = mathutils.Vector((cut_b, 0.0, panel_z))

        bisect_faces(bm, list(bm.faces), pt_a, x_axis)
        bm.faces.ensure_lookup_table()
        bisect_faces(bm, list(bm.faces), pt_b, x_axis)
        bm.faces.ensure_lookup_table()

        strip = collect_strip_faces(bm, x_axis, cut_a, cut_b, panel_z)
        if strip:
            extrude_groove(bm, strip, SCORE_DEPTH, x_axis)
            bm.faces.ensure_lookup_table()
            x_grooves += 1

    # --- Y-direction grooves (cut planes face X normal) ---
    y_positions = generate_cut_positions(y_span, SCORE_CUTS_Y,
                                         SCORE_IRREGULARITY, rng)
    y_pairs     = make_groove_pairs(y_positions, y_min, half_w)

    y_grooves = 0
    for cut_a, cut_b in y_pairs:
        pt_a = mathutils.Vector((0.0, cut_a, panel_z))
        pt_b = mathutils.Vector((0.0, cut_b, panel_z))

        bisect_faces(bm, list(bm.faces), pt_a, y_axis)
        bm.faces.ensure_lookup_table()
        bisect_faces(bm, list(bm.faces), pt_b, y_axis)
        bm.faces.ensure_lookup_table()

        strip = collect_strip_faces(bm, y_axis, cut_a, cut_b, panel_z)
        if strip:
            extrude_groove(bm, strip, SCORE_DEPTH, y_axis)
            bm.faces.ensure_lookup_table()
            y_grooves += 1

    bmesh.update_edit_mesh(obj.data)

    print(f"    [Step3] {x_grooves} X-grooves, {y_grooves} Y-grooves cut.")
