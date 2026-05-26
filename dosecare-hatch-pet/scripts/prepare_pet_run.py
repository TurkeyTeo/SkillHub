#!/usr/bin/env python3
"""Create a DoseCare companion pet run folder, prompts, and imagegen job manifest."""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image
from PIL import ImageDraw

ATLAS = {"columns": 8, "rows": 9, "cell_width": 192, "cell_height": 208}
ATLAS["width"] = ATLAS["columns"] * ATLAS["cell_width"]
ATLAS["height"] = ATLAS["rows"] * ATLAS["cell_height"]

ROWS = [
    ("idle", 0, 6, "calm resting, breathing, blinking, and small tail motion"),
    ("happy", 1, 6, "pleased on-time-care reaction"),
    ("sad", 2, 6, "low mood or missed-care reaction"),
    ("greeting", 3, 4, "friendly homepage or tap greeting"),
    ("jumping", 4, 5, "playful tap feedback or light celebration"),
    ("sick", 5, 6, "low health or repeated missed-care state"),
    ("levelup", 6, 8, "growth milestone and upgrade celebration"),
    ("eating", 7, 6, "reward snack after completed care"),
    ("sleeping", 8, 6, "night or long-idle rest loop"),
]

STATE_PROMPTS = {
    "idle": "Calm companion loop: gentle breathing, soft blink, slight head or tail motion, and warm relaxed presence.",
    "happy": "Happy care-success loop: bright eyes, lifted posture, quick tail wag, tiny bounce, and pleased expression.",
    "sad": "Sad missed-care loop: drooping ears or head, lowered posture, slow small motion, and tender disappointed expression.",
    "greeting": "Friendly greeting loop: raise and lower a paw or lean forward as if saying hello after the user opens the home screen or taps the pet.",
    "jumping": "Playful jump loop: anticipation, lift, airborne peak, descent, and soft settle through body height.",
    "sick": "Unwell low-health loop: curled or slumped posture, tired eyes, small attached sweat or warmth marks if needed, and weak motion.",
    "levelup": "Level-up loop: proud growth celebration with joyful pose change, upward energy, and optional attached crown, ribbon, or body-touching star accents.",
    "eating": "Reward snack loop: hold or nibble a tiny treat, chew gently, and end with a satisfied expression.",
    "sleeping": "Sleeping loop: curled or loaf resting pose, slow breathing, closed eyes, and a tiny ear or tail twitch.",
}

STATE_REQUIREMENTS = {
    "idle": [
        "CRITICAL: idle is the low-distraction baseline state and the first frame is also used as the reduced-motion static pet.",
        "Use only subtle idle motion: gentle breathing, a tiny blink, a slight head or body bob, a very small material sway, or another quiet motion that fits the pet persona.",
        "Keep the pet essentially in the same pose, facing direction, silhouette, markings, palette, and prop state across all 6 frames.",
        "Idle variation must stay calm but still read as animation; do not repeat effectively identical copies across the loop.",
        "Do not show greeting, walking, running, jumping, talking, eating, sleeping, emotional reactions, large gestures, item interactions, or new props.",
        "Feet, base, body, or object anchor should remain planted or nearly planted.",
        "The first and last frames should be very close visually so the loop feels calm and does not pop.",
    ],
    "greeting": [
        "Show the greeting through paw, hand, wing, or limb pose only.",
        "Do not draw wave marks, motion arcs, lines, sparkles, symbols, or floating effects around the gesture.",
    ],
    "jumping": [
        "Show the jump through pose and vertical body position only: anticipation, lift, airborne peak, descent, settle.",
        "Do not draw ground shadows, contact shadows, drop shadows, oval shadows, landing marks, dust, smears, bounce pads, or motion marks under the pet.",
        "Keep the background outside the pet perfectly flat chroma key with no darker key-colored patches.",
    ],
    "happy": [
        "Keep the pet recognizably the same character while making the body language clearly cheerful.",
        "Use a small bounce, brighter expression, perked ears, tail wag, or lifted paws; avoid confetti, loose sparkles, floating hearts, or text.",
    ],
    "sad": [
        "Show low mood through lowered head, drooping ears or limbs, slower motion, and sad eyes.",
        "Avoid dramatic crying effects, falling detached tears, storm clouds, punctuation, or symbols.",
    ],
    "sick": [
        "Show the pet feeling unwell through curled posture, weak eyes, lowered body, and minimal motion.",
        "Small opaque sweat drops or warmth marks are allowed only if attached to or overlapping the pet silhouette.",
        "Do not draw medical symbols, red crosses, thermometers, detached droplets, floating icons, dust, clouds, or text.",
    ],
    "levelup": [
        "Show a clear upgrade celebration through proud posture, a happy jump, twirl-like pose progression, or lifted paws.",
        "A tiny crown, ribbon, badge, or star accents are allowed only when attached to, touching, or overlapping the pet silhouette.",
        "Do not draw level numbers, UI panels, text, big glowing rings, explosions, loose confetti, detached sparkles, floor shadows, or scenery.",
    ],
    "eating": [
        "Show a small treat or snack as an attached prop held close to the pet, with subtle chewing and satisfied expression.",
        "Keep the treat simple and readable; do not add bowls, tables, scenery, crumbs, floating food icons, or text.",
    ],
    "sleeping": [
        "Use closed eyes, a curled or loaf pose, slow breathing, and a tiny ear or tail twitch.",
        "Do not draw Z letters, speech bubbles, pillows, beds, moons, stars, blankets, scenery, or floating sleep symbols.",
    ],
}

