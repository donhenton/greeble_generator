"""
steps/step4.py  —  STUB
Sparse interstitial scatter of objects from GREEBLE4 collection
across the face negative space (area outside all boxes).

Intentionally lays over Step 3 connectors — creates the visual effect
of greeble growing around existing infrastructure.

NOT YET IMPLEMENTED.
"""

GREEBLE4_COLLECTION = "GREEBLE4"


def run_step4(obj, bm, face, negative_space, rng, output_col):
    """
    Stub — sparse scatter in negative space.

    Args:
        obj            : Blender mesh object
        bm             : BMesh (edit mode)
        face           : selected BMesh face
        negative_space : dict from Step 1 {face, u_bounds, v_bounds,
                         origin, u_axis, v_axis, normal, boxes}
        rng            : seeded Random instance
        output_col     : Blender collection to place generated objects into
    """
    import bpy

    col = bpy.data.collections.get(GREEBLE4_COLLECTION)
    if col is None:
        print(f"    [Step4] WARNING: '{GREEBLE4_COLLECTION}' not found — skipping.")
        return
    if len(col.objects) == 0:
        print(f"    [Step4] WARNING: '{GREEBLE4_COLLECTION}' is empty — skipping.")
        return

    print(f"    [Step4] STUB — negative space ready for interstitial scatter.")
    # TODO:
    # 1. Sample candidate positions across face UV bounds
    # 2. Reject positions that fall inside any box_region
    # 3. Keep density sparse (separate density constant from Step 2)
    # 4. Pick objects randomly from GREEBLE4 collection (rng)
    # 5. Place objects — no collision checking against Step 3 (intentional overlap)
    # 6. Instance into output_col
