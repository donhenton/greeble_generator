"""
Greeble Generator — main.py
Batch production entry point.

Generates 20 greeble panels (10 x Square, 10 x 3:4) into numbered
GREEBLE_OUTPUT_XX collections, ready for Blender asset library curation.

Each panel is a single joined mesh object with:
  - Greebled front face
  - Clean flat back face (the base quad)
  - Origin at back face centre, -Z pointing away from greeble
  - Named GreeblePanel_{Ratio}_{index:02d}

Blender 4.x | Run from Blender Text Editor
"""

import bpy
import bmesh
import sys
import os
import random
import time

# ---------------------------------------------------------------------------
# PATH SETUP
# ---------------------------------------------------------------------------
_dir = os.path.dirname(bpy.context.space_data.text.filepath)
if _dir not in sys.path:
    sys.path.append(_dir)

from steps.step1 import run_step1
from steps.step2 import run_step2
from steps.step3 import run_step3
from steps.step4 import run_step4

# ---------------------------------------------------------------------------
# BATCH SETTINGS
# ---------------------------------------------------------------------------

# Set manually to reproduce a specific batch, or leave None for fresh results
BATCH_SEED = None           # e.g. BATCH_SEED = 482910 to reproduce

PANELS_PER_RATIO = 2        # SET TO 2 FOR TESTING — restore to 10 for production

MIN_BOX_SIZE     = 0.15     # shared minimum box dimension (all steps)

# Panel base dimensions (user scales to fit in their model)
PANEL_SIZES = {
    'Square': (2.0, 2.0),
    '3x4':    (2.0, 2.667),   # 3:4 ratio, 2 units on short side
}

# Layout spacing — extra gap between panels in the viewport grid
# Increase if panels overlap after scaling up panel dimensions
LAYOUT_SPACING = 1.0        # gap between panels (Blender units)

# Debug mode — when True, clears all objects and GREEBLE_OUTPUT_ collections
# before each run. GREEBLE2 and GREEBLE4 collections are preserved.
# Set to False for production runs (accumulates output collections).
DEBUG_MODE = True

# Required user collections
GREEBLE2_COLLECTION = "GREEBLE2"
GREEBLE4_COLLECTION = "GREEBLE4"

# Output collection prefix
OUTPUT_PREFIX = "GREEBLE_OUTPUT_"


# ---------------------------------------------------------------------------
# SCENE CLEAR (DEBUG MODE)
# ---------------------------------------------------------------------------

def clear_scene():
    """
    Remove all objects and all GREEBLE_OUTPUT_ collections from the scene.
    Preserves GREEBLE2 and GREEBLE4 collections and their contents.
    Called at the start of run_batch() when DEBUG_MODE is True.
    """
    protected = {GREEBLE2_COLLECTION, GREEBLE4_COLLECTION}

    # Collect objects NOT in protected collections
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

    print("  [Greeble] Scene cleared — GREEBLE2 and GREEBLE4 preserved.")


# ---------------------------------------------------------------------------
# COLLECTION MANAGEMENT
# ---------------------------------------------------------------------------

def get_next_output_index():
    """
    Scan existing collections for OUTPUT_PREFIX and return next increment.
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
    """
    col_name = f"{OUTPUT_PREFIX}{index:02d}"
    col = bpy.data.collections.new(col_name)
    bpy.context.scene.collection.children.link(col)

    col['greeble_panel_name']  = panel_name
    col['greeble_batch_seed']  = source_meta['batch_seed']
    col['greeble_panel_seed']  = source_meta['panel_seed']
    col['greeble_panel_index'] = source_meta['panel_index']
    col['greeble_ratio']       = source_meta['ratio']
    col['greeble_collections'] = f"{GREEBLE2_COLLECTION}, {GREEBLE4_COLLECTION}"
    col['greeble_timestamp']   = source_meta['timestamp']

    return col


# ---------------------------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------------------------

def validate_collections():
    """
    Warn if GREEBLE2 or GREEBLE4 are missing or empty.
    """
    ok = True
    for name in [GREEBLE2_COLLECTION, GREEBLE4_COLLECTION]:
        col = bpy.data.collections.get(name)
        if col is None:
            print(f"  [Greeble] WARNING: collection '{name}' not found.")
            ok = False
        elif len(col.objects) == 0:
            print(f"  [Greeble] WARNING: collection '{name}' is empty.")
            ok = False
    return ok


