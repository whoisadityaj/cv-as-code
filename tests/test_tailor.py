import copy
import json
import subprocess
from pathlib import Path

import pytest
import yaml

from easy_ai_resume import tailor as t
from conftest import EXAMPLES


def test_parse_response_tolerates_code_fences(cv, letter):
    raw = "```json\n" + json.dumps({"cv": cv, "cover_letter": letter, "notes": "- reordered"}) + "\n```"
    new_cv, new_letter, notes = t.parse_response(raw)
    assert new_cv["name"] == "Jane Doe" and new_letter["sender"]["name"] == "Jane Doe"
    assert notes == "- reordered"


@pytest.mark.parametrize("raw", ["no json here", "{not json}", '{"cv": {}}'])
def test_parse_response_rejects_bad_replies(raw):
    with pytest.raises(t.TailorError):
        t.parse_response(raw)


def test_check_facts_is_quiet_for_an_unchanged_copy(cv, letter):
    assert t.check_facts(cv, copy.deepcopy(cv), letter, copy.deepcopy(letter)) == []


def test_check_facts_allows_rewording(cv, letter):
    new_cv = copy.deepcopy(cv)
    new_cv["experience"][0]["bullets"].reverse()
    new_cv["experience"][0]["bullets"][0] = "Mentored **3** junior engineers and ran weekly API reviews."
    assert t.check_facts(cv, new_cv, letter, copy.deepcopy(letter)) == []


def test_check_facts_flags_invented_content(cv, letter):
    new_cv, new_letter = copy.deepcopy(cv), copy.deepcopy(letter)
    new_cv["experience"][0]["bullets"][0] = "Cut latency by **65%** for 3M users"
    new_cv["experience"][1]["start"] = "Jan 2016"
    new_cv["experience"].append({"company": "Hooli", "role": "CTO", "start": "2010", "end": "2012"})
    new_cv["skills"][0]["items"].append({"name": "Rust"})
    new_cv["contact"]["email"] = "someone@else.com"
    new_letter["body"][0] = "I have 12 years of experience."

    warns = "\n".join(t.check_facts(cv, new_cv, letter, new_letter))
    for expected in ["65%", "3m", "12", "dates changed", "CTO at Hooli", "rust", "contact.email"]:
        assert expected in warns


def test_auto_tries_subscriptions_then_api_keys(monkeypatch):
    installed = set()
    monkeypatch.setattr(t.shutil, "which", lambda name: f"/bin/{name}" if name in installed else None)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(t.TailorError, match="Claude Code"):
        t.providers_to_try()  # nothing at all: says what to install
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    assert t.providers_to_try() == ["anthropic"]
    installed |= {"opencode", "claude"}
    assert t.providers_to_try() == ["claude", "opencode", "anthropic"]  # subscriptions first
    assert t.providers_to_try("openai") == ["openai"]


def test_auto_moves_on_when_one_fails(tmp_path, monkeypatch, cv, letter, capsys):
    monkeypatch.setattr(t, "providers_to_try", lambda provider: ["claude", "opencode"])
    monkeypatch.setitem(t.CALLERS, "claude", lambda p, m: (_ for _ in ()).throw(t.TailorError("Not logged in")))
    monkeypatch.setitem(t.CALLERS, "opencode", lambda p, m: json.dumps({"cv": cv, "cover_letter": letter}))
    t.tailor(EXAMPLES / "job.md", EXAMPLES / "cv.yaml", EXAMPLES / "cover_letter.yaml", tmp_path)
    err = capsys.readouterr().err
    assert "claude didn't work: Not logged in" in err and "Tailoring with opencode" in err

    monkeypatch.setitem(t.CALLERS, "opencode", lambda p, m: "sorry, no JSON")
    with pytest.raises(t.TailorError, match="no AI could tailor"):
        t.tailor(EXAMPLES / "job.md", EXAMPLES / "cv.yaml", EXAMPLES / "cover_letter.yaml", tmp_path, force=True)


