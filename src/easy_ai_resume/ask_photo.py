"""Ask for a photo when a photo theme (sidebar, bold, executive) is used but the YAML has none.

Only in a terminal: GitHub Actions and scripts get the printed note instead. The answer is
saved in the YAML files (`photo: me.jpg`, or `photo: none` for no photo), so it's asked once.
"""
from __future__ import annotations

import copy
import json
import os
import re
import shlex
import shutil
import sys
from pathlib import Path
from typing import Any, Callable

import yaml

from .build import PHOTO_TYPES, detect_kind, load_yaml, missing_photo_note

NO_PHOTO = "none"


def is_terminal() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def clean_path(raw: str) -> str:
    """A path typed or dragged into the terminal, without its quotes or `\\ ` escapes."""
    raw = raw.strip()
    if os.name == "nt":  # backslashes are folder separators on Windows
        return raw.strip("'\"")
    try:
        return " ".join(shlex.split(raw))
    except ValueError:  # an unmatched quote
        return raw.strip("'\"")


def _top_level_line(lines: list[str], key: str) -> int | None:
    pattern = re.compile(rf"{key}:(\s|$)")
    return next((i for i, line in enumerate(lines) if pattern.match(line)), None)


def _child_indent(lines: list[str], parent: int) -> str:
    for line in lines[parent + 1 :]:
        if line.strip() and not line.lstrip().startswith("#"):
            return line[: len(line) - len(line.lstrip())] or "  "
    return "  "


def add_photo_line(path: Path, kind: str, value: str) -> bool:
    """Add `photo: <value>` to a CV (top level) or cover letter (under `sender:`), keeping comments.

    The YAML is edited as text so your comments and layout stay. The result is parsed again and
    only saved if the one change is the new photo, so a file this can't handle is left alone.
    """
    text = path.read_text(encoding="utf-8")
    if text and not text.endswith("\n"):
        text += "\n"
    lines = text.splitlines(keepends=True)
    shown = value if value == NO_PHOTO else json.dumps(value)  # quoted: safe for spaces and `:`

    expected: dict[str, Any] = copy.deepcopy(yaml.safe_load(text) or {})
    places: list[tuple[int, str]] = []
    if kind == "cv":
        expected["photo"] = value
        for key in ("theme", "name"):
            at = _top_level_line(lines, key)
            if at is not None:
                places.append((at + 1, f"photo: {shown}\n"))
        places.append((len(lines), f"photo: {shown}\n"))  # last resort: the end of the file
    else:
        if not isinstance(expected.get("sender"), dict):
            return False
        expected["sender"]["photo"] = value
        at = _top_level_line(lines, "sender")
        if at is not None:
            places.append((at + 1, f"{_child_indent(lines, at)}photo: {shown}\n"))

    for at, new_line in places:
        new_text = "".join(lines[:at] + [new_line] + lines[at:])
        try:
            if yaml.safe_load(new_text) == expected:
                path.write_text(new_text, encoding="utf-8")
                return True
        except yaml.YAMLError:
            continue
    return False


def _copy_next_to(photo: Path, folder: Path) -> Path:
    """Copy the photo next to the YAML files, so the folder has everything it needs."""
    dest = folder / photo.name
    if dest.exists():
        if dest.resolve() == photo.resolve() or dest.read_bytes() == photo.read_bytes():
            return dest
        return photo.resolve()  # a different file has that name: use the photo where it is
    shutil.copyfile(photo, dest)
    print(f"  copied your photo to {_show(dest)}")
    return dest


def _show(path: Path) -> str:
    """`input/cv.yaml` instead of the full path, when it's inside the current folder."""
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def _relative(photo: Path, folder: Path) -> str:
    try:
        return os.path.relpath(photo.resolve(), folder.resolve())
    except ValueError:  # Windows: different drives
        return str(photo.resolve())


def offer_photo(paths: list[Path], theme: str | None, ats: bool | None,
                ask: Callable[[str], str] | None = None) -> None:
    """Ask once for a photo for every file in `paths` that a photo theme would show without one."""
    if not is_terminal():
        return
    missing = []
    for path in paths:
        try:
            data = load_yaml(path)
            kind = detect_kind(data)
        except (FileNotFoundError, ValueError, yaml.YAMLError):
            continue  # the build reports these
        if missing_photo_note(data, kind, theme, ats):
            missing.append((path, kind, theme or data.get("theme")))
    if not missing:
        return

    ask = ask or input
    names = " and ".join(path.name for path, _, _ in missing)
    print(f"\nThe {missing[0][2]} theme shows a photo, but {names} {'has' if len(missing) == 1 else 'have'} none yet.")
    while True:
        try:
            raw = ask("Drag your photo into this window (or type its path) and press Enter.\n"
                      "Just press Enter for no photo: ")
        except EOFError:
            print()
            return
        except KeyboardInterrupt:
            print()
            raise SystemExit(130)
        source = clean_path(raw)
        if not source:
            stored = None
            break
        photo = Path(source).expanduser()
        if not photo.is_file():
            print(f"  can't find {photo}. Try again.")
        elif photo.suffix.lower() not in PHOTO_TYPES:
            print("  use a .jpg, .png, .webp or .svg file. Try again.")
        else:
            stored = _copy_next_to(photo, missing[0][0].parent)
            break

    for path, kind, _ in missing:
        value = NO_PHOTO if stored is None else _relative(stored, path.parent)
        where = " under `sender:`" if kind == "cover_letter" else ""
        if add_photo_line(path, kind, value):
            print(f"  added `photo: {value}`{where} in {_show(path)}")
        else:
            print(f"  couldn't edit {_show(path)}: add `photo: {value}`{where} yourself")
    if stored is None:
        print("  no photo. To add one later, change `photo: none` to the photo's file name.")
    print()
