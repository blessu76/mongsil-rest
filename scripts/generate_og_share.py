#!/usr/bin/env python3
"""Refresh the checked-in sharing image on macOS with Pillow and rsvg-convert.

Run: python3 scripts/generate_og_share.py
"""
from io import BytesIO
import subprocess

from PIL import Image, ImageDraw, ImageFont

from build import OG_HEIGHT, OG_IMAGE, OG_WIDTH, ROOT, STR, THEME_COLOR

FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
SCALE = 2


def main():
    output = ROOT / OG_IMAGE.lstrip("/")
    icon_size = 288 * SCALE
    icon_png = subprocess.check_output([
        "rsvg-convert", "--width", str(icon_size), "--height", str(icon_size),
        str(output.with_name("icon.svg")),
    ])
    with Image.open(BytesIO(icon_png)) as icon:
        mask = Image.new("L", icon.size)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, icon_size - 1, icon_size - 1), radius=64 * SCALE, fill=255)
        canvas = Image.new("RGB", (OG_WIDTH * SCALE, OG_HEIGHT * SCALE), THEME_COLOR)
        canvas.paste(icon.convert("RGB"), ((canvas.width - icon_size) // 2, 76 * SCALE), mask)

    draw = ImageDraw.Draw(canvas)
    # Bold and regular Apple SD Gothic Neo, already used by the site's font stack.
    title = ImageFont.truetype(FONT, 74 * SCALE, index=6)
    subtitle = ImageFont.truetype(FONT, 40 * SCALE)
    draw.text((canvas.width // 2, 438 * SCALE), STR["ko"]["site_title"], font=title, fill="#4a3a4f", anchor="mm")
    draw.text((canvas.width // 2, 510 * SCALE), STR["en"]["site_title"], font=subtitle, fill="#76657b", anchor="mm")
    canvas.resize((OG_WIDTH, OG_HEIGHT), Image.Resampling.LANCZOS).save(output, optimize=True)


if __name__ == "__main__":
    main()
