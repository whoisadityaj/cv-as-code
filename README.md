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
  <b>Your resume, made easy.</b> Keep your CV in one simple text file and build a clean PDF from it.<br>
  For each job, AI rewrites the <b>YAML</b> to match the posting, and a fact check
  makes sure it <b>never invents anything</b>.
</p>

<p align="center">
  <a href="#-step-by-step-guide">🧭 Step-by-step guide</a> ·
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

- 📄 **YAML in, PDF out.** Plain text you can diff, review and keep in Git.
- 🎨 **7 themes + ATS mode.** From classic to a two-column sidebar with your photo, plus a plain
  layout that applicant-tracking systems parse cleanly.
- 🤖 **AI tailoring with a fact check.** AI edits your YAML (never the PDF) to fit a job description,
  then easy-ai-resume flags any number, date, employer, school or skill that wasn't in your original.
- 🚀 **Runs in GitHub Actions.** Push your YAML, get fresh PDFs.

## 🧭 Step-by-step guide

No coding needed. You will edit one text file and run a few commands. It takes about 10 minutes.

> **Already use Python?** `pip install https://github.com/whoisadityaj/easy-ai-resume/archive/refs/heads/main.zip`,
> then `easy-ai-resume init` and `easy-ai-resume build cv.yaml`.

### Step 1: Check that you have Python

Open the **Terminal** app (Mac) or **PowerShell** (Windows) and type:

```bash
python3 --version
```