def _fake_run(monkeypatch, stdout="", returncode=0, stderr="", write=None):
    seen = {}

    def run(cmd, **kw):
        seen.update(cmd=cmd, **kw)
        if write:
            Path(cmd[cmd.index("-o") + 1]).write_text(write)
        return subprocess.CompletedProcess(cmd, returncode, stdout, stderr)

    monkeypatch.setattr(t.subprocess, "run", run)
    return seen


def test_claude_cli_answers_without_tools_in_an_empty_folder(monkeypatch):
    seen = _fake_run(monkeypatch, stdout='\x1b[0m{"cv": {}}')
    assert t.call_claude_cli("PROMPT", "sonnet") == '{"cv": {}}'  # colour codes removed
    cmd = seen["cmd"]
    assert cmd[:2] == ["claude", "-p"] and cmd[cmd.index("--tools") + 1] == ""
    assert cmd[cmd.index("--system-prompt") + 1] == t.SYSTEM_PROMPT and cmd[-2:] == ["--model", "sonnet"]
    assert seen["input"] == "PROMPT" and not any(Path(seen["cwd"]).iterdir() if Path(seen["cwd"]).exists() else [])


def test_codex_cli_reads_the_last_message_file(monkeypatch):
    seen = _fake_run(monkeypatch, stdout="lots of agent log", write='{"cv": 1}')
    assert t.call_codex_cli("PROMPT", None) == '{"cv": 1}'
    assert "read-only" in seen["cmd"] and seen["input"].endswith("PROMPT")


def test_cli_failure_is_one_clear_line(monkeypatch):
    _fake_run(monkeypatch, returncode=1, stderr="ERROR: model not supported\n")
    with pytest.raises(t.TailorError, match="opencode failed: ERROR: model not supported"):
        t.call_opencode_cli("PROMPT", None)


def test_openai_needs_a_model(monkeypatch):
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    with pytest.raises(t.TailorError):  # either "choose a model" or "install the AI extra"
        t.call_openai("prompt", None)


def _fake_llm(reply: dict):
    seen = {}

    def fake(prompt, model):
        seen["prompt"] = prompt
        return json.dumps(reply)

    return fake, seen


def test_tailor_writes_files_and_reports_warnings(tmp_path, monkeypatch, cv, letter):
    tailored = copy.deepcopy(cv)
    tailored["summary"] = "Backend engineer with 9 years of experience."  # 9 is invented
    fake, seen = _fake_llm({"cv": tailored, "cover_letter": letter, "notes": "- tightened summary"})
    monkeypatch.setitem(t.CALLERS, "anthropic", fake)

    out_cv, out_letter, notes, warns = t.tailor(
        EXAMPLES / "job.md", EXAMPLES / "cv.yaml", EXAMPLES / "cover_letter.yaml", tmp_path, provider="anthropic"
    )
    assert "Umbrella Health" in seen["prompt"] and "Globex Payments" in seen["prompt"]
    assert yaml.safe_load(out_cv.read_text())["summary"].startswith("Backend engineer with 9")
    assert out_letter.exists() and notes == "- tightened summary"
    assert any("9" in w for w in warns)


def test_tailor_refuses_to_overwrite_without_force(tmp_path, monkeypatch, cv, letter):
    fake, _ = _fake_llm({"cv": cv, "cover_letter": letter})
    monkeypatch.setitem(t.CALLERS, "anthropic", fake)
    (tmp_path / "cv.yaml").write_text("existing")
    args = (EXAMPLES / "job.md", EXAMPLES / "cv.yaml", EXAMPLES / "cover_letter.yaml", tmp_path)

    with pytest.raises(t.TailorError, match="already exists"):
        t.tailor(*args, provider="anthropic")
    assert (tmp_path / "cv.yaml").read_text() == "existing"

    t.tailor(*args, provider="anthropic", force=True)
    assert yaml.safe_load((tmp_path / "cv.yaml").read_text())["name"] == "Jane Doe"


