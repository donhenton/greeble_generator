"""
steps/step2.py  —  STUB
Growth-front diffusion scatter of flat objects from GREEBLE2 collection
across each box floor.

Object count scales with box area (soft cap ~10-15 per box).
Seed point derived from Step 1 attractor data.
Overlap between objects is permitted.

NOT YET IMPLEMENTED.
"""

GREEBLE2_COLLECTION = "GREEBLE2"


def run_step2(obj, bm, face, box_regions, rng, output_col):
    """
    Stub — growth-front diffusion scatter inside each box region.

    Args:
        obj         : Blender mesh object
        bm          : BMesh (edit mode)
        face        : selected BMesh face
        box_regions : list of box dicts from Step 1
        rng         : seeded Random instance
        output_col  : Blender collection to place generated objects into
    """
    import bpy

    col = bpy.data.collections.get(GREEBLE2_COLLECTION)
    if col is None:
        print(f"    [Step2] WARNING: '{GREEBLE2_COLLECTION}' not found — skipping.")
        return
    if len(col.objects) == 0:
        print(f"    [Step2] WARNING: '{GREEBLE2_COLLECTION}' is empty — skipping.")
        return

    print(f"    [Step2] STUB — {len(box_regions)} boxes ready for growth diffusion scatter.")
    # TODO:
    # 1. For each box_region:
    #    a. Calculate object count from box area (scale ~10-15, soft cap)
    #    b. Seed growth front from attractor data (box uv_center as initial seed)
    #    c. Iteratively place objects adjacent to existing placements
    #    d. Pick objects randomly from GREEBLE2 collection (rng)
    #    e. Place flush on box floor, random Z rotation
    #    f. Instance into output_col
