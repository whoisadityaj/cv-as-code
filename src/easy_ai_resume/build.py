"""Render CV / cover-letter YAML into HTML and PDF.

A YAML file with a top-level `sender:` block is treated as a cover letter;
anything else with a top-level `name:` is treated as a CV.
"""
from __future__ import annotations

import base64
import datetime as _dt
import re
from dataclasses import dataclass
import sys
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markdown_it import MarkdownIt
from markupsafe import Markup

TEMPLATES = Path(__file__).parent / "templates"

TEMPLATE_FOR = {"cv": "cv.html.jinja", "cover_letter": "cover_letter.html.jinja"}
STEM_SUFFIX = {"cv": "CV", "cover_letter": "Cover_Letter"}

# Named page-size presets. "single*" give one tall page so the whole CV fits
# without a page break — handy for PDFs that are only ever read on screen.
PAGE_PRESETS: dict[str, str] = {
    "a4": "A4",
    "letter": "letter",
    "legal": "legal",
    "single": "210mm 400mm",
    "single-tall": "210mm 500mm",
    "single-short": "210mm 350mm",
}


# ----------------------------------------------------------------- markdown

_md = MarkdownIt("commonmark", {"breaks": False, "html": False}).enable("table")


def md(text: str | None) -> Markup:
    """Render Markdown for INLINE contexts (inside <li>, <span>, ...).

    Strips the outer <p> when the output is a single paragraph.
    """
    if not text:
        return Markup("")
    html = _md.render(str(text).strip()).strip()
    if html.startswith("<p>") and html.endswith("</p>") and html.count("<p>") == 1:
        html = html[3:-4]
    return Markup(html)


def md_block(text: str | None) -> Markup:
    """Render Markdown for BLOCK contexts (cover-letter paragraphs, lists)."""
    if not text:
        return Markup("")
    return Markup(_md.render(str(text).strip()).strip())


def display_url(url: str | None) -> str:
    """Show `https://example.com/` as `example.com`."""
    if not url:
        return ""
    s = str(url).strip()
    for prefix in ("https://", "http://"):
        if s.startswith(prefix):
            s = s[len(prefix):]
            break
    return s.rstrip("/")


def jinja_env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES)),
        autoescape=select_autoescape(enabled_extensions=("jinja", "html")),
    )
    env.filters["md"] = md
    env.filters["md_block"] = md_block
    env.filters["display_url"] = display_url
    return env


# ----------------------------------------------------------------- input

def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"{path} not found")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a YAML mapping at the top level")
    return data


def detect_kind(data: dict[str, Any]) -> str:
    if isinstance(data.get("sender"), dict):
        return "cover_letter"
    if data.get("name"):
        return "cv"
    raise ValueError("can't tell if this is a CV (needs `name:`) or a cover letter (needs `sender:`)")


def person_name(data: dict[str, Any]) -> str:
    return str((data.get("sender") or {}).get("name") or data.get("name") or "").strip()


def output_stem(data: dict[str, Any], kind: str) -> str:
    """`Jane Doe` + cv -> `Jane_Doe_CV`."""
    slug = re.sub(r"[^A-Za-z0-9]+", "_", person_name(data)).strip("_") or "Document"
    return f"{slug}_{STEM_SUFFIX[kind]}"


# ----------------------------------------------------------------- rendering

def resolve_page_size(spec: str | None) -> str:
    """Map a preset name (`a4`, `single`, ...) or raw CSS size to an @page size.

    Returns "" to keep the stylesheet default.
    """
    if not spec:
        return ""
    key = str(spec).strip().lower()
    return PAGE_PRESETS.get(key, str(spec).strip())


def _page_size_for(data: dict[str, Any]) -> str:
    page = data.get("page")
    if isinstance(page, dict):
        page = page.get("size")
    return resolve_page_size(page)


@dataclass(frozen=True)
class Theme:
    """What a theme needs beyond its CSS file (themes/<name>.css)."""

    accent: str = "#d24f3a"  # default accent; keep in sync with the theme's CSS
    layout: str = "single"  # "single" column or two-column "sidebar" CV
    photo: bool = False  # show `photo:` if the YAML has one
    cv_band: bool = False  # paint a full-height accent column on CV pages
    letter_band: bool = False  # paint a full-height accent sidebar on cover letters


THEMES: dict[str, Theme] = {
    "bold": Theme(accent="#7c3aed", photo=True, letter_band=True),
    "classic": Theme(),
    "compact": Theme(),
    "minimal": Theme(accent="#111827"),
    "modern": Theme(accent="#2563eb", letter_band=True),
    "executive": Theme(accent="#a67c37", photo=True),
    "sidebar": Theme(accent="#1e3a5f", layout="sidebar", photo=True, cv_band=True, letter_band=True),
}


def theme_names() -> list[str]:
    return sorted(THEMES)


def get_theme(name: str) -> Theme:
    if name not in THEMES:
        raise ValueError(f"unknown theme {name!r}; choose from {', '.join(theme_names())}")
    return THEMES[name]


def _tint(colour: str, amount: float = 0.6) -> str | None:
    """Mix a hex colour with white, e.g. a light version of the accent for dark panels."""
    hexpart = colour.lstrip("#")
    if len(hexpart) == 3:
        hexpart = "".join(c * 2 for c in hexpart)
    if not colour.startswith("#") or len(hexpart) != 6:
        return None  # named colours keep the theme's default light accent
    rgb = [int(hexpart[i : i + 2], 16) for i in (0, 2, 4)]
    return "#" + "".join(f"{round(c + (255 - c) * amount):02x}" for c in rgb)


