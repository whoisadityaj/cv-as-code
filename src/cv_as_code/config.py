"""Optional project file, `cv-as-code.yaml`, so commands work without paths.

    cv: data/cv.yaml                 # used by `build` and `tailor`
    letter: data/cover_letter.yaml
    output: output                   # where `cv-as-code build` writes
    tailored: applications           # `tailor jobs/acme.md` writes to applications/acme/
    build: true                      # render PDFs after tailoring

Paths are relative to the folder that holds the file.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

CONFIG_NAME = "cv-as-code.yaml"
KEYS = ("cv", "letter", "output", "tailored", "build")


@dataclass(frozen=True)
class Project:
    cv: Path | None = None
    letter: Path | None = None
    output: Path = Path("output")
    tailored: Path = Path("tailored")
    build: bool = False
    found: bool = False  # True when settings came from a cv-as-code.yaml


def load_project(folder: Path | None = None) -> Project:
    """Read cv-as-code.yaml from `folder` (default: the current folder), or return defaults."""
    path = (folder or Path.cwd()) / CONFIG_NAME
    if not path.is_file():
        return Project()
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected settings like `cv: cv.yaml`")
    unknown = sorted(set(data) - set(KEYS))
    if unknown:
        raise ValueError(f"{path}: unknown setting(s) {', '.join(unknown)}; allowed: {', '.join(KEYS)}")
    root = path.parent
    return Project(
        cv=root / data["cv"] if data.get("cv") else None,
        letter=root / data["letter"] if data.get("letter") else None,
        output=root / data.get("output", "output"),
        tailored=root / data.get("tailored", "tailored"),
        build=bool(data.get("build", False)),
        found=True,
    )


def job_slug(job: Path) -> str:
    """`jobs/Acme Senior SDET.md` -> `acme-senior-sdet` (used as the tailored folder name)."""
    return re.sub(r"[^a-z0-9]+", "-", job.stem.lower()).strip("-") or "job"
