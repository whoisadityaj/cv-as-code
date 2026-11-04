"""Starter files for `easy-ai-resume init`: the Jane Doe examples, ready to edit in input/."""
from __future__ import annotations

import shutil
from pathlib import Path

from .config import INPUT_DIR

STARTER_FILES = ("cv.yaml", "cover_letter.yaml", "job.md", "jane.png")


def starter_dir() -> Path:
    """Packaged copies when installed from a wheel; the repo's examples/ in a checkout."""
    packaged = Path(__file__).parent / "starter"
    if packaged.is_dir():
        return packaged
    return Path(__file__).resolve().parents[2] / "examples"


def init(folder: Path, force: bool = False) -> list[Path]:
    """Copy the starter files into `folder`/input/. Never overwrites unless `force`."""
    target = folder / INPUT_DIR
    existing = [target / name for name in STARTER_FILES if (target / name).exists()]
    if existing and not force:
        raise FileExistsError(f"{existing[0]} already exists (use --force to overwrite)")
    target.mkdir(parents=True, exist_ok=True)
    written = []
    for name in STARTER_FILES:
        shutil.copyfile(starter_dir() / name, target / name)
        written.append(target / name)
    return written
