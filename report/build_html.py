"""Render report/phase1a_report.md to a single self-contained HTML file with
figures embedded as base64 (opens in any browser, no external files needed)."""
import base64
import re
from pathlib import Path

import markdown

ROOT = Path("/Users/joyce/Developer/gsbgen390/report")
MD = ROOT / "phase1a_report.md"
HTML = ROOT / "phase1a_report.html"

text = MD.read_text()

# inline figures as base64 data URIs
def embed(m):
    alt, src = m.group(1), m.group(2)
    p = ROOT / src
    if not p.exists():
        return m.group(0)
    b64 = base64.b64encode(p.read_bytes()).decode()
    return f'![{alt}](data:image/png;base64,{b64})'

text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', embed, text)

body = markdown.markdown(text, extensions=["tables", "attr_list", "sane_lists", "smarty"])

CSS = """
:root { --ink:#1a1a1a; --muted:#5f6b76; --line:#e2e6ea; --accent:#2f6f9f; --bg:#ffffff; }
* { box-sizing: border-box; }
body { font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; color: var(--ink);
       line-height: 1.62; max-width: 860px; margin: 0 auto; padding: 56px 28px 120px;
       background: var(--bg); font-size: 16px; -webkit-font-smoothing: antialiased; }
h1 { font-size: 30px; line-height: 1.22; margin: 0 0 6px; letter-spacing: -0.01em; }
h2 { font-size: 22px; margin: 46px 0 14px; padding-bottom: 7px; border-bottom: 2px solid var(--line); letter-spacing: -0.01em; }
h3 { font-size: 17.5px; margin: 30px 0 10px; color: #2a2a2a; }
p { margin: 13px 0; }
strong { font-weight: 650; }
a { color: var(--accent); text-decoration: none; }
hr { border: none; border-top: 1px solid var(--line); margin: 30px 0; }
blockquote { margin: 20px 0; padding: 14px 20px; background: #f4f8fb;
             border-left: 4px solid var(--accent); border-radius: 0 6px 6px 0; }
blockquote p { margin: 4px 0; }
img { display: block; max-width: 100%; height: auto; margin: 22px auto; border: 1px solid var(--line); border-radius: 6px; }
table { border-collapse: collapse; width: 100%; margin: 20px 0; font-size: 13.5px; }
th, td { border: 1px solid var(--line); padding: 7px 10px; text-align: right; }
th { background: #f0f4f7; font-weight: 600; text-align: right; }
td:first-child, th:first-child { text-align: left; }
table tr:nth-child(even) td { background: #fafbfc; }
code { background: #f0f2f4; padding: 1.5px 5px; border-radius: 4px; font-size: 13px;
       font-family: "SF Mono", Menlo, monospace; }
ol, ul { margin: 13px 0; padding-left: 26px; }
li { margin: 7px 0; }
em { color: inherit; }
/* lead block: author + dates under the title */
h1 + p { color: var(--muted); font-size: 14px; margin-top: 0; }
"""

out = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Phase 1A Results — GSS Attitude Simulation</title>
<style>{CSS}</style></head>
<body>
{body}
</body></html>"""

HTML.write_text(out)
print(f"wrote {HTML}  ({len(out)//1024} KB, figures embedded)")
