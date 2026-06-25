---
name: game-asset-cutouts
description: Use when turning a design image, concept art, UI mockup, or hand-drawn game scene into isolated game asset sprites, especially when exhaustive object recognition, no-grid contact sheets, white/black matte sheets, transparent PNG cutouts, or an extracted asset manifest are needed.
---

# Game Asset Cutouts

## Overview

Use this skill to convert a design image into isolated transparent game sprites. The workflow is: identify as many visible objects as practical, generate same-layout white/black matte contact sheets in the source art style, then recover alpha with the bundled script.

## Main Workflow

1. Inspect the source design and write an asset inventory before generating.
2. Group every recognizable item into buckets:
   - Architecture: houses, doors, windows, chimneys, stairs, porches.
   - Crops and tiles: each crop patch, crop variants, soil beds, field fences.
   - Characters and animals: pets, livestock, birds, insects, small creatures.
   - Props: signs, boards, benches, bridges, buckets, lamps, chests, pots, tools.
   - Nature: trees, shrubs, flowers, stones, water pieces, lily pads.
   - Background pieces when useful: clouds, mountain layers, forest strips, paths, fences.
3. Create a first-pass prompt that explicitly lists the inventory. Ask for “as many as can fit without overlap”; if the list is too large, split into multiple sheets by bucket.
4. Generate one image split into two equal panels:
   - Top panel: pure white `#ffffff`.
   - Bottom panel: pure black `#000000`.
   - Both panels must contain identical sprites at identical positions and sizes.
5. Save the generated sheet into the project, crop the panels into `*-white.png` and `*-black.png`, then run `scripts/extract_game_assets.py`.
6. Inspect `assets-rgba.png` and `manifest.json`.
7. Do a missing-object pass against the inventory. If important objects are missing, generate another white/black sheet for the missing bucket and extract again.

## Generation Prompt Pattern

Use this pattern with the image generation tool:

```text
Use case: background-extraction
Asset type: exhaustive game sprite contact sheet
Input image: the provided design image is the style and object reference.

Primary request: Create clean isolated game sprites in the same hand-drawn style as the source image. Identify and include as many recognizable objects as practical from the design. Arrange them as a no-grid contact sheet. Do not include labels, numbers, text, grid lines, tile outlines, or watermarks.

Required output layout: one single image split into two equal horizontal panels. Top panel has a perfectly pure white (#ffffff) background. Bottom panel has a perfectly pure black (#000000) background. Both panels must contain the exact same sprites at the exact same size and positions; only the background color differs.

Inventory to include:
- Architecture: [...]
- Crops/plots: [...]
- Animals/characters: [...]
- Props: [...]
- Nature/background pieces: [...]

Sprite constraints: isolate every object with generous padding; no overlap; clean silhouettes; no cast shadows; no contact shadows; no floor plane.
Style: preserve the original art direction, palette, brush texture, soft shading, and cozy game-ready sprite feel.
Background constraints: perfectly flat solid color only; no gradients, texture, lighting variation, shadow, reflection, border, or scene ground.
```

## Extraction Command

```bash
python /Users/n14637/.agents/skills/game-asset-cutouts/scripts/extract_game_assets.py \
  --white path/to/contact-sheet-white.png \
  --black path/to/contact-sheet-black.png \
  --out path/to/extracted-assets \
  --padding 10 \
  --min-area 256 \
  --transparent-threshold 10 \
  --alpha-threshold 18 \
  --min-component-width 16 \
  --min-component-height 16
```

Outputs:

- `assets-rgba.png`: recovered transparent full sheet.
- `asset-001.png`, `asset-002.png`, ...: individual transparent PNGs.
- `manifest.json`: filenames, bounding boxes, width, and height.

## Quality Rules

- Reject generated sheets if the white and black panels do not align.
- Reject textured, gradient, shadowed, or off-white/off-black backgrounds.
- If an object is missing, generate a supplemental sheet for that object bucket instead of overloading one sheet.
- If separate objects merge, regenerate with more padding or split the sheet.
- If tiny props disappear, rerun extraction with smaller `--min-area` and component dimensions.
- If a panel seam appears as an asset, rerun extraction with larger `--min-component-height`.
- Keep a written inventory next to outputs when doing exhaustive extraction, so missing-object passes are deliberate.

## Script Notes

`scripts/extract_game_assets.py` uses Pillow and NumPy. It recovers alpha from matching white/black matte renders and splits visible pixels into 8-connected components. It is deterministic once the matte sheets exist.
