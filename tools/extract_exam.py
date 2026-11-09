# -*- coding: utf-8 -*-
"""把本地真题 PDF 拆成可渲染的题目结构，输出 data/exam_*.js。

用法：python tools/extract_exam.py cet6_2026_06_1
      （对应 data/papers_local/cet6/2026.06/cet6_2026_06_1.pdf 与其 _ans.pdf）
"""
import json
import os
import re
import sys

import pymupdf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORE = os.path.join(ROOT, "data", "papers_local")
OUT = os.path.join(ROOT, "data")

def audio_for(level, session):
    """从 data/audio.js 里找同级别同考次的音频：优先本地，其次镜像。"""
    try:
        s = open(os.path.join(OUT, "audio.js"), encoding="utf-8").read()
        items = json.loads(s[s.index("=") + 1:].strip().rstrip(";"))
    except Exception:
        return ""
    best = None
    for it in items:
        if it.get("level") != level or it.get("s") != session:
            continue
        if it.get("local"):
            return "data/audio/" + it["local"]
        if best is None:
            best = it.get("p") or it.get("u") or ""
    return best or ""


TESS = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def ocr_pdf(path, dpi=250):
    """扫描件没有文字层时，逐页渲染再 OCR。"""
    import subprocess, tempfile
    doc = pymupdf.open(path)
    out = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=dpi)
        tmp = os.path.join(tempfile.gettempdir(), f"ocr_{os.getpid()}_{i}.png")
        pix.save(tmp)
        r = subprocess.run([TESS, tmp, "stdout", "-l", "eng", "--psm", "6"],
                           capture_output=True, text=True, encoding="utf-8", errors="ignore")
        out.append(r.stdout or "")
        try:
            os.remove(tmp)
        except OSError:
            pass
        print(f"  ocr page {i+1}/{doc.page_count}", flush=True)
    return "\n".join(out)


def pdf_text(path):
    doc = pymupdf.open(path)
    text = "\n".join(p.get_text() for p in doc)
    if len(text.strip()) < 500:
        print("  扫描件，转 OCR", flush=True)
        text = normalize_ocr(ocr_pdf(path))
    return text


def normalize_ocr(text):
    """OCR 出来的行很乱：把选项和题号强行断行，再交给普通解析。"""
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    text = re.sub(r"[ \t]*([A-D])\)[ \t]*", r"\n\1) ", text)
    text = re.sub(r"(?<![\d.])(\d{1,2})\.[ \t]*", r"\n\1. ", text)
    text = re.sub(r"\n[^\nA-D0-9]*\n", "\n", text)
    return text


def clean_lines(text):
    lines = [l.strip() for l in text.splitlines()]
    # 去掉页码行
    lines = [l for l in lines if l and not re.fullmatch(r"-?\s*\d+\s*-?", l)]
    return lines


def join_wrapped(lines):
    """把被 PDF 折断的英文行接回去：下一行小写开头、且不是选项/题号，就接上。"""
    out = []
    for l in lines:
        if out and re.match(r"^[a-z,;:.)]", l) and not re.match(r"^[A-D]\)", l):
            out[-1] += " " + l
        else:
            out.append(l)
    return out


Q_START = re.compile(r"^(\d{1,2})[.、]\s*(.*)$")
OPT = re.compile(r"^([A-D])[)）]\s*(.*)$")
PART = re.compile(r"^Part\s+(I{1,3}|IV|V)\b[^A-Za-z]*(.*)$")
SECTION = re.compile(r"^Section\s+([A-C])\b(.*)$", re.I)


def paper_no(key):
    m = re.search(r"_(\d)$", key) or re.search(r"第(\d)套", key)
    return m.group(1) if m else "1"


