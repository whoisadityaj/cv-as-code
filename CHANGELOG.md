# Changelog

## Unreleased

- **Fixed:** links in cover letter PDFs (LinkedIn, GitHub, website) couldn't be clicked, in any theme.
- **Fixed:** a large photo made each PDF over 2 MB, more than some job portals accept. Images are now
  embedded at up to 300 dpi (print quality): a 2.1 MB CV becomes about 250 KB.
- The `bold` cover letter now has its own look, a dark header band like the bold CV. It used to be
  the same as `sidebar`'s.
- New `startups:` section for your own companies, shown before `projects:` with the same fields.
- New `page: fit` (or `--page-size fit`): one page exactly as tall as your content, with no empty space
  at the bottom. Better than the fixed `single` sizes for CVs read on screen.

## 0.9.0 — 2026-11-05

- **Fixed:** `tailor --build` crashed with a photo theme (the tailored copy couldn't find the photo).
  The tailored YAML now points to your original photo.
- **Fixed:** a wrong or missing API key, no credit or no internet now prints one clear line instead of
  a Python traceback.
- **Fixed:** when the PDF can't be made, the advice is now `--html-only` (`--html` still needs the PDF).
- Every theme now uses the deep red from the README pictures (`#9b1b30`) by default, so you get what
  you see there. `accent:` in the YAML or the new `--accent` option (`build` and `tailor`) changes it.
- A photo theme (sidebar, bold, executive) without a `photo:` line now **asks for your photo** in the
  terminal: drag it in, and it's copied to `input/` and added to both YAML files. Enter alone saves
  `photo: none`. Outside a terminal (scripts, GitHub Actions) it prints a note instead.
- `init` no longer copies Jane's sample photo, so a photo theme asks for yours.
- `tailor` takes `--theme`, `--accent` and `--ats`, and makes the PDFs when any of them is given.
- README: numbered steps for picking a theme and adding your photo, tailoring as its own step with a
  plain-words explanation, plus an ATS section and a table of commands and options.

## 0.8.0 — 2026-11-04

- `init` now puts your files in an `input/` folder, and `build` / `tailor` look there first.
  Files directly in the folder still work.
- README: get started in 2 steps. Install with `uv tool install` (no virtual environment to
  create or activate; uv also sets up Python).

## 0.7.1 — 2026-11-04

- macOS: finds Pango installed by Homebrew automatically, so no `DYLD_FALLBACK_LIBRARY_PATH`
  export is needed.
- A missing YAML file now says which folder was searched and suggests `cd my-cv`.

## 0.7.0 — 2026-11-04

- With no file names, `build` and `tailor` use `cv.yaml` and `cover_letter.yaml` in the current
  folder (the files `init` creates). The settings file is now only needed to change that.
- Shorter, simpler README.

## 0.6.0 — 2026-11-04

- `build` now writes **only the PDF** by default. Pass `--html` to also write the HTML file, or
  `--html-only` to skip the PDF. If the PDF can't be made, the error suggests `--html`.

## 0.5.0 — 2026-11-04

- **Renamed from cv-as-code to easy-ai-resume**: the package, the `easy-ai-resume` command, the
  Python import (`easy_ai_resume`) and the GitHub Action. Old GitHub links redirect.
- The project file is now `easy-ai-resume.yaml`; an existing `cv-as-code.yaml` is still read.
- GitHub Action: red Marketplace branding and the full list of themes.

## 0.4.0 — 2026-11-03

- Optional `cv-as-code.yaml` project file (`cv`, `letter`, `output`, `tailored`, `build`), so
  `cv-as-code build` and `cv-as-code tailor jds/<job>.md` work without paths.
- `tailor` names its output folder after the job file, can build by default, and prints the
  `diff` commands to review changes. `--no-build` overrides the project file.

## 0.3.0 — 2026-11-03

- `cv-as-code init` creates starter files (`cv.yaml`, `cover_letter.yaml`, `job.md`, sample photo)
  to edit, so you don't need to clone the repo.
- A custom `accent:` now also sets the light accent used on dark panels (sidebar, bold).
- README: step-by-step guide in plain language, royal red look, emoji headings.

## 0.2.0 — 2026-11-03

- Four new themes: `sidebar` (two columns, photo, skill chips), `bold` (dark header band),
  `executive` (serif with gold accents) and `minimal` (light, airy, margin labels).
- Optional `photo:` for CVs and `sender.photo:` for cover letters, shown by photo themes,
  embedded in the HTML/PDF, and always left out in ATS mode.
- Fixed a 1px colour line on the right edge of pages with a colour band.
- README now makes clear that AI edits your YAML, never the PDF.

## 0.1.0 — 2026-11-03

- `cv-as-code build`: YAML to HTML and PDF, `classic`, `modern` and `compact` themes, ATS mode.
- `cv-as-code tailor`: tailor a CV and cover letter to a job with Claude or OpenAI, with a fact
  check for invented numbers, dates, employers, schools, skills, projects and contact details.
- GitHub Action that builds your PDFs on every push.
