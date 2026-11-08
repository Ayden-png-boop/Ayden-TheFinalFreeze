# -*- coding: utf-8 -*-
"""对 staging 里切好的 49 条真人配音做 ASR 复检：转写 vs 脚本，找切错/重复/漏句。"""
import difflib
import json
import os
import re
import sys

from faster_whisper import WhisperModel

BASE = r"C:\Users\-\Desktop\冰川信使海外版"
MODEL_DIR = r"D:\ai\VideoLingo\_model_cache\models--Systran--faster-whisper-large-v3\snapshots\edaa852ec7e145841d8ffdb056a99866b5f0a478"
SRC = os.path.join(BASE, r"_tools\_human_vo")
OUT = os.path.join(BASE, r"_tools\_human_vo_asr.json")

sys.path.insert(0, os.path.join(BASE, "_tools"))
import vo_match_en as V  # noqa: E402


def norm(s):
    s = s.lower().replace("—", " ").replace("–", " ")
    return re.findall(r"[a-z0-9']+", s)


def main():
    script = {r["id"]: r for r in V.load_script()}
    try:
        model = WhisperModel(MODEL_DIR, device="cuda", compute_type="float16", local_files_only=True)
        print("cuda", flush=True)
    except Exception:
        model = WhisperModel(MODEL_DIR, device="cpu", compute_type="int8", local_files_only=True)
        print("cpu", flush=True)

    files = sorted(f for f in os.listdir(SRC) if f.endswith(".mp3"))
    res = []
    for f in files:
        vid = f[:-4]
        segs, info = model.transcribe(
            os.path.join(SRC, f), language="en", beam_size=5, vad_filter=False,
            condition_on_previous_text=False,
            initial_prompt="English narration and dialogue voice-over for a documentary about glaciers and bar-headed geese.",
        )
        txt = " ".join(s.text.strip() for s in segs)
        ref = norm(script[vid]["text"])
        hyp = norm(txt)
        # 用参考词序列覆盖度衡量：参考里有多少词被转写命中
        sm = difflib.SequenceMatcher(None, ref, hyp, autojunk=False)
        covered = sum(b.size for b in sm.get_matching_blocks())
        cov = covered / max(1, len(ref))
        # 转写里出现参考没有的词（可能是重复念）
        sm2 = difflib.SequenceMatcher(None, hyp, ref, autojunk=False)
        extra = len(hyp) - sum(b.size for b in sm2.get_matching_blocks())
        res.append({"id": vid, "cov": round(cov, 3), "extra": extra, "hyp": txt,
                    "ref": script[vid]["text"]})
    json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    res.sort(key=lambda r: r["cov"])
    print("\n=== 覆盖度最低的 10 条 ===")
    for r in res[:10]:
        print(f"{r['id']} cov={r['cov']:.2f} extra={r['extra']}")
        print("   REF", r["ref"][:110])
        print("   HYP", r["hyp"][:110])
    low = [r["id"] for r in res if r["cov"] < 0.6]
    print("\n覆盖率<0.6:", low)
    print("平均覆盖度 %.3f" % (sum(r["cov"] for r in res) / len(res)))


if __name__ == "__main__":
    main()
