from pathlib import Path

import yaml

import pytest

from easy_ai_resume.build import TEMPLATES, build_file, detect_kind, output_stem, render, theme_names
from conftest import EXAMPLES, needs_pdf


def test_detects_document_kind(cv, letter):
    assert detect_kind(cv) == "cv"
    assert detect_kind(letter) == "cover_letter"
    with pytest.raises(ValueError):
        detect_kind({"summary": "no name"})


def test_output_stem_comes_from_the_name(cv, letter):
    assert output_stem(cv, "cv") == "Jane_Doe_CV"
    assert output_stem(letter, "cover_letter") == "Jane_Doe_Cover_Letter"
    assert output_stem({"name": "José O'Neil-Smith"}, "cv") == "Jos_O_Neil_Smith_CV"


def test_every_theme_has_a_stylesheet():
    assert "classic" in theme_names()
    for name in theme_names():
        assert (TEMPLATES / "themes" / f"{name}.css").is_file(), name


@pytest.mark.parametrize("theme", theme_names())
def test_every_theme_renders_both_documents(cv, letter, theme):
    assert "Globex Payments" in render(cv, "cv", theme=theme, base_dir=EXAMPLES)
    assert "Umbrella Health" in render(letter, "cover_letter", theme=theme, base_dir=EXAMPLES)


def test_unknown_theme_is_an_error(cv):
    with pytest.raises(ValueError, match="unknown theme"):
        render(cv, "cv", theme="neon")


def test_markdown_renders_and_raw_html_is_not_trusted(cv):
    cv["summary"] = "**bold** and <script>alert(1)</script>"
    html = render(cv, "cv")
    assert "<strong>bold</strong>" in html
    assert "<script>alert(1)</script>" not in html


def test_contact_values_are_escaped(cv):
    cv["contact"]["location"] = 'Austin <b>"TX"</b>'
    html = render(cv, "cv")
    assert "Austin &lt;b&gt;" in html
    assert '<span class="sep">●</span>' in html  # our own markup is not escaped


def test_ats_mode_uses_plain_text_contacts(cv):
    html = render(cv, "cv", ats=True)
    assert "github.com/example</a>" in html
    assert " | " in html
    assert '<span class="sep">' not in html


def test_ats_can_be_set_in_yaml(cv):
    cv["ats"] = True
    assert '<span class="sep">' not in render(cv, "cv")


def test_bad_accent_is_rejected(cv):
    cv["accent"] = "red; } body { display: none"
    with pytest.raises(ValueError, match="accent"):
        render(cv, "cv")


def test_page_size_applies_to_the_cover_letter_page(letter):
    letter["page"] = "letter"
    assert "@page cover-letter { size: letter; }" in render(letter, "cover_letter")


def test_cover_letter_salutation_uses_hiring_manager(letter):
    letter["recipient"]["hiring_manager"] = "Dr. Smith"
    assert "Dear Dr. Smith," in render(letter, "cover_letter")


def test_html_only_build(tmp_path):
    written = build_file(EXAMPLES / "cv.yaml", tmp_path, pdf=False)
    assert [p.name for p in written] == ["Jane_Doe_CV.html"]


@needs_pdf
@pytest.mark.parametrize("theme", theme_names())
@pytest.mark.parametrize("ats", [False, True])
def test_examples_render_to_one_page_pdfs(tmp_path, theme, ats):
    from weasyprint import HTML

    for name in ("cv.yaml", "cover_letter.yaml"):
        written = build_file(EXAMPLES / name, tmp_path, theme=theme, ats=ats, html=True)
        html, pdf = written[0], [p for p in written if p.suffix == ".pdf"]
        assert pdf and pdf[0].read_bytes().startswith(b"%PDF"), f"no PDF for {name}"
        assert len(HTML(filename=str(html)).render().pages) == 1, f"{name} is not one page"


def test_custom_accent_also_sets_a_light_accent(cv):
    cv["accent"] = "#9b1b30"
    html = render(cv, "cv", theme="sidebar", base_dir=EXAMPLES)
    assert "--accent: #9b1b30; --accent-soft: #d7a4ac;" in html


@needs_pdf
def test_build_writes_only_the_pdf_by_default(tmp_path):
    written = build_file(EXAMPLES / "cv.yaml", tmp_path)
    assert [p.name for p in written] == ["Jane_Doe_CV.pdf"]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["Jane_Doe_CV.pdf"]


@needs_pdf
def test_html_flag_writes_both(tmp_path):
    written = build_file(EXAMPLES / "cv.yaml", tmp_path, html=True)
    assert sorted(p.name for p in written) == ["Jane_Doe_CV.html", "Jane_Doe_CV.pdf"]


