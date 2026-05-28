from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


CANVAS_SIZE = (1290, 2796)
OUTPUT_ROOT = Path("output/app-store-previews")

LOCALES = {
    "zh-Hans": {
        "screenshots": [
            "/Users/n14637/Desktop/Simulator Screenshot - iPhone 17 - 2026-05-28 at 16.44.58.png",
            "/Users/n14637/Desktop/Simulator Screenshot - iPhone 17 - 2026-05-28 at 16.45.05.png",
            "/Users/n14637/Desktop/Simulator Screenshot - iPhone 17 - 2026-05-28 at 16.45.21.png",
            "/Users/n14637/Desktop/Simulator Screenshot - iPhone 17 - 2026-05-28 at 16.46.55.png",
        ],
        "copy": [
            {"eyebrow": "好好吃药", "title": "温柔提醒，安心用药", "subtitle": "糯米 陪你每一个小日常"},
            {"eyebrow": "记录", "title": "趋势与完成率一眼看懂", "subtitle": "用药记录、热力图和计划对比清晰呈现"},
            {"eyebrow": "意空间", "title": "把自己轻轻拉回来", "subtitle": "呼吸练习、喝水记录和轻量拉伸都在这里"},
            {"eyebrow": "药箱", "title": "库存与有效期提前提醒", "subtitle": "低库存、即将过期和关联提醒统一管理"},
        ],
    },
    "en-US": {
        "screenshots": [
            "/Users/n14637/Desktop/Simulator Screenshot - iPhone 17 - 2026-05-28 at 17.52.29.png",
            "/Users/n14637/Desktop/Simulator Screenshot - iPhone 17 - 2026-05-28 at 17.52.33.png",
            "/Users/n14637/Desktop/Simulator Screenshot - iPhone 17 - 2026-05-28 at 17.52.35.png",
            "/Users/n14637/Desktop/Simulator Screenshot - iPhone 17 - 2026-05-28 at 17.55.59.png",
        ],
        "copy": [
            {"eyebrow": "Take your meds", "title": "Gentle reminders,\npeace of mind", "subtitle": "Nuomi stays with every little routine"},
            {"eyebrow": "Records", "title": "Track progress at a glance", "subtitle": "Completion rates, trends, and heatmaps in one place"},
            {"eyebrow": "Unwind", "title": "Small resets for busy days", "subtitle": "Breathing, hydration, and stretches when you need them"},
            {"eyebrow": "Medicine Box", "title": "Never miss stock or expiry", "subtitle": "Low stock, expiring items, and linked reminders together"},
        ],
    },
    "ja-JP": {
        "screenshots": [
            "/Users/n14637/Desktop/Simulator Screenshot - iPhone 17 - 2026-05-28 at 18.11.29.png",
            "/Users/n14637/Desktop/Simulator Screenshot - iPhone 17 - 2026-05-28 at 18.11.32.png",
            "/Users/n14637/Desktop/Simulator Screenshot - iPhone 17 - 2026-05-28 at 18.11.36.png",
            "/Users/n14637/Desktop/Simulator Screenshot - iPhone 17 - 2026-05-28 at 18.11.45.png",
        ],
        "copy": [
            {"eyebrow": "お薬習慣", "title": "やさしく続ける\n服薬リマインダー", "subtitle": "糯米が毎日の小さな習慣に寄り添います"},
            {"eyebrow": "記録", "title": "達成状況をひと目で確認", "subtitle": "服薬の進捗、傾向、ヒートマップをまとめて表示"},
            {"eyebrow": "リラックス", "title": "忙しい日に小さなリセット", "subtitle": "呼吸、水分、ストレッチで自分を整える"},
            {"eyebrow": "お薬箱", "title": "在庫と期限を見逃さない", "subtitle": "在庫不足、期限切れ前、関連リマインダーをまとめて管理"},
        ],
    },
}

CORAL = (255, 108, 114)
CORAL_DARK = (236, 80, 88)
BG_TOP = (255, 226, 228)
BG_MID = (255, 242, 242)
BG_BOTTOM = (250, 251, 253)


