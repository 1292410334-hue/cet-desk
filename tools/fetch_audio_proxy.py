# -*- coding: utf-8 -*-
"""用 gh-proxy 镜像把听力抓到本地（比 api blob 快，且是普通 HTTP 下载）。

跑完会把 data/audio.js 里对应条目的 local 字段补上，页面自动标「本地」。
"""
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO = os.path.join(ROOT, "data", "audio")
TMP = os.path.join(ROOT, "tools", ".audio_tmp")
FF = r"C:\Users\lv\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"
CURL = "curl.exe"


def log(*a):
    print(*a, flush=True)


def main():
    only = set(sys.argv[1:])
    p = os.path.join(ROOT, "data", "audio.js")
    s = open(p, encoding="utf-8").read()
    items = json.loads(s[s.index("=") + 1:].strip().rstrip(";"))
    os.makedirs(AUDIO, exist_ok=True)
    os.makedirs(TMP, exist_ok=True)

    for it in items:
        if only and it["id"] not in only:
            continue
        out = os.path.join(AUDIO, it["id"] + ".mp3")
        if os.path.exists(out) and os.path.getsize(out) > 300000:
            it["local"] = it["id"] + ".mp3"
            log("have", it["id"])
            continue
        url = it.get("p") or it.get("u")
        if not url:
            continue
        raw = os.path.join(TMP, it["id"] + ".src")
        t0 = time.time()
        r = subprocess.run([CURL, "-sSL", "--fail", "--retry", "4", "--retry-all-errors",
                            "--retry-delay", "3", "--connect-timeout", "20", "--max-time", "900",
                            "-o", raw, url], capture_output=True, text=True)
        size = os.path.getsize(raw) if os.path.exists(raw) else 0
        log(f"{it['id']} {size/1048576:.1f}MB {time.time()-t0:.0f}s rc={r.returncode}")
        if size < 100000:
            continue
        subprocess.run([FF, "-y", "-loglevel", "error", "-i", raw, "-ac", "1", "-ar", "24000",
                        "-b:a", "40k", out], check=False)
        os.remove(raw)
        if os.path.exists(out):
            it["local"] = it["id"] + ".mp3"
            log("   ->", round(os.path.getsize(out) / 1048576, 2), "MB")
            # 每抓完一条就落盘，中途停也不丢
            open(p, "w", encoding="utf-8").write(
                "window.DATA_AUDIO=" + json.dumps(items, ensure_ascii=False, separators=(",", ":")) + ";\n")
    open(p, "w", encoding="utf-8").write(
        "window.DATA_AUDIO=" + json.dumps(items, ensure_ascii=False, separators=(",", ":")) + ";\n")
    log("done", sum(1 for i in items if i.get("local")), "local")


if __name__ == "__main__":
    main()
