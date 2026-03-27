"""
scene.py
Scene clearing, collection creation and validation.
"""

import bpy
from config import (
    GREEBLE2_COLLECTION,
    GREEBLE4_COLLECTION,
    OUTPUT_PREFIX,
)


def clear_scene():
    """
    Remove all objects and all GREEBLE_OUTPUT_ collections from the scene.
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

    # Delete all unprotected objects
    bpy.ops.object.select_all(action='DESELECT')
    for o in list(bpy.data.objects):
        if o.name not in protected_objects:
            bpy.data.objects.remove(o, do_unlink=True)

    # Remove all GREEBLE_OUTPUT_ collections
    for col in list(bpy.data.collections):
        if col.name.startswith(OUTPUT_PREFIX):
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


def get_next_output_index():
    """
    Scan existing collections for OUTPUT_PREFIX and return next increment.
    e.g. if GREEBLE_OUTPUT_01 and _02 exist, returns 3.
    """
    existing = [
        c.name for c in bpy.data.collections
        if c.name.startswith(OUTPUT_PREFIX)
    ]
    if not existing:
        return 1
    indices = []
    for name in existing:
        suffix = name[len(OUTPUT_PREFIX):]
        if suffix.isdigit():
            indices.append(int(suffix))
    return max(indices) + 1 if indices else 1


def create_output_collection(index, panel_name, source_meta):
    """
    Create a numbered output collection tagged with source metadata.
    Returns the collection.
    """
    col_name = f"{OUTPUT_PREFIX}{index:02d}"
    col = bpy.data.collections.new(col_name)
    bpy.context.scene.collection.children.link(col)

    col['greeble_panel_name']  = panel_name
    col['greeble_batch_seed']  = source_meta['batch_seed']
    col['greeble_panel_seed']  = source_meta['panel_seed']
    col['greeble_panel_index'] = source_meta['panel_index']
    col['greeble_ratio']       = source_meta['ratio']
    col['greeble_collections'] = (
        f"{GREEBLE2_COLLECTION}, {GREEBLE4_COLLECTION}"
    )
    col['greeble_timestamp']   = source_meta['timestamp']

    return col
