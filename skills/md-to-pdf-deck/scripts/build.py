"""v3: mermaid + alerts + cover slide + pandoc HTML + WeasyPrint PDF."""
import re
import subprocess
import pathlib
import sys
import hashlib

src_path = pathlib.Path(sys.argv[1])
out_pdf = pathlib.Path(sys.argv[2])
title = sys.argv[3] if len(sys.argv) > 3 else "Lumen Deck"
tagline = sys.argv[4] if len(sys.argv) > 4 else ""
author = sys.argv[5] if len(sys.argv) > 5 else ""

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
cover_match = re.search(r"^## ", src, re.MULTILINE)
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
print(f"✓ {mermaid_idx} mermaid diagrams, cover wrapped")

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
