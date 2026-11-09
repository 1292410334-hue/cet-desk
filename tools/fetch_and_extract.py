# -*- coding: utf-8 -*-
"""把需要的真题 PDF 通过 gh-proxy 抓到本地，然后逐套抽成题目。

用法：python tools/fetch_and_extract.py 2025.06 2024.12
"""
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
STORE = os.path.join(DATA, "papers_local")
CURL = "curl.exe"


def load(name):
    s = open(os.path.join(DATA, name + ".js"), encoding="utf-8").read()
    return json.loads(s[s.index("=") + 1:].strip().rstrip(";"))


def raw_from(u):
    return u.replace("https://github.com/", "https://raw.githubusercontent.com/").replace("/blob/", "/")


def main():
    sessions = set(sys.argv[1:])
    papers = load("papers")
    got = []
    for level, sess_list in papers["levels"].items():
        for se in sess_list:
            if sessions and se["s"] not in sessions:
                continue
            for it in se["i"]:
                if it["k"] != "真题PDF":
                    continue
                out_dir = os.path.join(STORE, level, se["s"])
                os.makedirs(out_dir, exist_ok=True)
                out = os.path.join(out_dir, it["n"])
                if os.path.exists(out) and os.path.getsize(out) > 50000:
                    got.append((level, se["s"], it["n"]))
                    continue
                url = "https://gh-proxy.com/" + raw_from(it["u"])
                t0 = time.time()
                r = subprocess.run([CURL, "-sSL", "--fail", "--retry", "4", "--retry-all-errors",
                                    "--connect-timeout", "20", "--max-time", "600", "-o", out, url],
                                   capture_output=True, text=True)
                ok = os.path.exists(out) and os.path.getsize(out) > 50000
                print(f"{level} {se['s']} {it['n']} {os.path.getsize(out)//1024 if ok else 0}KB {time.time()-t0:.0f}s rc={r.returncode}", flush=True)
                if ok:
                    got.append((level, se["s"], it["n"]))
    print("downloaded", len(got))


if __name__ == "__main__":
    main()
