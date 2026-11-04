<p align="center">
  <img src="docs/images/banner.svg" alt="easy-ai-resume: YAML typing into a live CV preview, then PDF ready" width="100%">
</p>

<p align="center">
  <a href="https://github.com/whoisadityaj/easy-ai-resume/actions/workflows/ci.yml"><img src="https://github.com/whoisadityaj/easy-ai-resume/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-b3122e" alt="MIT license"></a>
  <img src="https://img.shields.io/badge/python-3.10%2B-9b1b30?logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/AI-Claude%20%7C%20OpenAI-5c0a1a" alt="Works with Claude or OpenAI">
</p>

<h1 align="center">easy-ai-resume</h1>

<p align="center">
  <b>Your resume, made easy.</b> One text file in, a clean PDF out.<br>
  AI tailors it to each job, and a fact check stops it <b>inventing anything</b>.
</p>

<p align="center">
  <a href="#-step-by-step-guide">🧭 Guide</a> ·
  <a href="#-themes">🎨 Themes</a> ·
  <a href="#-tailor-to-a-job-with-ai">🤖 AI tailoring</a> ·
  <a href="#-build-in-github-actions">🚀 GitHub Action</a>
</p>

<p align="center">
  <img src="docs/images/demo.svg" alt="Terminal demo: build a PDF, then tailor to a job and get warned about an invented number and skill" width="100%">
</p>

## ✨ What you get

<p align="center">
  <img src="docs/images/showcase.png" alt="Three real pages rendered by easy-ai-resume from one YAML file: sidebar CV, bold cover letter and executive CV" width="100%">
</p>

- 📄 **YAML in, PDF out.** Plain text you can edit, diff and keep in Git.
- 🎨 **7 themes + ATS mode.** Classic to a photo sidebar, plus a plain layout hiring software can read.
- 🤖 **AI tailoring, fact-checked.** AI edits your YAML (never the PDF). Any new number, date, employer, school or skill gets flagged.
- 🚀 **GitHub Action.** Push your YAML, get fresh PDFs.

## 🧭 Step-by-step guide

No coding needed. About 10 minutes.

> **Know Python?** `pip install https://github.com/whoisadityaj/easy-ai-resume/archive/refs/heads/main.zip`,
> then `easy-ai-resume init` and `easy-ai-resume build`.

### 1. Check Python

In **Terminal** (Mac) or **PowerShell** (Windows):

```bash
python3 --version
```

