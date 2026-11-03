import copy
from pathlib import Path

import pytest
import yaml

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def _weasyprint_usable() -> bool:
    try:
        import weasyprint  # noqa: F401
    except Exception:
        return False
    return True


needs_pdf = pytest.mark.skipif(not _weasyprint_usable(), reason="WeasyPrint native libraries not available")


@pytest.fixture
def cv() -> dict:
    return copy.deepcopy(yaml.safe_load((EXAMPLES / "cv.yaml").read_text()))


@pytest.fixture
def letter() -> dict:
    return copy.deepcopy(yaml.safe_load((EXAMPLES / "cover_letter.yaml").read_text()))
