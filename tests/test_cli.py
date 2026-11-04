import json

import pytest

from easy_ai_resume import __version__
from easy_ai_resume import tailor as t
from easy_ai_resume.cli import main
from conftest import EXAMPLES


def test_version(capsys):
    with pytest.raises(SystemExit):
        main(["--version"])
    assert f"easy-ai-resume {__version__}" in capsys.readouterr().out


def test_build_html_only(tmp_path):
    code = main(["build", str(EXAMPLES / "cv.yaml"), str(EXAMPLES / "cover_letter.yaml"),
                 "--out", str(tmp_path), "--html-only", "--theme", "modern"])
    assert code == 0
    assert sorted(p.name for p in tmp_path.iterdir()) == ["Jane_Doe_CV.html", "Jane_Doe_Cover_Letter.html"]


def test_build_missing_file(tmp_path, capsys):
    assert main(["build", str(tmp_path / "nope.yaml"), "--out", str(tmp_path)]) == 1
    assert "not found" in capsys.readouterr().err


def test_build_fails_when_pdf_cannot_be_made(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("easy_ai_resume.build.write_pdf", lambda html, out: False)
    assert main(["build", str(EXAMPLES / "cv.yaml"), "--out", str(tmp_path)]) == 1
    assert "PDF generation failed" in capsys.readouterr().err
    assert (tmp_path / "Jane_Doe_CV.html").exists()


def test_tailor_strict_exit_code(tmp_path, monkeypatch, cv, letter):
    cv["summary"] = "Built systems for 50M users."  # invented number
    monkeypatch.setitem(t.CALLERS, "anthropic", lambda prompt, model: json.dumps({"cv": cv, "cover_letter": letter}))
    args = ["tailor", str(EXAMPLES / "job.md"), "--cv", str(EXAMPLES / "cv.yaml"),
            "--letter", str(EXAMPLES / "cover_letter.yaml"), "--out", str(tmp_path), "--provider", "anthropic"]
    assert main(args + ["--strict"]) == 2
    assert main(args + ["--force"]) == 0  # warnings only, without --strict


def test_init_creates_starter_files_that_build(tmp_path, capsys):
    assert main(["init", str(tmp_path)]) == 0
    assert sorted(p.name for p in tmp_path.iterdir()) == ["cover_letter.yaml", "cv.yaml", "jane.png", "job.md"]
    assert "easy-ai-resume build cv.yaml" in capsys.readouterr().out
    out = tmp_path / "out"
    assert main(["build", str(tmp_path / "cv.yaml"), "--theme", "sidebar", "--html-only", "--out", str(out)]) == 0
    assert "data:image/png;base64," in (out / "Jane_Doe_CV.html").read_text()  # photo found next to the YAML


def test_init_never_overwrites_without_force(tmp_path, capsys):
    (tmp_path / "cv.yaml").write_text("my real cv")
    assert main(["init", str(tmp_path)]) == 1
    assert "already exists" in capsys.readouterr().err
    assert (tmp_path / "cv.yaml").read_text() == "my real cv"
    assert main(["init", str(tmp_path), "--force"]) == 0
    assert "Jane Doe" in (tmp_path / "cv.yaml").read_text()