You need **3.10 or newer**. If you see an error or an older number, install Python from
[python.org/downloads](https://www.python.org/downloads/). On Windows, tick **"Add Python to PATH"**
during install, and use `python` instead of `python3` in the steps below.

### Step 2: Install the PDF helper

easy-ai-resume uses a free library called Pango to draw PDFs.

- **Mac:** install [Homebrew](https://brew.sh), then run `brew install pango`
- **Ubuntu / Debian:** `sudo apt install libpango-1.0-0 libpangoft2-1.0-0`
- **Windows:** follow [WeasyPrint's Windows steps](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows)

Can't get it working? Skip it. Add `--html` when you build (step 5) to get an HTML file, then
open it in your browser and use **Print → Save as PDF**.

### Step 3: Install easy-ai-resume

This creates a small private folder (`cv-env`) for the tool, so it doesn't touch anything else
on your computer.

```bash
python3 -m venv cv-env
source cv-env/bin/activate        # Windows: cv-env\Scripts\activate
pip install https://github.com/whoisadityaj/easy-ai-resume/archive/refs/heads/main.zip
```

> Every time you open a new terminal, run the `activate` line again before using easy-ai-resume.

### Step 4: Get the starter files

```bash
mkdir my-cv
cd my-cv
easy-ai-resume init
```

This gives you four files to start from: `cv.yaml` (your CV), `cover_letter.yaml`, `job.md`
(a job post, for AI tailoring) and `jane.png` (a sample photo).

### Step 5: Make your first PDF

```bash
easy-ai-resume build cv.yaml
```

Your PDF is now in the `output` folder (add `--html` if you also want the HTML file). Open it:

```bash
open output/Jane_Doe_CV.pdf       # Windows: start output\Jane_Doe_CV.pdf
```

> **Mac: "PDF generation failed"?** Run `export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib`
> and try again (add that line to `~/.zshrc` so you never need to type it again).

### Step 6: Put in your own details

Open `cv.yaml` in any text editor (TextEdit in plain-text mode, Notepad or VS Code) and replace
Jane's details with yours. A few simple rules:

```yaml
name: Your Name                  # "label: value", one per line
title: Product Designer
experience:
  - role: Senior Designer        # a line starting with "-" is one item in a list
    company: Your Company        # indent with 2 spaces, never with Tab
    start: Jan 2022
    end: Present
    bullets:
      - Led the redesign of the **checkout page**   # **text** makes it bold
```

- Keep the same structure as the example, and delete any section you don't need.
- If a value has a `:` or `#` in it, put it in quotes: `title: "Lead: Platform"`.
- Run `easy-ai-resume build cv.yaml` again after every change. The PDF is named after you
  (for example `output/Your_Name_CV.pdf`).

### Step 7: Pick a look

Change the `theme:` line in `cv.yaml` (see [Themes](#-themes) below), or try one without editing:

```bash
easy-ai-resume build cv.yaml --theme sidebar
```

**Your photo:** put it in the `my-cv` folder and change the line to `photo: me.jpg`. Only the
`sidebar`, `bold` and `executive` themes show a photo. Don't want one? Delete the `photo:` line.

### Step 8: Make your cover letter

Edit `cover_letter.yaml` the same way, then:

```bash
easy-ai-resume build cover_letter.yaml
```

### Step 9 (optional): Tailor it to a job with AI

1. Paste the job post into `job.md`.
2. Get an API key from [Anthropic](https://console.anthropic.com) (or OpenAI). Each run uses a
   little of your API credit.
3. Install the AI add-on and add your key:

   ```bash
   pip install "easy-ai-resume[ai] @ https://github.com/whoisadityaj/easy-ai-resume/archive/refs/heads/main.zip"
   export ANTHROPIC_API_KEY=your-key-here      # Windows: $env:ANTHROPIC_API_KEY="your-key-here"
   ```

4. Run it:

   ```bash
   easy-ai-resume tailor job.md --cv cv.yaml --letter cover_letter.yaml --out tailored/acme --build
   ```

Your originals are not changed. The tailored files and PDFs go in `tailored/acme`. Read any
**"Check these before sending"** warnings: they point at things the AI may have made up.

### Step 10: Before you send it

- Applying through an online job portal? Make a plain version that hiring software can read:
  `easy-ai-resume build cv.yaml --ats`
- Open the PDF and check the dates, numbers and contact details yourself.

## 🎨 Themes

Seven looks from the same YAML, plus an ATS mode. Three of them show your photo.

<p align="center">
  <img src="docs/images/gallery.png" alt="Photo themes (sidebar, bold, executive) on a dark band and clean themes (modern, minimal, classic, compact, ATS mode) on a light band" width="100%">
</p>

| Theme | Look | Photo |
|---|---|:---:|
| `sidebar` | Two columns: photo, contact and skill chips on a full-height colour panel | ✅ |
| `bold` | Dark header band, accent headings | ✅ |
| `executive` | Refined serif, gold accents, photo on the right | ✅ |
| `modern` | Sans-serif, accent colour, coloured cover-letter sidebar | ❌ |
| `minimal` | Light type, lots of white space, labels in the margin | ❌ |
| `classic` (default) | Serif, centred header, ruled section titles | ❌ |
| `compact` | Smaller type and tighter spacing to fit more on one page | ❌ |
| ATS mode | One plain column, full URLs, no photo, colour or icons | ❌ |

Set them in YAML or override on the command line:

```yaml
theme: sidebar
accent: "#0f766e"   # any hex colour; every theme has its own default
photo: me.jpg       # jpg, png, webp or svg, relative to this YAML file (photo themes only)
page: letter        # a4, letter, legal, single, single-tall, or a CSS size like "210mm 380mm"
ats: true           # plain output for applicant-tracking systems (drops the photo)
```

For a cover letter, put the photo under `sender:` (`sender: {photo: me.jpg}`).

```bash
easy-ai-resume build cv.yaml --theme bold
easy-ai-resume build cv.yaml cover_letter.yaml --ats
```

> 📸 **Photo or not?** Many US and UK employers prefer CVs without photos, and ATS software ignores
> them. Photos are common in much of Europe, Asia and Latin America. ATS mode always leaves it out.

## 🤖 Tailor to a job with AI

The AI never touches a PDF. It reads your YAML and the job post, and writes a new YAML:

```text
cv.yaml + job.md  ──AI──▶  tailored/acme/cv.yaml  ──fact check──▶  you review  ──build──▶  PDF
```

```bash
pip install "easy-ai-resume[ai] @ git+https://github.com/whoisadityaj/easy-ai-resume"
export ANTHROPIC_API_KEY=...        # or OPENAI_API_KEY plus OPENAI_MODEL
easy-ai-resume tailor job.md --cv cv.yaml --letter cover_letter.yaml --out tailored/acme --build
```

This writes `tailored/acme/cv.yaml` and `tailored/acme/cover_letter.yaml` (and PDFs with
`--build`). Your originals are never modified, and existing files are not overwritten unless you
pass `--force`.

The model is told to reword, reorder and drop content but never invent it. Then **easy-ai-resume
checks**, and warns you about:

- numbers that weren't in your originals (`65%`, `3M users`, `12 years`)
- changed dates, new employers or job titles, changed schools or degrees
- skills or projects you never listed
- changed contact details or cover-letter links

```text
Check these before sending (possible invented or changed facts):
  - numbers not in your originals (check metrics): 65%
  - skills not in original: rust
```

Add `--strict` to exit with code 2 when there are warnings (useful in scripts). It's still a
draft: read the diff before you send anything.

Options: `--provider anthropic|openai`, `--model NAME` (Anthropic defaults to Claude Sonnet; OpenAI
needs a model name). Your CV and the job description are sent to the provider you choose.

## 📁 Apply to many jobs from one folder

Keep your CV in its own folder (or a private repo) and add a `easy-ai-resume.yaml` so you never type
paths again:

```yaml
cv: data/cv.yaml
letter: data/cover_letter.yaml
output: output            # where `easy-ai-resume build` writes
tailored: applications    # one folder per job
build: true               # make the PDFs right after tailoring
```

```text
my-cv/
├── easy-ai-resume.yaml
├── data/cv.yaml, data/cover_letter.yaml
├── jds/acme-senior-sdet.md          ← paste each job post here
└── applications/acme-senior-sdet/   ← tailored YAML + PDFs for that job
```

```bash
easy-ai-resume build                           # your normal CV and cover letter
easy-ai-resume tailor jds/acme-senior-sdet.md  # tailored copy in applications/acme-senior-sdet/
```

`tailor` prints the `diff` commands to review every change. Tip: commit the tailored YAML files so
you always know what you sent to each company, and ignore the PDFs (you can rebuild them).

## 🚀 Build in GitHub Actions

Keep your CV in a (private) repo and copy [`examples/github-workflow.yml`](examples/github-workflow.yml)
to `.github/workflows/cv.yml`:

```yaml
- uses: whoisadityaj/easy-ai-resume@v0.5.0
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

**CV** (detected by a top-level `name:`): `name`, `title`, `photo`, `contact` (`phone`, `email`, `website`,
`linkedin`, `github`, `location`), `summary`, `skills` (groups of `items` with optional `bold`),
`experience` (`role`, `company`, `location`, `start`, `end`, `intro`, `bullets`), `education`,
`projects` (`name`, `stack`, `links`, `bullets`), `publications`, `awards`, `certifications`.

**Cover letter** (detected by a top-level `sender:`): `sender` (`name`, `tagline`, `photo`, `links`),
`date` (`auto` = today, format with `date_format`), `recipient` (`hiring_manager`, `team`,
`company`, `address`), `salutation`, `body` (list of Markdown paragraphs), `sign_off`.

Every section is optional. Run `easy-ai-resume init` (or see [examples](examples/)) for everything in use.

## License

[MIT](LICENSE). If easy-ai-resume helps you land an interview, a ⭐ helps the next person find it.
