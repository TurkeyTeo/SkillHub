# QA Rubric

Do not accept a DoseCare pet atlas until all checks pass.

## Geometry

- Exact `1536x1872` dimensions.
- 8 columns x 9 rows.
- Each frame fits inside its `192x208` cell.
- Unused cells are transparent.
- Fully transparent atlas pixels do not retain non-zero RGB residue after export.
- `qa/review.json` has no errors.
- `frames/frames-manifest.json` records component extraction for production rows unless `stable-slots` was intentionally chosen after visual inspection.

## Character Consistency

- Same pet identity across every row.
- Same silhouette, proportions, face, markings, palette, material, and edge treatment.
- The painterly style stays warm, rounded, clean, and readable at pet size.
- No frame introduces a new unintended character, scene object, readable text, UI icon, or environment.

## Animation Completeness

- Each row uses the exact expected number of frames.
- The first and last frames can loop without an obvious pop.
- State-specific actions are recognizable at `192x208`.
- Poses are generated animation variants, not repeated copies of the same source image.
- Preview GIFs do not show unintended size popping, extraction-induced baseline jumps, blank frames, or wrong row semantics.

## DoseCare State Fitness

- `idle` is calm and low-distraction; it should not read as happy, greeting, jumping, eating, or sleeping.
- `happy` reads as care success and is distinct from `levelup`.
- `sad` and `sick` are distinct: sad is low mood; sick is low health and weaker body language.
- `greeting` reads as a friendly tap/home-open interaction.
- `jumping` reads as playful feedback without large detached effects.
- `levelup` reads as a special upgrade celebration, not only a generic jump; attached crown/ribbon/star accents are allowed when clean.
- `eating` shows a simple close-held treat and satisfied motion.
- `sleeping` has closed eyes and slow resting motion, with no floating Z letters or scenery.

## Visual Safety

- No speech bubbles, text, level numbers, red crosses, app UI, medical symbols, loose confetti, detached sparkles, floor shadows, glow rings, scenery, or chroma-key-colored effects.
- No important detail is too small to read.
- No frame is clipped by the cell.
- Contact sheets must show whole sprite poses inside cells, not cropped tiles from a larger reference image.
- Used cells must not have white or opaque rectangular backgrounds unless the pet intentionally fills the whole cell and the user accepts that tradeoff.
- The chroma key must be visually absent from the character. If extraction removes character regions, choose a different key and regenerate the affected base/rows.

## Repair Policy

Repair the smallest failing scope first:

1. One row.
2. The base image only when identity or style is fundamentally wrong.
3. Full atlas regeneration only when identity or layout is broadly broken.

For extraction-induced motion popping, rerun extraction with `stable-slots` before regenerating the row, but only when the source strip itself has stable scale and placement.
