"""
steps/step3.py  —  STUB
Connectors drawn between boxes on the same face,
with random joint placement and decorative joint covers.

All connectors stay coplanar with the panel face.

NOT YET IMPLEMENTED.
"""


def run_step3(obj, bm, face, box_regions, rng, output_col):
    """
    Stub — connector geometry between box pairs.

    Args:
        obj         : Blender mesh object
        bm          : BMesh (edit mode)
        face        : selected BMesh face
        box_regions : list of box dicts from Step 1
        rng         : seeded Random instance
        output_col  : Blender collection to place generated objects into
    """
    if len(box_regions) < 2:
        print("    [Step3] Fewer than 2 boxes — no connectors to draw.")
        return

    print(f"    [Step3] STUB — {len(box_regions)} boxes ready for connector pass.")
    # TODO:
    # 1. Determine box pairs to connect (not necessarily all pairs)
    # 2. For each pair:
    #    a. Draw connector geometry between box edges (tube / cable / conduit)
    #    b. Place random joint objects along connector length
    #    c. Add joint cover objects at joint positions
    # 3. Place all geometry into output_col