def font(size: int, weight: str = "regular", locale: str = "zh-Hans") -> ImageFont.FreeTypeFont:
    if locale == "en-US":
        paths = [
            ("/System/Library/Fonts/SFNSRounded.ttf", 0),
            ("/System/Library/Fonts/SFNS.ttf", 0),
            ("/System/Library/Fonts/Avenir Next.ttc", 0),
            ("/System/Library/Fonts/HelveticaNeue.ttc", 0),
        ]
    elif weight == "bold":
        paths = [
            ("/System/Library/Fonts/STHeiti Medium.ttc", 0),
            ("/System/Library/Fonts/Hiragino Sans GB.ttc", 1),
            ("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", 0),
        ]
    else:
        paths = [
            ("/System/Library/Fonts/Hiragino Sans GB.ttc", 0),
            ("/System/Library/Fonts/STHeiti Light.ttc", 0),
            ("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", 0),
        ]
    for path, index in paths:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size, index=index)
    return ImageFont.load_default()


def app_background(size: tuple[int, int]) -> Image.Image:
    width, height = size
    image = Image.new("RGB", size, BG_BOTTOM)
    pixels = image.load()
    for y in range(height):
        t = y / max(height - 1, 1)
        if t < 0.34:
            local = t / 0.34
            start, end = BG_TOP, BG_MID
        else:
            local = (t - 0.34) / 0.66
            start, end = BG_MID, BG_BOTTOM
        color = tuple(round(start[i] * (1 - local) + end[i] * local) for i in range(3))
        for x in range(width):
            pixels[x, y] = color
    return image.convert("RGBA")


def rounded_mask(size: tuple[int, int], radius: int) -> Image.Image:
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
    return mask


