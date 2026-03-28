"""
steps/step2.py
Growth-front diffusion scatter of flat objects from GREEBLE2 collection
across the floor of each recessed box.

- Objects are linked copies (shared mesh data, independent transforms)
- Object origin placed directly on floor face world position
- No rotation or scale applied — user bakes variation into collection objects
- Count scales softly with box floor area
- Growth front seeds from box centre, spreads outward organically
- Overlap between objects is permitted
- Panel is always XY-parallel so no normal alignment needed
"""

import bpy
import math
import random
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import (
    GREEBLE2_COLLECTION,
    STEP2_DENSITY,
    STEP2_MIN_OBJECTS,
    STEP2_MAX_OBJECTS,
    STEP2_GROWTH_STEP,
)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def get_greeble2_objects():
    """
    Return list of objects from GREEBLE2 collection.
    Returns empty list with warning if collection missing or empty.
    """
    col = bpy.data.collections.get(GREEBLE2_COLLECTION)
    if col is None:
        print(f"    [Step2] WARNING: '{GREEBLE2_COLLECTION}' not found — skipping.")
        return []
    if len(col.objects) == 0:
        print(f"    [Step2] WARNING: '{GREEBLE2_COLLECTION}' is empty — skipping.")
        return []
    return list(col.objects)


def compute_floor_centre(floor_faces):
    """
    Return the average world-space centre of all floor faces.
    This is the growth front seed position.
    """
    if not floor_faces:
        return None
    total = sum(
        (f.calc_center_median() for f in floor_faces),
        start=floor_faces[0].calc_center_median() * 0
    )
    # Use mathutils Vector accumulation
    import mathutils
    acc = mathutils.Vector((0.0, 0.0, 0.0))
    for f in floor_faces:
        acc += f.calc_center_median()
    return acc / len(floor_faces)


def compute_floor_area(floor_faces):
    """Return total area of all floor faces."""
    return sum(f.calc_area() for f in floor_faces)


def compute_object_count(floor_area):
    """Scale object count to floor area, clamped to min/max."""
    count = int(floor_area / STEP2_DENSITY)
    return max(STEP2_MIN_OBJECTS, min(STEP2_MAX_OBJECTS, count))


def place_linked_copy(source_obj, location, staging_col):
    """
    Create a copy of source_obj placed at location and add to staging_col.

    Uses source_obj.copy() so the source object's transform (scale, rotation)
    is preserved correctly regardless of where the source lives in world space.
    The location is then overridden to the target floor position.
    Mesh data is shared — no full mesh duplication.
    """
    new_obj          = source_obj.copy()   # shared mesh data, correct transform
    new_obj.name     = f"GR2_{source_obj.name}"
    new_obj.location = location.copy()     # place at floor position
    new_obj.location.z = location.z        # lock Z to floor level
    staging_col.objects.link(new_obj)
    return new_obj


# ---------------------------------------------------------------------------
# GROWTH FRONT
# ---------------------------------------------------------------------------

def growth_front_positions(seed_pos, count, rng):
    """
    Generate `count` positions using a growth-front model.

    Starting from seed_pos, each new position steps outward from a
    randomly chosen existing position by STEP2_GROWTH_STEP in a random
    XY direction. Z stays fixed to the seed Z (floor level).

    Returns list of (x, y, z) positions.
    """
    positions = [seed_pos.copy()]

    for _ in range(count - 1):
        # Pick a random existing position to grow from
        base = rng.choice(positions)

        # Random angle in XY plane
        angle = rng.uniform(0, math.pi * 2)
        # Random step distance with some jitter
        dist  = STEP2_GROWTH_STEP * rng.uniform(0.6, 1.4)

        import mathutils
        new_pos = mathutils.Vector((
            base.x + math.cos(angle) * dist,
            base.y + math.sin(angle) * dist,
            seed_pos.z,                         # always on the floor
        ))
        positions.append(new_pos)

    return positions


# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------

def run_step2(obj, bm, face, box_regions, rng, staging_col):
    """
    Scatter flat GREEBLE2 objects across each box floor using
    a growth-front diffusion model.

    Args:
        obj         : Blender mesh object (panel)
        bm          : BMesh in edit mode
        face        : selected panel BMFace
        box_regions : list of dicts from Step 1, each with 'floor_faces'
        rng         : seeded Random instance
        staging_col : per-panel staging collection
    """
    source_objects = get_greeble2_objects()
    if not source_objects:
        return

    total_placed = 0

    for box in box_regions:
        floor_faces = box.get('floor_faces', [])
        if not floor_faces:
            continue

        floor_centre = compute_floor_centre(floor_faces)
        if floor_centre is None:
            continue

        floor_area   = compute_floor_area(floor_faces)
        count        = compute_object_count(floor_area)

        print(f"    [Step2] Box floor area={floor_area:.4f} → {count} objects")

        # Generate growth-front positions
        positions = growth_front_positions(floor_centre, count, rng)

        # Place a linked copy at each position
        for pos in positions:
            source = rng.choice(source_objects)
            place_linked_copy(source, pos, staging_col)
            total_placed += 1

    print(f"    [Step2] {total_placed} objects placed across {len(box_regions)} boxes.")
