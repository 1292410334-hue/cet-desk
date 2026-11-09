# -*- coding: utf-8 -*-
"""慢速但稳的听力下载：走 api.github.com 的 JSON blob（base64），逐条重试。

raw.githubusercontent 在国内不通，api 的 raw media type 会 302 到被封的 S3；
只有 JSON blob 这条路能走，速度约 20-30 KB/s，一段 15 MB 的音频要十几分钟。
"""
import base64
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
    targets = set(sys.argv[1:]) or {"cet4_2025_06_0", "cet6_2025_06_13", "cet6_2026_06_10"}
    s = open(os.path.join(ROOT, "data", "audio.js"), encoding="utf-8").read()
    items = json.loads(s[s.index("=") + 1:].strip().rstrip(";"))
    os.makedirs(AUDIO, exist_ok=True)
    os.makedirs(TMP, exist_ok=True)

    for it in items:
        if it["id"] not in targets:
            continue
        out = os.path.join(AUDIO, it["id"] + ".mp3")
        if os.path.exists(out) and os.path.getsize(out) > 500000:
            log("have", it["id"])
            continue
        if not it.get("sha"):
            log("no sha", it["id"])
            continue
        blob = os.path.join(TMP, it["id"] + ".json")
        ok = False
        for attempt in range(1, 4):
            log(f"[{attempt}] {it['id']} {round(it['z']/1048576,1)}MB 开始")
            t0 = time.time()
            r = subprocess.run([CURL, "-sS", "--fail", "-L", "--connect-timeout", "20",
                                "--max-time", "2400", "--retry", "2", "--retry-all-errors",
                                "-H", "User-Agent: cet", "-o", blob,
                                f"https://api.github.com/repos/0609x/CET46-Resources/git/blobs/{it['sha']}"],
                               capture_output=True, text=True)
            dt = time.time() - t0
            size = os.path.getsize(blob) if os.path.exists(blob) else 0
            log(f"    {dt:.0f}s {size/1048576:.2f}MB rc={r.returncode} {r.stderr.strip()[:120]}")
            if size > 1000:
                try:
                    data = json.load(open(blob, encoding="utf-8"))
                    raw = base64.b64decode(data["content"])
                    tmp_mp3 = os.path.join(TMP, it["id"] + ".mp3")
                    open(tmp_mp3, "wb").write(raw)
                    subprocess.run([FF, "-y", "-loglevel", "error", "-i", tmp_mp3,
                                    "-ac", "1", "-ar", "24000", "-b:a", "40k", out], check=False)
                    ok = True
                    log("    ->", os.path.basename(out), round(os.path.getsize(out) / 1048576, 2), "MB")
                except Exception as e:  # noqa: BLE001
                    log("    decode fail", e)
            if ok:
                break
            time.sleep(5)
        for p in (blob, os.path.join(TMP, it["id"] + ".mp3")):
            if os.path.exists(p):
                os.remove(p)
    log("done")


if __name__ == "__main__":
    main()
