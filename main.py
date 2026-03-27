"""
Greeble Generator — main.py
Batch production entry point. Pure orchestration — all settings in config.py.

Generates greeble panels into numbered GREEBLE_OUTPUT_XX collections,
ready for Blender asset library curation and Gumroad distribution.

Each panel is a single joined mesh object with:
  - Greebled front face (Steps 1-4)
  - Clean flat back face (base quad)
  - Origin at back face centre
  - Named GreeblePanel_{Ratio}_{index:02d}

Blender 4.x | Run from Blender Text Editor
"""

import bpy
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

from config import (
    BATCH_SEED,
    DEBUG_MODE,
    PANELS_PER_RATIO,
    PANEL_SIZES,
    OUTPUT_PREFIX,
    MIN_BOX_SIZE,
)
from scene  import (
    clear_scene,
    validate_collections,
    get_next_output_index,
    create_output_collection,
)
from panel  import create_panel_quad, compute_panel_position, finalise_panel
from steps.step1 import run_step1
from steps.step2 import run_step2
from steps.step3 import run_step3
from steps.step4 import run_step4


# ---------------------------------------------------------------------------
# PIPELINE
# ---------------------------------------------------------------------------

def run_pipeline(obj, bm, face, panel_seed, output_col):
    """Run all four steps on a single panel face."""
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
# BATCH LOOP
# ---------------------------------------------------------------------------

def run_batch():
    batch_seed = BATCH_SEED if BATCH_SEED is not None else random.randint(0, 999999)

    print(f"\n{'='*60}")
    print(f"  Greeble Generator — Batch Production")
    print(f"  DEBUG_MODE       = {DEBUG_MODE}")
    print(f"  BATCH_SEED       = {batch_seed}  (set BATCH_SEED={batch_seed} to reproduce)")
    print(f"  PANELS_PER_RATIO = {PANELS_PER_RATIO}")
    print(f"  Total panels     = {PANELS_PER_RATIO * len(PANEL_SIZES)}")
    print(f"{'='*60}\n")

    if DEBUG_MODE:
        print("  [Main] DEBUG_MODE=True — clearing scene.")
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

            # Layout position — non-overlapping grid
            layout_x, layout_y = compute_panel_position(
                panel_count, ratio_name, width, height
            )

            # Create base quad
            base_obj, bm, face = create_panel_quad(ratio_name, width, height)

            # Run pipeline — steps deposit geometry into output_col
            run_pipeline(base_obj, bm, face, panel_seed, output_col)

            # Join everything into one named asset object
            finalise_panel(
                base_obj, output_col, panel_name,
                batch_seed, panel_seed,
                layout_x, layout_y
            )

            panel_count += 1
            print(f"  -> {output_col.name}")

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
