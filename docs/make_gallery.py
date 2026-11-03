"""Render every theme from the examples and build the README showcase images.

    python docs/make_gallery.py   ->  docs/images/showcase.png, docs/images/gallery.png

Needs WeasyPrint working, Pillow (installed with WeasyPrint) and `pdftoppm`
from Poppler (`brew install poppler` / `apt install poppler-utils`).
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from cv_as_code.build import THEMES, build_file, theme_names

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples"
OUT = ROOT / "docs" / "images"

DARK, DARK_2, LIGHT = (11, 16, 32), (24, 33, 60), (241, 244, 249)
WHITE, INK, MUTED_DARK, MUTED_LIGHT = (255, 255, 255), (17, 24, 39), (148, 163, 184), (100, 116, 139)
PHOTO_ORDER = ["sidebar", "bold", "executive"]
CLEAN_ORDER = ["modern", "minimal", "classic", "compact"]


# ----------------------------------------------------------------- rendering

def snapshot(yaml_name: str, theme: str, tmp: Path, ats: bool = False) -> Image.Image:
    out = tmp / f"{theme}{'-ats' if ats else ''}"
    pdf = next(p for p in build_file(EXAMPLES / yaml_name, out, theme=theme, ats=ats) if p.suffix == ".pdf")
    subprocess.run(["pdftoppm", "-png", "-r", "150", "-singlefile", str(pdf), str(pdf.with_suffix(""))], check=True)
    return Image.open(pdf.with_suffix(".png")).convert("RGB")


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
        if bold
        else ["/System/Library/Fonts/Supplemental/Arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    )
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


# ----------------------------------------------------------------- compositing helpers

def page(im: Image.Image, width: int, radius: int = 10) -> Image.Image:
    """Resize a rendered page and round its corners (RGBA)."""
    im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=radius, fill=255)
    im.putalpha(mask)
    return im


def place(canvas: Image.Image, im: Image.Image, center: tuple[int, int], angle: float = 0,
          shadow: int = 140, blur: int = 28, drop: int = 26) -> None:
    """Paste `im` centred at `center`, optionally rotated, over a soft drop shadow."""
    if angle:
        im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    x, y = center[0] - im.width // 2, center[1] - im.height // 2
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    alpha = im.getchannel("A").point(lambda a: shadow if a > 0 else 0)
    sh.paste(Image.new("RGBA", im.size, (0, 0, 0, 255)), (x, y + drop), alpha)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    canvas.alpha_composite(sh)
    canvas.alpha_composite(im, (x, y))


def glow(canvas: Image.Image, center: tuple[int, int], radius: int, colour: tuple[int, int, int], strength: int) -> None:
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    cx, cy = center
    ImageDraw.Draw(layer).ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=colour + (strength,))
    canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(radius // 2)))


def vertical_gradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    w, h = size
    im = Image.new("RGBA", size)
    d = ImageDraw.Draw(im)
    for y in range(h):
        t = y / max(h - 1, 1)
        d.line([(0, y), (w, y)], fill=tuple(round(a + (b - a) * t) for a, b in zip(top, bottom)) + (255,))
    return im


def mono(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in ("/System/Library/Fonts/Menlo.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def text_with_code(draw: ImageDraw.ImageDraw, xy: tuple[int, int], parts: list[str], fill, code_fg, code_bg) -> None:
    """Draw a sentence where every odd-numbered part is shown as inline code."""
    x, y = xy
    for i, part in enumerate(parts):
        if i % 2:
            f = mono(20)
            w = draw.textlength(part, font=f)
            draw.rounded_rectangle([x, y - 2, x + w + 16, y + 30], radius=7, fill=code_bg)
            draw.text((x + 8, y + 3), part, font=f, fill=code_fg)
            x += w + 22
        else:
            f = font(22)
            draw.text((x, y), part, font=f, fill=fill)
            x += draw.textlength(part, font=f) + 6


def pill(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, fg, bg, size: int = 18) -> int:
    f = font(size, bold=True)
    x, y = xy
    w = draw.textlength(text, font=f) + 26
    draw.rounded_rectangle([x, y, x + w, y + size + 14], radius=(size + 14) // 2, fill=bg)
    draw.text((x + 13, y + 7), text, font=f, fill=fg)
    return int(w)


# ----------------------------------------------------------------- images

def showcase(shots: dict[str, Image.Image], letters: dict[str, Image.Image]) -> Image.Image:
    """Dark/light diagonal split with three pages fanned out."""
    W, H = 1600, 980
    canvas = vertical_gradient((W, H), DARK, DARK_2)
    light = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(light).polygon([(W * 0.62, 0), (W, 0), (W, H), (W * 0.40, H)], fill=LIGHT + (255,))
    canvas.alpha_composite(light)
    glow(canvas, (300, 260), 360, (59, 130, 246), 90)
    glow(canvas, (1350, 760), 300, (124, 58, 237), 40)

    d = ImageDraw.Draw(canvas)
    d.text((80, 70), "One YAML file.", font=font(54, bold=True), fill=WHITE)
    d.text((80, 134), "Seven good-looking PDFs.", font=font(54, bold=True), fill=(147, 197, 253))
    d.text((W - 80, H - 60), "every page rendered by cv-as-code from examples/", font=font(20), fill=MUTED_LIGHT, anchor="rs")

    place(canvas, page(letters["bold"], 400), (470, 610), angle=8)
    place(canvas, page(shots["executive"], 400), (1150, 560), angle=-7)
    place(canvas, page(shots["sidebar"], 470), (810, 600), shadow=170, blur=34, drop=30)
    return canvas


def gallery(shots: dict[str, Image.Image]) -> Image.Image:
    """Dark band with the photo themes, light band with the clean ones and ATS mode."""
    W, pad = 1600, 70
    big_w, small_w = 420, 236
    big_h = round(shots["sidebar"].height * big_w / shots["sidebar"].width)
    small_h = round(shots["classic"].height * small_w / shots["classic"].width)
    dark_h = 150 + big_h + 110
    light_h = 150 + small_h + 110
    canvas = Image.new("RGBA", (W, dark_h + light_h), LIGHT + (255,))
    canvas.alpha_composite(vertical_gradient((W, dark_h), DARK, DARK_2))
    glow(canvas, (W // 2, 120), 420, (59, 130, 246), 70)

    d = ImageDraw.Draw(canvas)
    d.text((pad, 52), "Photo themes", font=font(44, bold=True), fill=WHITE)
    text_with_code(d, (pad, 106), ["Add", "photo: me.jpg", "to your YAML and pick one. ATS mode always leaves the photo out."],
                   MUTED_DARK, (191, 219, 254), (30, 41, 70))
    gap = (W - 2 * pad - 3 * big_w) // 2
    for i, name in enumerate(PHOTO_ORDER):
        cx = pad + big_w // 2 + i * (big_w + gap)
        place(canvas, page(shots[name], big_w), (cx, 150 + big_h // 2 + 10), shadow=190, blur=26, drop=22)
        label_y = 150 + big_h + 46
        d.text((cx, label_y), name, font=font(30, bold=True), fill=WHITE, anchor="mm")

    top = dark_h
    d.text((pad, top + 52), "Clean themes", font=font(44, bold=True), fill=INK)
    text_with_code(d, (pad, top + 106), ["Single column, easy to skim.", "--ats", "gives plain text that hiring software parses cleanly."],
                   MUTED_LIGHT, (30, 41, 59), (226, 232, 240))
    names = CLEAN_ORDER + ["ATS mode"]
    gap = (W - 2 * pad - len(names) * small_w) // (len(names) - 1)
    for i, name in enumerate(names):
        cx = pad + small_w // 2 + i * (small_w + gap)
        place(canvas, page(shots[name], small_w, radius=8), (cx, top + 150 + small_h // 2 + 6), shadow=70, blur=16, drop=12)
        d.text((cx, top + 150 + small_h + 44), name, font=font(24, bold=True), fill=INK, anchor="mm")
    return canvas


def main() -> None:
    assert sorted(PHOTO_ORDER + CLEAN_ORDER) == theme_names(), "update the ORDER lists when adding a theme"
    assert all(THEMES[n].photo for n in PHOTO_ORDER) and not any(THEMES[n].photo for n in CLEAN_ORDER)
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        shots = {name: snapshot("cv.yaml", name, tmp) for name in theme_names()}
        shots["ATS mode"] = snapshot("cv.yaml", "classic", tmp, ats=True)
        letters = {"bold": snapshot("cover_letter.yaml", "bold", tmp)}
        images = {"showcase.png": showcase(shots, letters), "gallery.png": gallery(shots)}
    for name, im in images.items():
        im.convert("RGB").save(OUT / name, optimize=True)
        print(f"wrote docs/images/{name} {im.width}x{im.height} {(OUT / name).stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
