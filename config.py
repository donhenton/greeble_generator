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

# ---------------------------------------------------------------------------
# STEP 2 TUNING
# ---------------------------------------------------------------------------

# Active Step 2 algorithm — must match a key in the step2 registry
# Available: "growth_front", "poisson" (stub), "ca"
STEP2_ALGORITHM = "ca"

# Active CA rule — only used when STEP2_ALGORITHM = "ca"
# Available: "conway", "maze", "coral"
CA_RULE = "maze"

# CA simulation settings
CA_GENERATIONS   = 4     # iterations before reading alive cells
CA_SEED_DENSITY  = 0.35   # fraction of cells alive at start (0.0-1.0)
# Grid resolution multiplier relative to GRID_DIVISIONS
# 2 = twice the Step 1 grid resolution across the box floor
CA_RESOLUTION_MULTIPLIER = 2

# Object count scaling — count = clamp(int(floor_area / DENSITY), MIN, MAX)
STEP2_DENSITY     = 0.08    # floor area per object (lower = more objects)
STEP2_MIN_OBJECTS = 5       # minimum objects per box regardless of area
STEP2_MAX_OBJECTS = 15      # maximum objects per box regardless of area

# Growth front step distance — how far each new object steps from an existing one
STEP2_GROWTH_STEP = 0.25    # Blender units

# ---------------------------------------------------------------------------
# STEP 3 — SUB-PANEL EXTRUSIONS
# ---------------------------------------------------------------------------

# Preset extrusion depths — positive only (+Z proud)
# Sub-panels are always raised to avoid competing with recessed boxes
PANEL_DEPTHS    = [0.02, 0.04, 0.06, 0.08]

# Fraction of negative space cells that receive a sub-panel (0.0-1.0)
PANEL_COVERAGE  = 0.6

# Sub-panel rectangle size in grid cells per side (min/max)
PANEL_MIN_CELLS = 2
PANEL_MAX_CELLS = 4
