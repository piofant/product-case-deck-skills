---
name: md-to-pdf-deck
description: Convert a markdown file into a polished, presentation-style PDF with dark GitHub theme, centered cover slide, one-slide-per-H2 layout, real dialog blockquotes, and rendered mermaid diagrams. Use when the user asks to export a weekly sync, product update, deck, or documentation as a PDF and wants it to feel like a presentation — not a flowing document. Built for weekly syncs, board updates, product case studies, and technical documentation that needs print-ready polish.
---

# Markdown → Presentation PDF

Pipeline: **Markdown → (pre-rendered mermaid SVG + GitHub alerts + cover block) → pandoc HTML → WeasyPrint PDF**.

Produces A4 landscape PDF with:
- Centered cover slide (title / subtitle / tagline / author)
- One slide per `## H2` (via `page-break-before: always`)
- Dark GitHub palette (`#0d1117` background, `#58a6ff` headings)
- Colored emoji via Noto Color Emoji
- Dialog blockquotes with blue left-border + golden italics for quoted speech
- GitHub alerts (`> [!NOTE]`, `> [!WARNING]`, etc.) as colored callouts
- Mermaid diagrams pre-rendered to SVG with node labels intact
- Tables with striped rows, code blocks with JetBrains Mono

## When to use

- User asks to "export as PDF" a markdown weekly sync, update, deck, case study, or glossary
- User says "make it look like a preza" or "нормальный PDF"
- User wants to share a GitHub markdown document externally where readers may not know GitHub

**Do NOT use for:** short notes, single-page readmes, or documents that have no section structure (no `##` headings). For those, GitHub's native markdown view is better.

## When NOT to use

- User wants a truly interactive slide deck (use reveal-md or marp instead)
- Document has heavy client-side interactivity assumptions
- User needs pixel-perfect corporate branding (commission a designer)

## The pipeline — why these choices

| Choice | Reason |
|--------|--------|
| **WeasyPrint, not Chrome headless** | Chrome injects print headers (`date, file://...`, page numbers) that are hard to disable reliably. WeasyPrint is silent. |
| **pandoc HTML, not direct markdown** | pandoc handles pipe tables, task lists, fenced code, and auto-IDs consistently. |
| **Mermaid pre-rendered to SVG via mmdc** | Neither pandoc nor WeasyPrint render mermaid. Pre-render to SVG and embed as `<img>`. Set `htmlLabels: false` or WeasyPrint can't render node labels (it doesn't support `<foreignObject>`). |
| **Emoji font scoped OUT of body stack** | Noto Color Emoji has keycap glyphs (`0️⃣ 1️⃣`) that hijack digit fallback in WeasyPrint — "2026" renders as "2 0 2 6". Keep emoji font resolved only via system fontconfig for emoji codepoints, not via CSS body stack. |
| **Pandoc default body CSS overridden** | Pandoc adds `body { max-width: 36em }` which squashes content into a narrow column. Must override with `!important`. |
| **Cover slide built from script, not markdown** | The first `# H1 + ### H3` block gets wrapped in `<div class="cover">` with subtitle/tagline/author classes. Lets us keep the markdown source clean. |

## Quick start

```bash
cd /path/to/skill/scripts
cp /path/to/your-doc.md source.md

python3 build.py source.md output.pdf "Title" "Subtitle or tagline" "Author · Date"
```

Example:

```bash
python3 build.py deck.md weekly-sync.pdf \
  "Lumen Weekly Sync" \
  "Что неделя значит для продукта" \
  "Вова · 2026-04-23"
```

Outputs `weekly-sync.pdf` (A4 landscape, dark theme, one slide per H2).

## Install dependencies

Linux (Debian/Ubuntu):

```bash
apt install -y pandoc weasyprint imagemagick \
  fonts-inter fonts-noto-color-emoji fonts-noto fonts-noto-cjk

npm install -g @mermaid-js/mermaid-cli
```

macOS:

```bash
brew install pandoc weasyprint imagemagick
brew tap homebrew/cask-fonts
brew install --cask font-inter
npm install -g @mermaid-js/mermaid-cli
```

Running as root? Mermaid CLI (Puppeteer) needs sandbox disabled — `puppeteer-config.json` in `scripts/` handles that.

## Expected markdown structure

```markdown
<div align="center">

# 🌙 Title With Emoji

### Subtitle or date range

</div>

---

## First slide heading

Content for slide 1…

> 👤 *«user message»*
> 🌙 *«bot response»*

> [!IMPORTANT]
> callout block

---

## Second slide heading

| col | col |
|-----|-----|
| ... | ... |

` ``mermaid
flowchart LR
    A --> B
` ``
```

Every `## H2` becomes a new page. Every `---` between sections is harmless (they're hidden via CSS — page breaks do the work). The first block up to the first `## H2` becomes the cover.

## Script arguments

```
python3 build.py <source.md> <output.pdf> <title> [tagline] [author]
```

- `source.md` — input markdown (required)
- `output.pdf` — output PDF path (required)
- `title` — slide title shown as giant H1 on cover (required)
- `tagline` — italic line below subtitle (optional)
- `author` — small byline at bottom of cover (optional)

The subtitle under the title is auto-extracted from the first `### ` heading in the source.

## Variants

- **Landscape preza** (default): A4 landscape, big fonts, one-slide-per-H2 — for syncs, pitches, demos
- **Portrait doc** (future): A4 portrait, smaller fonts, no forced page breaks — for long reference docs like glossaries. Currently same CSS works OK for portrait too with minor tweaks.

## Known rough edges

- WeasyPrint has limited flexbox support — use block layout for covers
- WeasyPrint doesn't support `@font-face unicode-range` — scope emoji via font-stack order, not `@font-face`
- Mermaid CLI requires Puppeteer, which requires Chromium — heavy dep for a side utility
- Long tables that don't fit on one page will split awkwardly; add `break-inside: avoid` selectively if needed

## Files in this skill

- `scripts/build.py` — the pipeline
- `scripts/preza.css` — dark landscape theme
- `scripts/mermaid-config.json` — mermaid dark theme (with `htmlLabels: false`!)
- `scripts/puppeteer-config.json` — `--no-sandbox` for root
- `scripts/head.html` — pandoc `<head>` injection for CSS linking
- `references/example-weekly-sync.md` — minimal working example
- `assets/preview-cover.png` — sample output
