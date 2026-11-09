# -*- coding: utf-8 -*-
"""分块下载听力（gh-proxy 镜像 + Range），每块单独重试，慢但不卡死。

用法：python tools/fetch_audio_chunks.py [id ...]
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
CHUNK = 1 << 20


def log(*a):
    print(*a, flush=True)


def fetch_range(url, start, end, out, tries=8):
    for i in range(tries):
        r = subprocess.run([CURL, "-sS", "-L", "--fail", "--connect-timeout", "20", "--max-time", "240",
                            "-r", f"{start}-{end}", "-o", out, url], capture_output=True, text=True)
        if r.returncode == 0 and os.path.exists(out) and os.path.getsize(out) > 0:
            return True
        time.sleep(2 + i)
    return False


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
        url = it.get("p")
        total = int(it["z"])
        if not url or total <= 0:
            continue
        log(it["id"], round(total / 1048576, 1), "MB")
        parts = []
        ok = True
        for start in range(0, total, CHUNK):
            end = min(start + CHUNK - 1, total - 1)
            part = os.path.join(TMP, f"{it['id']}.{start//CHUNK:04d}")
            if os.path.exists(part) and os.path.getsize(part) == end - start + 1:
                parts.append(part)
                continue
            if not fetch_range(url, start, end, part):
                log("  块失败", start)
                ok = False
                break
            parts.append(part)
            log("  ", start // CHUNK, "/", total // CHUNK)
        if not ok:
            continue
        src = os.path.join(TMP, it["id"] + ".src")
        with open(src, "wb") as f:
            for part in parts:
                f.write(open(part, "rb").read())
        subprocess.run([FF, "-y", "-loglevel", "error", "-i", src, "-ac", "1", "-ar", "24000",
                        "-b:a", "40k", out], check=False)
        if os.path.exists(out):
            it["local"] = it["id"] + ".mp3"
            log("  ->", round(os.path.getsize(out) / 1048576, 2), "MB")
            open(p, "w", encoding="utf-8").write(
                "window.DATA_AUDIO=" + json.dumps(items, ensure_ascii=False, separators=(",", ":")) + ";\n")
        for part in parts + [src]:
            if os.path.exists(part):
                os.remove(part)
    log("done")


if __name__ == "__main__":
    main()
