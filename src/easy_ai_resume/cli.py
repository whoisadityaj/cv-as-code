"""Command line: `easy-ai-resume init`, `build` and `tailor`."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .build import PAGE_PRESETS, build_file, theme_names
from .config import CONFIG_NAME, job_slug, load_project


def cmd_init(args: argparse.Namespace) -> int:
    from .starter import init

    try:
        written = init(args.folder, force=args.force)
    except FileExistsError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    for p in written:
        print(f"wrote {p}")
    print("\nNext: put your details in input/cv.yaml, then run:  easy-ai-resume build")
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    try:
        project = load_project()
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    files = args.files or [p for p in (project.cv, project.letter) if p]
    if not files:
        print(f"error: no input/cv.yaml or input/cover_letter.yaml in {Path.cwd()}. "
              "Run `easy-ai-resume init` to create them, or name the YAML files to build.", file=sys.stderr)
        return 1
    out = args.out or project.output
    from .ask_photo import offer_photo

    offer_photo(files, args.theme, True if args.ats else None)  # only asks in a terminal
    missing_pdf = False
    for path in files:
        try:
            written = build_file(
                path, out, page_size=args.page_size, pdf=not args.html_only,
                theme=args.theme, ats=True if args.ats else None, html=args.html, accent=args.accent,
            )
        except (FileNotFoundError, ValueError) as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        for p in written:
            print(f"wrote {p}")
        missing_pdf |= not args.html_only and not any(p.suffix == ".pdf" for p in written)
    if missing_pdf:
        print("error: PDF generation failed. Run again with --html-only to get an HTML file, open it "
              "in a browser and use Print -> Save as PDF.", file=sys.stderr)
        return 1
    return 0


def cmd_tailor(args: argparse.Namespace) -> int:
    from .tailor import TailorError, tailor

    try:
        project = load_project()
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    cv, letter = args.cv or project.cv, args.letter or project.letter
    if not cv or not letter:
        print(f"error: need a CV and cover letter: put cv.yaml and cover_letter.yaml in input/, pass --cv and "
              f"--letter, or set cv: and letter: in {CONFIG_NAME}", file=sys.stderr)
        return 1
    out = args.out or project.tailored / job_slug(args.jd)
    look = {"theme": args.theme, "accent": args.accent, "ats": True if args.ats else None}
    asked_for_look = any(v is not None for v in look.values())
    build = (project.build or asked_for_look) if args.build is None else args.build
    for p in (args.jd, cv, letter):
        if not p.exists():
            print(f"error: {p} not found", file=sys.stderr)
            return 1
    try:
        out_cv, out_letter, notes, warns = tailor(
            args.jd, cv, letter, out,
            provider=args.provider, model=args.model, force=args.force,
        )
    except TailorError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    print(f"wrote {out_cv}\nwrote {out_letter}")
    if notes:
        print(f"\nWhat changed:\n{notes}")
    if warns:
        print("\nCheck these before sending (possible invented or changed facts):", file=sys.stderr)
        for w in warns:
            print(f"  - {w}", file=sys.stderr)
    if build:
        for path in (out_cv, out_letter):
            try:
                written = build_file(path, out, **look)
            except (FileNotFoundError, ValueError) as e:
                print(f"error: {e}", file=sys.stderr)
                return 1
            for p in written:
                print(f"wrote {p}")
    print(f"\nReview what changed before sending:\n  diff -u {cv} {out_cv}\n  diff -u {letter} {out_letter}")
    return 2 if warns and args.strict else 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="easy-ai-resume", description="Easy AI resume: YAML in, clean PDF out, tailored to any job.")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    i = sub.add_parser("init", help="Create input/ with starter cv.yaml, cover_letter.yaml, job.md and a sample photo.")
    i.add_argument("folder", nargs="?", type=Path, default=Path("."), help="Folder to create input/ in (default: here).")
    i.add_argument("--force", action="store_true", help="Overwrite files that already exist.")
    i.set_defaults(func=cmd_init)

    b = sub.add_parser("build", help="Render CV / cover-letter YAML files to HTML and PDF.")
    b.add_argument("files", nargs="*", type=Path,
                   help="YAML files (CV or cover letter, detected automatically). Default: input/cv.yaml and input/cover_letter.yaml.")
    b.add_argument("--out", type=Path, help=f"Output directory (default: ./output, or `output:` in {CONFIG_NAME}).")
    b.add_argument(
        "--page-size", default="",
        help=f"Preset ({', '.join(PAGE_PRESETS)}), 'fit' (one page exactly as tall as the content) "
             "or a CSS size like '210mm 380mm'.",
    )
    b.add_argument("--theme", choices=theme_names(), help="Override the YAML `theme:` (default: classic).")
    b.add_argument("--accent", help="Override the YAML `accent:` colour, e.g. '#0f766e' (default: '#9b1b30', deep red).")
    b.add_argument("--ats", action="store_true", help="Plain single-column output that applicant-tracking systems parse well.")
    html = b.add_mutually_exclusive_group()
    html.add_argument("--html", action="store_true", help="Also write the HTML file (by default only the PDF is written).")
    html.add_argument("--html-only", action="store_true", help="Write only the HTML file, no PDF.")
    b.set_defaults(func=cmd_build)

    t = sub.add_parser("tailor", help="Tailor your CV and cover letter to a job description with AI.")
    t.add_argument("jd", type=Path, help="Job description (text or Markdown file).")
    t.add_argument("--cv", type=Path, help="Your CV YAML (default: input/cv.yaml).")
    t.add_argument("--letter", type=Path, help="Your cover-letter YAML (default: input/cover_letter.yaml).")
    t.add_argument("--out", type=Path,
                   help="Folder for the tailored YAML and PDFs (default: tailored/<job file name>, "
                        f"or `tailored:` in {CONFIG_NAME}).")
    t.add_argument("--provider", choices=["auto", "claude", "codex", "opencode", "anthropic", "openai"], default="auto",
                   help="auto (default) tries your installed subscription tools (claude, codex, opencode), "
                        "then API keys (anthropic, openai).")
    t.add_argument("--model", help="Model name for the chosen provider (default: the tool's own default; "
                                   "required for the OpenAI API).")
    t.add_argument("--build", action=argparse.BooleanOptionalAction, default=None,
                   help=f"Also make the tailored PDFs (default: yes if --theme, --accent or --ats is given, "
                        f"else `build:` in {CONFIG_NAME}, else no).")
    t.add_argument("--theme", choices=theme_names(), help="Theme for the tailored PDFs (default: the YAML `theme:`).")
    t.add_argument("--accent", help="Accent colour for the tailored PDFs, e.g. '#0f766e' (default: the YAML `accent:`, else deep red).")
    t.add_argument("--ats", action="store_true", help="Make the tailored PDFs in plain ATS-friendly mode.")
    t.add_argument("--force", action="store_true", help="Overwrite existing files in --out.")
    t.add_argument("--strict", action="store_true", help="Exit with code 2 if the fact check raises warnings.")
    t.set_defaults(func=cmd_tailor)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
