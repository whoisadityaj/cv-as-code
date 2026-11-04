import json
from pathlib import Path

import pytest

from easy_ai_resume import cli
from easy_ai_resume import tailor as t
from easy_ai_resume.config import job_slug, load_project
from easy_ai_resume.starter import init

CONFIG = """\
cv: data/cv.yaml
letter: data/cover_letter.yaml
output: output
tailored: applications
build: true
"""


@pytest.fixture
def project(tmp_path, monkeypatch):
    """A CV folder laid out like a real one: data/, jds/ and an easy-ai-resume.yaml."""
    init(tmp_path / "data")
    (tmp_path / "jds").mkdir()
    (tmp_path / "data" / "job.md").rename(tmp_path / "jds" / "Acme Senior SDET.md")
    (tmp_path / "easy-ai-resume.yaml").write_text(CONFIG)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_job_slug():
    assert job_slug(Path("jds/Acme Senior SDET.md")) == "acme-senior-sdet"


def test_load_project_resolves_paths_from_the_file(project):
    p = load_project()
    assert p.found and p.build
    assert p.cv == project / "data" / "cv.yaml"
    assert p.tailored == project / "applications"


def test_no_config_means_defaults(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    p = load_project()
    assert not p.found and p.cv is None and not p.build


def test_unknown_setting_is_an_error(project, capsys):
    (project / "easy-ai-resume.yaml").write_text(CONFIG + "colour: red\n")
    assert cli.main(["build", "--html-only"]) == 1
    assert "unknown setting(s) colour" in capsys.readouterr().err


def test_build_without_paths_uses_the_project_file(project):
    assert cli.main(["build", "--html-only"]) == 0
    assert sorted(p.name for p in (project / "output").iterdir()) == ["Jane_Doe_CV.html", "Jane_Doe_Cover_Letter.html"]


def test_build_without_paths_or_project_file(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert cli.main(["build"]) == 1
    assert "easy-ai-resume.yaml" in capsys.readouterr().err


def _fake(monkeypatch, cv, letter):
    monkeypatch.setitem(t.CALLERS, "anthropic", lambda prompt, model: json.dumps({"cv": cv, "cover_letter": letter}))


def test_tailor_uses_project_paths_and_names_the_folder_after_the_job(project, monkeypatch, capsys, cv, letter):
    _fake(monkeypatch, cv, letter)
    built = []
    monkeypatch.setattr(cli, "build_file", lambda path, out: built.append((path.name, out)) or [])
    assert cli.main(["tailor", "jds/Acme Senior SDET.md", "--provider", "anthropic"]) == 0

    out = project / "applications" / "acme-senior-sdet"
    assert (out / "cv.yaml").is_file() and (out / "cover_letter.yaml").is_file()
    assert built == [("cv.yaml", out), ("cover_letter.yaml", out)]  # build: true in the project file
    assert f"diff -u {project / 'data' / 'cv.yaml'} {out / 'cv.yaml'}" in capsys.readouterr().out


def test_no_build_flag_overrides_the_project_file(project, monkeypatch, cv, letter):
    _fake(monkeypatch, cv, letter)
    monkeypatch.setattr(cli, "build_file", lambda *a, **k: pytest.fail("should not build"))
    assert cli.main(["tailor", "jds/Acme Senior SDET.md", "--provider", "anthropic", "--no-build"]) == 0


def test_tailor_needs_cv_and_letter_from_somewhere(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "job.md").write_text("a job")
    assert cli.main(["tailor", "job.md"]) == 1
    assert "--cv and --letter" in capsys.readouterr().err


def test_old_cv_as_code_project_file_still_works(project):
    (project / "easy-ai-resume.yaml").rename(project / "cv-as-code.yaml")
    assert load_project().found
    assert cli.main(["build", "--html-only"]) == 0
