<p align="center">
  <img src="docs/images/banner.svg" alt="easy-ai-resume: YAML typing into a live CV preview, then PDF ready" width="100%">
</p>

<p align="center">
  <a href="https://github.com/whoisadityaj/easy-ai-resume/actions/workflows/ci.yml"><img src="https://github.com/whoisadityaj/easy-ai-resume/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-b3122e" alt="MIT license"></a>
  <img src="https://img.shields.io/badge/AI-Claude%20%7C%20OpenAI-5c0a1a" alt="Works with Claude or OpenAI">
</p>

<h1 align="center">easy-ai-resume</h1>

<p align="center">
  <b>Your resume, made easy.</b> One text file in, a clean PDF out.<br>
  AI tailors it to each job, and a fact check stops it <b>inventing anything</b>.
</p>

<p align="center">
  <img src="docs/images/demo.svg" alt="Terminal demo: build PDFs, then tailor to a job and get warned about an invented number and skill" width="100%">
</p>

<p align="center">
  <img src="docs/images/showcase.png" alt="Three real pages rendered by easy-ai-resume from one YAML file: sidebar CV, bold cover letter and executive CV" width="100%">
</p>

## 🧭 Get started

### 1. Install (once)

**Mac** (needs [Homebrew](https://brew.sh)):

```bash
brew install uv pango
uv tool install "easy-ai-resume[ai] @ https://github.com/whoisadityaj/easy-ai-resume/archive/refs/tags/v0.8.0.zip"
```

- **Ubuntu / Debian:** `sudo apt install libpango-1.0-0 libpangoft2-1.0-0`, install [uv](https://docs.astral.sh/uv/getting-started/installation/), then the `uv tool install` line.
- **Windows:** install [uv](https://docs.astral.sh/uv/getting-started/installation/) and [Pango](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows), then the `uv tool install` line.
- uv installs Python for you. `command not found`? Run `uv tool update-shell` and open a new terminal.
- **Update later:** run the `uv tool install` line again with the newer version and `--force`.

### 2. Add your details

```bash
mkdir my-cv && cd my-cv
easy-ai-resume init
```

This makes `input/` with a sample `cv.yaml`, `cover_letter.yaml`, `job.md` and photo. Replace the sample details with yours:

```yaml
name: Your Name                  # "label: value", one per line
experience:
  - role: Senior Designer        # "-" starts a list item
    company: Your Company        # indent with 2 spaces, never Tab
    start: Jan 2022
    end: Present
    bullets:
      - Led the redesign of the **checkout page**   # **text** = bold
```

Delete sections you don't need. Quote values containing `:` or `#`: `title: "Lead: Platform"`.

### 3. Make your PDFs (pick one)

| | A. Standard | B. Tailored to a job |
|---|---|---|
| Run | `easy-ai-resume build` | `easy-ai-resume tailor input/job.md --build` |
| Needs | nothing else | the job post pasted into `input/job.md` + an AI key ¹ |
| PDFs in | `output/` | `tailored/job/` (with the tailored YAML) |

¹ Get a key from [Anthropic](https://console.anthropic.com) (or OpenAI), then `export ANTHROPIC_API_KEY=your-key`
(Windows: `$env:ANTHROPIC_API_KEY="your-key"`). Each run costs a little API credit, and your CV and the job post are sent to that provider.

```text
my-cv/
├── input/      ← cv.yaml, cover_letter.yaml, job.md, photo (you edit these)
├── output/     ← standard PDFs
└── tailored/   ← one folder per job: tailored YAML + PDFs
```

**More jobs:** one file per job post in `input/`, e.g. `input/acme.md` → `tailored/acme/`.

**What tailoring does:** the AI rewords, reorders and drops content in a *copy* of your YAML. It never edits your
originals or the PDF. Then easy-ai-resume warns you about anything it may have invented: new numbers, dates,
employers, job titles, schools, skills, projects or contact details. It prints `diff` commands so you can review every change.

```text
Check these before sending (possible invented or changed facts):
  - numbers not in your originals (check metrics): 65%
  - skills not in original: rust
```

Before sending, always check dates, numbers and contact details yourself.

## 🎨 Themes

<p align="center">
  <img src="docs/images/gallery.png" alt="Photo themes (sidebar, bold, executive) on a dark band and clean themes (modern, minimal, classic, compact, ATS mode) on a light band" width="100%">
</p>

| Theme | Look | Photo |
|---|---|:---:|
| `sidebar` | Two columns, colour panel with photo and skill chips | ✅ |
| `bold` | Dark header band, accent headings | ✅ |
| `executive` | Refined serif, gold accents | ✅ |
| `modern` | Sans-serif, accent colour | ❌ |
| `minimal` | Light type, labels in the margin | ❌ |
| `classic` (default) | Serif, centred header | ❌ |
| `compact` | Smaller type, fits more on a page | ❌ |
| ATS mode | One plain column hiring software can read | ❌ |

Set them at the top of `input/cv.yaml`, or try one with `easy-ai-resume build --theme sidebar` (or `--ats`):

```yaml
theme: sidebar
accent: "#0f766e"   # any hex colour
photo: me.jpg       # put the photo in input/ (photo themes only)
page: a4            # a4, letter, legal, single, single-tall, or a CSS size like "210mm 380mm"
```

No PDF because Pango won't install? `easy-ai-resume build --html`, open it in a browser, **Print → Save as PDF**.

## ⚙️ More

- **Other options:** `easy-ai-resume build --help` and `easy-ai-resume tailor --help`
  (`--provider`, `--model`, `--strict`, `--out`, `--force`, page size and more).
- **Other file names:** add `easy-ai-resume.yaml` to `my-cv/` with `cv: input/resume.yaml`, `letter:`, `output:`, `tailored:` or `build: true`.
- **GitHub Action:** keep `my-cv/` in a private repo and copy [`examples/github-workflow.yml`](examples/github-workflow.yml)
  to `.github/workflows/cv.yml`. Every push rebuilds your PDFs.
- **All YAML fields:** see the samples `init` creates (also in [examples/](examples/)). Every section is optional.

## License

[MIT](LICENSE). If it helps you land an interview, a ⭐ helps the next person find it.
