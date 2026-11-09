# -*- coding: utf-8 -*-
"""从中文解析 PDF 里抽答案：解析是「……所以答案是 C 项」这种写法，没有答案表。
按题号切块，每块找第一处「答案是X / 选项X为正确答案」，OCR 用 chi_sim+eng。"""
import json
import os
import re
import subprocess
import sys
import tempfile

import pymupdf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
TESS = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def ocr_pdf(path, dpi=200):
    doc = pymupdf.open(path)
    out = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=dpi)
        tmp = os.path.join(tempfile.gettempdir(), f"ans_{os.getpid()}_{i}.png")
        pix.save(tmp)
        r = subprocess.run([TESS, tmp, "stdout", "-l", "chi_sim+eng", "--psm", "6"],
                           capture_output=True, text=True, encoding="utf-8", errors="ignore")
        out.append(r.stdout or "")
        os.remove(tmp)
        print(f"  ocr {i+1}/{doc.page_count}", flush=True)
    return "\n".join(out)


def extract(text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    # 题号切块：单独一行的数字，或行首「12.」
    blocks = {}
    cur = None
    for l in lines:
        m = re.fullmatch(r"(\d{1,2})[.、]?", l) or re.match(r"^(\d{1,2})[.、]\s", l)
        if m and 1 <= int(m.group(1)) <= 56:
            cur = int(m.group(1))
            blocks.setdefault(cur, [])
            if not re.fullmatch(r"(\d{1,2})[.、]?", l):
                blocks[cur].append(l)
            continue
        if cur is not None:
            blocks[cur].append(l)
    ans = {}
    for n, ls in blocks.items():
        joined = " ".join(ls)
        m = re.search(r"答案[是为:：]?\s*([A-D])\s*[项]?", joined) or re.search(r"选项\s*([A-D])\s*为正确答案", joined)
        if m:
            ans[n] = m.group(1)
    return ans


def main():
    key = sys.argv[1]
    path = sys.argv[2]
    print("OCR", os.path.basename(path), flush=True)
    text = ocr_pdf(path)
    ans = extract(text)
    print("answers", len(ans), sorted(ans.items())[:10], flush=True)
    p = os.path.join(DATA, f"exam_{key}.js")
    s = open(p, encoding="utf-8").read()
    d = json.loads(s[s.index("=") + 1:].strip().rstrip(";"))
    d["answers"] = {str(k): v for k, v in sorted(ans.items())}
    open(p, "w", encoding="utf-8").write("window.DATA_EXAM=" + json.dumps(d, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print("written", p)


if __name__ == "__main__":
    main()
