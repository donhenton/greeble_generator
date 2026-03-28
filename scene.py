"""
scene.py
Scene clearing, collection creation and validation.
"""

import bpy
from config import (
    GREEBLE2_COLLECTION,
    GREEBLE4_COLLECTION,
    OUTPUT_COLLECTION,
)


def clear_scene():
    """
    Remove all objects and the GREEBLE_OUTPUT collection from the scene.
    Preserves GREEBLE2 and GREEBLE4 collections and their contents.
    Called at the start of run_batch() when DEBUG_MODE is True.
    """
    protected = {GREEBLE2_COLLECTION, GREEBLE4_COLLECTION}

    # Mark objects belonging to protected collections
    protected_objects = set()
    for name in protected:
        col = bpy.data.collections.get(name)
        if col:
            for o in col.objects:
                protected_objects.add(o.name)

    # Delete all unprotected objects directly — no bpy.ops needed
    for o in list(bpy.data.objects):
        if o.name not in protected_objects:
            bpy.data.objects.remove(o, do_unlink=True)

    # Remove GREEBLE_OUTPUT collection if it exists
    col = bpy.data.collections.get(OUTPUT_COLLECTION)
    if col:
        bpy.data.collections.remove(col)

    print("  [Scene] Cleared — GREEBLE2 and GREEBLE4 preserved.")


def validate_collections():
    """
    Warn if GREEBLE2 or GREEBLE4 are missing or empty.
    Returns True if both present and populated, False otherwise.
    """
    ok = True
    for name in [GREEBLE2_COLLECTION, GREEBLE4_COLLECTION]:
        col = bpy.data.collections.get(name)
        if col is None:
            print(f"  [Scene] WARNING: collection '{name}' not found.")
            ok = False
        elif len(col.objects) == 0:
            print(f"  [Scene] WARNING: collection '{name}' is empty.")
            ok = False
    return ok


def get_or_create_output_collection(batch_seed, timestamp):
    """
    Find or create the single GREEBLE_OUTPUT collection.
    Tags it with batch metadata. Returns the collection.
    """
    col = bpy.data.collections.get(OUTPUT_COLLECTION)
    if col is None:
        col = bpy.data.collections.new(OUTPUT_COLLECTION)
        bpy.context.scene.collection.children.link(col)

    col['greeble_batch_seed'] = batch_seed
    col['greeble_timestamp']  = timestamp
    col['greeble_sources']    = f"{GREEBLE2_COLLECTION}, {GREEBLE4_COLLECTION}"

    return col


def create_staging_collection(panel_name):
    """
    Create a temporary per-panel staging collection.
    Steps deposit geometry here during the pipeline run.
    finalise_panel() joins everything in it, then removes it.
    """
    name = f"_staging_{panel_name}"
    col  = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col
