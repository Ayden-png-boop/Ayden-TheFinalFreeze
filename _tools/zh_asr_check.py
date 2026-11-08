# -*- coding: utf-8 -*-
"""中文版配音 ASR 抽检：重点覆盖数字/缩写/破折号等清洗过的句子。"""
import difflib
import json
import os
import re
import sys

from faster_whisper import WhisperModel

BASE = r"C:\Users\-\Desktop\冰川信使海外版"
MODEL_DIR = r"D:\ai\VideoLingo\_model_cache\models--Systran--faster-whisper-large-v3\snapshots\edaa852ec7e145841d8ffdb056a99866b5f0a478"
SRC = os.path.join(BASE, r"_tools\_zh_stage")
OUT = os.path.join(BASE, r"_tools\_zh_asr_check.json")

sys.path.insert(0, os.path.join(BASE, "_tools"))
import zh_gen as Z  # noqa: E402

PICK = ["VO-003", "VO-008", "VO-011", "VO-016", "VO-028", "VO-029", "VO-032", "VO-036",
        "VO-037", "VO-046", "VO-047", "VO-052", "VO-055", "VO-062", "VO-068", "VO-076",
        "VO-082", "VO-084", "VO-087", "VO-095", "VO-114"]


def norm(s):
    s = re.sub(r"[^\u4e00-\u9fa5a-z0-9]", "", s.lower())
    return list(s)


def main():
    script = {r["id"]: r for r in Z.load_script()}
    try:
        model = WhisperModel(MODEL_DIR, device="cuda", compute_type="float16", local_files_only=True)
    except Exception:
        model = WhisperModel(MODEL_DIR, device="cpu", compute_type="int8", local_files_only=True)

    res = []
    for vid in PICK:
        p = os.path.join(SRC, vid + ".mp3")
        segs, _ = model.transcribe(p, language="zh", beam_size=5, vad_filter=False,
                                   condition_on_previous_text=False,
                                   initial_prompt="纪录片旁白，关于冰川与斑头雁。")
        hyp = "".join(s.text.strip() for s in segs)
        ref = norm(Z.clean(script[vid]["text"]))
        h = norm(hyp)
        sm = difflib.SequenceMatcher(None, ref, h, autojunk=False)
        cov = sum(b.size for b in sm.get_matching_blocks()) / max(1, len(ref))
        res.append({"id": vid, "cov": cov, "ref": Z.clean(script[vid]["text"]), "hyp": hyp})
        print(f"{vid} cov={cov:.2f}  {hyp[:60]}", flush=True)
    json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n平均覆盖 %.3f" % (sum(r["cov"] for r in res) / len(res)))
    print("低覆盖:", [(r["id"], round(r["cov"], 2)) for r in res if r["cov"] < 0.75])


if __name__ == "__main__":
    main()
