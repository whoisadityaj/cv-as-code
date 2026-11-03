"""Render every theme from the examples and build the README preview images.

    python docs/make_gallery.py   ->  docs/images/hero.png, docs/images/themes.png

Needs WeasyPrint working, Pillow (installed with WeasyPrint) and `pdftoppm`
from Poppler (`brew install poppler` / `apt install poppler-utils`).
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from cv_as_code.build import build_file, theme_names

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples"
OUT = ROOT / "docs" / "images"
BG = "#f6f8fa"
ORDER = ["sidebar", "bold", "executive", "modern", "minimal", "classic", "compact"]


def snapshot(yaml_name: str, theme: str, tmp: Path, ats: bool = False) -> Image.Image:
    out = tmp / f"{theme}{'-ats' if ats else ''}"
    pdf = next(p for p in build_file(EXAMPLES / yaml_name, out, theme=theme, ats=ats) if p.suffix == ".pdf")
    subprocess.run(["pdftoppm", "-png", "-r", "110", "-singlefile", str(pdf), str(pdf.with_suffix(""))], check=True)
    return Image.open(pdf.with_suffix(".png")).convert("RGB")


def card(im: Image.Image, width: int) -> Image.Image:
    im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    return ImageOps.expand(im, border=1, fill="#d0d7de")


def font(size: int) -> ImageFont.ImageFont:
    for name in ("/System/Library/Fonts/Helvetica.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def main() -> None:
    assert sorted(ORDER) == theme_names(), "update ORDER when adding a theme"
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        # Hero: two of the most distinctive looks side by side.
        a, b = card(snapshot("cv.yaml", "sidebar", tmp), 620), card(snapshot("cover_letter.yaml", "bold", tmp), 620)
        hero = Image.new("RGB", (a.width + b.width + 60, max(a.height, b.height) + 40), BG)
        hero.paste(a, (20, 20))
        hero.paste(b, (a.width + 40, 20))
        hero.save(OUT / "hero.png", optimize=True)

        # Gallery: every theme plus ATS mode, 4 per row, labelled.
        shots = [(name, snapshot("cv.yaml", name, tmp)) for name in ORDER]
        shots.append(("ATS mode", snapshot("cv.yaml", "classic", tmp, ats=True)))
        w, gap, label_h, cols = 360, 24, 40, 4
        cards = [(name, card(im, w)) for name, im in shots]
        h = max(c.height for _, c in cards)
        rows = (len(cards) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * (w + 2) + (cols + 1) * gap, rows * (h + label_h) + (rows + 1) * gap), BG)
        draw, f = ImageDraw.Draw(sheet), font(22)
        for i, (name, c) in enumerate(cards):
            x = gap + (i % cols) * (w + 2 + gap)
            y = gap + (i // cols) * (h + label_h + gap)
            sheet.paste(c, (x, y))
            draw.text((x + c.width / 2, y + h + 10), name, fill="#24292f", font=f, anchor="ma")
        sheet.save(OUT / "themes.png", optimize=True)
    for p in ("hero.png", "themes.png"):
        im = Image.open(OUT / p)
        print(f"wrote docs/images/{p} {im.size[0]}x{im.size[1]} {(OUT / p).stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
