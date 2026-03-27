"""
steps/step2.py  —  STUB
Growth-front diffusion scatter of flat objects from GREEBLE2 collection
across the floor of each recessed box.

Object count scales with box floor area (soft cap ~10-15 per box).
Overlap between objects is permitted.

NOT YET IMPLEMENTED.
"""

GREEBLE2_COLLECTION = "GREEBLE2"


def run_step2(obj, bm, face, box_regions, rng, output_col):
    """
    Stub — growth-front diffusion scatter on box floors.

    box_regions items: {
        'floor_faces' : [BMFace, ...]   — floor of the recessed box
        'rect'        : (r0,c0,r1,c1)  — grid cell rect
        'normal'      : Vector
        'depth'       : float
    }
    """
    import bpy

    col = bpy.data.collections.get(GREEBLE2_COLLECTION)
    if col is None:
        print(f"    [Step2] WARNING: '{GREEBLE2_COLLECTION}' not found — skipping.")
        return
    if len(col.objects) == 0:
        print(f"    [Step2] WARNING: '{GREEBLE2_COLLECTION}' is empty — skipping.")
        return

    print(f"    [Step2] STUB — {len(box_regions)} box floors ready for growth diffusion scatter.")
    # TODO:
    # 1. For each box_region:
    #    a. Compute floor area from floor_faces
    #    b. Scale object count to area (soft cap ~10-15)
    #    c. Seed growth front from box centre
    #    d. Iteratively place objects adjacent to existing placements
    #    e. Pick objects randomly from GREEBLE2 (rng)
    #    f. Place flush on floor face, random Z rotation
    #    g. Instance into output_col
