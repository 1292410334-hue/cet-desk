# -*- coding: utf-8 -*-
"""抓几段最新听力到本地并压成 40k 单声道（走 api 的 raw blob，避开被墙的 raw 域名）。"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO = os.path.join(ROOT, "data", "audio")
TMP = os.path.join(ROOT, "tools", ".audio_tmp")
FF = r"C:\Users\lv\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"
CURL = "curl.exe"


def load_audio_manifest():
    p = os.path.join(ROOT, "data", "audio.js")
    s = open(p, encoding="utf-8").read()
    return json.loads(s[s.index("=") + 1:].strip().rstrip(";"))


def main():
    items = load_audio_manifest()
    want_sessions = set(sys.argv[1:]) or {"2025.06", "2026.06"}
    os.makedirs(AUDIO, exist_ok=True)
    os.makedirs(TMP, exist_ok=True)
    for it in items:
        if it["s"] not in want_sessions:
            continue
        out = os.path.join(AUDIO, it["id"] + ".mp3")
        if os.path.exists(out) and os.path.getsize(out) > 500000:
            print("have", it["id"])
            continue
        if not it.get("path"):
            continue
        print("get", it["n"], round(it["z"] / 1048576, 1), "MB")
        raw = os.path.join(TMP, it["id"] + ".src")
        # 用 tree 找 sha
        cmd = [CURL, "-sSL", "--fail", "--retry", "5", "--retry-all-errors", "--connect-timeout", "20",
               "--max-time", "2400", "-H", "Accept: application/vnd.github.raw",
               "-H", "User-Agent: cet", "-o", raw, "https://api.github.com/repos/0609x/CET46-Resources/git/blobs/__SHA__"]
        sha = it.get("sha")
        if not sha:
            print("  no sha, skip")
            continue
        cmd[cmd.index("__SHA__")] = sha
        r = subprocess.run(cmd)
        if r.returncode != 0 or not os.path.exists(raw):
            print("  curl fail", r.returncode)
            continue
        subprocess.run([FF, "-y", "-loglevel", "error", "-i", raw, "-ac", "1", "-ar", "24000",
                        "-b:a", "40k", out], check=False)
        os.remove(raw)
        print("  ->", os.path.basename(out), round(os.path.getsize(out) / 1048576, 2), "MB")


if __name__ == "__main__":
    main()
