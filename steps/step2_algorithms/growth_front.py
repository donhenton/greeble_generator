"""
steps/step2_algorithms/growth_front.py
Growth-front diffusion scatter algorithm for Step 2.

Seeds from box floor centre, grows outward organically.
Each new position steps from a randomly chosen existing position
by STEP2_GROWTH_STEP in a random XY direction.
"""

import math
import mathutils
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import (
    STEP2_DENSITY,
    STEP2_MIN_OBJECTS,
    STEP2_MAX_OBJECTS,
    STEP2_GROWTH_STEP,
)


def compute_object_count(floor_area):
    """Scale object count to floor area, clamped to min/max."""
    count = int(floor_area / STEP2_DENSITY)
    return max(STEP2_MIN_OBJECTS, min(STEP2_MAX_OBJECTS, count))


def generate_positions(seed_pos, count, rng):
    """
    Generate `count` positions using a growth-front model.

    Seeds from seed_pos, each subsequent position steps outward
    from a randomly chosen existing position by STEP2_GROWTH_STEP
    with jitter, in a random XY direction. Z stays at floor level.
    """
    positions = [seed_pos.copy()]

    for _ in range(count - 1):
        base  = rng.choice(positions)
        angle = rng.uniform(0, math.pi * 2)
        dist  = STEP2_GROWTH_STEP * rng.uniform(0.6, 1.4)

        new_pos = mathutils.Vector((
            base.x + math.cos(angle) * dist,
            base.y + math.sin(angle) * dist,
            seed_pos.z,
        ))
        positions.append(new_pos)

    return positions


def run(box_regions, rng, staging_col, source_objects,
        compute_floor_centre, compute_floor_area, place_copy):
    """
    Public entry point — called by step2.py dispatcher.

    Args:
        box_regions          : list of box dicts from Step 1
        rng                  : seeded Random instance
        staging_col          : per-panel staging collection
        source_objects       : list of objects from GREEBLE2
        compute_floor_centre : helper from step2.py
        compute_floor_area   : helper from step2.py
        place_copy           : helper from step2.py
    """
    total_placed = 0

    for box in box_regions:
        floor_faces = box.get('floor_faces', [])
        if not floor_faces:
            continue

        floor_centre = compute_floor_centre(floor_faces)
        if floor_centre is None:
            continue

        floor_area = compute_floor_area(floor_faces)
        count      = compute_object_count(floor_area)

        print(f"      [growth_front] floor_area={floor_area:.4f} → {count} objects")

        positions = generate_positions(floor_centre, count, rng)

        for pos in positions:
            source = rng.choice(source_objects)
            place_copy(source, pos, staging_col)
            total_placed += 1

    return total_placed
