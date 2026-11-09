# -*- coding: utf-8 -*-
"""把站点里的资料抽出来，整理成与界面无关的一份（纯 JSON + 原始文件）。

输出目录：<仓库根>/materials
  words/cet4.json   4190 词，字段 w/us/uk/tr/s/p/y/c
  words/cet6.json   3991 词
  words/core.json   核心词表
  papers/papers.json  55 个考次、455 份文件的清单（含本地路径）
  papers/files/...    已下载到本地的真题与解析
  audio/audio.json    22 段听力清单（本地/镜像地址）
  audio/files/*.mp3   已下载的听力
  README.md           字段说明、数量、来源、许可
"""
import json
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data")
OUT = os.path.join(os.path.dirname(ROOT), "materials")


def load_js(name):
    s = open(os.path.join(SRC, name), encoding="utf-8").read()
    return json.loads(s[s.index("=") + 1:].strip().rstrip(";"))


def dump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    print("  ", os.path.relpath(path, OUT), round(os.path.getsize(path) / 1048576, 2), "MB")


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    c4 = load_js("cet4.js")
    c6 = load_js("cet6.js")
    core = load_js("core.js")
    papers = load_js("papers.js")
    audio = load_js("audio.js")

    dump(os.path.join(OUT, "words", "cet4.json"), c4)
    dump(os.path.join(OUT, "words", "cet6.json"), c6)
    dump(os.path.join(OUT, "words", "core.json"), core)

    # 真题清单：把本地路径改成 materials 内的相对路径
    for level, sessions in papers["levels"].items():
        for se in sessions:
            for it in se["i"]:
                if it.get("l"):
                    it["l"] = "papers/files/" + it["l"].split("papers_local/", 1)[-1]
    dump(os.path.join(OUT, "papers", "papers.json"), papers)

    src_files = os.path.join(SRC, "papers_local")
    if os.path.isdir(src_files):
        shutil.copytree(src_files, os.path.join(OUT, "papers", "files"))

    for it in audio:
        if it.get("local"):
            it["file"] = "audio/files/" + it["local"]
    dump(os.path.join(OUT, "audio", "audio.json"), audio)

    src_audio = os.path.join(SRC, "audio")
    if os.path.isdir(src_audio):
        shutil.copytree(src_audio, os.path.join(OUT, "audio", "files"))

    n4 = len(c4)
    n6 = len(c6)
    npaper = sum(len(se["i"]) for lv in papers["levels"].values() for se in lv)
    nlocal = sum(1 for lv in papers["levels"].values() for se in lv for i in se["i"] if i.get("l"))
    nmic = sum(1 for a in audio if a.get("local"))

    readme = f"""# 四六级资料包

这是从站点里抽出来的一份与界面无关的资料，纯 JSON + 原始文件，任何前端都能直接用。

## 数量

| 项 | 数量 |
| --- | --- |
| 四级词 | {n4} |
| 六级词 | {n6} |
| 四级核心词 | {len(core['cet4'])} |
| 六级核心词 | {len(core['cet6'])} |
| 真题考次 | {len(papers['levels']['cet4']) + len(papers['levels']['cet6'])} |
| 真题文件 | {npaper}（其中 {nlocal} 份已下载到本地） |
| 听力段数 | {len(audio)}（其中 {nmic} 段已下载到本地） |

## 字段

### words/cet4.json、words/cet6.json

数组，每项：

| 字段 | 含义 |
| --- | --- |
| `w` | 单词 |
| `us` / `uk` | 美音 / 英音音标（无斜杠） |
| `tr` | 释义数组，形如 `["v 丢弃；放弃，抛弃"]` |
| `s` | 例句，`[[英文, 中文], ...]`，最多 2 条 |
| `p` | 短语，`[[英文, 中文], ...]`，最多 4 条 |
| `y` | 同近义，字符串数组 |
| `c` | 1 表示核心词（可能缺省） |

按字母序排好。

### words/core.json

```json
{{ "cet4": ["abandon", ...], "cet6": [...], "note": "四级核心=四级词减初中高中词表；六级核心=六级词减四级词表" }}
```

### papers/papers.json

```json
{{ "src": "0609x/CET46-Resources",
  "levels": {{
    "cet4": [ {{ "s": "2026.06",
      "i": [ {{ "k": "真题PDF", "n": "文件名.pdf", "z": 227000, "e": "pdf",
               "u": "https://github.com/...", "l": "papers/files/cet4/2026.06/xxx.pdf" }} ] }} ],
    "cet6": [ ... ] }} }}
```

`k` 是四类之一：`真题PDF` / `真题Word` / `答案解析` / `听力音频`。
`u` 是原始仓库地址；`l` 是本地相对路径（有就说明已下载）。
未下载的文件可用 `https://gh-proxy.com/` + `u` 里 `/blob/main/` 换成 `/main/` 的 raw 地址访问。

### audio/audio.json

| 字段 | 含义 |
| --- | --- |
| `id` | 唯一 id |
| `level` | `cet4` / `cet6` |
| `s` | 考次，如 `2025.06` |
| `n` | 原始文件名 |
| `z` | 原始字节数 |
| `u` | raw.githubusercontent 地址 |
| `p` | gh-proxy 镜像地址（境内可用） |
| `path` | 仓库内路径 |
| `sha` | blob sha（可用 api.github.com 取字节） |
| `local` | 本地文件名（有就说明已下载） |
| `file` | 本地相对路径 |

## 来源与许可

- 词库：KyleBing/english-vocabulary（有道词条）
- 音标：RealKai42/qwerty-learner
- 真题与听力：0609x/CET46-Resources

全部为公开整理的学习资料，版权归原作者与原出版方，仅限个人学习，请勿商用。

## 重新生成

`../cet/tools/` 下有脚本：`build_data.py`（词库+真题清单）、`build_core.py`（核心词）、
`build_audio.py`（听力清单）、`fetch_audio_chunks.py`（分块下载听力）、`fetch_papers.py`（下载真题）。
"""
    with open(os.path.join(OUT, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme)
    total = sum(os.path.getsize(os.path.join(dp, f))
                for dp, _, fs in os.walk(OUT) for f in fs)
    print("materials total", round(total / 1048576, 1), "MB")


if __name__ == "__main__":
    main()