NON_DERIVABLE_STATES = {
    "happy",
    "sad",
    "greeting",
    "jumping",
    "sick",
    "levelup",
    "eating",
    "sleeping",
}

PET_SAFE_STYLE = (
    "Pet-safe sprite: compact full-body mascot, readable in a 192x208 cell, "
    "clear silhouette, simple face, stable palette/materials, and crisp edges "
    "for chroma-key extraction."
)

REFERENCE_IMAGE_PRIORITY = (
    "Reference image priority: the attached reference image(s) are the visual "
    "source of truth. Match the character design, silhouette, proportions, pose "
    "language, facial features, markings, palette, line weight, material/rendering "
    "style, and overall cuteness from the reference. Do not redesign, re-breed, "
    "re-color, re-outline, or reinterpret the pet into a different mascot style. "
    "Only change pose, expression, and state action as required for animation."
)

STYLE_PRESETS = {
    "auto": (
        "Infer the most appropriate pet-safe style from the user request and "
        "reference images, then keep that exact style consistent across every row."
    ),
    "pixel": (
        "Pixel-art-adjacent digital mascot with a chunky silhouette, simple dark "
        "outline, limited palette, flat cel shading, and visible stepped edges."
    ),
    "plush": (
        "Soft plush toy mascot with rounded stitched forms, fuzzy fabric feel, "
        "simple sewn details, and readable toy-like proportions."
    ),
    "clay": (
        "Handmade clay or polymer-clay mascot with rounded sculpted forms, soft "
        "material texture, simple features, and clean readable edges."
    ),
    "sticker": (
        "Polished sticker mascot with bold clean shapes, crisp outline, flat "
        "colors, and minimal highlight detail."
    ),
    "flat-vector": (
        "Flat vector-style mascot with simple geometric forms, crisp color areas, "
        "clean outline, and minimal shading."
    ),
    "3d-toy": (
        "Stylized 3D toy mascot with smooth rounded forms, simple materials, "
        "clear silhouette, and no photoreal complexity."
    ),
    "painterly": (
        "Soft painterly companion mascot with warm simplified brush texture, rounded "
        "cute proportions, expressive face, stable palette, and clean readable edges "
        "for transparent extraction at small pet size."
    ),
    "brand-inspired": (
        "Brand-inspired mascot using approved public or user-provided brand cues "
        "such as colors, mascot themes, and vibe while avoiding readable text or "
        "logo copying unless explicitly approved."
    ),
}

