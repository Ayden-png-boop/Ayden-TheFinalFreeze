# -*- coding: utf-8 -*-
"""英文配音覆盖度对齐：录音 ASR 结果 vs 英文配音脚本(115 条)。"""
import json, re, os, difflib, itertools

BASE = r"C:\Users\-\Desktop\冰川信使海外版"
SCRIPT = os.path.join(BASE, r"output\voice-script\配音脚本-英文.txt")
ASR = os.path.join(BASE, r"_tools\_vo_asr.json")
OUT = os.path.join(BASE, r"_tools\_vo_coverage_en.json")
TH = 0.55


def words(s):
    s = s.lower()
    s = s.replace("—", " ").replace("–", " ").replace("…", " ")
    return re.findall(r"[a-z0-9']+", s)


def load_script():
    rows = []
    for line in open(SCRIPT, encoding="utf-8"):
        line = line.strip()
        m = re.match(r"^(VO-\d+)\s+\[([^\]]+)\]\s*(.*)$", line)
        if not m:
            continue
        vid, role, text = m.group(1), m.group(2), m.group(3)
        if "不配音" in role:
            continue
        rows.append({"id": vid, "role": role, "text": text, "w": words(text)})
    return rows


def best_window(q, T):
    n = len(q)
    if not n or not T:
        return 0.0, 0, 0
    best = (0.0, 0, 0)
    lo = max(1, int(n * 0.6))
    hi = min(len(T), int(n * 1.8) + 3)
    step = max(1, n // 10)
    for w in range(lo, hi + 1, step):
        for i in range(0, max(1, len(T) - w + 1), step):
            r = difflib.SequenceMatcher(None, q, T[i:i + w], autojunk=False).ratio()
            if r > best[0]:
                best = (r, i, i + w)
    return best


def main():
    script = load_script()
    asr = json.load(open(ASR, encoding="utf-8"))
    files = [{"file": r["file"], "dur": r["dur"], "w": words(" ".join(s["text"] for s in r["segments"]))}
             for r in asr]

    matches = {}
    for f in files:
        for vo in script:
            sc, a, b = best_window(vo["w"], f["w"])
            if sc >= TH:
                cur = matches.get(vo["id"])
                if not cur or sc > cur["score"]:
                    matches[vo["id"]] = {"score": round(sc, 3), "file": f["file"], "words": b - a}

    covered = set(matches)
    missing = [v for v in script if v["id"] not in covered]
    print(f"脚本需配音 {len(script)} 条 | 录音文件 {len(files)} 个 | 命中 {len(covered)} 条 | 缺 {len(missing)} 条\n")
    print("=== 缺口 ===")
    for v in missing:
        print(f"{v['id']} [{v['role']}] {v['text'][:70]}")
    print("\n=== 每个文件覆盖的 VO ===")
    byfile = {}
    for vid, mt in matches.items():
        byfile.setdefault(mt["file"], []).append((vid, mt["score"]))
    for f in files:
        items = sorted(byfile.get(f["file"], []))
        print(f"{f['file']:<22} dur={f['dur']:>5.1f}s  命中{len(items)}条: " + ", ".join(f"{v}({s:.2f})" for v, s in items))
    json.dump({"matches": matches, "missing": [v["id"] for v in missing]}, open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
