from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = [ROOT / "action.yml", ROOT / "examples" / "github-workflow.yml", *(ROOT / ".github" / "workflows").glob("*.yml")]


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_action_and_workflow_files_are_valid_yaml(path):
    assert isinstance(yaml.safe_load(path.read_text()), dict)


def test_action_metadata_is_ready_for_the_marketplace():
    action = yaml.safe_load((ROOT / "action.yml").read_text())
    assert action["name"] == "easy-ai-resume"
    assert action["branding"]["icon"] and action["branding"]["color"]
    assert "easy-ai-resume build" in action["runs"]["steps"][-1]["run"]
