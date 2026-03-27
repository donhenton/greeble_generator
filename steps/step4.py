"""
steps/step4.py  —  STUB
Sparse interstitial scatter of objects from GREEBLE4 collection
across the negative space (flat panel faces outside all boxes).

Intentionally lays over Step 3 connectors — creates the visual effect
of greeble growing around existing infrastructure.

NOT YET IMPLEMENTED.
"""

GREEBLE4_COLLECTION = "GREEBLE4"


def run_step4(obj, bm, face, negative_space, rng, output_col):
    """
    Stub — sparse scatter across negative space faces.

    negative_space: {
        'faces'  : [BMFace, ...]   — flat panel faces outside all boxes
        'normal' : Vector
    }
    """
    import bpy

    col = bpy.data.collections.get(GREEBLE4_COLLECTION)
    if col is None:
        print(f"    [Step4] WARNING: '{GREEBLE4_COLLECTION}' not found — skipping.")
        return
    if len(col.objects) == 0:
        print(f"    [Step4] WARNING: '{GREEBLE4_COLLECTION}' is empty — skipping.")
        return

    print(f"    [Step4] STUB — {len(negative_space['faces'])} negative space faces ready.")
    # TODO:
    # 1. Sample positions across negative_space faces
    # 2. Keep density sparse (separate constant from Step 2)
    # 3. Pick objects randomly from GREEBLE4 (rng)
    # 4. No collision checking against Step 3 — overlap intentional
    # 5. Instance into output_col
