<p align="center">
  <img src="docs/images/banner.svg" alt="easy-ai-resume: YAML typing into a live CV preview, then PDF ready" width="100%">
</p>

<p align="center">
  <a href="https://github.com/whoisadityaj/easy-ai-resume/actions/workflows/ci.yml"><img src="https://github.com/whoisadityaj/easy-ai-resume/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-b3122e" alt="MIT license"></a>
  <img src="https://img.shields.io/badge/AI-Claude%20%7C%20Codex%20%7C%20opencode-5c0a1a" alt="Works with Claude, Codex, opencode or OpenAI">
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
uv tool install "easy-ai-resume[ai] @ https://github.com/whoisadityaj/easy-ai-resume/archive/refs/tags/v0.11.0.zip"
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

This makes `input/` with a sample `cv.yaml`, `cover_letter.yaml` and `job.md`. Replace the sample details with yours:

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

### 3. Make your PDFs

```bash
easy-ai-resume build
```

Your CV and cover letter PDFs are in `output/`, in the default look: `classic`, in red.

### 4. Pick a look and add your photo (optional)

1. **Try a theme.** Each run replaces the PDFs in `output/`, so try as many as you like ([all themes](#-themes)):

   ```bash
   easy-ai-resume build --theme sidebar
   ```

2. **Add your photo.** `sidebar`, `bold` and `executive` show one. The first time you use one of them, `build` asks:

   ```text
   The sidebar theme shows a photo, but cv.yaml and cover_letter.yaml have none yet.
   Drag your photo into this window (or type its path) and press Enter.
   Just press Enter for no photo:
   ```

   Drag your photo file (jpg or png) from Finder or Explorer into the terminal window and press **Enter**.
   It's copied into `input/` and a `photo:` line is added to both YAML files, so it never asks again.
   Pressing Enter alone saves `photo: none` (no photo); change that line later to add one.

3. **Keep the theme.** Add it near the top of **both** `input/cv.yaml` and `input/cover_letter.yaml`,
   so plain `easy-ai-resume build` uses it without `--theme`:

   ```yaml
   theme: sidebar
   # accent: "#0f766e"   # optional: any hex colour instead of the default red
   # page: fit           # a4 (default), letter, fit = one page as tall as your content
   ```

4. **For job portals**, also make a plain version that hiring software reads well ([why](#-ats-mode-for-job-portals)):

   ```bash
   easy-ai-resume build --ats --out output/ats
   ```

### 5. Tailor to a job (optional, uses AI)

Paste the job post into `input/job.md`, then:

```bash
easy-ai-resume tailor input/job.md --build       # add --ats or --theme sidebar for that look
```

**No API key needed if you have an AI subscription.** It uses the first of these that's installed and
logged in, and moves on to the next if one fails:

1. [Claude Code](https://claude.com/claude-code) (`claude`, your Claude subscription)
2. [Codex](https://developers.openai.com/codex/cli) (`codex`, your ChatGPT subscription)
3. [opencode](https://opencode.ai) (`opencode`)
4. An API key, if none of those work: `export ANTHROPIC_API_KEY=your-key` from
   [console.anthropic.com](https://console.anthropic.com) (or `OPENAI_API_KEY` with `--model`). Each run costs a little credit.

Pick one with `--provider claude` (or `codex`, `opencode`, `anthropic`, `openai`). The tool runs in an
empty temporary folder and gets only your CV, letter and the job post (Claude Code with its tools off,
Codex read-only). It counts toward your subscription's usage limits. `build` never uses AI.

```text
my-cv/
├── input/      ← cv.yaml, cover_letter.yaml, job.md, photo (you edit these)
├── output/     ← standard PDFs
└── tailored/   ← one folder per job: tailored YAML + PDFs
```

**More jobs:** one file per job post in `input/`, e.g. `input/acme.md` → `tailored/acme/`.

**How tailoring works, in plain words:**

1. **AI step.** Your `cv.yaml`, `cover_letter.yaml` and the job post are sent to the AI (your subscription tool, or the API).
   It returns a reworded *copy*: the most relevant experience first, bullets that don't fit dropped, the job's
   words used where you really have that experience, and a cover letter written for that company. It is told never
   to add facts. Your files in `input/` are never changed.
2. **Fact check (no AI, plain code).** easy-ai-resume compares the copy with your originals and warns about
   anything new or changed: numbers, dates, employers, job titles, schools, skills in your skills list, projects
   and contact details.
3. **You review.** `tailored/job/changes.diff` lists every change (`-` your original, `+` tailored). Fix anything wrong in the tailored YAML,
   then rebuild with `easy-ai-resume build tailored/job/*.yaml --out tailored/job`.

```text
Check these before sending (possible invented or changed facts):
  - numbers not in your originals (check metrics): 65%
  - skills not in original: rust
```

The fact check can't judge meaning ("helped with" becoming "led"), so always read the diff before sending.

## 🎨 Themes

<p align="center">
  <img src="docs/images/gallery.png" alt="Photo themes (sidebar, bold, executive) on a dark band and clean themes (modern, minimal, classic, compact, ATS mode) on a light band" width="100%">
</p>

Every theme uses the deep red in the pictures (`#9b1b30`) unless you set `accent:` or pass `--accent`.

| Theme | Look | Photo |
|---|---|:---:|
| `sidebar` | Two columns, colour panel with photo and skill chips | ✅ |
| `bold` | Dark header band, accent headings | ✅ |
| `executive` | Refined serif, accent rules | ✅ |
| `modern` | Sans-serif, accent colour | ❌ |
| `minimal` | Light type, labels in the margin | ❌ |
| `classic` (default) | Serif, centred header | ❌ |

No PDF because Pango won't install? `easy-ai-resume build --html-only`, open the HTML file in a browser, **Print → Save as PDF**.

## 🤖 ATS mode (for job portals)

Most job portals run your PDF through an **ATS** (applicant tracking system, like Workday, Greenhouse or Lever).
It pulls the text out of your PDF to fill a form and to search for keywords. Columns, icons and colour panels can
scramble that text. `--ats` (or `ats: true` in the YAML) makes a version that reads cleanly:

- one column, so the text comes out top to bottom in the right order
- standard headings (Skills, Experience, Education, Projects)
- a common font (Arial), black text, no photo, icons or colour panels
- full links (`linkedin.com/in/you`) instead of the word "linkedin"
- real text, not an image (true for every theme)

Use `--ats` when you upload to a portal, and a styled theme when you email a person. ATS mode doesn't add
keywords or give a score: matching the job's wording is what `tailor` does.

**Check it yourself:** open the PDF, select all, copy and paste into a text editor. If it reads in order, an ATS
can read it. Try the same with `sidebar` and you'll see the two columns mixed together.

## ⚙️ Commands and options

| Command | What it does |
|---|---|
| `easy-ai-resume init` | Creates `input/` with sample files to edit. Never overwrites (`--force` resets them). |
| `easy-ai-resume build` | Makes PDFs from `input/cv.yaml` and `input/cover_letter.yaml` in `output/`. |
| `easy-ai-resume build some/file.yaml` | Builds just that file, e.g. a tailored copy you edited. |
| `easy-ai-resume tailor input/acme.md` | Makes an AI-tailored copy for that job in `tailored/acme/`. Add `--build` for the PDFs. |

| Option | Works with | What it does |
|---|---|---|
| `--theme sidebar` | build, tailor | Use this theme for this run |
| `--accent "#0f766e"` | build, tailor | Use this colour for this run (default: red `#9b1b30`) |
| `--ats` | build, tailor | Plain ATS-friendly PDFs |
| `--page-size fit` | build | a4, letter, legal, `fit` (one page exactly as tall as the content), or a CSS size like "210mm 380mm" |
| `--out folder` | build, tailor | Write the files somewhere else |
| `--html-only` / `--html` | build | Write an HTML file instead of / as well as the PDF |
| `--provider claude` | tailor | Use this AI: `claude`, `codex`, `opencode` (subscriptions), `anthropic`, `openai` (API keys). Default: the first that works |
| `--model <name>` | tailor | Model for that AI. Defaults: Claude `opus`, Codex `gpt-5.6-terra`, opencode `opencode-go/deepseek-v4.1-flash` (needed for `openai`) |
| `--effort medium` | tailor | How hard it thinks: low, medium, high, max. Default: medium (opencode: high) |
| `--force` | init, tailor | Overwrite files from an earlier run |
| `--strict` | tailor | Exit with code 2 when the fact check warns (for scripts) |

`easy-ai-resume build --help` and `easy-ai-resume tailor --help` list everything.

- **Other file names:** add `easy-ai-resume.yaml` to `my-cv/`. Every line is optional:

  ```yaml
  cv: input/resume.yaml       # default: input/cv.yaml
  letter: input/letter.yaml   # default: input/cover_letter.yaml
  output: pdfs                # default: output
  tailored: jobs              # default: tailored
  build: true                 # tailor always makes PDFs, no --build needed
  ```

- **GitHub Action:** keep `my-cv/` in a private repo and copy [`examples/github-workflow.yml`](examples/github-workflow.yml)
  to `.github/workflows/cv.yml`. Every push rebuilds your PDFs.
- **All YAML fields:** see the samples `init` creates (also in [examples/](examples/)). Every section is optional.

## License

[MIT](LICENSE). If it helps you land an interview, a ⭐ helps the next person find it.
