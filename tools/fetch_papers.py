# -*- coding: utf-8 -*-
"""把指定考次的真题/解析下到本地，并给 papers.js 打上本地路径。

本机 raw.githubusercontent 不通，所以走 api.github.com 的 blob 接口（base64）。

用法：
  python tools/fetch_papers.py --session 2026.06
  python tools/fetch_papers.py --level cet6 --from 2024 --kinds 答案解析
  python tools/fetch_papers.py --session 2026.06 --kinds 真题PDF --audio
"""
import argparse
import base64
import json
import os
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
STORE = os.path.join(DATA, "papers_local")
REPO = "0609x/CET46-Resources"
UA = {"User-Agent": "cet-desk-builder"}
_SHA = {}


def api(url, tries=4):
    req = urllib.request.Request(url, headers=UA)
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(3 + i * 4)
    raise RuntimeError(f"{url[:90]} {last}")


def sha_map():
    if _SHA:
        return _SHA
    tree = api(f"https://api.github.com/repos/{REPO}/git/trees/main?recursive=1")
    for x in tree["tree"]:
        if x["type"] == "blob":
            _SHA[x["path"]] = x["sha"]
    return _SHA


def load_papers():
    p = os.path.join(DATA, "papers.js")
    s = open(p, encoding="utf-8").read()
    return json.loads(s[s.index("=") + 1:].strip().rstrip(";"))


def rel_path(level, session, name):
    return f"papers_local/{level}/{session}/{name}"


def download(item, level, session):
    path = urllib.parse.unquote(item["u"].split("/main/", 1)[1])
    out = os.path.join(STORE, level, session, item["n"])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if os.path.exists(out) and os.path.getsize(out) > 1000:
        print("  skip", item["n"])
        return True
    sha = sha_map().get(path)
    if not sha:
        print("  no sha", path)
        return False
    print("  get", item["n"], round(item["z"] / 1024), "KB")
    blob = api(f"https://api.github.com/repos/{REPO}/git/blobs/{sha}")
    raw = base64.b64decode(blob["content"]) if blob.get("content") else b""
    if not raw:
        print("  empty")
        return False
    with open(out, "wb") as f:
        f.write(raw)
    return True


def mark_local(papers):
    for level, sessions in papers["levels"].items():
        for s in sessions:
            for it in s["i"]:
                p = os.path.join(DATA, rel_path(level, s["s"], it["n"]))
                if os.path.exists(p):
                    it["l"] = rel_path(level, s["s"], it["n"])
                else:
                    it.pop("l", None)
    with open(os.path.join(DATA, "papers.js"), "w", encoding="utf-8") as f:
        f.write("window.DATA_PAPERS=" + json.dumps(papers, ensure_ascii=False, separators=(",", ":")) + ";\n")
    n = sum(1 for lv in papers["levels"].values() for s in lv for i in s["i"] if i.get("l"))
    print("local files:", n)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", default="")
    ap.add_argument("--level", default="all", choices=["all", "cet4", "cet6"])
    ap.add_argument("--from", dest="from_year", default="")
    ap.add_argument("--kinds", default="真题PDF,答案解析")
    ap.add_argument("--audio", action="store_true")
    a = ap.parse_args()

    kinds = [k.strip() for k in a.kinds.split(",") if k.strip()]
    if a.audio and "听力音频" not in kinds:
        kinds.append("听力音频")

    papers = load_papers()
    for level, sessions in papers["levels"].items():
        if a.level != "all" and level != a.level:
            continue
        for s in sessions:
            if a.session and s["s"] != a.session:
                continue
            if a.from_year and s["s"] < a.from_year:
                continue
            todo = [i for i in s["i"] if i["k"] in kinds]
            if not todo:
                continue
            print(level, s["s"], len(todo), "files")
            for it in todo:
                download(it, level, s["s"])
    mark_local(papers)