CHROMA_KEY_CANDIDATES = [
    ("magenta", "#FF00FF"),
    ("cyan", "#00FFFF"),
    ("yellow", "#FFFF00"),
    ("blue", "#0000FF"),
    ("orange", "#FF7F00"),
    ("green", "#00FF00"),
]

DEFAULT_PET_NAME = "Sprout"
CANONICAL_BASE_PATH = "references/canonical-base.png"
BRAND_DISCOVERY_PATH = "references/brand-discovery.md"
LAYOUT_GUIDE_DIR = "references/layout-guides"
LAYOUT_GUIDE_SAFE_MARGIN_X = 18
LAYOUT_GUIDE_SAFE_MARGIN_Y = 16


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value)
    return value.strip("-")


def display_from_slug(value: str) -> str:
    words = [word for word in re.split(r"[^a-zA-Z0-9]+", value.strip()) if word]
    return " ".join(word.capitalize() for word in words)


def concept_words(value: str) -> list[str]:
    stop_words = {
        "a",
        "an",
        "and",
        "app",
        "based",
        "codex",
        "compact",
        "digital",
        "for",
        "from",
        "in",
        "of",
        "on",
        "pet",
        "ready",
        "small",
        "the",
        "to",
        "with",
    }
    words = [
        word.lower()
        for word in re.findall(r"[a-zA-Z0-9]+", value)
        if word.lower() not in stop_words
    ]
    return words


def infer_name(args: argparse.Namespace, reference_paths: list[Path]) -> str:
    for raw_value in [args.display_name, args.pet_name]:
        value = raw_value.strip()
        if value:
            return value

    if args.pet_id.strip():
        display = display_from_slug(args.pet_id)
        if display:
            return display

    for raw_value in [args.pet_notes, args.description, args.brand_name]:
        words = concept_words(raw_value)
        if words:
            return words[0].capitalize()

    for path in reference_paths:
        display = display_from_slug(path.stem)
        if display:
            return display

    return DEFAULT_PET_NAME


def sentence(value: str) -> str:
    value = " ".join(value.strip().split())
    if not value:
        return value
    if value[-1] not in ".!?":
        value += "."
    return value


def infer_description(args: argparse.Namespace, reference_paths: list[Path]) -> str:
    if args.description.strip():
        return sentence(args.description)
    if args.pet_notes.strip():
        return sentence(f"A compact DoseCare companion pet: {args.pet_notes}")
    if args.brand_name.strip():
        return sentence(f"A compact DoseCare companion pet inspired by {args.brand_name}")
    if reference_paths:
        return "A compact DoseCare companion pet based on the provided reference image."
    return "A compact original DoseCare companion pet ready for animation."


def infer_pet_notes(args: argparse.Namespace, reference_paths: list[Path]) -> str:
    if args.pet_notes.strip():
        return args.pet_notes.strip()
    if args.description.strip():
        return args.description.strip().rstrip(".")
    if args.brand_name.strip():
        return f"a compact mascot inspired by {args.brand_name.strip()}"
    if reference_paths:
        return "the pet shown in the reference image(s)"
    return "a compact original DoseCare companion pet"


def default_output_dir(pet_id: str) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path.cwd() / "output" / "hatch-pet" / f"{pet_id}-{timestamp}"


def rel(path: Path, root: Path) -> str:
    return str(path.resolve().relative_to(root.resolve()))


def image_metadata(path: Path) -> dict[str, object]:
    with Image.open(path) as image:
        return {
            "path": str(path),
            "width": image.width,
            "height": image.height,
            "mode": image.mode,
            "format": image.format,
        }


def draw_dashed_line(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    *,
    fill: str,
    dash: int = 8,
    gap: int = 6,
) -> None:
    x1, y1 = start
    x2, y2 = end
    if x1 == x2:
        step = dash + gap
        for y in range(min(y1, y2), max(y1, y2), step):
            draw.line((x1, y, x2, min(y + dash, max(y1, y2))), fill=fill)
        return
    if y1 == y2:
        step = dash + gap
        for x in range(min(x1, x2), max(x1, x2), step):
            draw.line((x, y1, min(x + dash, max(x1, x2)), y2), fill=fill)
        return
    raise ValueError("draw_dashed_line only supports horizontal or vertical lines")


