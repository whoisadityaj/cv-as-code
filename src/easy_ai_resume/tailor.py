"""Tailor a CV + cover letter to a job description with an LLM.

The model may reword, reorder and drop content, but not invent facts.
`check_facts` compares the result with the original and reports anything
that looks invented or changed. Always review the diff before sending.
"""
from __future__ import annotations

import json
import os
import re
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

Style: lead with the most relevant experience, use the JD's vocabulary only
where the candidate truly has that experience, keep every existing number,
no filler like "self-motivated team player".

Return ONLY a JSON object:
{"cv": {...}, "cover_letter": {...}, "notes": "2-3 short bullets on what you changed"}
"""


class TailorError(RuntimeError):
    pass


# ----------------------------------------------------------------- LLM calls

def pick_provider(provider: str = "auto") -> str:
    if provider != "auto":
        return provider
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    raise TailorError("set ANTHROPIC_API_KEY or OPENAI_API_KEY (or pass --provider)")


def call_anthropic(prompt: str, model: str | None) -> str:
    try:
        import anthropic  # type: ignore
    except ImportError as e:
        raise TailorError("install the AI extra: pip install 'easy-ai-resume[ai]'") from e
    resp = anthropic.Anthropic().messages.create(
        model=model or os.environ.get("ANTHROPIC_MODEL") or DEFAULT_ANTHROPIC_MODEL,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")


def call_openai(prompt: str, model: str | None) -> str:
    try:
        from openai import OpenAI  # type: ignore
    except ImportError as e:
        raise TailorError("install the AI extra: pip install 'easy-ai-resume[ai]'") from e
    model = model or os.environ.get("OPENAI_MODEL")
    if not model:
        raise TailorError("choose an OpenAI model with --model or OPENAI_MODEL")
    resp = OpenAI().chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    return resp.choices[0].message.content or ""


CALLERS = {"anthropic": call_anthropic, "openai": call_openai}


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

    projects = {p.get("name") for p in _items(cv, "projects")}
    for p in _items(new_cv, "projects"):
        if p.get("name") not in projects:
            warns.append(f"project not in original: {p.get('name')}")

    added = _skills(new_cv) - _skills(cv)
    if added:
        warns.append(f"skills not in original: {', '.join(sorted(added))}")

    sender, new_sender = letter.get("sender") or {}, new_letter.get("sender") or {}
    if sender.get("name") != new_sender.get("name") or sender.get("links") != new_sender.get("links"):
        warns.append("cover letter sender name or links changed")
    return warns


# ----------------------------------------------------------------- main flow

def tailor(
    jd_path: Path,
    cv_path: Path,
    letter_path: Path,
    out_dir: Path,
    provider: str = "auto",
    model: str | None = None,
    force: bool = False,
) -> tuple[Path, Path, str, list[str]]:
    """Tailor both documents and write them to out_dir/cv.yaml and out_dir/cover_letter.yaml."""
    out_cv, out_letter = out_dir / "cv.yaml", out_dir / "cover_letter.yaml"
    existing = [p for p in (out_cv, out_letter) if p.exists()]
    if existing and not force:
        raise TailorError(f"{existing[0]} already exists (use --force to overwrite)")

    cv_yaml = cv_path.read_text(encoding="utf-8")
    letter_yaml = letter_path.read_text(encoding="utf-8")
    prompt = build_prompt(jd_path.read_text(encoding="utf-8"), cv_yaml, letter_yaml)

    raw = CALLERS[pick_provider(provider)](prompt, model)
    new_cv, new_letter, notes = parse_response(raw)
    warns = check_facts(yaml.safe_load(cv_yaml) or {}, new_cv, yaml.safe_load(letter_yaml) or {}, new_letter)

    out_dir.mkdir(parents=True, exist_ok=True)
    dump = lambda d: yaml.safe_dump(d, sort_keys=False, allow_unicode=True, width=100)  # noqa: E731
    out_cv.write_text(dump(new_cv), encoding="utf-8")
    out_letter.write_text(dump(new_letter), encoding="utf-8")
    return out_cv, out_letter, notes, warns
