"""Generate the animated SVGs used on the README landing page.

    python docs/make_animations.py   ->  docs/images/banner.svg, docs/images/demo.svg

GitHub shows README images through <img>, so these use SMIL animation only:
no JavaScript, no web fonts, no external references.
"""
from __future__ import annotations

from html import escape
from pathlib import Path

OUT = Path(__file__).parent / "images"

# Dark "royal / Dracula" red brand palette.
BG, PANEL, BORDER = "#14060a", "#220b11", "#4a1d27"
TEXT, MUTED = "#f4e9eb", "#b49aa0"
BRAND, BRIGHT, PINK, ORANGE, RED = "#b3122e", "#ff5c74", "#ff79c6", "#ffb86c", "#ff5555"
KEY, STR = PINK, "#f1fa8c"  # Dracula syntax colours
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
SERIF = "Georgia, 'Times New Roman', serif"


def appear(at: float, cycle: float, hide: float, dy: float = 6) -> str:
    """Fade + slide in at `at` seconds, stay until `hide`, fade out, repeat every `cycle`."""
    a, b, h1, h2 = at / cycle, (at + 0.35) / cycle, hide / cycle, (hide + 0.4) / cycle
    kt = f"0;{a:.4f};{b:.4f};{h1:.4f};{h2:.4f};1"
    return (
        f'<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="{kt}" dur="{cycle}s" repeatCount="indefinite"/>'
        f'<animateTransform attributeName="transform" type="translate" values="0 {dy};0 {dy};0 0;0 0;0 0;0 {dy}" '
        f'keyTimes="{kt}" dur="{cycle}s" repeatCount="indefinite"/>'
    )


def typed(text: str, x: float, y: float, at: float, secs: float, cycle: float, hide: float, size: int, uid: str) -> str:
    """Monospace text revealed left to right, like typing."""
    width = len(text) * size * 0.62 + 4
    a, b, h1, h2 = at / cycle, (at + secs) / cycle, hide / cycle, (hide + 0.4) / cycle
    kt = f"0;{a:.4f};{b:.4f};{h1:.4f};{h2:.4f};1"
    return (
        f'<clipPath id="{uid}"><rect x="{x}" y="{y - size}" height="{size + 8}" width="0">'
        f'<animate attributeName="width" values="0;0;{width:.0f};{width:.0f};{width:.0f};0" keyTimes="{kt}" '
        f'dur="{cycle}s" repeatCount="indefinite"/></rect></clipPath>'
        f'<g clip-path="url(#{uid})"><text x="{x}" y="{y}" font-family="{MONO}" font-size="{size}" fill="{TEXT}">'
        f"{escape(text)}<animate attributeName=\"opacity\" values=\"1;1;0;0\" keyTimes=\"0;{h1:.4f};{h2:.4f};1\" "
        f'dur="{cycle}s" repeatCount="indefinite"/></text></g>'
    )


# ----------------------------------------------------------------- banner

