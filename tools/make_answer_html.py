# -*- coding: utf-8 -*-
"""把 papers_local 里的 .md 参考答案转成能直接读的 .html（纸面样式，自带样式表）。"""
import glob
import html
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORE = os.path.join(ROOT, "data", "papers_local")

CSS = """
:root{--paper:#F7F2E6;--ink:#1E1B16;--ink2:#575044;--ink3:#8B8272;--red:#A33A2C;--line:rgba(30,27,22,.18)}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:"Songti SC","STSong",SimSun,serif;font-size:15.5px;line-height:1.9;padding:48px 32px 72px}
.doc{max-width:760px;margin:0 auto}
h1{font-size:27px;line-height:1.4;margin:0 0 18px;font-weight:600;letter-spacing:.01em}
h2{font-size:20px;margin:38px 0 10px;font-weight:600;border-left:3px solid var(--red);padding-left:10px}
h3{font-size:16.5px;margin:26px 0 8px;font-weight:600;color:var(--ink2)}
p{margin:10px 0}
blockquote{margin:16px 0;padding:10px 14px;border-left:2px solid rgba(163,58,44,.35);color:var(--ink2);font-size:14px;background:rgba(163,58,44,.035)}
table{border-collapse:collapse;width:100%;margin:14px 0 20px;font-size:13.5px}
th,td{border:1px solid var(--line);padding:6px 9px;text-align:left;vertical-align:top}
th{background:rgba(30,27,22,.05);font-weight:600;font-family:"PingFang SC",sans-serif;font-size:12.5px;letter-spacing:.04em}
a{color:var(--ink2)}
strong{font-weight:600}
hr{border:0;border-top:1px solid var(--line);margin:28px 0}
code{font-family:Consolas,monospace;font-size:13px;background:rgba(30,27,22,.06);padding:1px 4px}
.foot{margin-top:44px;padding-top:14px;border-top:1px solid var(--line);font-size:12px;color:var(--ink3);font-family:"Kaiti SC",KaiTi,serif}
"""


def inline(t):
    t = html.escape(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', t)
    return t


def convert(md):
    out = []
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            i += 1
            continue
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not re.match(r"^[\s\-:|]+$", lines[i]):
                    rows.append(cells)
                i += 1
            if rows:
                head = rows[0]
                body = rows[1:]
                out.append("<table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in head) +
                           "</tr></thead><tbody>" +
                           "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in body) +
                           "</tbody></table>")
            continue
        if line.startswith("#"):
            lvl = len(line) - len(line.lstrip("#"))
            text = line[lvl:].strip()
            out.append(f"<h{min(lvl,3)}>{inline(text)}</h{min(lvl,3)}>")
            i += 1
            continue
        if line.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i].lstrip("> ").rstrip())
                i += 1
            out.append("<blockquote>" + inline(" ".join(buf)) + "</blockquote>")
            continue
        if line.strip() in ("---", "***"):
            out.append("<hr>")
            i += 1
            continue
        buf = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not lines[i].startswith(("#", "|", ">", "-", "*")):
            buf.append(lines[i].rstrip())
            i += 1
        out.append("<p>" + inline(" ".join(buf)) + "</p>")
    return "\n".join(out)


def main():
    for md_path in glob.glob(os.path.join(STORE, "**", "*.md"), recursive=True):
        md = open(md_path, encoding="utf-8").read()
        title = re.sub(r"^#\s*", "", md.splitlines()[0]) if md.startswith("#") else os.path.basename(md_path)
        body = convert(md)
        page = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title>
<style>{CSS}</style></head><body><div class="doc">{body}
<p class="foot">来源：0609x/CET46-Resources · 仅限个人学习</p></div></body></html>"""
        out = os.path.splitext(md_path)[0] + ".html"
        open(out, "w", encoding="utf-8").write(page)
        print("wrote", os.path.relpath(out, ROOT), round(os.path.getsize(out) / 1024), "KB")


if __name__ == "__main__":
    main()
