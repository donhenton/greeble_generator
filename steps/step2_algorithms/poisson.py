"""
steps/step2_algorithms/poisson.py
Poisson disk sampling scatter algorithm for Step 2.  —  STUB

Distributes objects with a minimum spacing enforced between placements,
giving a more uniform, less clustered distribution than growth_front.

NOT YET IMPLEMENTED.
"""


def run(box_regions, rng, staging_col, source_objects,
        compute_floor_centre, compute_floor_area, place_copy):
    """
    Stub — Poisson disk sampling scatter across box floors.

    Each placed object maintains a minimum distance from all others,
    producing a more uniform distribution than growth_front.
    """
    print("      [poisson] STUB — not yet implemented.")
    # TODO:
    # 1. For each box_region:
    #    a. Compute floor bounds from floor_faces
    #    b. Run Poisson disk sampling within bounds
    #    c. Scale sample count to floor area
    #    d. Place linked copies at sample positions
    return 0
