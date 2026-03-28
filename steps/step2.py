"""
steps/step2.py
Dispatcher for Step 2 scatter algorithms.

Shared helpers live here — all algorithm modules import them from this file.
The active algorithm is set by STEP2_ALGORITHM in config.py.

To add a new algorithm:
  1. Create steps/step2_algorithms/my_algo.py with a run() function
  2. Import it below and add to REGISTRY
  3. Set STEP2_ALGORITHM = "my_algo" in config.py
"""

import bpy
import mathutils
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import GREEBLE2_COLLECTION, STEP2_ALGORITHM

# Algorithm imports
from steps.step2_algorithms import growth_front
from steps.step2_algorithms import poisson

# ---------------------------------------------------------------------------
# REGISTRY — maps config name → algorithm module
# ---------------------------------------------------------------------------

REGISTRY = {
    "growth_front" : growth_front,
    "poisson"      : poisson,
}


# ---------------------------------------------------------------------------
# SHARED HELPERS — used by all algorithm modules
# ---------------------------------------------------------------------------

def get_greeble2_objects():
    """Return objects from GREEBLE2 collection, or [] with warning."""
    col = bpy.data.collections.get(GREEBLE2_COLLECTION)
    if col is None:
        print(f"    [Step2] WARNING: '{GREEBLE2_COLLECTION}' not found — skipping.")
        return []
    if len(col.objects) == 0:
        print(f"    [Step2] WARNING: '{GREEBLE2_COLLECTION}' is empty — skipping.")
        return []
    return list(col.objects)


def compute_floor_centre(floor_faces):
    """Return average world-space centre of all floor faces."""
    if not floor_faces:
        return None
    acc = mathutils.Vector((0.0, 0.0, 0.0))
    for f in floor_faces:
        acc += f.calc_center_median()
    return acc / len(floor_faces)


def compute_floor_area(floor_faces):
    """Return total area of all floor faces."""
    return sum(f.calc_area() for f in floor_faces)


def place_copy(source_obj, location, staging_col):
    """
    Create a copy of source_obj at location and link into staging_col.
    Uses source_obj.copy() so transform (scale, rotation) is preserved
    regardless of where the source lives in world space.
    Mesh data is shared — no full duplication.
    """
    new_obj          = source_obj.copy()
    new_obj.name     = f"GR2_{source_obj.name}"
    new_obj.location = location.copy()
    new_obj.location.z = location.z
    staging_col.objects.link(new_obj)
    return new_obj


# ---------------------------------------------------------------------------
# DISPATCHER
# ---------------------------------------------------------------------------

def run_step2(obj, bm, face, box_regions, rng, staging_col):
    """
    Dispatch to the active Step 2 algorithm as set by STEP2_ALGORITHM
    in config.py.
    """
    source_objects = get_greeble2_objects()
    if not source_objects:
        return

    algo = REGISTRY.get(STEP2_ALGORITHM)
    if algo is None:
        print(f"    [Step2] ERROR: unknown algorithm '{STEP2_ALGORITHM}'. "
              f"Available: {list(REGISTRY.keys())}")
        return

    print(f"    [Step2] Algorithm: {STEP2_ALGORITHM}")

    total_placed = algo.run(
        box_regions, rng, staging_col, source_objects,
        compute_floor_centre, compute_floor_area, place_copy
    )

    print(f"    [Step2] {total_placed} objects placed across {len(box_regions)} boxes.")
