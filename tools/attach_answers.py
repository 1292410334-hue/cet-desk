# -*- coding: utf-8 -*-
"""给已经拆好的卷子补答案：能下到的解析 PDF 下载后解析，扫描件走 OCR。

用法：python tools/attach_answers.py
"""
import json
import os
import re
import subprocess
import sys

import pymupdf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
STORE = os.path.join(DATA, "papers_local")
TESS = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def load_manifest():
    s = open(os.path.join(DATA, "papers.js"), encoding="utf-8").read()
    return json.loads(s[s.index("=") + 1:].strip().rstrip(";"))


def pdf_text(path):
    doc = pymupdf.open(path)
    text = "\n".join(p.get_text() for p in doc)
    if len(text.strip()) > 400:
        return text
    out = []
    print("    OCR", os.path.basename(path), doc.page_count, "页", flush=True)
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=200)
        tmp = os.path.join(os.environ.get("TEMP", "."), f"ans_{os.getpid()}_{i}.png")
        pix.save(tmp)
        r = subprocess.run([TESS, tmp, "stdout", "-l", "eng", "--psm", "6"],
                           capture_output=True, text=True, encoding="utf-8", errors="ignore")
        out.append(r.stdout or "")
        os.remove(tmp)
    return "\n".join(out)


def parse_answers(text):
    """三种格式：36. D — 解析 / 数字一行字母一行 / 表格 1-5 C A B D B。"""
    ans = {}
    # 1) 逐题：1. C  或  1 C
    for m in re.finditer(r"(?m)^\s*(\d{1,2})\s*[.、)]?\s*([A-D])\b", text):
        n = int(m.group(1))
        if 1 <= n <= 60:
            ans.setdefault(n, m.group(2))
    # 2) 数字、字母分两行
    lines = [l.strip() for l in text.splitlines()]
    for i in range(len(lines) - 1):
        if re.fullmatch(r"\d{1,2}", lines[i]) and re.fullmatch(r"[A-D]", lines[i + 1]):
            n = int(lines[i])
            if 1 <= n <= 60:
                ans.setdefault(n, lines[i + 1])
    # 3) 区间表格：1-5 C A B D B
    for m in re.finditer(r"(\d{1,2})\s*[-–~]\s*(\d{1,2})\s*((?:[A-D]\s*){3,10})", text):
        a, b, body = int(m.group(1)), int(m.group(2)), m.group(3)
        letters = re.findall(r"[A-D]", body)
        for k, ch in enumerate(letters):
            n = a + k
            if n <= b:
                ans.setdefault(n, ch)
    return ans


def main():
    man = load_manifest()
    files = {}
    for lv in ("cet4", "cet6"):
        for se in man["levels"][lv]:
            for it in se["i"]:
                if it["k"] == "答案解析":
                    files[(lv, se["s"], it["n"])] = it
    # 找每个已拆卷子对应的解析
    done = []
    for f in sorted(os.listdir(DATA)):
        if not (f.startswith("exam_") and f.endswith(".js")):
            continue
        key = f[5:-3]
        if key == "mock":
            continue
        p = os.path.join(DATA, f)
        s = open(p, encoding="utf-8").read()
        d = json.loads(s[s.index("=") + 1:].strip().rstrip(";"))
        lv, sess = d["level"], d["session"]
        cand = [n for (l, ss, n) in files if l == lv and ss == sess]
        if not cand:
            continue
        # 优先同名 _ans，其次本套关键词，最后取第一个
        pick = next((n for n in cand if n.startswith(key)), None) \
            or next((n for n in cand if str(key).split("_")[-1] in n), None) \
            or cand[0]
        it = files[(lv, sess, pick)]
        local = it.get("l")
        path = os.path.join(DATA, local) if local else None
        if not path or not os.path.exists(path):
            url = it["u"].replace("https://github.com/", "https://raw.githubusercontent.com/").replace("/blob/", "/")
            os.makedirs(os.path.join(STORE, lv, sess), exist_ok=True)
            path = os.path.join(STORE, lv, sess, pick)
            print("下载", pick, round(it["z"] / 1048576, 1), "MB", flush=True)
            subprocess.run(["curl.exe", "-sSL", "--fail", "--retry", "3", "--retry-all-errors",
                            "--max-time", "900", "-o", path, "https://gh-proxy.com/" + url])
        if not path.lower().endswith(".pdf"):
            continue
        print("解析", key, "<-", pick, flush=True)
        ans = parse_answers(pdf_text(path))
        if not ans:
            print("   没抽到答案")
            continue
        d["answers"] = {str(k): v for k, v in sorted(ans.items())}
        open(p, "w", encoding="utf-8").write(
            "window.DATA_EXAM=" + json.dumps(d, ensure_ascii=False, separators=(",", ":")) + ";\n")
        done.append((key, len(ans)))
        print("   答案", len(ans), "条")
        # 抓完就删，别把几百兆留在包里
        if os.path.getsize(path) > 8 * 1048576:
            os.remove(path)
    print("done", done)


if __name__ == "__main__":
    main()
