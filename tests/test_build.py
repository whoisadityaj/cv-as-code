import pytest

from cv_as_code.build import TEMPLATES, build_file, detect_kind, output_stem, render, theme_names
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
        written = build_file(EXAMPLES / name, tmp_path, theme=theme, ats=ats)
        html, pdf = written[0], [p for p in written if p.suffix == ".pdf"]
        assert pdf and pdf[0].read_bytes().startswith(b"%PDF"), f"no PDF for {name}"
        assert len(HTML(filename=str(html)).render().pages) == 1, f"{name} is not one page"


def test_custom_accent_also_sets_a_light_accent(cv):
    cv["accent"] = "#9b1b30"
    html = render(cv, "cv", theme="sidebar", base_dir=EXAMPLES)
    assert "--accent: #9b1b30; --accent-soft: #d7a4ac;" in html
