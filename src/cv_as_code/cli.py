"""Command line: `cv-as-code build ...` and `cv-as-code tailor ...`."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .build import PAGE_PRESETS, build_file, theme_names


def cmd_init(args: argparse.Namespace) -> int:
    from .starter import init

    try:
        written = init(args.folder, force=args.force)
    except FileExistsError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    for p in written:
        print(f"wrote {p}")
    print("\nNext: edit cv.yaml, then run:  cv-as-code build cv.yaml")
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    missing_pdf = False
    for path in args.files:
        try:
            written = build_file(
                path, args.out, page_size=args.page_size, pdf=not args.html_only,
                theme=args.theme, ats=True if args.ats else None,
            )
        except (FileNotFoundError, ValueError) as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        for p in written:
            print(f"wrote {p}")
        missing_pdf |= not args.html_only and not any(p.suffix == ".pdf" for p in written)
    if missing_pdf:
        print("error: HTML was written but PDF generation failed (use --html-only to skip PDFs).", file=sys.stderr)
        return 1
    return 0


def cmd_tailor(args: argparse.Namespace) -> int:
    from .tailor import TailorError, tailor

    for p in (args.jd, args.cv, args.letter):
        if not p.exists():
            print(f"error: {p} not found", file=sys.stderr)
            return 1
    try:
        out_cv, out_letter, notes, warns = tailor(
            args.jd, args.cv, args.letter, args.out,
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
    if args.build:
        for path in (out_cv, out_letter):
            for p in build_file(path, args.out):
                print(f"wrote {p}")
    return 2 if warns and args.strict else 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="cv-as-code", description="Your CV as code: YAML in, clean PDF out.")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    i = sub.add_parser("init", help="Create starter cv.yaml, cover_letter.yaml, job.md and a sample photo.")
    i.add_argument("folder", nargs="?", type=Path, default=Path("."), help="Where to put them (default: here).")
    i.add_argument("--force", action="store_true", help="Overwrite files that already exist.")
    i.set_defaults(func=cmd_init)

    b = sub.add_parser("build", help="Render CV / cover-letter YAML files to HTML and PDF.")
    b.add_argument("files", nargs="+", type=Path, help="YAML files (CV or cover letter, detected automatically).")
    b.add_argument("--out", type=Path, default=Path("output"), help="Output directory (default: ./output).")
    b.add_argument(
        "--page-size", default="",
        help=f"Preset ({', '.join(PAGE_PRESETS)}) or a CSS size like '210mm 380mm'.",
    )
    b.add_argument("--theme", choices=theme_names(), help="Override the YAML `theme:` (default: classic).")
    b.add_argument("--ats", action="store_true", help="Plain single-column output that applicant-tracking systems parse well.")
    b.add_argument("--html-only", action="store_true", help="Skip PDF generation.")
    b.set_defaults(func=cmd_build)

    t = sub.add_parser("tailor", help="Tailor your CV and cover letter to a job description with AI.")
    t.add_argument("jd", type=Path, help="Job description (text or Markdown file).")
    t.add_argument("--cv", type=Path, required=True, help="Your CV YAML.")
    t.add_argument("--letter", type=Path, required=True, help="Your cover-letter YAML.")
    t.add_argument("--out", type=Path, required=True, help="Folder for the tailored YAML (and PDFs with --build).")
    t.add_argument("--provider", choices=["auto", "anthropic", "openai"], default="auto")
    t.add_argument("--model", help="Model name (default: Anthropic's Claude Sonnet; required for OpenAI).")
    t.add_argument("--build", action="store_true", help="Also render the tailored documents.")
    t.add_argument("--force", action="store_true", help="Overwrite existing files in --out.")
    t.add_argument("--strict", action="store_true", help="Exit with code 2 if the fact check raises warnings.")
    t.set_defaults(func=cmd_tailor)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