# ---------------------------------------------------------------------------
# PANEL QUAD CREATION
# ---------------------------------------------------------------------------

def create_panel_quad(ratio_name, width, height):
    """
    Create a single flat quad mesh of the given dimensions.
    Lies in the XY plane, normal pointing +Z (front/greeble face).
    Back face is at Z=0.

    Returns (obj, bm, face) — obj stays alive for the finalise step.
    """
    mesh = bpy.data.meshes.new(f"PanelMesh_{ratio_name}")
    obj  = bpy.data.objects.new(f"Panel_{ratio_name}", mesh)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    hw = width  / 2.0
    hh = height / 2.0

    bm = bmesh.new()
    verts = [
        bm.verts.new((-hw, -hh, 0)),
        bm.verts.new(( hw, -hh, 0)),
        bm.verts.new(( hw,  hh, 0)),
        bm.verts.new((-hw,  hh, 0)),
    ]
    bm.faces.new(verts)
    bm.to_mesh(mesh)
    bm.free()

    # Return to object mode so origin can be set
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # Origin at geometry centre — back face centre at Z=0
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

    # Re-enter edit mode and return bmesh face for pipeline
    bpy.ops.object.mode_set(mode='EDIT')
    bm2 = bmesh.from_edit_mesh(obj.data)
    bm2.faces.ensure_lookup_table()
    face = bm2.faces[0]
    face.select = True

    return obj, bm2, face


# ---------------------------------------------------------------------------
# FINALISE — join all geometry into one panel object
# ---------------------------------------------------------------------------

def finalise_panel(base_obj, output_col, panel_name, batch_seed, panel_seed,
                   layout_x=0.0, layout_y=0.0):
    """
    Join all objects in output_col together with the base quad into
    a single named panel mesh object, then move it to its layout position.

    Steps:
      1. Exit edit mode on base_obj
      2. Link base_obj into output_col (remove from scene root)
      3. Select every object in output_col, make base_obj active
      4. Join — produces one object inheriting base_obj transform
      5. Set origin to back face centre (bounding box centre for flat panel)
      6. Move to layout_x, layout_y so panels don't overlap in viewport
      7. Rename to panel_name
      8. Mark as Blender asset
    """
    # Exit edit mode
    bpy.ops.object.mode_set(mode='OBJECT')

    # Move base quad into output collection
    for c in base_obj.users_collection:
        c.objects.unlink(base_obj)
    output_col.objects.link(base_obj)

    # Select all objects in output collection
    bpy.ops.object.select_all(action='DESELECT')
    for o in output_col.objects:
        o.select_set(True)

    # Base quad is active so join inherits its coordinate space
    bpy.context.view_layer.objects.active = base_obj

    if len(output_col.objects) > 1:
        bpy.ops.object.join()

    # Joined result is now the active object
    panel_obj           = bpy.context.active_object
    panel_obj.name      = panel_name
    panel_obj.data.name = panel_name

    # Origin at bounding box centre — correct for flat quad with
    # greeble only on +Z side, places origin at back face centre
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

    # Move to grid layout position so panels don't overlap
    panel_obj.location.x = layout_x
    panel_obj.location.y = layout_y
    panel_obj.location.z = 0.0

    # Mark as Blender asset
    panel_obj.asset_mark()
    panel_obj.asset_data.description = (
        f"{panel_name} | batch_seed={batch_seed} | panel_seed={panel_seed}"
    )

    print(f"    [Finalise] '{panel_name}' → layout ({layout_x:.2f}, {layout_y:.2f}), asset marked.")
    return panel_obj


# ---------------------------------------------------------------------------
# PIPELINE
# ---------------------------------------------------------------------------

def run_pipeline(obj, bm, face, panel_seed, output_col):
    """
    Run all four steps on a single panel face.
    Steps 1-4 add geometry into output_col.
    Base quad (obj) is left untouched — finalise handles it.
    """
    rng = random.Random(panel_seed)

    box_regions, negative_space = run_step1(obj, bm, face, rng, MIN_BOX_SIZE)
    print(f"    [Step1] {len(box_regions)} boxes placed.")

    run_step2(obj, bm, face, box_regions, rng, output_col)
    print("    [Step2] done.")

    run_step3(obj, bm, face, box_regions, rng, output_col)
    print("    [Step3] done.")

    run_step4(obj, bm, face, negative_space, rng, output_col)
    print("    [Step4] done.")



