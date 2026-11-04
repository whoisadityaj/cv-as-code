import pytest

from easy_ai_resume.build import THEMES, photo_src, render
from conftest import EXAMPLES

PHOTO_THEMES = [name for name, spec in THEMES.items() if spec.photo]
PLAIN_THEMES = [name for name, spec in THEMES.items() if not spec.photo]


def test_there_are_photo_themes():
    assert {"sidebar", "executive", "bold"} <= set(PHOTO_THEMES)


@pytest.mark.parametrize("theme", PHOTO_THEMES)
def test_photo_themes_embed_the_photo(cv, letter, theme):
    assert 'src="data:image/png;base64,' in render(cv, "cv", theme=theme, base_dir=EXAMPLES)
    assert 'src="data:image/png;base64,' in render(letter, "cover_letter", theme=theme, base_dir=EXAMPLES)


@pytest.mark.parametrize("theme", PLAIN_THEMES)
def test_plain_themes_ignore_the_photo(cv, theme):
    assert 'class="photo"' not in render(cv, "cv", theme=theme, base_dir=EXAMPLES)


@pytest.mark.parametrize("theme", PHOTO_THEMES)
def test_ats_never_includes_a_photo(cv, theme):
    html = render(cv, "cv", theme=theme, ats=True, base_dir=EXAMPLES)
    assert "data:image" not in html
    assert 'class="sidebar-layout"' not in html  # ATS always uses the single column


def test_missing_photo_is_a_clear_error(cv, tmp_path):
    cv["photo"] = "nope.jpg"
    with pytest.raises(ValueError, match="photo not found"):
        render(cv, "cv", theme="sidebar", base_dir=tmp_path)


def test_unsupported_photo_type(tmp_path):
    (tmp_path / "me.bmp").write_bytes(b"BM")
    with pytest.raises(ValueError, match="unsupported photo type"):
        photo_src("me.bmp", tmp_path)


def test_photo_urls_pass_through():
    assert photo_src("https://example.com/me.jpg") == "https://example.com/me.jpg"


def test_sidebar_layout_puts_contacts_in_a_list(cv):
    html = render(cv, "cv", theme="sidebar", base_dir=EXAMPLES)
    assert 'class="sidebar-layout"' in html
    assert '<ul class="contact-list">' in html
    assert "github.com/example</a>" in html  # full URLs, since there is room


def test_photo_theme_without_photo_gives_a_note(cv, letter):
    from easy_ai_resume.build import missing_photo_note

    del cv["photo"], letter["sender"]["photo"]
    assert "photo: me.jpg" in missing_photo_note(cv, "cv", "sidebar", None)
    assert "under `sender:`" in missing_photo_note(letter, "cover_letter", "sidebar", None)
    assert missing_photo_note(cv, "cv", "classic", None) is None  # theme has no photo
    assert missing_photo_note(cv, "cv", "sidebar", True) is None  # ATS never shows one
    cv["photo"] = "none"
    assert missing_photo_note(cv, "cv", "sidebar", None) is None
    assert 'class="photo"' not in render(cv, "cv", theme="sidebar", base_dir=EXAMPLES)  # "none" isn't a file
