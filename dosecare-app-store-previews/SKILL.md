---
name: dosecare-app-store-previews
description: Generate polished localized DoseCare App Store preview images from iPhone simulator screenshots. Use when the user asks to create DoseCare App Store previews, marketing preview screenshots, localized preview images, or regenerate zh-Hans, en-US, or ja-JP preview art from simulator screenshots.
---

# DoseCare App Store Previews

## Overview

Create consistent 1284 x 2778 RGB App Store preview images for DoseCare. The bundled script places simulator screenshots inside a soft rounded device frame, adds localized marketing copy, uses a blush-to-warm-white background, removes alpha channels before saving, and can create a contact sheet for quick visual review.

## Workflow

1. Collect four iPhone simulator screenshots in this order:
   - Reminders
   - Records
   - Unwind / Relax
   - Medicine Box / Profile
2. Run the bundled script from the DoseCare repo root.
3. Inspect the generated contact sheet before reporting completion.
4. Verify every PNG is `1284 x 2778` and RGB/non-alpha before reporting completion.
5. If text overflows, reduce title length first, then adjust locale-specific font sizes in the script.

## Quick Commands

Use built-in screenshot paths and copy when they are still valid:

```bash
python3 .agents/skills/dosecare-app-store-previews/scripts/generate_dosecare_previews.py --locale zh-Hans
python3 .agents/skills/dosecare-app-store-previews/scripts/generate_dosecare_previews.py --locale en-US
python3 .agents/skills/dosecare-app-store-previews/scripts/generate_dosecare_previews.py --locale ja-JP
```

Use new screenshots without editing the script:

```bash
python3 .agents/skills/dosecare-app-store-previews/scripts/generate_dosecare_previews.py \
  --locale ja-JP \
  --screenshots /path/reminders.png /path/records.png /path/unwind.png /path/medicine-box.png
```

The default output is:

```text
output/app-store-previews/<locale>/dosecare-preview-01.png
output/app-store-previews/<locale>/dosecare-preview-02.png
output/app-store-previews/<locale>/dosecare-preview-03.png
output/app-store-previews/<locale>/dosecare-preview-04.png
```

The script also writes:

```text
/private/tmp/dosecare-previews-<locale>-contact-sheet.jpg
```

## Validation

Always run:

```bash
file output/app-store-previews/<locale>/dosecare-preview-*.png
```

The result must not mention `RGBA`, `alpha`, or transparency. If it does, convert the files to RGB and fix the script before finishing.

## Style Rules

- Keep the pure soft blush-to-warm-white gradient; avoid bubbles, orbs, or decorative clutter.
- Save final PNGs as RGB only; do not leave alpha channels.
- Keep all languages visually aligned as one campaign.
- Add Nuomi only on the first preview, extracted from the reminder screenshot when possible.
- Prefer short localized titles; App Store preview text should scan quickly.
- Use the app theme coral as the accent, with dark text and muted subtitles.