def wrap_text(draw: ImageDraw.ImageDraw, text: str, text_font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for char in text:
        candidate = current + char
        if draw.textlength(candidate, font=text_font) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = char
    if current:
        lines.append(current)
    return lines


def paste_screenshot(canvas: Image.Image, screenshot_path: Path, top: int) -> None:
    screenshot = Image.open(screenshot_path).convert("RGBA")
    target_w = 1016
    target_h = round(screenshot.height * target_w / screenshot.width)
    shot = screenshot.resize((target_w, target_h), Image.Resampling.LANCZOS)

    x = (CANVAS_SIZE[0] - target_w) // 2
    y = top
    card_w = target_w + 34
    card_h = min(target_h + 34, CANVAS_SIZE[1] - y - 70)
    card_x = x - 17
    card_y = y - 17

    shadow = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle((card_x, card_y, card_x + card_w, card_y + card_h), radius=82, fill=(54, 40, 55, 42))
    shadow = shadow.filter(ImageFilter.GaussianBlur(34))
    canvas.alpha_composite(shadow)

    frame = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    frame_draw = ImageDraw.Draw(frame)
    frame_draw.rounded_rectangle((0, 0, card_w, card_h), radius=82, fill=(255, 255, 255, 255))
    frame_draw.rounded_rectangle((2, 2, card_w - 2, card_h - 2), radius=80, outline=(255, 214, 216, 180), width=3)
    canvas.alpha_composite(frame, (card_x, card_y))

    visible_h = min(target_h, card_h - 34)
    shot = shot.crop((0, 0, target_w, visible_h))
    mask = rounded_mask((target_w, visible_h), 66)
    canvas.paste(shot, (x, y), mask)


def extract_nuomi(screenshot_path: Path, locale: str) -> Image.Image:
    screenshot = Image.open(screenshot_path).convert("RGBA")
    if locale == "zh-Hans":
        cat_box = (880, 1760, 1072, 2048)
    elif locale == "ja-JP":
        cat_box = (880, 1834, 1068, 2118)
    else:
        cat_box = (895, 1840, 1060, 2118)
    cat = screenshot.crop(cat_box)

    sticker = Image.new("RGBA", (330, 330), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (330, 330), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.ellipse((32, 38, 300, 306), fill=(118, 72, 80, 40))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    sticker.alpha_composite(shadow)

    back = Image.new("RGBA", (286, 286), (255, 255, 255, 238))
    back_mask = Image.new("L", (286, 286), 0)
    ImageDraw.Draw(back_mask).ellipse((0, 0, 286, 286), fill=255)
    sticker.paste(back, (22, 18), back_mask)

    cat = cat.resize((214, 320), Image.Resampling.LANCZOS)
    cat_mask = Image.new("L", cat.size, 0)
    ImageDraw.Draw(cat_mask).ellipse((0, 0, cat.width, cat.height + 24), fill=255)
    cat.putalpha(Image.composite(cat.getchannel("A"), Image.new("L", cat.size, 0), cat_mask))
    sticker.alpha_composite(cat, (58, 10))
    return sticker


def draw_sparkle(draw: ImageDraw.ImageDraw, center: tuple[int, int], size: int) -> None:
    x, y = center
    points = [(x, y - size), (x + 8, y - 8), (x + size, y), (x + 8, y + 8), (x, y + size), (x - 8, y + 8), (x - size, y), (x - 8, y - 8)]
    draw.polygon(points, fill=(255, 199, 57))


def create_preview(index: int, screenshot_path: Path, locale: str, copy: list[dict[str, str]]) -> Image.Image:
    canvas = app_background(CANVAS_SIZE)
    draw = ImageDraw.Draw(canvas)
    meta = copy[index]

    left = 106
    y = 112
    pill_font = font(31, "bold", locale)
    title_size = 76 if index == 0 else 66
    if locale == "en-US":
        title_size = 66 if index == 0 else 58
    elif locale == "ja-JP":
        title_size = 64 if index == 0 else 60
    title_font = font(title_size, "bold", locale)
    subtitle_font = font(34 if locale in {"en-US", "ja-JP"} else 36, "regular", locale)

    pill_text = meta["eyebrow"]
    pill_w = math.ceil(draw.textlength(pill_text, font=pill_font)) + 54
    pill_shadow = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    pill_shadow_draw = ImageDraw.Draw(pill_shadow)
    pill_shadow_draw.rounded_rectangle((left, y, left + pill_w, y + 62), radius=31, fill=(130, 64, 72, 28))
    pill_shadow = pill_shadow.filter(ImageFilter.GaussianBlur(12))
    canvas.alpha_composite(pill_shadow)
    draw.rounded_rectangle((left, y, left + pill_w, y + 62), radius=31, fill=(255, 255, 255, 246))
    draw.text((left + 27, y + 11), pill_text, font=pill_font, fill=CORAL_DARK)

    y += 92
    lines: list[str] = []
    for paragraph in meta["title"].split("\n"):
        lines.extend(wrap_text(draw, paragraph, title_font, 890 if locale in {"en-US", "ja-JP"} else 880))
    for line in lines:
        draw.text((left, y), line, font=title_font, fill=(30, 28, 34))
        y += 78 if locale in {"en-US", "ja-JP"} else 90

    y += 12
    for line in wrap_text(draw, meta["subtitle"], subtitle_font, 900):
        draw.text((left, y), line, font=subtitle_font, fill=(108, 99, 112))
        y += 48

    if index == 0:
        nuomi = extract_nuomi(screenshot_path, locale)
        canvas.alpha_composite(nuomi, (880, 142))
        draw_sparkle(draw, (944, 152), 28)
        draw_sparkle(draw, (914, 124), 13)

    paste_screenshot(canvas, screenshot_path, top=594)
    return canvas


def make_contact_sheet(files: list[Path], locale: str) -> Path:
    thumbs = []
    for path in files:
        image = Image.open(path).convert("RGB")
        image.thumbnail((258, 559), Image.Resampling.LANCZOS)
        thumbs.append((path, image.copy()))

    width = 258 * len(thumbs) + 24 * (len(thumbs) + 1)
    height = 559 + 72
    sheet = Image.new("RGB", (width, height), (246, 246, 248))
    draw = ImageDraw.Draw(sheet)
    for index, (path, image) in enumerate(thumbs):
        x = 24 + index * (258 + 24)
        sheet.paste(image, (x, 24))
        draw.text((x, 594), path.name, fill=(40, 40, 44))

    output = Path(f"/private/tmp/dosecare-previews-{locale}-contact-sheet.jpg")
    sheet.save(output, quality=92)
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate localized DoseCare App Store preview images.")
    parser.add_argument("--locale", choices=sorted(LOCALES), required=True)
    parser.add_argument("--screenshots", nargs=4, metavar="PNG", help="Four screenshots: reminders records unwind medicine-box.")
    parser.add_argument("--output-dir", type=Path, help="Override output directory.")
    parser.add_argument("--no-contact-sheet", action="store_true", help="Skip contact sheet generation.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    locale_data = LOCALES[args.locale]
    screenshots = [Path(path) for path in (args.screenshots or locale_data["screenshots"])]
    for path in screenshots:
        if not path.exists():
            raise SystemExit(f"Missing screenshot: {path}")

    output_dir = args.output_dir or OUTPUT_ROOT / args.locale
    output_dir.mkdir(parents=True, exist_ok=True)

    generated: list[Path] = []
    for index, path in enumerate(screenshots):
        preview = create_preview(index, path, args.locale, locale_data["copy"])
        output_path = output_dir / f"dosecare-preview-{index + 1:02d}.png"
        preview.save(output_path)
        generated.append(output_path)
        print(output_path)

    if not args.no_contact_sheet:
        print(make_contact_sheet(generated, args.locale))


if __name__ == "__main__":
    main()
