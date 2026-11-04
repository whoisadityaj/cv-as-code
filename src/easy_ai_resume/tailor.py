"""Tailor a CV + cover letter to a job description with an LLM.

The model may reword, reorder and drop content, but not invent facts.
`check_facts` compares the result with the original and reports anything
that looks invented or changed. Always review the diff before sending.
"""
from __future__ import annotations

import copy
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-5-5"

SYSTEM_PROMPT = """\
You are a careful senior recruiter and editor.

You will be given a candidate's CV (YAML), cover letter (YAML) and a job
description (JD). Tailor the CV and cover letter to the JD.

HARD RULES — breaking any of these is a failure:
  - Never invent or change facts: company names, job titles, dates, schools,
    degrees, grades, project names, contact details, metrics, or skills the
    candidate has not listed.
  - You MAY rephrase bullets, reorder or drop bullets that don't fit the JD,
    bold key terms with **markdown**, and rewrite the cover letter, as long
    as everything stays true to the original.
  - Keep the YAML schema identical: same keys, nesting and types.
  - Cover letter `body`: about 3 short paragraphs. Fill `recipient.company`
    (and `recipient.team` if obvious) from the JD. Use "Dear Hiring Manager,"
    unless the JD names a person.

Style: be decisive, a recruiter reads this in seconds.
  - Summary: 2-3 sentences aimed at this job, leading with the candidate's
    most relevant real experience.
  - Reorder items inside every section (skills, bullets, startups, projects)
    so the ones that matter for this job come first.
  - For each role keep the 3-5 bullets that best fit the job, reworded to
    lead with the relevant result. Drop or shorten the rest.
  - Use the JD's vocabulary only where the candidate truly has that
    experience. Keep every existing number. No filler like "self-motivated
    team player".

Return ONLY a JSON object:
{"cv": {...}, "cover_letter": {...}, "notes": "2-3 short bullets on what you changed"}
"""


class TailorError(RuntimeError):
    pass


# ----------------------------------------------------------------- LLM calls

KEY_HINT = (
    "Check your API key (ANTHROPIC_API_KEY or OPENAI_API_KEY), your account's credit, "
    "and your internet connection."
)


def _short(error: Exception) -> str:
    return " ".join(str(error).split())[:300]


# AI command-line tools that run on a subscription you already pay for, tried first (no API key,
# no extra cost), then API keys. Each name is also a --provider value.
SUBSCRIPTION_TOOLS = ("claude", "codex", "opencode")
API_KEYS = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY"}
LABELS = {
    "claude": "Claude Code (your Claude subscription)",
    "codex": "Codex (your ChatGPT subscription)",
    "opencode": "opencode",
    "anthropic": "the Anthropic API",
    "openai": "the OpenAI API",
}
NO_PROVIDER = (
    "no AI to tailor with. Install and log in to one of these (uses your subscription):\n"
    "  Claude Code: https://claude.com/claude-code\n"
    "  Codex:       https://developers.openai.com/codex/cli\n"
    "  opencode:    https://opencode.ai\n"
    "or set an API key: export ANTHROPIC_API_KEY=... (or OPENAI_API_KEY with --model)"
)


def providers_to_try(provider: str = "auto") -> list[str]:
    """`auto`: every installed subscription tool, then every API key that is set, in that order."""
    if provider != "auto":
        return [provider]
    found = [name for name in SUBSCRIPTION_TOOLS if shutil.which(name)]
    found += [name for name, key in API_KEYS.items() if os.environ.get(key)]
    if not found:
        raise TailorError(NO_PROVIDER)
    return found


def pick_provider(provider: str = "auto") -> str:
    return providers_to_try(provider)[0]


# ----------------------------------------------------------------- subscription tools

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
CLI_TIMEOUT = 15 * 60


def _run(name: str, cmd: list[str], cwd: str, stdin: str | None = None) -> str:
    """Run an AI command-line tool and return what it printed, or a one-line TailorError."""
    try:
        done = subprocess.run(cmd, input=stdin, capture_output=True, text=True, cwd=cwd, timeout=CLI_TIMEOUT,
                              stdin=None if stdin is not None else subprocess.DEVNULL)
    except FileNotFoundError as e:
        raise TailorError(f"{name} is not installed") from e
    except subprocess.TimeoutExpired as e:
        raise TailorError(f"{name} took longer than {CLI_TIMEOUT // 60} minutes") from e
    out = ANSI.sub("", done.stdout or "")
    if done.returncode != 0:
        lines = [l for l in ANSI.sub("", f"{done.stderr}\n{out}").splitlines() if l.strip()]
        raise TailorError(f"{name} failed: {_short(lines[-1]) if lines else f'exit code {done.returncode}'}")
    return out