def create_layout_guide(path: Path, state: str, frames: int) -> dict[str, object]:
    width = frames * ATLAS["cell_width"]
    height = ATLAS["cell_height"]
    cell_width = ATLAS["cell_width"]
    image = Image.new("RGB", (width, height), "#f7f7f7")
    draw = ImageDraw.Draw(image)

    for index in range(frames):
        left = index * cell_width
        right = left + cell_width - 1
        draw.rectangle((left, 0, right, height - 1), outline="#111111", width=2)

        safe_left = left + LAYOUT_GUIDE_SAFE_MARGIN_X
        safe_top = LAYOUT_GUIDE_SAFE_MARGIN_Y
        safe_right = right - LAYOUT_GUIDE_SAFE_MARGIN_X
        safe_bottom = height - 1 - LAYOUT_GUIDE_SAFE_MARGIN_Y
        draw.rectangle(
            (safe_left, safe_top, safe_right, safe_bottom),
            outline="#2f80ed",
            width=2,
        )

        center_x = left + cell_width // 2
        center_y = height // 2
        draw_dashed_line(
            draw,
            (center_x, safe_top),
            (center_x, safe_bottom),
            fill="#b8b8b8",
        )
        draw_dashed_line(
            draw,
            (safe_left, center_y),
            (safe_right, center_y),
            fill="#b8b8b8",
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    return {
        "state": state,
        "path": str(path),
        "width": width,
        "height": height,
        "frames": frames,
        "cell_width": ATLAS["cell_width"],
        "cell_height": ATLAS["cell_height"],
        "safe_margin_x": LAYOUT_GUIDE_SAFE_MARGIN_X,
        "safe_margin_y": LAYOUT_GUIDE_SAFE_MARGIN_Y,
        "usage": "layout guide input only; do not copy visible guide lines into generated sprite strips",
    }


def create_layout_guides(run_dir: Path) -> list[dict[str, object]]:
    guide_dir = run_dir / LAYOUT_GUIDE_DIR
    return [
        create_layout_guide(guide_dir / f"{state}.png", state, frames)
        for state, _row, frames, _purpose in ROWS
    ]


def parse_hex_color(value: str) -> tuple[int, int, int]:
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        raise SystemExit(f"invalid chroma key color: {value}; expected #RRGGBB")
    return tuple(int(value[index : index + 2], 16) for index in (1, 3, 5))


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"


def color_distance(left: tuple[int, int, int], right: tuple[int, int, int]) -> float:
    return math.sqrt(sum((left[index] - right[index]) ** 2 for index in range(3)))


def sampled_reference_pixels(paths: list[Path]) -> list[tuple[int, int, int]]:
    pixels: list[tuple[int, int, int]] = []
    for path in paths:
        with Image.open(path) as opened:
            image = opened.convert("RGBA")
            image.thumbnail((128, 128), Image.Resampling.LANCZOS)
            data = image.tobytes()
            for index in range(0, len(data), 4):
                red, green, blue, alpha = data[index : index + 4]
                if alpha <= 16:
                    continue
                pixels.append((red, green, blue))

    non_background = [
        pixel
        for pixel in pixels
        if not (pixel[0] > 244 and pixel[1] > 244 and pixel[2] > 244)
    ]
    return non_background or pixels


def choose_chroma_key(reference_paths: list[Path], requested: str) -> dict[str, object]:
    if requested.lower() != "auto":
        rgb = parse_hex_color(requested)
        return {
            "hex": rgb_to_hex(rgb),
            "rgb": list(rgb),
            "name": "user-selected",
            "selection": "manual",
        }

    pixels = sampled_reference_pixels(reference_paths)
    if not pixels:
        rgb = parse_hex_color("#FF00FF")
        return {
            "hex": "#FF00FF",
            "rgb": list(rgb),
            "name": "magenta",
            "selection": "fallback",
        }

    scored: list[tuple[float, int, str, tuple[int, int, int]]] = []
    for preference_index, (name, hex_color) in enumerate(CHROMA_KEY_CANDIDATES):
        rgb = parse_hex_color(hex_color)
        distances = sorted(color_distance(rgb, pixel) for pixel in pixels)
        percentile_index = max(0, min(len(distances) - 1, int(len(distances) * 0.01)))
        scored.append((distances[percentile_index], -preference_index, name, rgb))

    score, _preference, name, rgb = max(scored)
    return {
        "hex": rgb_to_hex(rgb),
        "rgb": list(rgb),
        "name": name,
        "selection": "auto",
        "score": round(score, 2),
    }


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def resolved_style_contract(
    style_preset: str,
    raw_style_notes: str,
    has_reference: bool = False,
) -> str:
    style_preset = style_preset.strip().lower()
    if style_preset not in STYLE_PRESETS:
        allowed = ", ".join(sorted(STYLE_PRESETS))
        raise SystemExit(
            f"invalid style preset: {style_preset}; expected one of: {allowed}"
        )
    raw_style_notes = raw_style_notes.strip()
    preset_contract = STYLE_PRESETS[style_preset]
    if has_reference and not raw_style_notes:
        return (
            f"{REFERENCE_IMAGE_PRIORITY} {PET_SAFE_STYLE} "
            f"Use style preset `{style_preset}` only as technical sprite-readability "
            "guidance; preserve the reference image's own visual style."
        )
    if has_reference:
        return (
            f"{REFERENCE_IMAGE_PRIORITY} {PET_SAFE_STYLE} "
            f"Style preset `{style_preset}`: {preset_contract} "
            f"User style notes: {raw_style_notes}. Apply these notes only where they "
            "do not conflict with the reference identity, unless the notes explicitly "
            "ask to transform the reference style."
        )
    if not raw_style_notes:
        return f"{PET_SAFE_STYLE} Style `{style_preset}`: {preset_contract}"
    return (
        f"{PET_SAFE_STYLE} Style `{style_preset}`: {preset_contract} "
        f"User style notes: {raw_style_notes}."
    )


def compact(value: str) -> str:
    return " ".join(value.strip().split())


def brand_inspiration_line(args: argparse.Namespace) -> str:
    brand_name = compact(args.brand_name)
    brand_brief = compact(args.brand_brief)
    if not brand_name and not brand_brief:
        return ""

    prefix = f"{brand_name}: " if brand_name else ""
    if brand_brief:
        return (
            f"{prefix}{brand_brief} Use only broad mascot-safe cues; do not copy "
            "readable logos, marks, UI screenshots, or text."
        )
    return (
        f"{prefix}Use only broad mascot-safe brand cues. Do not copy readable "
        "logos, marks, UI screenshots, or text."
    )


def base_pet_prompt(args: argparse.Namespace) -> str:
    pet_notes = args.pet_notes or "the pet shown in the reference image(s)"
    has_reference = bool(getattr(args, "has_reference", False))
    style_contract = resolved_style_contract(
        args.style_preset,
        args.style_notes,
        has_reference,
    )
    brand_line = brand_inspiration_line(args)
    brand_block = f"\nBrand inspiration: {brand_line}\n" if brand_line else "\n"
    chroma_key = args.chroma_key["hex"]
    chroma_name = args.chroma_key["name"]
    return f"""Create one clean full-body reference sprite for DoseCare companion pet {args.display_name}.

Pet identity: {pet_notes}.
Style: {style_contract}
{brand_block}
Place a single centered pose on a perfectly flat pure {chroma_name} {chroma_key} chroma-key background. Keep the full pet visible, compact, warm, cute, readable at 192x208, and easy to animate. If reference images are attached, copy the reference pet's shape language and visual style faithfully while adapting it to a clean sprite pose. No scenery, text, borders, checkerboard transparency, shadows, glows, detached effects, or extra props. Keep {chroma_key} and close colors out of the pet, props, highlights, and effects."""


def row_prompt(
    args: argparse.Namespace, state: str, row: int, frames: int, purpose: str
) -> str:
    pet_notes = args.pet_notes or "the same pet from the approved base reference"
    has_reference = bool(getattr(args, "has_reference", False))
    style_contract = resolved_style_contract(
        args.style_preset,
        args.style_notes,
        has_reference,
    )
    chroma_key = args.chroma_key["hex"]
    chroma_name = args.chroma_key["name"]
    state_prompt = STATE_PROMPTS[state]
    state_requirements = "\n".join(f"- {line}" for line in STATE_REQUIREMENTS[state])
    return f"""Create one horizontal animation strip for DoseCare companion pet `{args.pet_id}`, state `{state}`.

Use the attached canonical base for identity. Use the attached layout guide only for slot count, spacing, centering, and padding; do not draw the guide.

Output exactly {frames} full-body frames in one left-to-right row on flat pure {chroma_name} {chroma_key}. Treat the row as {frames} invisible equal-width slots: one centered complete pose per slot, evenly spaced, with no overlap, clipping, empty slots, labels, or borders.

Identity: same pet in every frame: {pet_notes}. Preserve the canonical base and original reference image's silhouette, face, proportions, markings, palette, material/rendering style, line weight, and props.
Style: {style_contract}
Animation continuity: keep apparent pet scale and baseline stable within the row unless the state itself intentionally changes vertical position, such as `jumping`. Move the pose within the slot instead of redrawing the pet larger or smaller frame to frame.

State action: {state_prompt}

State requirements:
{state_requirements}

Clean extraction: crisp opaque edges, safe padding, no scenery, text, guide marks, checkerboard, shadows, glows, motion blur, speed lines, dust, detached effects, stray pixels, or chroma-key colors inside the pet."""


def retry_row_prompt(
    args: argparse.Namespace, state: str, row: int, frames: int, purpose: str
) -> str:
    pet_notes = args.pet_notes or "the canonical base pet"
    chroma_key = args.chroma_key["hex"]
    chroma_name = args.chroma_key["name"]
    state_prompt = STATE_PROMPTS[state]
    state_requirements = "\n".join(f"- {line}" for line in STATE_REQUIREMENTS[state])
    return f"""Create DoseCare companion pet row `{state}` for `{args.pet_id}`: exactly {frames} full-body frames in one horizontal strip on flat pure {chroma_name} {chroma_key}.

Use the attached canonical base for identity and the layout guide only for spacing. Same pet in every frame: {pet_notes}. Preserve silhouette, face, palette, material, proportions, markings, and props.

Keep apparent pet scale and baseline stable within the row unless the state itself intentionally changes vertical position, such as `jumping`.

Action: {state_prompt}

State requirements:
{state_requirements}

One centered complete pose per invisible slot. No text, boxes, guide marks, scenery, shadows, glows, motion blur, speed lines, dust, detached effects, stray pixels, or {chroma_key} colors in the pet."""


def make_jobs(
    run_dir: Path, copied_refs: list[dict[str, object]]
) -> list[dict[str, object]]:
    reference_inputs = [
        {
            "path": rel(Path(str(ref["copied_path"])), run_dir),
            "role": "primary visual identity and style reference",
        }
        for ref in copied_refs
    ]
    identity_reference_paths = [CANONICAL_BASE_PATH]
    jobs: list[dict[str, object]] = [
        {
            "id": "base",
            "kind": "base-pet",
            "status": "pending",
            "prompt_file": "prompts/base-pet.md",
            "input_images": reference_inputs,
            "output_path": "decoded/base.png",
            "depends_on": [],
            "generation_skill": "$imagegen",
            "requires_grounded_generation": bool(reference_inputs),
            "allow_prompt_only_generation": not reference_inputs,
        }
    ]
    for state, _row, frames, _purpose in ROWS:
        depends_on = ["base"]
        derivation_policy: dict[str, object] = {
            "may_derive": False,
            "reason": "state requires its own generated animation semantics",
        }
        if state not in NON_DERIVABLE_STATES:
            derivation_policy["reason"] = "no deterministic derivation is configured for this state"
        jobs.append(
            {
                "id": state,
                "kind": "row-strip",
                "status": "pending",
                "prompt_file": f"prompts/rows/{state}.md",
                "retry_prompt_file": f"prompts/row-retries/{state}.md",
                "input_images": [
                    *reference_inputs,
                    {
                        "path": f"{LAYOUT_GUIDE_DIR}/{state}.png",
                        "role": f"layout guide for {frames} frame slots; use for spacing only, do not copy guide lines",
                    },
                    {
                        "path": CANONICAL_BASE_PATH,
                        "role": "canonical identity reference",
                    },
                ],
                "output_path": f"decoded/{state}.png",
                "depends_on": depends_on,
                "generation_skill": "$imagegen",
                "requires_grounded_generation": True,
                "allow_prompt_only_generation": False,
                "identity_reference_paths": identity_reference_paths,
                "parallelizable_after": depends_on,
                "derivation_policy": derivation_policy,
                "mirror_policy": {},
            }
        )
    return jobs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pet-name",
        default="",
        help="User-facing pet name. Ask the user for this when practical; otherwise choose a short appropriate name.",
    )
    parser.add_argument(
        "--pet-id",
        default="",
        help="Stable pet folder/id slug. Defaults to the slugified pet name.",
    )
    parser.add_argument(
        "--display-name",
        default="",
        help="Display label. Defaults to the pet name.",
    )
    parser.add_argument("--description", default="")
    parser.add_argument("--reference", action="append", default=[])
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--pet-notes", default="")
    parser.add_argument(
        "--brand-name",
        default="",
        help="Brand, company, or product name used for broad mascot inspiration.",
    )
    parser.add_argument(
        "--brand-brief",
        default="",
        help="Compact researched brand cue sentence for the base pet only.",
    )
    parser.add_argument(
        "--brand-source",
        action="append",
        default=[],
        help="Source URL used to produce the brand brief. May be passed multiple times.",
    )
    parser.add_argument(
        "--brand-discovery-file",
        default="",
        help="Optional markdown discovery brief to copy into the run for review.",
    )
    parser.add_argument(
        "--style-preset",
        default="painterly",
        choices=sorted(STYLE_PRESETS),
        help="Pet-safe style preset to use across the base and all animation rows.",
    )
    parser.add_argument("--style-notes", default="")
    parser.add_argument(
        "--chroma-key",
        default="auto",
        help="Chroma key as #RRGGBB, or auto to choose a safe key from reference colors.",
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    raw_reference_paths = [
        Path(raw_path).expanduser().resolve() for raw_path in args.reference
    ]
    raw_brand_discovery_path = (
        Path(args.brand_discovery_file).expanduser().resolve()
        if args.brand_discovery_file.strip()
        else None
    )

    args.display_name = infer_name(args, raw_reference_paths)
    args.pet_name = (args.pet_name or args.display_name).strip()
    args.description = infer_description(args, raw_reference_paths)
    args.pet_notes = infer_pet_notes(args, raw_reference_paths)
    args.pet_id = slugify(args.pet_id or args.pet_name or args.display_name)
    args.style_preset = args.style_preset.strip().lower()
    args.has_reference = bool(raw_reference_paths)
    args.style_contract = resolved_style_contract(
        args.style_preset,
        args.style_notes,
        args.has_reference,
    )
    args.brand_name = compact(args.brand_name)
    args.brand_brief = compact(args.brand_brief)
    args.brand_source = [
        compact(source) for source in args.brand_source if compact(source)
    ]
    if not args.pet_id:
        raise SystemExit("pet id must contain at least one letter or digit")

    run_dir = (
        Path(args.output_dir).expanduser().resolve()
        if args.output_dir
        else default_output_dir(args.pet_id).resolve()
    )
    if run_dir.exists() and any(run_dir.iterdir()) and not args.force:
        raise SystemExit(
            f"{run_dir} already exists and is not empty; pass --force to reuse it"
        )
    run_dir.mkdir(parents=True, exist_ok=True)

    ref_dir = run_dir / "references"
    prompt_dir = run_dir / "prompts"
    row_prompt_dir = prompt_dir / "rows"
    row_retry_prompt_dir = prompt_dir / "row-retries"
    for directory in [
        ref_dir,
        prompt_dir,
        row_prompt_dir,
        row_retry_prompt_dir,
        run_dir / "decoded",
        run_dir / "qa",
    ]:
        directory.mkdir(parents=True, exist_ok=True)

    copied_refs: list[dict[str, object]] = []
    copied_ref_paths: list[Path] = []
    for index, source in enumerate(raw_reference_paths, start=1):
        if not source.is_file():
            raise SystemExit(f"reference not found: {source}")
        suffix = source.suffix.lower() or ".png"
        copied = ref_dir / f"reference-{index:02d}{suffix}"
        shutil.copy2(source, copied)
        meta = image_metadata(copied)
        meta["source_path"] = str(source)
        meta["copied_path"] = str(copied)
        copied_refs.append(meta)
        copied_ref_paths.append(copied)

    brand_discovery_path = ""
    if raw_brand_discovery_path is not None:
        if not raw_brand_discovery_path.is_file():
            raise SystemExit(f"brand discovery file not found: {raw_brand_discovery_path}")
        copied_discovery = run_dir / BRAND_DISCOVERY_PATH
        shutil.copy2(raw_brand_discovery_path, copied_discovery)
        brand_discovery_path = rel(copied_discovery, run_dir)

    args.chroma_key = choose_chroma_key(copied_ref_paths, args.chroma_key)
    layout_guides = create_layout_guides(run_dir)

    request = {
        "pet_id": args.pet_id,
        "display_name": args.display_name,
        "description": args.description,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "atlas": ATLAS,
        "rows": [
            {"state": state, "row": row, "frames": frames, "purpose": purpose}
            for state, row, frames, purpose in ROWS
        ],
        "layout_guides": [
            {**guide, "path": rel(Path(str(guide["path"])), run_dir)}
            for guide in layout_guides
        ],
        "references": copied_refs,
        "chroma_key": args.chroma_key,
        "pet_notes": args.pet_notes,
        "style_preset": args.style_preset,
        "style_notes": args.style_notes,
        "style_contract": args.style_contract,
        "reference_image_priority": args.has_reference,
        "brand_name": args.brand_name,
        "brand_brief": args.brand_brief,
        "brand_sources": args.brand_source,
        "pet_safe_style": PET_SAFE_STYLE,
        "primary_generation_skill": "$imagegen",
    }
    if brand_discovery_path:
        request["brand_discovery_path"] = brand_discovery_path
    (run_dir / "pet_request.json").write_text(
        json.dumps(request, indent=2) + "\n", encoding="utf-8"
    )

    write_text(prompt_dir / "base-pet.md", base_pet_prompt(args))
    for state, row, frames, purpose in ROWS:
        write_text(
            row_prompt_dir / f"{state}.md",
            row_prompt(args, state, row, frames, purpose),
        )
        write_text(
            row_retry_prompt_dir / f"{state}.md",
            retry_row_prompt(args, state, row, frames, purpose),
        )

    jobs = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "run_dir": str(run_dir),
        "primary_generation_skill": "$imagegen",
        "jobs": make_jobs(run_dir, copied_refs),
    }
    (run_dir / "imagegen-jobs.json").write_text(
        json.dumps(jobs, indent=2) + "\n", encoding="utf-8"
    )

    print(
        json.dumps(
            {
                "ok": True,
                "run_dir": str(run_dir),
                "request": str(run_dir / "pet_request.json"),
                "jobs": str(run_dir / "imagegen-jobs.json"),
                "ready_jobs": ["base"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
