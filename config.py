"""
config.py
All tunable parameters for the Greeble Generator in one place.
Edit this file to change batch behaviour, panel sizes, and step tuning.
"""

# ---------------------------------------------------------------------------
# BATCH CONTROL
# ---------------------------------------------------------------------------

# Set to an integer to reproduce a specific batch, or None for fresh results
# e.g. BATCH_SEED = 482910
BATCH_SEED = None

# Number of panels generated per aspect ratio
# SET TO 2 FOR TESTING — restore to 10 for production
PANELS_PER_RATIO = 2

# Debug mode — when True, clears all objects and GREEBLE_OUTPUT_ collections
# before each run. GREEBLE2 and GREEBLE4 collections are preserved.
# Set to False for production runs (accumulates output collections).
DEBUG_MODE = True

# ---------------------------------------------------------------------------
# PANEL DIMENSIONS
# ---------------------------------------------------------------------------

# Base panel dimensions in Blender units (user scales to fit in their model)
PANEL_SIZES = {
    'Square': (2.0, 2.0),
    '3x4':    (2.0, 2.667),   # 3:4 ratio, 2 units on short side
}

# ---------------------------------------------------------------------------
# LAYOUT
# ---------------------------------------------------------------------------

# Extra gap between panels in the viewport grid layout
# Increase if panels overlap when running at full production count
LAYOUT_SPACING = 1.0

# ---------------------------------------------------------------------------
# SHARED GEOMETRY
# ---------------------------------------------------------------------------

# Minimum box dimension — shared across all steps
# Step 2 uses this to ensure boxes are large enough to fill with greeble
MIN_BOX_SIZE = 0.15

# ---------------------------------------------------------------------------
# COLLECTIONS
# ---------------------------------------------------------------------------

# User-curated greeble source collections
GREEBLE2_COLLECTION = "GREEBLE2"   # flat objects for box floors (Step 2)
GREEBLE4_COLLECTION = "GREEBLE4"   # interstitial objects for negative space (Step 4)

# Single output collection — all panels land here
OUTPUT_COLLECTION = "GREEBLE_OUTPUT"

# Material applied to the base quad back face
# Create a material with this exact name in your production scene
GREEBLE_BASE_MATERIAL = "GREEBLE_BASE"

# ---------------------------------------------------------------------------
# STEP 1 TUNING
# ---------------------------------------------------------------------------

# Grid subdivision — NxN quads across the panel face
# Higher = finer grid, more box size variation, more geometry
GRID_DIVISIONS = 10

# How deep boxes are recessed into the panel (-Z direction, Blender units)
BOX_EXTRUDE_DEPTH = 0.08

# Attractor/repeller simulation
ATTRACTOR_COUNT    = 4      # attractors scattered per panel
ATTRACTOR_STRENGTH = 1.2    # pull force scale (inverse-square)
REPELLER_STRENGTH  = 1.0    # push force between box centres
ITERATIONS         = 100    # max simulation steps
CONVERGENCE_DELTA  = 0.0005 # stop early if max movement drops below this
STEP_SIZE          = 0.04   # movement scale per iteration

# Box size in grid cells per side (random within this range)
BOX_MIN_CELLS = 2
BOX_MAX_CELLS = 4

# Face area (Blender units²) → target box count
AREA_BOX_COUNT = [
    (0.0,  2),
    (1.0,  3),
    (2.5,  4),
    (4.5,  5),
]