# A capable model at medium effort for each tool: tailoring needs judgement, not speed.
# --model / --effort override these. If a default model isn't on someone's plan, the
# tool's own default model is used instead.
DEFAULT_MODELS = {
    "claude": ("opus", "medium"),  # always the latest Opus
    "codex": ("gpt-6.1-sol", "medium"),  # the latest mid-tier model
    "opencode": ("opencode-go/deepseek-v4.1-flash", "high"),  # newest DeepSeek; efforts: high, max
}
MODEL_ERROR = re.compile(r"model|variant", re.IGNORECASE)


def model_and_effort(name: str, model: str | None, effort: str | None) -> tuple[str | None, str | None]:
    default_model, default_effort = DEFAULT_MODELS.get(name, (None, None))
    return model or default_model, effort or (default_effort if not model else None)


def describe(name: str, model: str | None = None, effort: str | None = None) -> str:
    model, effort = model_and_effort(name, model, effort)
    detail = ", ".join(x for x in (model, effort and f"{effort} effort") if x)
    return f"{LABELS.get(name, name)}{f' ({detail})' if detail else ''}"


def _with_fallback(name: str, model: str | None, effort: str | None, run) -> str:
    """Run with our default model; if the tool rejects that model, retry with its own default."""
    chosen, level = model_and_effort(name, model, effort)
    try:
        return run(chosen, level)
    except TailorError as e:
        if model or not MODEL_ERROR.search(str(e)):
            raise
        print(f"  {name} can't use {chosen} on your plan; trying its default model", file=sys.stderr)
        return run(None, effort)


def call_claude_cli(prompt: str, model: str | None, effort: str | None = None) -> str:
    def run(model, effort):
        # No tools: it can only answer. Our instructions replace Claude Code's own system prompt.
        cmd = ["claude", "-p", "--tools", "", "--output-format", "text", "--no-session-persistence",
               "--system-prompt", SYSTEM_PROMPT, *(["--model", model] if model else []),
               *(["--effort", effort] if effort else [])]
        with tempfile.TemporaryDirectory() as empty:  # an empty folder: nothing of yours to read
            return _run("claude", cmd, empty, stdin=prompt)

    return _with_fallback("claude", model, effort, run)


def call_codex_cli(prompt: str, model: str | None, effort: str | None = None) -> str:
    def run(model, effort):
        with tempfile.TemporaryDirectory() as empty:
            answer = Path(empty) / "answer.txt"
            cmd = ["codex", "exec", "--skip-git-repo-check", "--sandbox", "read-only", "--ephemeral",
                   "-C", empty, "-o", str(answer), *(["-m", model] if model else []),
                   *(["-c", f'model_reasoning_effort="{effort}"'] if effort else []), "-"]
            _run("codex", cmd, empty, stdin=f"{SYSTEM_PROMPT}\n\n{prompt}")
            return answer.read_text(encoding="utf-8") if answer.exists() else ""

    return _with_fallback("codex", model, effort, run)


def call_opencode_cli(prompt: str, model: str | None, effort: str | None = None) -> str:
    def run(model, effort):
        if model and effort and "#" not in model:
            model = f"{model}#{effort}"  # opencode's effort is a model "variant"
        cmd = ["opencode", "run", *(["-m", model] if model else []), f"{SYSTEM_PROMPT}\n\n{prompt}"]
        with tempfile.TemporaryDirectory() as empty:
            return _run("opencode", cmd, empty)

    return _with_fallback("opencode", model, effort, run)


# ----------------------------------------------------------------- APIs


