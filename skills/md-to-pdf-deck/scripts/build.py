"""v4: mermaid + alerts + cover slide + pandoc HTML + WeasyPrint PDF.

Supports two slide-break strategies:
  --break h2 (default, legacy): every ## = new slide
  --break h1: every # = new slide; ## becomes in-slide section header

Use h1 mode for source docs structured as chapters (# Chapter) with
sub-sections (## Sub). Produces denser slides.
"""
import argparse
import re
import subprocess
import pathlib
import hashlib

parser = argparse.ArgumentParser(description="Markdown → presentation PDF")
parser.add_argument("src", help="source markdown")
parser.add_argument("out", help="output pdf path")
parser.add_argument("title", nargs="?", default="Deck", help="cover title")
parser.add_argument("tagline", nargs="?", default="", help="cover tagline (italic)")
parser.add_argument("author", nargs="?", default="", help="cover author/date byline")
parser.add_argument(
    "--break", dest="break_level", choices=["h1", "h2"], default="h2",
    help="slide-break level: h2 = every ## (default), h1 = every # (denser slides)",
)
args = parser.parse_args()

src_path = pathlib.Path(args.src)
out_pdf = pathlib.Path(args.out)
title = args.title
tagline = args.tagline
author = args.author
break_level = args.break_level

src = src_path.read_text()
work = pathlib.Path(".")
mermaid_idx = 0


def render_mermaid(code: str) -> str:
    global mermaid_idx
    mermaid_idx += 1
    h = hashlib.md5(code.encode()).hexdigest()[:8]
    mmd = work / f"m_{mermaid_idx}_{h}.mmd"
    svg = work / f"m_{mermaid_idx}_{h}.svg"
    mmd.write_text(code)
    subprocess.run(
        ["mmdc", "-i", str(mmd), "-o", str(svg),
         "-t", "dark", "-b", "#0d1117",
         "-c", "mermaid-config.json",
         "-p", "puppeteer-config.json",
         "-w", "1400"],
        check=True, capture_output=True,
    )
    return f'\n<p class="mermaid-wrap"><img src="./{svg.name}" alt="diagram"></p>\n'


src = re.sub(r"```mermaid\n(.*?)\n```", lambda m: render_mermaid(m.group(1)), src, flags=re.DOTALL)


def gh_alert(match):
    kind = match.group(1).lower()
    body = match.group(2)
    cleaned = re.sub(r"^> ?", "", body, flags=re.MULTILINE).rstrip()
    icons = {"note": "📝", "tip": "💡", "important": "❗", "warning": "⚠️", "caution": "🚨"}
    label = {"note": "NOTE", "tip": "TIP", "important": "IMPORTANT", "warning": "WARNING", "caution": "CAUTION"}
    return (
        f'\n<div class="gh-alert gh-alert-{kind}">\n'
        f'<div class="gh-alert-title">{icons.get(kind,"")} {label.get(kind,kind.upper())}</div>\n\n'
        f'{cleaned}\n\n'
        f'</div>\n'
    )


src = re.sub(
    r"^> \[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\n((?:> .*(?:\n|$))+)",
    gh_alert, src, flags=re.MULTILINE,
)

# Strip double HRs
src = re.sub(r"^---\n---\s*$", "---", src, flags=re.MULTILINE)

# Extract cover content: everything from start up to (but not including) the first ## heading
# (or first # heading in h1-break mode, since H1s become slide boundaries)
first_slide_pat = r"^# " if break_level == "h1" else r"^## "
# In h1 mode the cover # must be skipped — take the SECOND # as the slide boundary
if break_level == "h1":
    # First # is the cover title, we want the next # after it
    matches = list(re.finditer(r"^# ", src, re.MULTILINE))
    cover_match = matches[1] if len(matches) >= 2 else None
else:
    cover_match = re.search(first_slide_pat, src, re.MULTILINE)

if cover_match:
    cover_src = src[:cover_match.start()]
    rest_src = src[cover_match.start():]
else:
    cover_src = src
    rest_src = ""

# Extract title (# heading) and subtitle (### heading) from cover
h1_match = re.search(r"^# (.+)$", cover_src, re.MULTILINE)
h3_match = re.search(r"^### (.+)$", cover_src, re.MULTILINE)
cover_title = h1_match.group(1).strip() if h1_match else title
cover_subtitle = h3_match.group(1).strip() if h3_match else ""

# Build cover HTML (use <p> so text-align: center centers the text properly)
cover_html = f"""
<div class="cover">
<h1>{cover_title}</h1>
<p class="subtitle">{cover_subtitle}</p>
"""
if tagline:
    cover_html += f'<p class="tagline">{tagline}</p>\n'
if author:
    cover_html += f'<p class="author">{author}</p>\n'
cover_html += "</div>\n\n"

# Replace cover with our structured HTML, then strip leading --- from rest
rest_src = re.sub(r"^---\s*\n", "", rest_src, count=1, flags=re.MULTILINE)
final = cover_html + rest_src

proc = work / "processed.md"
proc.write_text(final)
print(f"✓ {mermaid_idx} mermaid diagrams, cover wrapped, break-level={break_level}")

# Write override CSS for h1-break mode (empty in h2 mode)
if break_level == "h1":
    override_css = """
/* --break h1 mode: # becomes slide boundary, ## stays in-flow */
h2 { page-break-before: auto !important; }
h1 { page-break-before: always !important; font-size: 28pt; border-bottom: 2pt solid #21262d; padding-bottom: 10pt; margin: 0 0 14pt; }
.cover h1 { page-break-before: avoid !important; font-size: 46pt; border: none; padding: 0; margin: 0 0 18pt; }
h2 { font-size: 17pt; color: #79c0ff; border: none; padding: 0; margin: 12pt 0 6pt; font-weight: 600; }
"""
else:
    override_css = ""

(work / "override.css").write_text(override_css)

subprocess.run([
    "pandoc", str(proc),
    "-f", "markdown+raw_html+pipe_tables+fenced_code_blocks+task_lists+auto_identifiers",
    "-t", "html5",
    "-o", "out.html",
    "--standalone",
    "--metadata", f"title={title}",
    "-H", "head.html",
], check=True)
print("✓ HTML generated")

subprocess.run(["weasyprint", "out.html", str(out_pdf)], check=True)
print(f"✓ PDF → {out_pdf}")
