#!/usr/bin/env python3
import argparse
import json
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image


def recover_rgba_from_matte_pair(white_image, black_image, transparent_threshold=8):
    """Recover straight-alpha RGBA from matching white and black matte renders."""
    white = white_image.convert("RGB")
    black = black_image.convert("RGB")
    if white.size != black.size:
        raise ValueError(
            f"white and black images must have the same size: {white.size} != {black.size}"
        )

    white_arr = np.asarray(white, dtype=np.float32)
    black_arr = np.asarray(black, dtype=np.float32)

    alpha = 255.0 - np.mean(white_arr - black_arr, axis=2)
    alpha = np.clip(alpha, 0.0, 255.0)
    alpha[alpha < transparent_threshold] = 0.0

    color = np.zeros_like(black_arr)
    visible = alpha > 0
    color[visible] = black_arr[visible] * 255.0 / alpha[visible, None]
    color = np.clip(color, 0.0, 255.0)

    rgba = np.dstack([color, alpha]).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


def find_asset_boxes(
    rgba_image,
    alpha_threshold=12,
    padding=8,
    min_area=128,
    min_component_width=1,
    min_component_height=1,
):
    alpha = np.asarray(rgba_image.convert("RGBA").getchannel("A"))
    mask = alpha > alpha_threshold
    height, width = mask.shape
    seen = np.zeros(mask.shape, dtype=bool)
    boxes = []

    for y in range(height):
        for x in range(width):
            if seen[y, x] or not mask[y, x]:
                continue

            queue = deque([(x, y)])
            seen[y, x] = True
            min_x = max_x = x
            min_y = max_y = y
            area = 0

            while queue:
                cx, cy = queue.popleft()
                area += 1
                min_x = min(min_x, cx)
                max_x = max(max_x, cx)
                min_y = min(min_y, cy)
                max_y = max(max_y, cy)

                for ny in range(max(0, cy - 1), min(height, cy + 2)):
                    for nx in range(max(0, cx - 1), min(width, cx + 2)):
                        if seen[ny, nx] or not mask[ny, nx]:
                            continue
                        seen[ny, nx] = True
                        queue.append((nx, ny))

            component_width = max_x - min_x + 1
            component_height = max_y - min_y + 1
            if (
                area < min_area
                or component_width < min_component_width
                or component_height < min_component_height
            ):
                continue

            boxes.append(
                (
                    max(0, min_x - padding),
                    max(0, min_y - padding),
                    min(width, max_x + padding + 1),
                    min(height, max_y + padding + 1),
                )
            )

    return sorted(boxes, key=lambda box: (box[1], box[0]))


def export_assets(rgba_image, boxes, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    assets = []
    for index, box in enumerate(boxes, start=1):
        filename = f"asset-{index:03d}.png"
        crop = rgba_image.crop(box)
        crop.save(out_dir / filename)
        assets.append(
            {
                "id": f"asset-{index:03d}",
                "file": filename,
                "bbox": list(box),
                "width": crop.width,
                "height": crop.height,
            }
        )

    return assets


def clear_previous_outputs(out_dir, sheet_name):
    out_dir = Path(out_dir)
    if not out_dir.exists():
        return
    for path in out_dir.glob("asset-*.png"):
        path.unlink()
    for name in [sheet_name, "manifest.json"]:
        path = out_dir / name
        if path.exists():
            path.unlink()


def run_cli(args):
    white = Image.open(args.white)
    black = Image.open(args.black)
    rgba = recover_rgba_from_matte_pair(
        white,
        black,
        transparent_threshold=args.transparent_threshold,
    )
    boxes = find_asset_boxes(
        rgba,
        alpha_threshold=args.alpha_threshold,
        padding=args.padding,
        min_area=args.min_area,
        min_component_width=args.min_component_width,
        min_component_height=args.min_component_height,
    )

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    sheet_name = args.sheet_name
    clear_previous_outputs(out_dir, sheet_name)
    rgba.save(out_dir / sheet_name)
    assets = export_assets(rgba, boxes, out_dir)

    manifest = {
        "white": str(args.white),
        "black": str(args.black),
        "sheet": sheet_name,
        "asset_count": len(assets),
        "assets": assets,
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    )
    print(f"Exported {len(assets)} assets to {out_dir}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract transparent game assets from matching white/black matte sheets."
    )
    parser.add_argument("--white", required=True, type=Path, help="White background sheet")
    parser.add_argument("--black", required=True, type=Path, help="Black background sheet")
    parser.add_argument("--out", required=True, type=Path, help="Output directory")
    parser.add_argument("--padding", type=int, default=8, help="Pixels around each asset")
    parser.add_argument("--min-area", type=int, default=128, help="Minimum alpha area")
    parser.add_argument(
        "--min-component-width",
        type=int,
        default=1,
        help="Ignore components narrower than this before padding",
    )
    parser.add_argument(
        "--min-component-height",
        type=int,
        default=1,
        help="Ignore components shorter than this before padding",
    )
    parser.add_argument(
        "--transparent-threshold",
        type=int,
        default=8,
        help="Recovered alpha below this is transparent",
    )
    parser.add_argument(
        "--alpha-threshold",
        type=int,
        default=12,
        help="Alpha threshold for connected-component asset detection",
    )
    parser.add_argument(
        "--sheet-name",
        default="assets-rgba.png",
        help="Filename for the recovered transparent sheet",
    )
    return parser.parse_args()


if __name__ == "__main__":
    run_cli(parse_args())