def _band(page: str, colour: str, width: str) -> str:
    # WeasyPrint doesn't resolve var() inside @page, so the band gets the literal colour.
    # The page paints it edge to edge; root and column backgrounds must stay transparent.
    return (
        f"{page} {{ background: linear-gradient(90deg, {colour} {width}, #ffffff {width}) no-repeat; }}\n"
        "html, body { background: transparent; }\n"
        ".letter .sidebar, .sidebar-layout .side { background: transparent; }"
    )


def stylesheet(theme: str, ats: bool, accent: str | None, kind: str = "cv") -> str:
    """Base CSS + theme layer (+ ATS layer), with an optional accent colour."""
    spec = get_theme(theme)
    css = [(TEMPLATES / "style.css").read_text(encoding="utf-8")]
    css.append((TEMPLATES / "themes" / f"{theme}.css").read_text(encoding="utf-8"))
    if accent:
        if not re.fullmatch(r"#[0-9a-fA-F]{3,8}|[a-zA-Z]+", str(accent)):
            raise ValueError(f"accent must be a hex colour like #2563eb, got {accent!r}")
        soft = _tint(str(accent))
        css.append(f":root {{ --accent: {accent};{f' --accent-soft: {soft};' if soft else ''} }}")
    colour = accent or spec.accent
    if not ats and kind == "cv" and spec.cv_band:
        css.append(_band("@page", colour, "34%"))
    if not ats and kind == "cover_letter" and spec.letter_band:
        css.append(_band("@page cover-letter", colour, "33%"))
    if ats:
        css.append((TEMPLATES / "themes" / "ats.css").read_text(encoding="utf-8"))
    return "\n".join(css)


PHOTO_TYPES = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
    ".webp": "image/webp", ".gif": "image/gif", ".svg": "image/svg+xml",
}


def photo_src(value: str, base_dir: Path | None = None) -> str:
    """Turn a `photo:` value into an <img> src.

    Local files (relative to the YAML file) are embedded as data URIs so the
    HTML and PDF are self-contained. URLs are passed through.
    """
    s = str(value).strip()
    if s.startswith(("http://", "https://", "data:")):
        return s
    path = Path(s).expanduser()
    if not path.is_absolute():
        path = (base_dir or Path.cwd()) / path
    if not path.is_file():
        raise ValueError(f"photo not found: {path}")
    mime = PHOTO_TYPES.get(path.suffix.lower())
    if not mime:
        raise ValueError(f"unsupported photo type {path.suffix!r}; use jpg, png, webp or svg")
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def render(
    data: dict[str, Any],
    kind: str,
    page_size: str = "",
    theme: str | None = None,
    ats: bool | None = None,
    base_dir: Path | None = None,
) -> str:
    """Render one document. CLI options (theme, ats) override the YAML settings.

    `base_dir` is where relative paths in the YAML (like `photo:`) are looked up.
    """
    ats = bool(data.get("ats")) if ats is None else ats
    theme = theme or data.get("theme") or "classic"
    spec = get_theme(theme)
    layout = "single" if ats else spec.layout
    ctx: dict[str, Any] = {
        "data": data,
        "css": stylesheet(theme, ats, data.get("accent"), kind),
        "page_size": page_size or _page_size_for(data),
        "ats": ats,
        "theme": theme,
        "layout": layout,
        "photo": None,
        "stacked_contacts": layout == "sidebar",
    }
    photo = data.get("photo") if kind == "cv" else (data.get("sender") or {}).get("photo")
    if photo and spec.photo and not ats:  # photos never go in ATS output
        ctx["photo"] = photo_src(photo, base_dir)
    if kind == "cover_letter":
        raw_date = data.get("date") or "auto"
        if str(raw_date).strip().lower() == "auto":
            ctx["rendered_date"] = _dt.date.today().strftime(data.get("date_format") or "%d %B %Y")
        else:
            ctx["rendered_date"] = str(raw_date)

        salutation = data.get("salutation") or "Dear Hiring Manager,"
        manager = (data.get("recipient") or {}).get("hiring_manager")
        if manager and salutation.strip().lower() in ("hi there,", "dear hiring manager,"):
            salutation = f"Dear {manager},"
        ctx["rendered_salutation"] = salutation
    return jinja_env().get_template(TEMPLATE_FOR[kind]).render(**ctx)


def write_pdf(html: str, out_pdf: Path) -> bool:
    """Write a PDF with WeasyPrint. Returns False (with a hint) if it isn't usable."""
    try:
        from weasyprint import HTML  # type: ignore
    except Exception as e:  # ImportError or missing native libraries (Pango)
        print(
            f"warning: PDF skipped, WeasyPrint is not usable ({e.__class__.__name__}: {str(e)[:120]}).\n"
            "         See https://doc.courtbouillon.org/weasyprint/stable/first_steps.html\n"
            "         (macOS + Homebrew: brew install pango, then\n"
            "          export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib)\n"
            "         or open the HTML in a browser and use Print -> Save as PDF.",
            file=sys.stderr,
        )
        return False
    HTML(string=html, base_url=str(TEMPLATES)).write_pdf(str(out_pdf))
    return True


def build_file(
    path: Path,
    out_dir: Path,
    page_size: str = "",
    pdf: bool = True,
    theme: str | None = None,
    ats: bool | None = None,
) -> list[Path]:
    """Render one YAML file. Returns the files written (HTML first)."""
    data = load_yaml(path)
    kind = detect_kind(data)
    html = render(data, kind, page_size=resolve_page_size(page_size), theme=theme, ats=ats, base_dir=path.parent)

    out_dir.mkdir(parents=True, exist_ok=True)
    stem = output_stem(data, kind)
    out_html = out_dir / f"{stem}.html"
    out_html.write_text(html, encoding="utf-8")
    written = [out_html]
    if pdf and write_pdf(html, out_dir / f"{stem}.pdf"):
        written.append(out_dir / f"{stem}.pdf")
    return written
