# -*- coding: utf-8 -*-
"""把用户录音的 ASR 结果与配音脚本逐条对齐，找出已录 / 未录的 VO 条目。"""
import json, re, sys, os, difflib

BASE = r"C:\Users\-\Desktop\冰川信使海外版"
SCRIPT = os.path.join(BASE, r"output\voice-script\配音脚本-中文.txt")
ASR = os.path.join(BASE, r"_tools\_vo_asr.json")
OUT = os.path.join(BASE, r"_tools\_vo_coverage.json")


def norm(s):
    return re.sub(r"[^\u4e00-\u9fa5A-Za-z0-9]", "", s)


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
        rows.append({"id": vid, "role": role, "text": text, "n": norm(text)})
    return rows


def best_window(q, T):
    """在长文本 T 中找与 q 最相似的窗口，返回 (score, start, end, snippet)"""
    m = len(q)
    if m == 0 or not T:
        return 0.0, 0, 0, ""
    best = (0.0, 0, 0, "")
    lo = max(1, int(m * 0.55))
    hi = min(len(T), int(m * 1.75) + 4)
    if hi < lo:
        lo, hi = 1, len(T)
    step = max(1, m // 12)
    for w in range(lo, hi + 1, step):
        for i in range(0, max(1, len(T) - w + 1), step):
            cand = T[i:i + w]
            s = difflib.SequenceMatcher(None, q, cand).quick_ratio()
            if s > best[0]:
                s2 = difflib.SequenceMatcher(None, q, cand).ratio()
                if s2 > best[0]:
                    best = (s2, i, i + w, cand)
    return best


def main():
    script = load_script()
    asr = json.load(open(ASR, encoding="utf-8"))
    files = []
    for rec in asr:
        txt = norm("".join(s["text"] for s in rec["segments"]))
        files.append({"file": rec["file"], "dur": rec["dur"], "norm": txt})

    # 每个文件对所有台词打分
    matches = {}
    for f in files:
        for vo in script:
            sc, a, b, snip = best_window(vo["n"], f["norm"])
            if sc >= 0.45:
                key = vo["id"]
                if key not in matches or sc > matches[key]["score"]:
                    matches[key] = {"score": round(sc, 3), "file": f["file"],
                                    "pos": a, "snippet": snip, "vo": vo["id"]}

    covered = set(matches)
    missing = [v for v in script if v["id"] not in covered]
    print(f"脚本需配音 {len(script)} 条 | 录音文件 {len(files)} 个 | 匹配上 {len(covered)} 条 | 缺 {len(missing)} 条")
    print("\n=== 未匹配（缺口）===")
    for v in missing:
        print(f"{v['id']} [{v['role']}] {v['text'][:50]}")
    print("\n=== 匹配明细 ===")
    for v in script:
        if v["id"] in matches:
            mt = matches[v["id"]]
            print(f"{v['id']} <= {mt['file']} ({mt['score']:.2f})")
    json.dump({"matches": matches, "missing": [v["id"] for v in missing]}, open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