# ---------------------------------------------------------------------------
# LAYOUT — position panels in a grid so they don't overlap
# ---------------------------------------------------------------------------

def compute_panel_position(panel_count, ratio_name, width, height):
    """
    Given a running panel count across all ratios, return an (x, y) world
    position that places the panel in a non-overlapping grid layout.

    Layout strategy:
      - Panels of each ratio get their own row (Y axis)
      - Within a row, panels are spaced along X by their width + LAYOUT_SPACING
      - Rows are separated on Y by the tallest panel height + LAYOUT_SPACING
    """
    ratio_names  = list(PANEL_SIZES.keys())
    ratio_index  = ratio_names.index(ratio_name)
    panel_index_in_ratio = panel_count % PANELS_PER_RATIO

    # X position — spaced by panel width + gap
    x = panel_index_in_ratio * (width + LAYOUT_SPACING)

    # Y position — each ratio gets its own row
    # Use the max height across all ratios for uniform row height
    max_height = max(h for _, (_, h) in PANEL_SIZES.items())
    y = ratio_index * (max_height + LAYOUT_SPACING)

    return x, y

# ---------------------------------------------------------------------------
# BATCH LOOP
# ---------------------------------------------------------------------------

def run_batch():
    batch_seed = BATCH_SEED if BATCH_SEED is not None else random.randint(0, 999999)
    print(f"\n{'='*60}")
    print(f"  Greeble Generator — Batch Production")
    print(f"  BATCH_SEED = {batch_seed}  (set BATCH_SEED={batch_seed} to reproduce)")
    print(f"{'='*60}\n")

    if DEBUG_MODE:
        print("  [Greeble] DEBUG_MODE=True — clearing scene.")
        clear_scene()

    validate_collections()

    timestamp   = time.strftime("%Y-%m-%d %H:%M:%S")
    start_index = get_next_output_index()
    panel_count = 0

    for ratio_name, (width, height) in PANEL_SIZES.items():
        print(f"\n--- Ratio: {ratio_name} ({width} x {height}) ---")

        for i in range(PANELS_PER_RATIO):
            panel_index  = panel_count + 1
            output_index = start_index + panel_count
            panel_seed   = batch_seed + panel_count
            panel_name   = f"GreeblePanel_{ratio_name}_{i+1:02d}"

            print(f"\n  Panel {panel_index:02d}/{PANELS_PER_RATIO * len(PANEL_SIZES)} "
                  f"— {panel_name}  (seed={panel_seed})")

            # Create output collection with metadata
            meta = {
                'batch_seed'  : batch_seed,
                'panel_seed'  : panel_seed,
                'panel_index' : output_index,
                'ratio'       : ratio_name,
                'timestamp'   : timestamp,
            }
            output_col = create_output_collection(output_index, panel_name, meta)

            # Compute non-overlapping layout position for this panel
            layout_x, layout_y = compute_panel_position(
                panel_count, ratio_name, width, height
            )

            # Create base quad — kept alive through to finalise
            base_obj, bm, face = create_panel_quad(ratio_name, width, height)

            # Steps 1-4 — all geometry goes into output_col
            run_pipeline(base_obj, bm, face, panel_seed, output_col)

            # Join everything including base quad into one named asset object
            # and move to its layout position
            finalise_panel(
                base_obj, output_col, panel_name,
                batch_seed, panel_seed,
                layout_x, layout_y
            )

            panel_count += 1
            print(f"  -> Saved to {output_col.name}")

    print(f"\n{'='*60}")
    print(f"  Batch complete — {panel_count} panels generated.")
    print(f"  Collections: {OUTPUT_PREFIX}{start_index:02d} "
          f"to {OUTPUT_PREFIX}{start_index + panel_count - 1:02d}")
    print(f"  BATCH_SEED was: {batch_seed}")
    print(f"{'='*60}\n")


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_batch()