def test_tailored_copy_still_finds_the_photo(tmp_path, monkeypatch, cv, letter):
    # The tailored YAML lives in another folder, so `photo: jane.png` must be rewritten.
    cv["photo"] = "something-the-model-made-up.png"
    fake, _ = _fake_llm({"cv": cv, "cover_letter": letter})
    monkeypatch.setitem(t.CALLERS, "anthropic", fake)
    out = tmp_path / "tailored" / "acme"

    out_cv, out_letter, _, _ = t.tailor(
        EXAMPLES / "job.md", EXAMPLES / "cv.yaml", EXAMPLES / "cover_letter.yaml", out, provider="anthropic"
    )
    for path, photo in ((out_cv, yaml.safe_load(out_cv.read_text())["photo"]),
                        (out_letter, yaml.safe_load(out_letter.read_text())["sender"]["photo"])):
        assert (path.parent / photo).resolve() == (EXAMPLES / "jane.png").resolve()


def test_ai_errors_become_a_clear_message(monkeypatch):
    anthropic = pytest.importorskip("anthropic")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    with pytest.raises(t.TailorError, match="API key"):
        t.call_anthropic("prompt", None)  # no key: no traceback, a one-line error

    class Boom:
        def __init__(self, *a, **k):
            self.messages = self

        def create(self, **kwargs):
            raise anthropic.APIConnectionError(request=None)

    monkeypatch.setattr(anthropic, "Anthropic", Boom)
    with pytest.raises(t.TailorError, match="request failed"):
        t.call_anthropic("prompt", None)


def test_check_facts_flags_invented_startups(cv, letter):
    cv["startups"] = [{"name": "Hush Mouse"}]
    new_cv = copy.deepcopy(cv)
    new_cv["startups"].append({"name": "Unicorn AI"})
    assert "startup not in original: Unicorn AI" in t.check_facts(cv, new_cv, letter, letter)


def test_subscription_tools_default_to_a_capable_model_at_medium_effort(monkeypatch):
    seen = _fake_run(monkeypatch, stdout="{}")
    t.call_claude_cli("PROMPT", None)
    cmd = seen["cmd"]
    assert cmd[cmd.index("--model") + 1] == "opus" and cmd[cmd.index("--effort") + 1] == "medium"

    t.call_opencode_cli("PROMPT", None)
    assert seen["cmd"][seen["cmd"].index("-m") + 1] == "opencode-go/deepseek-v4.1-flash#high"

    seen = _fake_run(monkeypatch, write="{}")
    t.call_codex_cli("PROMPT", None, effort="low")
    assert 'model_reasoning_effort="low"' in seen["cmd"] and "gpt-6.1-sol" in seen["cmd"]
    assert "opus, medium effort" in t.describe("claude")


def test_falls_back_to_the_tools_own_model_when_ours_isnt_on_the_plan(monkeypatch, capsys):
    calls = []

    def run(cmd, **kw):
        calls.append(cmd)
        if "-m" in cmd:
            return subprocess.CompletedProcess(cmd, 1, "", "Error: model not found: opencode-go/deepseek-v4.1-flash")
        return subprocess.CompletedProcess(cmd, 0, '{"ok": 1}', "")

    monkeypatch.setattr(t.subprocess, "run", run)
    assert t.call_opencode_cli("PROMPT", None) == '{"ok": 1}'
    assert len(calls) == 2 and "trying its default model" in capsys.readouterr().err
    with pytest.raises(t.TailorError):  # a model you chose yourself is never swapped
        t.call_opencode_cli("PROMPT", "opencode-go/deepseek-v4.1-flash")


def test_changes_diff_shows_only_real_changes(tmp_path, monkeypatch, cv, letter):
    tailored = copy.deepcopy(cv)
    tailored["summary"] = "Backend engineer focused on payments."
    fake, _ = _fake_llm({"cv": tailored, "cover_letter": letter})
    monkeypatch.setitem(t.CALLERS, "anthropic", fake)
    t.tailor(EXAMPLES / "job.md", EXAMPLES / "cv.yaml", EXAMPLES / "cover_letter.yaml", tmp_path, provider="anthropic")
    diff = (tmp_path / "changes.diff").read_text()
    changed = [l for l in diff.splitlines() if l[:1] in "+-" and not l.startswith(("+++", "---"))]
    assert changed == [f"-summary: {cv['summary']}", "+summary: Backend engineer focused on payments."]
