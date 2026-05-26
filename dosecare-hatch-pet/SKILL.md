---
name: dosecare-hatch-pet
description: Create, repair, validate, visually QA, and package DoseCare companion pets using a painterly 8x9 animated spritesheet. This project-local fork keeps the hatch-pet deterministic atlas pipeline while replacing Codex work-state rows with DoseCare growth, care, mood, reward, and rest states.
---

# DoseCare Hatch Pet

## Overview

Create a DoseCare养成类桌宠 from a text concept, reference image, or both. This is a project-local fork of `hatch-pet`: it keeps the proven fixed atlas geometry and deterministic image-processing scripts, but changes the art direction and row semantics for DoseCare.

When the user provides reference images and does not explicitly ask for a different style, the reference images are the source of truth. Preserve the uploaded pet's character design, proportions, colors, markings, line weight, material/rendering style, and overall cuteness. The `painterly` default is only a sprite-readability and extraction constraint in that case; it must not redesign the pet into a different painterly mascot.

Use `$imagegen` for visual generation. The deterministic scripts own layout guides, chroma-key extraction, frame inspection, atlas composition, validation, contact sheets, and GIF previews.

## Fixed First-Stage Contract

This first stage intentionally keeps the original atlas shape:

- Format: PNG or WebP.
- Atlas: `1536x1872`.
- Grid: 8 columns x 9 rows.
- Cell: `192x208`.
- Unused cells after each row's used frame count must be fully transparent.
- Style preset default: `painterly`.

## DoseCare Rows

| Row | State | Frames | Purpose |
| ---: | --- | ---: | --- |
| 0 | `idle` | 6 | Calm companion loop: breathing, blink, subtle tail/head motion. |
| 1 | `happy` | 6 | On-time-care success: bright expression, small bounce, tail wag. |
| 2 | `sad` | 6 | Missed-care or low mood: drooping ears/head, slow motion. |
| 3 | `greeting` | 4 | Home open or tap: friendly paw raise or lean-in greeting. |
| 4 | `jumping` | 5 | Tap feedback or light celebration: anticipation, lift, peak, settle. |
| 5 | `sick` | 6 | Low health: curled/slumped, tired eyes, weak motion. |
| 6 | `levelup` | 8 | Growth milestone: proud joyful upgrade celebration. |
| 7 | `eating` | 6 | Care reward: holds or nibbles a small treat, satisfied finish. |
| 8 | `sleeping` | 6 | Night or long-idle rest: closed eyes, slow breathing, tiny twitch. |

## Art Direction

Use a soft painterly mascot style:

- warm simplified brush texture
- rounded cute proportions, large readable face, short limbs
- stable palette and identity across every row
- clean readable edges for chroma-key extraction
- detail level that still reads inside a `192x208` cell

Reference-image priority:

- If `--reference` is provided and `--style-notes` is empty, match the reference image's own visual style instead of imposing a new house style.
- Preserve the reference pet's silhouette, head/body ratio, line/edge treatment, palette, markings, eye shape, paw shape, and material feel.
- Only change pose, expression, and state action for animation.
- Do not reinterpret a flat/vector/plush/3D/sticker reference as painterly unless the user explicitly asks for that transformation.

Avoid scene backgrounds, text, UI symbols, speech bubbles, floor shadows, glow rings, loose confetti, detached sparkles, floating icons, or chroma-key-adjacent colors inside the pet.

`levelup` may use a tiny crown, ribbon, badge, or star accents only when attached to, touching, or overlapping the pet silhouette.

## Workflow

1. Prepare the run:

```bash
SKILL_DIR="/Users/n14637/Desktop/YY-Git/microgame/Project/DoseCare/.agents/skills/dosecare-hatch-pet"
python "$SKILL_DIR/scripts/prepare_pet_run.py" \
  --pet-name "<Name>" \
  --description "<one sentence>" \
  --reference /absolute/path/to/reference.png \
  --output-dir /absolute/path/to/run \
  --pet-notes "<stable pet description>" \
  --style-preset painterly \
  --force
```