You need **3.10+**. Otherwise install it from [python.org](https://www.python.org/downloads/).
On Windows, tick **"Add Python to PATH"** and type `python` instead of `python3`.

### 2. Install the PDF helper (Pango)

- **Mac:** install [Homebrew](https://brew.sh), then `brew install pango`
- **Ubuntu / Debian:** `sudo apt install libpango-1.0-0 libpangoft2-1.0-0`
- **Windows:** see [WeasyPrint's Windows steps](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows)

Stuck? Skip it. Build with `--html`, open the file in a browser, and **Print → Save as PDF**.

### 3. Install easy-ai-resume

Make one folder for your resume. The tool, your YAML files and your PDFs all live in it.
`cv-env` (inside it) holds the tool and doesn't touch anything else.

```bash
mkdir my-cv && cd my-cv
python3 -m venv cv-env
source cv-env/bin/activate        # Windows: cv-env\Scripts\activate
pip install https://github.com/whoisadityaj/easy-ai-resume/archive/refs/heads/main.zip
```

> New terminal? Run the `activate` line again first.

### 4. Get the starter files

In the same `my-cv` folder:

```bash
easy-ai-resume init
```

You get `cv.yaml`, `cover_letter.yaml`, `job.md` (a job post for AI tailoring) and `jane.png` (a sample photo).

### 5. Make your PDFs

```bash
easy-ai-resume build
open output/Jane_Doe_CV.pdf       # Windows: start output\Jane_Doe_CV.pdf
```

With no file names, `build` uses `cv.yaml` and `cover_letter.yaml` in this folder. Add `--html` to also get the HTML.

> Run every command inside `my-cv`, with `cv-env` activated (step 3).

### 6. Add your details

Open `cv.yaml` in any text editor and replace Jane's details:

```yaml
name: Your Name                  # "label: value", one per line
title: Product Designer
experience:
  - role: Senior Designer        # "-" starts a list item
    company: Your Company        # indent with 2 spaces, never Tab
    start: Jan 2022
    end: Present
    bullets:
      - Led the redesign of the **checkout page**   # **text** = bold
```

- Keep the structure. Delete sections you don't need.
- Quote values with `:` or `#`: `title: "Lead: Platform"`.
- Rebuild after each change. The PDF is named after you, e.g. `output/Your_Name_CV.pdf`.

Do the same for `cover_letter.yaml`.

### 7. Pick a look

Change `theme:` in `cv.yaml`, or try one without editing:

```bash
easy-ai-resume build --theme sidebar
```

**Photo:** put it in `my-cv/` and set `photo: me.jpg`. Only `sidebar`, `bold` and `executive` show it. No photo? Delete the line.

### 8. Tailor to a job (optional)

1. Paste the job post into `job.md`.
2. Get an API key from [Anthropic](https://console.anthropic.com) (or OpenAI). Each run uses a little API credit.
3. Install the AI add-on, set your key, run it:

   ```bash
   pip install "easy-ai-resume[ai] @ https://github.com/whoisadityaj/easy-ai-resume/archive/refs/heads/main.zip"
   export ANTHROPIC_API_KEY=your-key-here      # Windows: $env:ANTHROPIC_API_KEY="your-key-here"
   easy-ai-resume tailor job.md --build
   ```

Your originals stay untouched. The tailored files and PDFs go to `tailored/job/`.
Read any **"Check these before sending"** warnings: the AI may have made those up.

### 9. Before you send it

- Job portal? Make a plain version hiring software can read: `easy-ai-resume build --ats`
- Check dates, numbers and contact details yourself.

## 🎨 Themes

Seven looks from one YAML, plus ATS mode. Three show your photo.

<p align="center">
  <img src="docs/images/gallery.png" alt="Photo themes (sidebar, bold, executive) on a dark band and clean themes (modern, minimal, classic, compact, ATS mode) on a light band" width="100%">
</p>

| Theme | Look | Photo |
|---|---|:---:|
| `sidebar` | Two columns, colour panel with photo, contact and skill chips | ✅ |
| `bold` | Dark header band, accent headings | ✅ |
| `executive` | Refined serif, gold accents, photo on the right | ✅ |
| `modern` | Sans-serif, accent colour, coloured cover-letter sidebar | ❌ |
| `minimal` | Light type, lots of white space, labels in the margin | ❌ |
| `classic` (default) | Serif, centred header, ruled section titles | ❌ |
| `compact` | Smaller type, fits more on one page | ❌ |
| ATS mode | One plain column, full URLs, no photo, colour or icons | ❌ |

Set them in YAML:

```yaml
theme: sidebar
accent: "#0f766e"   # any hex colour; each theme has a default
photo: me.jpg       # jpg, png, webp or svg, next to this file (photo themes only)
page: letter        # a4, letter, legal, single, single-tall, or a CSS size like "210mm 380mm"
ats: true           # plain output for hiring software (drops the photo)
```

Or on the command line: `easy-ai-resume build --theme bold` or `--ats`.
Cover letter photo goes under `sender:` (`sender: {photo: me.jpg}`).

> 📸 **Photo or not?** US and UK employers often prefer none, and ATS software ignores it.
> Photos are common in Europe, Asia and Latin America. ATS mode always drops it.

## 🤖 Tailor to a job with AI

The AI never touches the PDF. It reads your YAML and the job post, and writes a new YAML:

```text
cv.yaml + job.md  ──AI──▶  tailored/job/cv.yaml  ──fact check──▶  you review  ──build──▶  PDF
```

```bash
export ANTHROPIC_API_KEY=...        # or OPENAI_API_KEY plus OPENAI_MODEL
easy-ai-resume tailor job.md --build
```

- Output goes to `tailored/<job file name>/`. Change it with `--out`.
- Originals are never changed. Existing files aren't overwritten without `--force`.
- Use other files with `--cv` and `--letter`.
- It prints `diff` commands so you can review every change.

The AI may reword, reorder and drop content, never invent it. easy-ai-resume then warns you about:

- numbers not in your originals (`65%`, `3M users`, `12 years`)
- changed dates, new employers or job titles, changed schools or degrees
- skills or projects you never listed
- changed contact details or cover-letter links

```text
Check these before sending (possible invented or changed facts):
  - numbers not in your originals (check metrics): 65%
  - skills not in original: rust
```

`--strict` exits with code 2 on warnings (handy in scripts). It's still a draft: read the diff.

Options: `--provider anthropic|openai`, `--model NAME` (Anthropic defaults to Claude Sonnet; OpenAI needs a model).
Your CV and the job post are sent to that provider.

## 📁 Many jobs, one folder

Save each job post as its own file and tailor each one:

```text
my-cv/
├── cv-env/                     ← the tool (step 3)
├── cv.yaml, cover_letter.yaml
├── jobs/acme-backend.md        ← one file per job post
└── tailored/acme-backend/      ← tailored YAML + PDFs
```

```bash
easy-ai-resume tailor jobs/acme-backend.md --build
```

Want other file names or folders? Add an optional `easy-ai-resume.yaml`:

```yaml
cv: data/cv.yaml                 # default: cv.yaml
letter: data/cover_letter.yaml   # default: cover_letter.yaml
output: output                   # where build writes
tailored: applications           # where tailor writes
build: true                      # make PDFs after tailoring
```

Tip: keep the tailored YAML so you know what you sent where. The PDFs can always be rebuilt.

## 🚀 Build in GitHub Actions

Keep your CV in a private repo. Copy [`examples/github-workflow.yml`](examples/github-workflow.yml) to `.github/workflows/cv.yml`:

```yaml
- uses: whoisadityaj/easy-ai-resume@v0.7.1
  with:
    files: cv.yaml cover_letter.yaml
    # theme: modern
    # ats: "true"
- uses: actions/upload-artifact@v4
  with:
    name: cv-pdfs
    path: output/*.pdf
```

Every push rebuilds the PDFs and attaches them to the run.

## YAML reference

**CV** (has a top-level `name:`): `name`, `title`, `photo`, `contact` (`phone`, `email`, `website`,
`linkedin`, `github`, `location`), `summary`, `skills` (groups of `items`, optional `bold`),
`experience` (`role`, `company`, `location`, `start`, `end`, `intro`, `bullets`), `education`,
`projects` (`name`, `stack`, `links`, `bullets`), `publications`, `awards`, `certifications`.

**Cover letter** (has a top-level `sender:`): `sender` (`name`, `tagline`, `photo`, `links`),
`date` (`auto` = today, format with `date_format`), `recipient` (`hiring_manager`, `team`,
`company`, `address`), `salutation`, `body` (Markdown paragraphs), `sign_off`.

Every section is optional. `easy-ai-resume init` (or [examples](examples/)) shows them all.

## License

[MIT](LICENSE). If it helps you land an interview, a ⭐ helps the next person find it.
