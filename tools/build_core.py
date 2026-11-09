# -*- coding: utf-8 -*-
"""划出「核心词」。

口径（可复现）：
  四级核心 = 四级大纲词 − 初中词表 − 高中词表   （大学阶段才出现的那批）
  六级核心 = 六级大纲词 − 四级大纲词              （六级相对四级新增的那批）

词表来源：KyleBing/english-vocabulary 的 1 初中-乱序.txt / 2 高中-乱序.txt
输出：data/core.json + data/core.js，并给 cet4.js / cet6.js 的每个词打上 c=1
"""
import base64
import json
import os
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
REPO = "KyleBing/english-vocabulary"
UA = {"User-Agent": "cet-desk-builder"}
_TREE = None


def api(url, tries=5):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 + i * 3)
    raise RuntimeError(f"{url[:80]} {last}")


def tree():
    global _TREE
    if _TREE is None:
        _TREE = api(f"https://api.github.com/repos/{REPO}/git/trees/master?recursive=1")
    return _TREE


def words_of(path):
    e = next(x for x in tree()["tree"] if x["path"] == path)
    b = api(f"https://api.github.com/repos/{REPO}/git/blobs/{e['sha']}")
    text = base64.b64decode(b["content"]).decode("utf-8")
    return {l.split("\t")[0].strip().lower() for l in text.splitlines() if "\t" in l}


def load(name):
    p = os.path.join(DATA, name + ".json")
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8"))
    s = open(os.path.join(DATA, name + ".js"), encoding="utf-8").read()
    return json.loads(s[s.index("=") + 1:].strip().rstrip(";"))


def save(name, words):
    p = os.path.join(DATA, name + ".js")
    with open(p, "w", encoding="utf-8") as f:
        f.write("window.DATA_" + name.upper() + "=" +
                json.dumps(words, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print("  wrote", os.path.basename(p), round(os.path.getsize(p) / 1048576, 2), "MB")


def main():
    junior = words_of("1 初中-乱序.txt")
    senior = words_of("2 高中-乱序.txt")
    print("初中", len(junior), "高中", len(senior))

    c4, c6 = load("cet4"), load("cet6")
    set4 = {w["w"].lower() for w in c4}
    set6 = {w["w"].lower() for w in c6}

    core4 = {k for k in set4 if k not in junior and k not in senior}
    core6 = {k for k in set6 if k not in set4}

    for w in c4:
        if w["w"].lower() in core4:
            w["c"] = 1
        else:
            w.pop("c", None)
    for w in c6:
        if w["w"].lower() in core6:
            w["c"] = 1
        else:
            w.pop("c", None)

    save("cet4", c4)
    save("cet6", c6)

    core = {
        "cet4": sorted(core4),
        "cet6": sorted(core6),
        "note": "四级核心=四级词减初中高中词表；六级核心=六级词减四级词表",
    }
    with open(os.path.join(DATA, "core.js"), "w", encoding="utf-8") as f:
        f.write("window.DATA_CORE=" + json.dumps(core, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print("core:", len(core4), len(core6))


if __name__ == "__main__":
    main()
