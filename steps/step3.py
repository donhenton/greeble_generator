"""
steps/step3.py  —  STUB
Connectors drawn between boxes on the same face,
with random joint placement and decorative joint covers.

Connectors run across the flat panel surface between box edges.
All geometry stays coplanar with the panel face.

NOT YET IMPLEMENTED.
"""


def run_step3(obj, bm, face, box_regions, rng, output_col):
    """
    Stub — connector geometry between box pairs.

    box_regions items: {
        'floor_faces' : [BMFace, ...]
        'rect'        : (r0,c0,r1,c1)
        'normal'      : Vector
        'depth'       : float
    }
    """
    if len(box_regions) < 2:
        print("    [Step3] Fewer than 2 boxes — no connectors to draw.")
        return

    print(f"    [Step3] STUB — {len(box_regions)} boxes ready for connector pass.")
    # TODO:
    # 1. Determine which box pairs to connect
    # 2. For each pair:
    #    a. Route connector across panel surface between box edges
    #    b. Place random joint objects along connector
    #    c. Add joint cover objects at joint positions
    # 3. All geometry into output_col