def parse_paper(text):
    lines = join_wrapped(clean_lines(text))
    parts = []
    cur = {"name": "正文", "blocks": []}
    last_q = None
    last_opt = None
    expect = 1

    def flush_part():
        nonlocal cur
        if cur["blocks"]:
            parts.append(cur)
        cur = {"name": "正文", "blocks": []}

    i = 0
    while i < len(lines):
        line = lines[i]
        pm = PART.match(line)
        if pm:
            flush_part()
            name = ("Part " + pm.group(1) + " " + pm.group(2)).strip()
            i += 1
            while i < len(lines) and len(name) < 60 and not lines[i].startswith("Directions"):
                nxt = lines[i]
                if PART.match(nxt) or SECTION.match(nxt) or Q_START.match(nxt):
                    break
                name = (name + " " + nxt).strip()
                i += 1
            cur["name"] = name
            continue
        sm = SECTION.match(line)
        if sm:
            cur["blocks"].append({"t": "h", "x": ("Section " + sm.group(1) + " " + sm.group(2)).strip()})
            last_q = None
            i += 1
            continue
        qm = Q_START.match(line)
        if qm and 1 <= int(qm.group(1)) <= 60 and int(qm.group(1)) == expect:
            q = {"t": "q", "n": int(qm.group(1)), "stem": qm.group(2).strip(), "opts": []}
            cur["blocks"].append(q)
            last_q = q
            last_opt = None
            expect += 1
            i += 1
            # 收集这道题的剩余内容（题干续行 / 选项）
            while i < len(lines):
                nxt = lines[i]
                if Q_START.match(nxt) and int(Q_START.match(nxt).group(1)) == expect:
                    break
                if PART.match(nxt) or SECTION.match(nxt):
                    break
                om = OPT.match(nxt)
                if om and last_q is not None:
                    last_q["opts"].append([om.group(1), om.group(2).strip()])
                    last_opt = len(last_q["opts"]) - 1
                elif last_q["opts"] and last_opt is not None:
                    last_q["opts"][last_opt][1] += " " + nxt
                else:
                    last_q["stem"] += " " + nxt
                i += 1
            continue
        cur["blocks"].append({"t": "p", "x": line})
        i += 1
    flush_part()
    return parts


def parse_answers(text):
    ans, expl = {}, {}
    # 形式一：36. D — 解析
    for line in text.splitlines():
        m = re.match(r"^\s*(\d{1,2})[.、]\s*([A-D])\b(.*)$", line.strip())
        if m:
            n = int(m.group(1))
            ans[n] = m.group(2)
            tail = m.group(3).strip(" —-—:")
            if tail:
                expl[n] = tail
    # 形式二：数字一行、字母一行
    lines = [l.strip() for l in text.splitlines()]
    for i in range(len(lines) - 1):
        a, b = lines[i], lines[i + 1]
        if re.fullmatch(r"\d{1,2}", a) and re.fullmatch(r"[A-D]", b):
            n = int(a)
            if 1 <= n <= 60 and n not in ans:
                ans[n] = b
    return ans, expl


def main():
    key = sys.argv[1] if len(sys.argv) > 1 else "cet6_2026_06_1"
    base = None
    for level_dir in os.listdir(STORE):
        for sess in os.listdir(os.path.join(STORE, level_dir)):
            d = os.path.join(STORE, level_dir, sess)
            if os.path.exists(os.path.join(d, key + ".pdf")):
                base, level, session = d, level_dir, sess
    if not base:
        print("no paper for", key)
        return
    paper = os.path.join(base, key + ".pdf")
    ans_pdf = os.path.join(base, key + "_ans.pdf")
    parts = parse_paper(pdf_text(paper))
    # 同一份 PDF 里可能重复出现整套（卷面 + 另一份），每个 Part 只留第一次
    seen, uniq = set(), []
    for part in parts:
        name = re.sub(r"\s*\(.*?\)\s*$", "", part["name"]).strip()
        if name in seen:
            break
        seen.add(name)
        uniq.append(part)
    parts = uniq
    ans, expl = ({}, {})
    if os.path.exists(ans_pdf):
        ans, expl = parse_answers(pdf_text(ans_pdf))

    nq = sum(1 for p in parts for b in p["blocks"] if b["t"] == "q")
    data = {
        "key": key,
        "title": ("六级" if level == "cet6" else "四级") + " " + session + " 第 " + paper_no(key) + " 套",
        "audio": audio_for(level, session),
        "level": level,
        "session": session,
        "parts": parts,
        "answers": ans,
        "explanations": expl,
    }
    out = os.path.join(OUT, "exam_" + key + ".js")
    with open(out, "w", encoding="utf-8") as f:
        f.write("window.DATA_EXAM=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print("questions", nq, "answers", len(ans), "size", round(os.path.getsize(out) / 1024), "KB")


if __name__ == "__main__":
    main()
