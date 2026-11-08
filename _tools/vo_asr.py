# -*- coding: utf-8 -*-
"""用本地 faster-whisper large-v3 转写用户自录配音，输出带时间戳的句子。"""
import os, json, sys, time
from faster_whisper import WhisperModel

MODEL_DIR = r"D:\ai\VideoLingo\_model_cache\models--Systran--faster-whisper-large-v3\snapshots\edaa852ec7e145841d8ffdb056a99866b5f0a478"
SRC = r"C:\Users\-\Desktop\冰川信使海外版\mp3"
OUT = r"C:\Users\-\Desktop\冰川信使海外版\_tools\_vo_asr.json"


def main():
    dev, ct = "cuda", "float16"
    try:
        model = WhisperModel(MODEL_DIR, device=dev, compute_type=ct, local_files_only=True)
        # 触发一次加载验证
    except Exception as e:
        print("cuda failed:", e, flush=True)
        dev, ct = "cpu", "int8"
        model = WhisperModel(MODEL_DIR, device=dev, compute_type=ct, local_files_only=True)
    print("device", dev, ct, flush=True)

    files = sorted([f for f in os.listdir(SRC) if f.lower().endswith(".m4a")])
    result = []
    t0 = time.time()
    for i, f in enumerate(files, 1):
        p = os.path.join(SRC, f)
        segs, info = model.transcribe(
            p, language="en", beam_size=5, vad_filter=False,
            condition_on_previous_text=False,
            initial_prompt="English narration and dialogue voice-over for a documentary story about glaciers and bar-headed geese.",
        )
        items = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()} for s in segs]
        result.append({"file": f, "dur": round(info.duration, 2), "segments": items})
        txt = " / ".join(x["text"] for x in items)
        print(f"[{i}/{len(files)}] {f} ({info.duration:.1f}s) {time.time()-t0:.0f}s :: {txt[:120]}", flush=True)
        with open(OUT, "w", encoding="utf-8") as fp:
            json.dump(result, fp, ensure_ascii=False, indent=1)
    print("DONE", OUT, flush=True)


if __name__ == "__main__":
    main()
