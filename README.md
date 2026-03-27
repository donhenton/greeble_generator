# Greeble Generator — v02

Blender 4.x | Batch Production Pipeline | Asset Library Output

## Overview

Generates 20 pre-greebled panel assets (10 x Square, 10 x 3:4 ratio)
into numbered GREEBLE_OUTPUT_XX collections, ready for Blender asset
library curation and Gumroad distribution.

## File Layout

```
main.py
steps/
    __init__.py
    step1.py   — Box placement (attractor/repeller)  ✅ Implemented
    step2.py   — STUB: growth diffusion scatter (GREEBLE2)
    step3.py   — STUB: connectors between boxes
    step4.py   — STUB: interstitial scatter (GREEBLE4)
```

## Setup

### Required Collections
Create these collections in your production scene before running:

| Collection | Purpose |
|------------|---------|
| `GREEBLE2` | Flat objects scattered on box floors (Step 2) |
| `GREEBLE4` | Interstitial objects in negative space (Step 4) |

Steps 2 and 4 skip gracefully with a warning if their collection is
missing or empty.

### Running the Batch
1. Open `main.py` in Blender's Text Editor
2. Open all `steps/*.py` files in additional Text Editor slots
3. Set `main.py` as active
4. Press **Run Script**

## Output

Each run produces:
- 20 panels across 2 aspect ratios (Square, 3:4)
- Collections named `GREEBLE_OUTPUT_01` through `GREEBLE_OUTPUT_20`
- Each collection tagged with metadata (batch seed, panel seed, ratio, timestamp)
- Each object marked as a Blender asset, ready for library curation

Collections increment automatically — running again produces
`GREEBLE_OUTPUT_21` through `GREEBLE_OUTPUT_40`, and so on.

## Reproducibility

```python
# In main.py — set to reproduce a specific batch
BATCH_SEED = None       # None = fresh results every run
BATCH_SEED = 482910     # Set a value to reproduce that exact batch
```

The batch seed is always printed to the console after each run.
Note it down if you produce a batch you want to reproduce later.

## Settings

### main.py
| Constant | Purpose |
|----------|---------|
| `BATCH_SEED` | None for fresh, integer to reproduce |
| `PANELS_PER_RATIO` | Panels generated per aspect ratio (default 10) |
| `MIN_BOX_SIZE` | Shared minimum box dimension |
| `PANEL_SIZES` | Aspect ratio definitions |

### steps/step1.py
| Constant | Purpose |
|----------|---------|
| `ATTRACTOR_COUNT` | Attractors per face |
| `ATTRACTOR_STRENGTH` | Pull force scale |
| `REPELLER_STRENGTH` | Push force between boxes |
| `ITERATIONS` | Max simulation steps |
| `CONVERGENCE_DELTA` | Early stop threshold |
| `AREA_BOX_COUNT` | Area thresholds → box count |
| `BOX_SIZE_MIN_FRAC` | Min box size as fraction of short edge |
| `BOX_SIZE_MAX_FRAC` | Max box size as fraction of short edge |

## Step Status

| Step | Status | Notes |
|------|--------|-------|
| Step 1 — Box placement | ✅ Implemented | Attractor/repeller sim |
| Step 2 — Box greeble fill | 🔲 Stub | Growth diffusion model |
| Step 3 — Connectors | 🔲 Stub | Coplanar, joint covers |
| Step 4 — Interstitial scatter | 🔲 Stub | Overlaps Step 3 intentionally |

## Product Architecture

```
Engine (this script)
    └── Collection Packs (GREEBLE2 + GREEBLE4 object sets)
            └── Generated Panel Libraries (asset .blend files)
                    └── Placement Guide PDF (ships with every tier)
```
