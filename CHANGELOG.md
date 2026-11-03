# Changelog

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
