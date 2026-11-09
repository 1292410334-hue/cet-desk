# -*- coding: utf-8 -*-
"""从 GitHub 拉取真实四六级词库与真题清单，生成站点数据。

词库：KyleBing/english-vocabulary（有道词典完整条目：音标/释义/例句/短语/同近义）
补音标：RealKai42/qwerty-learner 的 CET4_T/CET6_T
真题：0609x/CET46-Resources（2013-2026 真题 PDF/Word/答案/听力）
"""
import json, os, re, time, base64, urllib.request, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
TOOLS = os.path.join(ROOT, "tools")
os.makedirs(DATA, exist_ok=True)
UA = {"User-Agent": "cet-desk-builder"}
VOCAB = "KyleBing/english-vocabulary"
PAPERS = "0609x/CET46-Resources"


def api(url, tries=4):
    req = urllib.request.Request(url, headers=UA)
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 + i * 3)
    raise RuntimeError(f"{url[:90]} {last}")


def tree():
    return api(f"https://api.github.com/repos/{VOCAB}/git/trees/master?recursive=1")


def blob_text(sha):
    b = api(f"https://api.github.com/repos/{VOCAB}/git/blobs/{sha}")
    return base64.b64decode(b["content"]).decode("utf-8")


def parse_jl(raw):
    """有道的 jsonl -> 精简条目"""
    out = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        head = obj.get("headWord") or ""
        c = (((obj.get("content") or {}).get("word") or {}).get("content")) or {}
        if not head or not c:
            continue
        trans = []
        for t in c.get("trans") or []:
            pos = (t.get("pos") or "").strip()
            cn = (t.get("tranCn") or "").strip()
            if cn:
                trans.append(f"{pos} {cn}".strip())
        sents = []
        for s in ((c.get("sentence") or {}).get("sentences") or [])[:2]:
            en, cn = (s.get("sContent") or "").strip(), (s.get("sCn") or "").strip()
            if en:
                sents.append([en, cn])
        phr = []
        for p in ((c.get("phrase") or {}).get("phrases") or [])[:4]:
            en, cn = (p.get("pContent") or "").strip(), (p.get("pCn") or "").strip()
            if en:
                phr.append([en, cn])
        syn = []
        for s in ((c.get("syno") or {}).get("synos") or [])[:3]:
            tr = (s.get("tran") or "").strip()
            if tr:
                syn.append(tr)
        out[head.lower()] = {
            "w": head,
            "us": (c.get("usphone") or "").strip(),
            "uk": (c.get("ukphone") or "").strip(),
            "tr": trans[:3],
            "s": sents,
            "p": phr,
            "y": syn,
        }
    return out


def qwerty(name):
    r = api(f"https://api.github.com/repos/RealKai42/qwerty-learner/contents/public/dicts/{name}")
    data = json.loads(base64.b64decode(r["content"]).decode("utf-8"))
    out = {}
    for x in data:
        w = (x.get("name") or "").strip()
        if not w:
            continue
        out[w.lower()] = {
            "w": w,
            "us": (x.get("usphone") or "").strip(),
            "uk": (x.get("ukphone") or "").strip(),
            "tr": [(t or "").strip() for t in (x.get("trans") or []) if (t or "").strip()][:2],
        }
    return out