def call_anthropic(prompt: str, model: str | None) -> str:
    try:
        import anthropic  # type: ignore
    except ImportError as e:
        raise TailorError("install the AI extra: pip install 'easy-ai-resume[ai]'") from e
    try:
        resp = anthropic.Anthropic().messages.create(
            model=model or os.environ.get("ANTHROPIC_MODEL") or DEFAULT_ANTHROPIC_MODEL,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
    except (anthropic.AnthropicError, TypeError) as e:  # TypeError: no API key set
        raise TailorError(f"the Anthropic request failed: {_short(e)}\n{KEY_HINT}") from e
    return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")


def call_openai(prompt: str, model: str | None) -> str:
    try:
        from openai import OpenAI, OpenAIError  # type: ignore
    except ImportError as e:
        raise TailorError("install the AI extra: pip install 'easy-ai-resume[ai]'") from e
    model = model or os.environ.get("OPENAI_MODEL")
    if not model:
        raise TailorError("choose an OpenAI model with --model or OPENAI_MODEL")
    try:
        resp = OpenAI().chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
    except OpenAIError as e:
        raise TailorError(f"the OpenAI request failed: {_short(e)}\n{KEY_HINT}") from e
    return resp.choices[0].message.content or ""


CALLERS = {
    "claude": call_claude_cli, "codex": call_codex_cli, "opencode": call_opencode_cli,
    "anthropic": call_anthropic, "openai": call_openai,
}


# ----------------------------------------------------------------- parsing

def build_prompt(jd: str, cv_yaml: str, letter_yaml: str) -> str:
    return (
        f"=== JOB DESCRIPTION ===\n{jd}\n\n"
        f"=== CV (YAML) ===\n{cv_yaml}\n\n"
        f"=== COVER LETTER (YAML) ===\n{letter_yaml}\n\n"
        "Reply with the JSON object only."
    )


def parse_response(raw: str) -> tuple[dict[str, Any], dict[str, Any], str]:
    """Pull the JSON object out of a model reply (tolerates code fences)."""
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end <= start:
        raise TailorError(f"model did not return JSON:\n{raw[:1000]}")
    try:
        payload = json.loads(raw[start : end + 1])
    except json.JSONDecodeError as e:
        raise TailorError(f"model returned invalid JSON: {e}") from e
    cv, letter = payload.get("cv"), payload.get("cover_letter")
    if not isinstance(cv, dict) or not isinstance(letter, dict):
        raise TailorError("model reply is missing the 'cv' or 'cover_letter' object")
    return cv, letter, str(payload.get("notes") or "")


# ----------------------------------------------------------------- fact checks

def _items(data: dict[str, Any], section: str) -> list[dict[str, Any]]:
    return [x for x in data.get(section) or [] if isinstance(x, dict)]


def _skills(cv: dict[str, Any]) -> set[str]:
    names = set()
    for group in _items(cv, "skills"):
        for item in group.get("items") or []:
            name = item.get("name") if isinstance(item, dict) else item
            if name:
                names.add(str(name).replace("*", "").strip().lower())
    return names


_NUMBER = re.compile(r"\d[\d,.]*\s?(?:[kKmMbB]\b|%|\+)?")


def _numbers(obj: Any, skip: tuple[str, ...] = ("date", "date_format", "page")) -> set[str]:
    """All numbers in a YAML tree, normalised ("40,000" -> "40000", "31 %" -> "31%")."""
    found: set[str] = set()
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key not in skip:
                found |= _numbers(value, skip)
    elif isinstance(obj, list):
        for value in obj:
            found |= _numbers(value, skip)
    elif isinstance(obj, (str, int, float)) and not isinstance(obj, bool):
        for m in _NUMBER.findall(str(obj)):
            found.add(m.replace(",", "").replace(" ", "").rstrip(".").lower())
    return found


def check_facts(
    cv: dict[str, Any], new_cv: dict[str, Any], letter: dict[str, Any], new_letter: dict[str, Any]
) -> list[str]:
    """Return warnings for anything that looks invented or changed (empty == clean)."""
    warns: list[str] = []

    invented = (_numbers(new_cv) | _numbers(new_letter)) - (_numbers(cv) | _numbers(letter))
    if invented:
        warns.append(f"numbers not in your originals (check metrics): {', '.join(sorted(invented))}")

    if (new_cv.get("name") or "") != (cv.get("name") or ""):
        warns.append("CV name changed")
    for key, value in (cv.get("contact") or {}).items():
        if (new_cv.get("contact") or {}).get(key) != value:
            warns.append(f"contact.{key} changed")

    jobs = {(j.get("company"), j.get("role")): (j.get("start"), j.get("end")) for j in _items(cv, "experience")}
    for job in _items(new_cv, "experience"):
        key = (job.get("company"), job.get("role"))
        if key not in jobs:
            warns.append(f"experience not in original: {key[1]} at {key[0]}")
        elif (job.get("start"), job.get("end")) != jobs[key]:
            warns.append(f"dates changed for {key[1]} at {key[0]}")

    schools = {(e.get("school"), e.get("degree"), e.get("start"), e.get("end")) for e in _items(cv, "education")}
    for ed in _items(new_cv, "education"):
        if (ed.get("school"), ed.get("degree"), ed.get("start"), ed.get("end")) not in schools:
            warns.append(f"education changed or added: {ed.get('school')}")

    for section, label in (("startups", "startup"), ("projects", "project")):
        names = {p.get("name") for p in _items(cv, section)}
        for p in _items(new_cv, section):
            if p.get("name") not in names:
                warns.append(f"{label} not in original: {p.get('name')}")

    added = _skills(new_cv) - _skills(cv)
    if added:
        warns.append(f"skills not in original: {', '.join(sorted(added))}")

    sender, new_sender = letter.get("sender") or {}, new_letter.get("sender") or {}
    if sender.get("name") != new_sender.get("name") or sender.get("links") != new_sender.get("links"):
        warns.append("cover letter sender name or links changed")
    return warns


# ----------------------------------------------------------------- main flow

def keep_photo(original: dict[str, Any], new: dict[str, Any], src_dir: Path, out_dir: Path) -> None:
    """Copy `photo:` from the original, fixing a relative path for the tailored file's folder.

    A relative photo path is read from the YAML file's folder. The tailored copy lives in
    another folder, so `jane.png` has to become e.g. `../../input/jane.png` there.
    """
    photo = original.get("photo")
    if not photo:
        return
    value = str(photo).strip()
    if not value.startswith(("http://", "https://", "data:")) and not Path(value).expanduser().is_absolute():
        target = (src_dir / value).resolve()
        try:
            value = os.path.relpath(target, out_dir.resolve())
        except ValueError:  # Windows: different drives have no relative path
            value = str(target)
    new["photo"] = value


def tailor(
    jd_path: Path,
    cv_path: Path,
    letter_path: Path,
    out_dir: Path,
    provider: str = "auto",
    model: str | None = None,
    force: bool = False,
    effort: str | None = None,
) -> tuple[Path, Path, str, list[str]]:
    """Tailor both documents and write them to out_dir/cv.yaml and out_dir/cover_letter.yaml."""
    out_cv, out_letter = out_dir / "cv.yaml", out_dir / "cover_letter.yaml"
    existing = [p for p in (out_cv, out_letter) if p.exists()]
    if existing and not force:
        raise TailorError(f"{existing[0]} already exists (use --force to overwrite)")

    cv_yaml = cv_path.read_text(encoding="utf-8")
    letter_yaml = letter_path.read_text(encoding="utf-8")
    prompt = build_prompt(jd_path.read_text(encoding="utf-8"), cv_yaml, letter_yaml)

    errors = []
    for name in providers_to_try(provider):
        print(f"Tailoring with {describe(name, model, effort)}. This can take a minute or two...", file=sys.stderr)
        try:
            extra = {"effort": effort} if effort and name in DEFAULT_MODELS else {}
            new_cv, new_letter, notes = parse_response(CALLERS[name](prompt, model, **extra))
            break
        except TailorError as e:
            errors.append(f"  {name}: {e}")
            print(f"  {name} didn't work: {e}", file=sys.stderr)
    else:
        raise TailorError("no AI could tailor your files:\n" + "\n".join(errors) + f"\n\n{NO_PROVIDER}")
    cv, letter = yaml.safe_load(cv_yaml) or {}, yaml.safe_load(letter_yaml) or {}
    warns = check_facts(cv, new_cv, letter, new_letter)
    keep_photo(cv, new_cv, cv_path.parent, out_dir)
    if isinstance(new_letter.get("sender"), dict):
        keep_photo(letter.get("sender") or {}, new_letter["sender"], letter_path.parent, out_dir)

    out_dir.mkdir(parents=True, exist_ok=True)
    dump = lambda d: yaml.safe_dump(d, sort_keys=False, allow_unicode=True, width=100)  # noqa: E731
    out_cv.write_text(dump(new_cv), encoding="utf-8")
    out_letter.write_text(dump(new_letter), encoding="utf-8")
    (out_dir / "changes.diff").write_text(
        changes(cv, new_cv, cv_path.name, "cv.yaml") + changes(letter, new_letter, letter_path.name, "cover_letter.yaml"),
        encoding="utf-8",
    )
    return out_cv, out_letter, notes, warns


def changes(before: dict[str, Any], after: dict[str, Any], old_name: str, new_name: str) -> str:
    """Only what really changed. Both sides are written the same way, so comments, quotes and
    line wrapping in your original don't show up as changes."""
    def lines(data: dict[str, Any]) -> list[str]:
        data = copy.deepcopy(data)
        data.pop("photo", None)  # the path is rewritten for the new folder
        if isinstance(data.get("sender"), dict):
            data["sender"].pop("photo", None)
        return yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=10**6).splitlines()

    diff = difflib.unified_diff(lines(before), lines(after), f"original {old_name}", f"tailored {new_name}",
                                lineterm="", n=1)
    return "".join(f"{line}\n" for line in diff)
