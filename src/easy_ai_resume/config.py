"""Which files `build` and `tailor` use when you don't name any.

By default they look for `input/cv.yaml` and `input/cover_letter.yaml` (what
`easy-ai-resume init` creates), then for `cv.yaml` and `cover_letter.yaml` in the
current folder. An optional `easy-ai-resume.yaml` changes that or sets other defaults:

    cv: data/cv.yaml                 # default: cv.yaml
    letter: data/cover_letter.yaml   # default: cover_letter.yaml
    output: output                   # where `easy-ai-resume build` writes
    tailored: applications           # `tailor jobs/acme.md` writes to applications/acme/
    build: true                      # render PDFs after tailoring

Paths are relative to the folder that holds the file.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

CONFIG_NAME = "easy-ai-resume.yaml"
LEGACY_CONFIG_NAMES = ("cv-as-code.yaml",)  # still read, from before the rename
KEYS = ("cv", "letter", "output", "tailored", "build")
DEFAULT_CV, DEFAULT_LETTER = "cv.yaml", "cover_letter.yaml"
INPUT_DIR = "input"  # where `init` puts your files


@dataclass(frozen=True)
class Project:
    cv: Path | None = None
    letter: Path | None = None
    output: Path = Path("output")
    tailored: Path = Path("tailored")
    build: bool = False
    found: bool = False  # True when settings came from a project file


def load_project(folder: Path | None = None) -> Project:
    """Read the project file from `folder` (default: the current folder), or return defaults."""
    folder = folder or Path.cwd()

    def existing(name: str) -> Path | None:
        return next((p for p in (folder / INPUT_DIR / name, folder / name) if p.is_file()), None)

    path = next((folder / n for n in (CONFIG_NAME, *LEGACY_CONFIG_NAMES) if (folder / n).is_file()), None)
    if path is None:
        return Project(cv=existing(DEFAULT_CV), letter=existing(DEFAULT_LETTER))
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected settings like `cv: cv.yaml`")
    unknown = sorted(set(data) - set(KEYS))
    if unknown:
        raise ValueError(f"{path}: unknown setting(s) {', '.join(unknown)}; allowed: {', '.join(KEYS)}")
    root = path.parent
    return Project(
        cv=root / data["cv"] if data.get("cv") else existing(DEFAULT_CV),
        letter=root / data["letter"] if data.get("letter") else existing(DEFAULT_LETTER),
        output=root / data.get("output", "output"),
        tailored=root / data.get("tailored", "tailored"),
        build=bool(data.get("build", False)),
        found=True,
    )


def job_slug(job: Path) -> str:
    """`jobs/Acme Senior SDET.md` -> `acme-senior-sdet` (used as the tailored folder name)."""
    return re.sub(r"[^a-z0-9]+", "-", job.stem.lower()).strip("-") or "job"