def write_js(path, var):
    """站点用 .js 而不是 .json：file:// 双击打开也能读到数据。"""
    with open(path, encoding="utf-8") as f:
        obj = json.load(f)
    js = os.path.splitext(path)[0] + ".js"
    with open(js, "w", encoding="utf-8") as f:
        f.write(f"window.{var}=" + json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print(f"  {os.path.basename(js)}: {os.path.getsize(js)/1048576:.2f} MB")


def write(name, words):
    words.sort(key=lambda x: x["w"].lower())
    p = os.path.join(DATA, f"{name}.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  {name}: {len(words)} 词, {os.path.getsize(p)/1048576:.2f} MB")
    write_js(p, "DATA_" + name.upper())


def build_words():
    t = tree()
    def by_path(path):
        e = next(x for x in t["tree"] if x["path"] == path)
        return blob_text(e["sha"])

    j4 = parse_jl(by_path("full_line_jsonl/full/乱序/四级.jsonl"))
    j6 = parse_jl(by_path("full_line_jsonl/full/乱序/六级.jsonl"))
    q4, q6 = qwerty("CET4_T.json"), qwerty("CET6_T.json")
    txt6 = by_path("4 六级-乱序.txt")
    print("四/六级 jsonl:", len(j4), len(j6), "| qwerty:", len(q4), len(q6))

    def merge(base, *layers):
        """用低优先层补齐音标/释义"""
        for layer in layers:
            hit = layer.get(base["w"].lower())
            if not hit:
                continue
            if not base.get("us"):
                base["us"] = hit.get("us", "")
                base["uk"] = hit.get("uk", "") or base.get("uk", "")
            if not base.get("tr"):
                base["tr"] = hit.get("tr", [])
        return base

    # 四级：以 jsonl 4190 词为底，qwerty 补音标
    cet4 = [merge(dict(v), q4) for v in j4.values()]
    cet4 = [w for w in cet4 if w["tr"]]
    write("cet4", cet4)

    # 六级：以官方乱序 txt（3991 词）为词表底，jsonl 六级 > jsonl 四级 > qwerty 六级 补细节
    cet6 = []
    for line in txt6.splitlines():
        if "\t" not in line:
            continue
        word, mean = line.split("\t", 1)
        word, mean = word.strip(), mean.strip()
        if not word:
            continue
        k = word.lower()
        detail = j6.get(k) or j4.get(k)
        if detail:
            w = dict(detail)
            w["w"] = word
        else:
            w = {"w": word, "us": "", "uk": "", "tr": [mean], "s": [], "p": [], "y": []}
        w = merge(w, q6, q4)
        if not w["tr"]:
            w["tr"] = [mean]
        cet6.append(w)
    # 去重
    seen, uniq = set(), []
    for w in cet6:
        k = w["w"].lower()
        if k in seen:
            continue
        seen.add(k)
        uniq.append(w)
    write("cet6", uniq)
    return len(cet4), len(uniq)


def build_papers():
    t = api(f"https://api.github.com/repos/{PAPERS}/git/trees/main?recursive=1")
    levels = {"cet4": "四级真题", "cet6": "六级真题"}
    kinds = ["真题PDF", "真题Word", "答案解析", "听力音频"]
    out = {}
    for key, folder in levels.items():
        sess = {}
        for x in t["tree"]:
            if x["type"] != "blob":
                continue
            p = x["path"]
            if not p.startswith(folder + "/"):
                continue
            parts = p.split("/")
            if len(parts) < 4:
                continue
            session, kind = parts[1], parts[2]
            if kind not in kinds:
                continue
            item = {
                "k": kind,
                "n": parts[-1],
                "z": x["size"],
                "e": os.path.splitext(parts[-1])[1].lower().lstrip("."),
                "u": f"https://github.com/{PAPERS}/blob/main/" + urllib.parse.quote(p),
            }
            sess.setdefault(session, []).append(item)
        ordered = []
        for s in sorted(sess, reverse=True):
            items = sorted(sess[s], key=lambda i: (kinds.index(i["k"]), i["n"]))
            ordered.append({"s": s, "i": items})
        out[key] = ordered
    with open(os.path.join(DATA, "papers.json"), "w", encoding="utf-8") as f:
        json.dump({"src": PAPERS, "levels": out}, f, ensure_ascii=False, separators=(",", ":"))
    write_js(os.path.join(DATA, "papers.json"), "DATA_PAPERS")
    print("  papers:", {k: (len(v), sum(len(x["i"]) for x in v)) for k, v in out.items()})


if __name__ == "__main__":
    n4, n6 = build_words()
    build_papers()
    meta = {"cet4": n4, "cet6": n6, "built": time.strftime("%Y-%m-%d")}
    with open(os.path.join(DATA, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print("done", meta)