def banner() -> str:
    W, H, C, HIDE = 1200, 470, 11.0, 10.0
    yaml_lines = [  # (indent, key, value, paper element to reveal)
        (0, "name", "Jane Doe", "name"),
        (0, "title", "Senior Backend Engineer", "title"),
        (0, "theme", "modern", "accent"),
        (0, "experience", "", "heading"),
        (1, "- role", "Senior Backend Engineer", "role"),
        (2, "company", "Globex Payments", "company"),
        (2, "bullets", "", None),
        (3, "-", "Cut p95 latency 820 ms → 190 ms", "bullet1"),
        (3, "-", "Migrated 40M records, zero downtime", "bullet2"),
    ]
    px, py, pw, ph = 690, 170, 450, 262  # paper
    start, step = 1.0, 0.55
    reveal = {}
    rows = []
    for i, (indent, key, value, target) in enumerate(yaml_lines):
        t = start + i * step
        if target:
            reveal[target] = t + 0.25
        x, y = 92 + indent * 20, 214 + i * 24
        dash = key.startswith("-")
        k = key.lstrip("- ")
        parts = []
        if dash:
            parts.append(f'<tspan fill="{RED}">- </tspan>')
        if k:
            parts.append(f'<tspan fill="{KEY}">{escape(k)}</tspan><tspan fill="{MUTED}">: </tspan>')
        if value:
            parts.append(f'<tspan fill="{STR}">{escape(value)}</tspan>')
        rows.append(f'<g opacity="0">{appear(t, C, HIDE, 0)}<text x="{x}" y="{y}" font-family="{MONO}" '
                    f'font-size="15">{"".join(parts)}</text></g>')

    def on_paper(name: str, body: str) -> str:
        return f'<g opacity="0">{appear(reveal[name], C, HIDE)}{body}</g>'

    bar = lambda x, y, w, c="#d0d7de", h=7: f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3.5" fill="{c}"/>'  # noqa: E731
    paper = "".join([
        on_paper("accent", f'<rect x="{px + 28}" y="{py + 26}" width="5" height="56" rx="2.5" fill="{BRAND}"/>'),
        on_paper("name", f'<text x="{px + 44}" y="{py + 56}" font-family="{SANS}" font-weight="700" font-size="28" fill="#111">Jane Doe</text>'),
        on_paper("title", f'<text x="{px + 44}" y="{py + 78}" font-family="{SANS}" font-weight="600" font-size="14" fill="{BRAND}">Senior Backend Engineer</text>'),
        on_paper("heading", f'<text x="{px + 30}" y="{py + 116}" font-family="{SANS}" font-weight="700" font-size="11" letter-spacing="1.6" fill="{BRAND}">EXPERIENCE</text>'),
        on_paper("role", f'<text x="{px + 30}" y="{py + 140}" font-family="{SANS}" font-weight="700" font-size="13" fill="#111">Senior Backend Engineer</text>'
                         f'<text x="{px + pw - 30}" y="{py + 140}" text-anchor="end" font-family="{SANS}" font-size="12" fill="#57606a">2022 – Present</text>'),
        on_paper("company", f'<text x="{px + 30}" y="{py + 159}" font-family="{SANS}" font-weight="600" font-size="12" fill="#24292f">Globex Payments</text>'),
        on_paper("bullet1", f'<circle cx="{px + 36}" cy="{py + 181}" r="2.2" fill="#24292f"/>' + bar(px + 46, py + 177, 300)),
        on_paper("bullet2", f'<circle cx="{px + 36}" cy="{py + 201}" r="2.2" fill="#24292f"/>' + bar(px + 46, py + 197, 250)
                            + f'<circle cx="{px + 36}" cy="{py + 221}" r="2.2" fill="#24292f"/>' + bar(px + 46, py + 217, 280)),
    ])
    done = start + len(yaml_lines) * step + 0.5
    badge = (f'<g opacity="0">{appear(done, C, HIDE, 10)}'
             f'<rect x="{px + pw - 116}" y="{py + ph - 20}" width="132" height="40" rx="20" fill="{BRAND}"/>'
             f'<text x="{px + pw - 50}" y="{py + ph + 6}" text-anchor="middle" font-family="{SANS}" font-weight="700" '
             f'font-size="16" fill="#ffffff">PDF ready ✓</text></g>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="easy-ai-resume: YAML in, PDF out. Your CV as code.">
  <defs>
    <radialGradient id="glow" cx="80%" cy="0%" r="70%"><stop offset="0" stop-color="{BRAND}" stop-opacity=".45"/><stop offset="1" stop-color="{BRAND}" stop-opacity="0"/></radialGradient>
    <linearGradient id="arrow" x1="0" x2="1"><stop offset="0" stop-color="{BRIGHT}" stop-opacity=".2"/><stop offset="1" stop-color="{BRIGHT}"/></linearGradient>
  </defs>
  <rect width="{W}" height="{H}" rx="24" fill="{BG}"/>
  <rect width="{W}" height="{H}" rx="24" fill="url(#glow)"/>
  <rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="24" fill="none" stroke="{BORDER}"/>

  <text x="60" y="86" font-family="{MONO}" font-weight="700" font-size="46" fill="{TEXT}">easy<tspan fill="{BRIGHT}">-ai-</tspan>resume</text>
  <text x="60" y="124" font-family="{SANS}" font-size="20" fill="{MUTED}">Your CV lives in YAML. Build a clean PDF. AI tailors the YAML to each job, fact-checked.</text>

  <rect x="60" y="170" width="560" height="262" rx="14" fill="{PANEL}" stroke="{BORDER}"/>
  <circle cx="82" cy="189" r="5" fill="#ff5f57"/><circle cx="100" cy="189" r="5" fill="#febc2e"/><circle cx="118" cy="189" r="5" fill="#28c840"/>
  <text x="600" y="194" text-anchor="end" font-family="{MONO}" font-size="12" fill="{MUTED}">cv.yaml</text>
  {"".join(rows)}

  <g transform="translate(630 284)">
    <rect width="48" height="6" rx="3" fill="url(#arrow)"/>
    <path d="M44 -7 L58 3 L44 13 Z" fill="{BRIGHT}"/>
    <animateTransform attributeName="transform" type="translate" values="626 284;636 284;626 284" dur="1.4s" repeatCount="indefinite"/>
  </g>

  <rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="10" fill="#ffffff"/>
  {paper}
  {badge}
</svg>
'''


# ----------------------------------------------------------------- terminal demo

def demo() -> str:
    W, H, C, HIDE = 1000, 430, 16.0, 14.6
    size, x0, lh = 15, 40, 26
    y = lambda row: 92 + row * lh  # noqa: E731
    out = []

    def line(row: int, at: float, text: str, colour: str = MUTED, prefix: str = "") -> None:
        out.append(f'<g opacity="0">{appear(at, C, HIDE, 0)}<text x="{x0}" y="{y(row)}" font-family="{MONO}" '
                   f'font-size="{size}" fill="{colour}">{prefix}{escape(text).replace(" ", "\u00a0")}</text></g>')

    def prompt(row: int, at: float, cmd: str, secs: float, uid: str) -> None:
        out.append(f'<g opacity="0">{appear(at - 0.3, C, HIDE, 0)}<text x="{x0}" y="{y(row)}" font-family="{MONO}" '
                   f'font-size="{size}" fill="{BRIGHT}">$</text></g>')
        out.append(typed(cmd, x0 + 20, y(row), at, secs, C, HIDE, size, uid))

    # Output lines match what the CLI really prints.
    prompt(0, 0.8, "easy-ai-resume build cv.yaml --theme modern", 1.3, "c1")
    line(1, 2.4, "wrote output/Jane_Doe_CV.html")
    line(2, 2.6, "wrote output/Jane_Doe_CV.pdf", TEXT)
    prompt(4, 4.0, "easy-ai-resume tailor job.md --cv cv.yaml --letter cover_letter.yaml --out tailored/umbrella", 2.4, "c2")
    line(5, 6.8, "wrote tailored/umbrella/cv.yaml", TEXT)
    line(6, 7.0, "wrote tailored/umbrella/cover_letter.yaml", TEXT)
    line(7, 7.9, "Check these before sending (possible invented or changed facts):", ORANGE)
    line(8, 8.4, "  - numbers not in your originals (check metrics): 65%", ORANGE)
    line(9, 8.7, "  - skills not in original: rust", ORANGE)
    line(11, 9.8, "# the AI rewords. easy-ai-resume makes sure it doesn't invent.", PINK)

    cursor_at = 10.4
    cursor = (f'<rect x="{x0}" y="{y(12) - 14}" width="9" height="18" fill="{TEXT}" opacity="0">'
              f'<animate attributeName="opacity" values="0;0;1;0;1;0;1;0;0" '
              f'keyTimes="0;{cursor_at / C:.4f};{(cursor_at + .5) / C:.4f};{(cursor_at + 1) / C:.4f};{(cursor_at + 1.5) / C:.4f};'
              f'{(cursor_at + 2) / C:.4f};{(cursor_at + 2.5) / C:.4f};{HIDE / C:.4f};1" calcMode="discrete" dur="{C}s" '
              f'repeatCount="indefinite"/></rect>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Terminal demo: easy-ai-resume builds PDFs, then tailors a CV and flags an invented number and skill.">
  <rect width="{W}" height="{H}" rx="16" fill="{BG}"/>
  <rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="none" stroke="{BORDER}"/>
  <path d="M0 16 Q0 0 16 0 H{W - 16} Q{W} 0 {W} 16 V44 H0 Z" fill="{PANEL}"/>
  <line x1="0" y1="44" x2="{W}" y2="44" stroke="{BORDER}"/>
  <circle cx="24" cy="22" r="6" fill="#ff5f57"/><circle cx="44" cy="22" r="6" fill="#febc2e"/><circle cx="64" cy="22" r="6" fill="#28c840"/>
  <text x="{W / 2}" y="27" text-anchor="middle" font-family="{SANS}" font-size="13" fill="{MUTED}">~/my-cv</text>
  {"".join(out)}
  {cursor}
</svg>
'''


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    (OUT / "banner.svg").write_text(banner(), encoding="utf-8")
    (OUT / "demo.svg").write_text(demo(), encoding="utf-8")
    print("wrote", OUT / "banner.svg", "and", OUT / "demo.svg")
