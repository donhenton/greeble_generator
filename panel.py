"""
panel.py
Panel quad creation, viewport layout positioning, and finalisation.
Finalise joins all step geometry + base quad into one named asset object.
"""

import bpy
import bmesh
from config import (
    PANEL_SIZES,
    PANELS_PER_RATIO,
    LAYOUT_SPACING,
    GREEBLE_BASE_MATERIAL,
    GREEBLE2_COLLECTION,
    GREEBLE4_COLLECTION,
)


def create_panel_quad(ratio_name, width, height):
    """
    Create a single flat quad mesh of the given dimensions.
    Lies in the XY plane, normal pointing +Z (front/greeble face).
    Back face sits at Z=0.

    Returns (obj, bm, face) — obj stays alive through to finalise_panel().
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

    # Assign GREEBLE_BASE material to back face if available
    mat = bpy.data.materials.get(GREEBLE_BASE_MATERIAL)
    if mat:
        mesh.materials.append(mat)
    else:
        print(f"  [Panel] WARNING: material '{GREEBLE_BASE_MATERIAL}' not found — "
              f"base face will be unassigned.")

    # Set origin to geometry centre (back face centre at Z=0)
    bpy.ops.object.mode_set(mode='OBJECT')
    for o in bpy.context.selected_objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

    # Enter edit mode and return bmesh face for pipeline
    bpy.ops.object.mode_set(mode='EDIT')
    bm2 = bmesh.from_edit_mesh(obj.data)
    bm2.faces.ensure_lookup_table()
    face = bm2.faces[0]
    face.select = True

    return obj, bm2, face


def compute_panel_position(panel_count, ratio_name, width, height):
    """
    Return an (x, y) world position for the panel in the viewport grid layout.

    Layout:
      - Each ratio gets its own row on the Y axis
      - Within a row, panels step along X by width + LAYOUT_SPACING
      - Rows are separated by the tallest panel height + LAYOUT_SPACING
    """
    ratio_names          = list(PANEL_SIZES.keys())
    ratio_index          = ratio_names.index(ratio_name)
    panel_index_in_ratio = panel_count % PANELS_PER_RATIO

    x = panel_index_in_ratio * (width + LAYOUT_SPACING)

    max_height = max(h for _, (_, h) in PANEL_SIZES.items())
    y = ratio_index * (max_height + LAYOUT_SPACING)

    return x, y


def finalise_panel(base_obj, staging_col, output_col, panel_name,
                   batch_seed, panel_seed, layout_x=0.0, layout_y=0.0):
    """
    Join all objects in staging_col (this panel only) with the base quad
    into a single named mesh object, then move it into output_col.

    Using a per-panel staging collection ensures the join only touches
    this panel's geometry — not panels already sitting in GREEBLE_OUTPUT.

    Steps:
      1. Exit edit mode
      2. Link base_obj into staging_col
      3. Select all objects in staging_col, make base_obj active
      4. Join into one mesh
      5. Set origin to bounding box centre (back face centre)
      6. Move to layout position
      7. Rename object and mesh data
      8. Move from staging_col into output_col (GREEBLE_OUTPUT)
      9. Remove staging_col (now empty)
     10. Mark as Blender asset
    """
    bpy.ops.object.mode_set(mode='OBJECT')

    # Link base quad into this panel's staging collection
    for c in base_obj.users_collection:
        c.objects.unlink(base_obj)
    staging_col.objects.link(base_obj)

    # Select only this panel's objects
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for o in staging_col.objects:
        o.select_set(True)

    # Base quad active — join inherits its coordinate space
    bpy.context.view_layer.objects.active = base_obj

    if len(list(staging_col.objects)) > 1:
        bpy.ops.object.join()

    panel_obj           = bpy.context.active_object
    panel_obj.name      = panel_name
    panel_obj.data.name = panel_name

    # Origin at bounding box centre — back face centre for flat panel
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

    # Move to non-overlapping grid position
    panel_obj.location.x = layout_x
    panel_obj.location.y = layout_y
    panel_obj.location.z = 0.0

    # Move panel from staging into GREEBLE_OUTPUT
    for c in panel_obj.users_collection:
        c.objects.unlink(panel_obj)
    output_col.objects.link(panel_obj)

    # Clean up empty staging collection
    bpy.data.collections.remove(staging_col)

    # Mark as Blender asset
    panel_obj.asset_mark()
    panel_obj.asset_data.description = (
        f"{panel_name} | batch_seed={batch_seed} | panel_seed={panel_seed}"
    )

    print(f"    [Panel] '{panel_name}' -> ({layout_x:.2f}, {layout_y:.2f}), asset marked.")
    return panel_obj