2. Inspect ready jobs:

```bash
jq '.jobs[] | {id, kind, status, depends_on, prompt_file, retry_prompt_file, input_images, output_path}' /absolute/path/to/run/imagegen-jobs.json
```

3. Generate visual jobs with `$imagegen`:

- Generate `base` first.
- Copy the selected base into `decoded/base.png`.
- Copy `decoded/base.png` to `references/canonical-base.png`.
- Generate each row independently using its row prompt, canonical base, original references, and matching layout guide.
- Copy each selected row strip into `decoded/<state>.png`.
- Mark each completed job in `imagegen-jobs.json`.

Do not locally synthesize missing visual rows. Every row is its own generated animation strip.

4. Run deterministic processing:

```bash
RUN_DIR=/absolute/path/to/run
mkdir -p "$RUN_DIR/final" "$RUN_DIR/qa"

python "$SKILL_DIR/scripts/extract_strip_frames.py" \
  --decoded-dir "$RUN_DIR/decoded" \
  --output-dir "$RUN_DIR/frames" \
  --states all \
  --method auto

python "$SKILL_DIR/scripts/inspect_frames.py" \
  --frames-root "$RUN_DIR/frames" \
  --json-out "$RUN_DIR/qa/review.json" \
  --require-components

python "$SKILL_DIR/scripts/compose_atlas.py" \
  --frames-root "$RUN_DIR/frames" \
  --output "$RUN_DIR/final/spritesheet.png" \
  --webp-output "$RUN_DIR/final/spritesheet.webp"

python "$SKILL_DIR/scripts/validate_atlas.py" \
  "$RUN_DIR/final/spritesheet.webp" \
  --json-out "$RUN_DIR/final/validation.json"

python "$SKILL_DIR/scripts/make_contact_sheet.py" \
  "$RUN_DIR/final/spritesheet.webp" \
  --output "$RUN_DIR/qa/contact-sheet.png"

python "$SKILL_DIR/scripts/render_animation_previews.py" \
  --frames-root "$RUN_DIR/frames" \
  --output-dir "$RUN_DIR/qa/previews"
```

If previews show extraction-induced size popping and the original strip has stable slots, rerun extraction with `--method stable-slots`, then rerun inspection, composition, validation, contact sheet, and previews.

5. Package:

```bash
RUN_DIR=/absolute/path/to/run
PET_ID=$(jq -r '.pet_id' "$RUN_DIR/pet_request.json")
DISPLAY_NAME=$(jq -r '.display_name' "$RUN_DIR/pet_request.json")
DESCRIPTION=$(jq -r '.description' "$RUN_DIR/pet_request.json")
PET_DIR="${CODEX_HOME:-$HOME/.codex}/pets/$PET_ID"
mkdir -p "$PET_DIR"
cp "$RUN_DIR/final/spritesheet.webp" "$PET_DIR/spritesheet.webp"
jq -n --arg id "$PET_ID" --arg displayName "$DISPLAY_NAME" --arg description "$DESCRIPTION" \
  '{id: $id, displayName: $displayName, description: $description, spritesheetPath: "spritesheet.webp"}' \
  > "$PET_DIR/pet.json"
```

## QA Rules

- `qa/review.json` and `final/validation.json` must have no errors.
- The contact sheet must show the same pet identity, style, palette, silhouette, face, proportions, and props across all 9 rows.
- Motion previews must not show unintended size popping, blank frames, guide marks, detached effects, shadows, glows, scenery, or row semantics drifting into another state.
- `levelup` should read as a joyful upgrade animation, not a generic jump or a cloud of effects.
- `idle` and `sleeping` must be visually distinct.

## Repair

Repair the smallest failing scope. Regenerate only the failed row when the row strip is semantically wrong, clipped, inconsistent, or visually noisy. Use `stable-slots` only for extraction-induced motion popping when the source strip itself is already stable.