def test_homebrew_lib_folders_are_added_on_macos(tmp_path, monkeypatch):
    import os
    import sys

    from easy_ai_resume.build import use_homebrew_libraries

    real, absent = tmp_path / "lib", str(tmp_path / "nope")
    real.mkdir()
    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setenv("DYLD_FALLBACK_LIBRARY_PATH", "/already/here")
    use_homebrew_libraries((str(real), absent))
    assert os.environ["DYLD_FALLBACK_LIBRARY_PATH"] == f"/already/here:{real}"
    use_homebrew_libraries((str(real),))  # no duplicates on a second call
    assert os.environ["DYLD_FALLBACK_LIBRARY_PATH"].count(str(real)) == 1


def test_missing_file_error_says_where_it_looked(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FileNotFoundError, match="holds input/"):
        build_file(Path("cv.yaml"), tmp_path / "out")


@pytest.mark.parametrize("theme", ["sidebar", "classic", "executive"])
def test_default_accent_is_the_readme_red(cv, theme):
    cv.pop("accent", None)
    html = render(cv, "cv", theme=theme, base_dir=EXAMPLES)
    assert "--accent: #9b1b30;" in html
    assert "--accent: #000000" in render(cv, "cv", theme=theme, ats=True, base_dir=EXAMPLES)  # ATS stays black


@needs_pdf
@pytest.mark.parametrize("theme", theme_names())
@pytest.mark.parametrize("ats", [False, True])
def test_cover_letter_links_are_clickable_in_the_pdf(letter, theme, ats):
    from weasyprint import HTML

    page = HTML(string=render(letter, "cover_letter", theme=theme, ats=ats, base_dir=EXAMPLES)).render().pages[0]
    clickable = {target for kind, target, *_ in page.links if kind == "external"}
    assert {link["url"] for link in letter["sender"]["links"]} <= clickable


def test_bold_and_sidebar_cover_letters_look_different(letter):
    sidebar = render(letter, "cover_letter", theme="sidebar", base_dir=EXAMPLES)
    bold = render(letter, "cover_letter", theme="bold", base_dir=EXAMPLES)
    assert "linear-gradient" in sidebar  # a coloured column down the side
    assert "linear-gradient" not in bold and "border-bottom: 1.5mm solid var(--accent)" in bold  # a header band


@pytest.mark.parametrize("theme", ["classic", "sidebar"])
def test_startups_come_before_projects(cv, theme):
    cv["startups"] = [{"name": "Hush Mouse", "links": [{"label": "Live", "url": "https://hushmouse.com"}],
                       "bullets": ["Built it."]}]
    html = render(cv, "cv", theme=theme, base_dir=EXAMPLES)
    assert "<h2>Startups</h2>" in html and html.index("Hush Mouse") < html.index("<h2>Projects</h2>")
    assert 'href="https://hushmouse.com"' in html


@needs_pdf
@pytest.mark.parametrize("theme", theme_names())
@pytest.mark.parametrize("kind", ["cv", "cover_letter"])
@pytest.mark.parametrize("longer", [False, True])
def test_fit_makes_one_page_as_tall_as_the_content(cv, letter, theme, kind, longer):
    from weasyprint import HTML

    from easy_ai_resume.build import FIT_TALL, fit_page_size

    data = cv if kind == "cv" else letter
    if longer:  # six times the content: taller than A4, still one page
        if kind == "cv":
            cv["experience"] *= 6
        else:
            letter["body"] *= 6
    size = fit_page_size(render(data, kind, page_size=FIT_TALL, theme=theme, base_dir=EXAMPLES))
    height = float(size.split()[1].removesuffix("mm"))
    assert (height > 297) if longer else (120 < height < 297)
    pages = HTML(string=render(data, kind, page_size=size, theme=theme, base_dir=EXAMPLES)).render().pages
    assert len(pages) == 1


def test_page_fit_from_the_yaml(cv, tmp_path, monkeypatch, capsys):
    cv["page"] = {"size": "fit"}
    (tmp_path / "cv.yaml").write_text(yaml.safe_dump(cv))
    monkeypatch.setattr("easy_ai_resume.build.fit_page_size", lambda html: "210mm 240mm")
    build_file(tmp_path / "cv.yaml", tmp_path, pdf=False)
    assert "size: 210mm 240mm;" in (tmp_path / "Jane_Doe_CV.html").read_text()

    monkeypatch.setattr("easy_ai_resume.build.fit_page_size", lambda html: None)  # no WeasyPrint
    build_file(tmp_path / "cv.yaml", tmp_path, pdf=False)
    assert "size: A4;" in (tmp_path / "Jane_Doe_CV.html").read_text()
    assert "using A4" in capsys.readouterr().err


def test_removed_compact_theme_falls_back_to_classic(cv, tmp_path, capsys):
    cv["theme"] = "compact"
    (tmp_path / "cv.yaml").write_text(yaml.safe_dump(cv))
    build_file(tmp_path / "cv.yaml", tmp_path, pdf=False)
    assert "theme-classic" in (tmp_path / "Jane_Doe_CV.html").read_text()
    assert "compact theme was removed; using classic" in capsys.readouterr().err
