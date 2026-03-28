"""
steps/step2_algorithms/ca.py
Cellular automata scatter algorithm for Step 2.

Creates an in-memory 2D grid mapped to each box floor at
CA_RESOLUTION_MULTIPLIER x GRID_DIVISIONS resolution.
Seeds randomly across the whole grid, runs CA_GENERATIONS iterations,
then places one object per alive cell.

Active rule set is set by CA_RULE in config.py.
Each rule lives in its own file under ca_rules/.

To add a new rule:
  1. Create steps/step2_algorithms/ca_rules/my_rule.py with apply(grid, rows, cols)
  2. Import it below and add to CA_REGISTRY
  3. Set CA_RULE = "my_rule" in config.py
"""

import math
import mathutils
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import (
    CA_RULE,
    CA_GENERATIONS,
    CA_SEED_DENSITY,
    CA_RESOLUTION_MULTIPLIER,
    GRID_DIVISIONS,
)

from steps.step2_algorithms.ca_rules import conway, maze, coral

# ---------------------------------------------------------------------------
# CA RULE REGISTRY
# ---------------------------------------------------------------------------

CA_REGISTRY = {
    "conway" : conway,
    "maze"   : maze,
    "coral"  : coral,
}


# ---------------------------------------------------------------------------
# GRID HELPERS
# ---------------------------------------------------------------------------

def build_floor_bounds(floor_faces):
    """
    Return (u_min, u_max, v_min, v_max) bounding box of the floor faces
    in world XY space (panel is always XY-parallel).
    """
    xs = [v.co.x for f in floor_faces for v in f.verts]
    ys = [v.co.y for f in floor_faces for v in f.verts]
    return min(xs), max(xs), min(ys), max(ys)


def build_grid(rows, cols, seed_density, rng):
    """
    Create a 2D bool grid [rows][cols] seeded randomly.
    Each cell is alive with probability seed_density.
    """
    return [
        [rng.random() < seed_density for _ in range(cols)]
        for _ in range(rows)
    ]


def run_simulation(grid, rows, cols, rule_module, generations):
    """
    Run the CA simulation for the given number of generations.
    Returns the final grid state.
    """
    for gen in range(generations):
        grid = rule_module.apply(grid, rows, cols)
        alive_count = sum(grid[r][c] for r in range(rows) for c in range(cols))
        if alive_count == 0:
            print(f"      [CA] All cells dead at generation {gen+1} — stopping early.")
            break
    return grid


def cell_to_world(row, col, rows, cols, x_min, x_max, y_min, y_max, floor_z):
    """
    Convert a grid cell (row, col) to world XY position on the box floor.
    Cell centres are evenly distributed across the floor bounds.
    """
    cell_w = (x_max - x_min) / cols
    cell_h = (y_max - y_min) / rows

    x = x_min + (col + 0.5) * cell_w
    y = y_min + (row + 0.5) * cell_h

    return mathutils.Vector((x, y, floor_z))


# ---------------------------------------------------------------------------
# PUBLIC ENTRY POINT
# ---------------------------------------------------------------------------

def run(box_regions, rng, staging_col, source_objects,
        compute_floor_centre, compute_floor_area, place_copy):
    """
    CA scatter across all box floors.

    For each box:
      1. Build floor bounds and grid dimensions
      2. Seed grid randomly across whole floor
      3. Run CA simulation using active CA_RULE
      4. Place one object per alive cell at cell world position
    """
    rule_module = CA_REGISTRY.get(CA_RULE)
    if rule_module is None:
        print(f"      [CA] ERROR: unknown rule '{CA_RULE}'. "
              f"Available: {list(CA_REGISTRY.keys())}")
        return 0

    print(f"      [CA] Rule={CA_RULE}  Generations={CA_GENERATIONS}  "
          f"Seed density={CA_SEED_DENSITY}")

    total_placed = 0

    for box in box_regions:
        floor_faces = box.get('floor_faces', [])
        if not floor_faces:
            continue

        # Floor bounds in world XY
        x_min, x_max, y_min, y_max = build_floor_bounds(floor_faces)

        # Floor Z — use centre of floor faces
        floor_centre = compute_floor_centre(floor_faces)
        floor_z      = floor_centre.z if floor_centre else 0.0

        # Grid dimensions — 2x Step 1 resolution across the box
        box_cols = int((x_max - x_min) / ((x_max - x_min) / (GRID_DIVISIONS * CA_RESOLUTION_MULTIPLIER))) 
        box_rows = int((y_max - y_min) / ((y_max - y_min) / (GRID_DIVISIONS * CA_RESOLUTION_MULTIPLIER)))
        # Simplified: always use GRID_DIVISIONS * multiplier per unit
        span_x   = x_max - x_min
        span_y   = y_max - y_min
        cell_size = 1.0 / (GRID_DIVISIONS * CA_RESOLUTION_MULTIPLIER)
        cols     = max(2, int(span_x / cell_size))
        rows     = max(2, int(span_y / cell_size))

        print(f"      [CA] Box grid: {rows}x{cols}  floor_area={compute_floor_area(floor_faces):.4f}")

        # Seed and simulate
        grid = build_grid(rows, cols, CA_SEED_DENSITY, rng)
        grid = run_simulation(grid, rows, cols, rule_module, CA_GENERATIONS)

        # Place one object per alive cell
        box_placed = 0
        for r in range(rows):
            for c in range(cols):
                if grid[r][c]:
                    pos    = cell_to_world(r, c, rows, cols,
                                           x_min, x_max, y_min, y_max, floor_z)
                    source = rng.choice(source_objects)
                    place_copy(source, pos, staging_col)
                    box_placed  += 1
                    total_placed += 1

        print(f"      [CA] {box_placed} objects placed in box.")

    return total_placed
