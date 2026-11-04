import shutil

import pytest
import yaml

from easy_ai_resume import ask_photo
from easy_ai_resume.cli import main
from conftest import EXAMPLES


@pytest.fixture
def folder(tmp_path):
    """A user's input/ folder with the samples, minus their `photo:` lines."""
    inp = tmp_path / "input"
    inp.mkdir()
    for name in ("cv.yaml", "cover_letter.yaml"):
        text = (EXAMPLES / name).read_text()
        (inp / name).write_text("\n".join(l for l in text.splitlines() if not l.lstrip().startswith("photo:")) + "\n")
    shutil.copyfile(EXAMPLES / "jane.png", tmp_path / "my photo.png")  # somewhere else, with a space
    return tmp_path


def build(folder, answers, monkeypatch, *extra):
    monkeypatch.setattr(ask_photo, "is_terminal", lambda: True)
    replies = iter(answers)
    monkeypatch.setattr("builtins.input", lambda prompt: next(replies))
    inp = folder / "input"
    return main(["build", str(inp / "cv.yaml"), str(inp / "cover_letter.yaml"), "--theme", "sidebar",
                 "--html-only", "--out", str(folder / "out"), *extra])


def test_asks_for_the_photo_and_saves_it(folder, monkeypatch, capsys):
    dragged = str(folder / "my photo.png").replace(" ", "\\ ")  # how macOS Terminal pastes a dragged file
    assert build(folder, ["~/nope.png", dragged], monkeypatch) == 0
    out = capsys.readouterr().out
    assert "can't find" in out and "added `photo: my photo.png`" in out
    inp = folder / "input"
    assert (inp / "my photo.png").is_file()  # copied next to the YAML
    assert yaml.safe_load((inp / "cv.yaml").read_text())["photo"] == "my photo.png"
    assert yaml.safe_load((inp / "cover_letter.yaml").read_text())["sender"]["photo"] == "my photo.png"
    assert "# Optional. Pick a look" in (inp / "cv.yaml").read_text()  # comments kept
    for name in ("Jane_Doe_CV.html", "Jane_Doe_Cover_Letter.html"):
        assert "data:image/png;base64," in (folder / "out" / name).read_text()

    capsys.readouterr()
    assert build(folder, [], monkeypatch) == 0  # answered once: never asks again
    assert "Drag" not in capsys.readouterr().out


def test_enter_means_no_photo_and_stops_asking(folder, monkeypatch, capsys):
    assert build(folder, [""], monkeypatch) == 0
    assert yaml.safe_load((folder / "input" / "cv.yaml").read_text())["photo"] == "none"
    assert build(folder, [], monkeypatch) == 0
    assert "note" not in capsys.readouterr().err


def test_never_asks_outside_a_terminal_or_in_ats_mode(folder, monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda prompt: pytest.fail("asked"))
    inp = folder / "input"
    args = ["build", str(inp / "cv.yaml"), "--theme", "sidebar", "--html-only", "--out", str(folder / "out")]
    assert main(args) == 0  # pytest's stdin isn't a terminal: just the note
    assert "the sidebar theme shows a photo" in capsys.readouterr().err
    monkeypatch.setattr(ask_photo, "is_terminal", lambda: True)
    assert main(args + ["--ats"]) == 0  # ATS never shows a photo


@pytest.mark.parametrize("text, kind", [
    ("name: Jane\nskills:\n  - group: A\n    items: [x]", "cv"),  # no newline at the end
    ("# top comment\nname: >-\n  Jane\n  Doe\ntitle: x\n", "cv"),  # can't go after a folded name
    ("sender:\n    name: Jane  # four spaces\ndate: auto\n", "cover_letter"),
])
def test_add_photo_line_keeps_the_yaml_valid(tmp_path, text, kind):
    path = tmp_path / "f.yaml"
    path.write_text(text)
    before = yaml.safe_load(text)
    assert ask_photo.add_photo_line(path, kind, "me.jpg")
    after = yaml.safe_load(path.read_text())
    photo = after.pop("photo") if kind == "cv" else after["sender"].pop("photo")
    assert photo == "me.jpg" and after == before


def test_clean_path():
    assert ask_photo.clean_path(" '/a b/me.jpg' ") == "/a b/me.jpg"
    assert ask_photo.clean_path("/a\\ b/me.jpg") == "/a b/me.jpg"
    assert ask_photo.clean_path("") == ""
