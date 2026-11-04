"""Starter files for `easy-ai-resume init`: the Jane Doe examples, ready to edit in input/."""
from __future__ import annotations

import re
from pathlib import Path

from .config import INPUT_DIR

STARTER_FILES = ("cv.yaml", "cover_letter.yaml", "job.md")
# The examples show Jane's photo. Your copy leaves it out, so a photo theme asks for yours.
SAMPLE_PHOTO = re.compile(r"^(\s*)photo: jane\.png.*$", re.MULTILINE)


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
        text = (starter_dir() / name).read_text(encoding="utf-8")
        text = SAMPLE_PHOTO.sub(r"\1# photo: me.jpg   # a photo theme asks for it when you build", text)
        (target / name).write_text(text, encoding="utf-8")
        written.append(target / name)
    return written
