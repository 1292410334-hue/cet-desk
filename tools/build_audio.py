# -*- coding: utf-8 -*-
"""生成听力清单 data/audio.js，并可把指定音频抓到本地（压缩成 48k 单声道）。

用法：
  python tools/build_audio.py                 # 只生成清单
  python tools/build_audio.py --fetch 2025.06 # 下载这些考次的音频到 data/audio/
  python tools/build_audio.py --fetch all     # 全抓（约 25 段，压缩后 ~220MB）

说明：本机 raw.githubusercontent 被阻断，所以下载走 api.github.com 的 blob 接口（base64），
再用 ffmpeg 压成 48kbps 单声道 —— 听力人声够用，体积降到约 1/4。
"""
import base64
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
AUDIO = os.path.join(DATA, "audio")
REPO = "0609x/CET46-Resources"
RAW = f"https://raw.githubusercontent.com/{REPO}/main/"
UA = {"User-Agent": "cet-desk-builder"}
FFMPEG = r"C:\Users\lv\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"


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


def load_papers():
    p = os.path.join(DATA, "papers.js")
    s = open(p, encoding="utf-8").read()
    return json.loads(s[s.index("=") + 1:].strip().rstrip(";"))


def build_manifest():
    papers = load_papers()
    os.makedirs(AUDIO, exist_ok=True)
    items = []
    for level in ("cet4", "cet6"):
        for sess in papers["levels"][level]:
            for it in sess["i"]:
                if it["k"] != "听力音频" or it["e"] != "mp3" or it["z"] < 500000:
                    continue
                key = f"{level}_{sess['s'].replace('.', '_')}_{len(items)}"
                local_name = key + ".mp3"
                items.append({
                    "id": key,
                    "level": level,
                    "s": sess["s"],
                    "n": it["n"],
                    "z": it["z"],
                    "u": RAW + it["u"].split("/main/", 1)[1] if "/main/" in it["u"] else "",
                    "path": urllib.parse.unquote(it["u"].split("/main/", 1)[1]) if "/main/" in it["u"] else "",
                    "local": local_name if os.path.exists(os.path.join(AUDIO, local_name)) else "",
                })
    with open(os.path.join(DATA, "audio.js"), "w", encoding="utf-8") as f:
        f.write("window.DATA_AUDIO=" + json.dumps(items, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print("audio items", len(items), "local", sum(1 for i in items if i["local"]),
          "size", round(os.path.getsize(os.path.join(DATA, "audio.js")) / 1024, 1), "KB")
    return items


_SHA = {}


def sha_map():
    if _SHA:
        return _SHA
    tree = api(f"https://api.github.com/repos/{REPO}/git/trees/main?recursive=1")
    for x in tree["tree"]:
        if x["type"] == "blob":
            _SHA[x["path"]] = x["sha"]
    return _SHA


def fetch(items, which):
    """which: 'all' | 考次如 '2025.06' | 前缀 'cet4:2025.06'"""
    os.makedirs(AUDIO, exist_ok=True)
    picks = []
    for it in items:
        if which == "all":
            picks.append(it)
        elif which.startswith("cet4:") or which.startswith("cet6:"):
            if it["id"].startswith(which.replace(":", "_")):
                picks.append(it)
        elif it["s"] == which or which in it["id"]:
            picks.append(it)
    if not picks:
        print("没有匹配的音频：", which)
        return
    for it in picks:
        out = os.path.join(AUDIO, it["id"] + ".mp3")
        if os.path.exists(out):
            print("skip", it["id"])
            continue
        if not it["path"]:
            print("no path", it["id"])
            continue
        print("fetch", it["n"], round(it["z"] / 1048576, 1), "MB")
        sha = sha_map().get(it["path"])
        if not sha:
            print("  no sha")
            continue
        blob = api(f"https://api.github.com/repos/{REPO}/git/blobs/{sha}")
        raw = base64.b64decode(blob["content"]) if blob.get("content") else b""
        if not raw:
            print("  empty blob")
            continue
        tmp = out + ".src"
        with open(tmp, "wb") as f:
            f.write(raw)
        if os.path.exists(FFMPEG):
            subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", tmp,
                            "-ac", "1", "-b:a", "48k", out], check=False)
            os.remove(tmp)
        else:
            os.replace(tmp, out)
        print("  ->", os.path.basename(out), round(os.path.getsize(out) / 1048576, 2), "MB")


if __name__ == "__main__":
    items = build_manifest()
    if "--fetch" in sys.argv:
        fetch(items, sys.argv[sys.argv.index("--fetch") + 1])
        build_manifest()
