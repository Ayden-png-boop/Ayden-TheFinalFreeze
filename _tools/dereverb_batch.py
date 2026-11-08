# -*- coding: utf-8 -*-
"""全量重做 49 条真人英文配音：源 m4a 按已核实的切分区间 → WPE 去混响 + 谱减降噪
→ loudnorm 两遍 -21 LUFS → 24kHz mono 48kbps mp3，输出 staging _tools/_human_vo_dry。

参数自适应：短文件（T<300 帧）减少抽头与迭代，防止过拟合。
"""
import json
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vo_dereverb as DR
import apply_human_vo as A
from dereverb_ab import decode

BASE = A.BASE
REPORT = {r["id"]: r for r in json.load(
    open(os.path.join(BASE, r"_tools\_human_vo_report.json"), encoding="utf-8"))}
OUT_DIR = os.path.join(BASE, r"_tools\_human_vo_dry")
QC = os.path.join(BASE, r"_tools\_human_vo_dry_qc.json")


def render_mp3(wav_path, dur, out):
    meas = A.loudnorm_measure(wav_path, 0.0, dur)
    A.render(wav_path, 0.0, dur, meas, out)
    return meas


def process(vid):
    r = REPORT[vid]
    src = os.path.join(A.SRC_DIR, r["src"])
    x = decode(src, r["start"], r["end"])
    # 自适应参数
    n_frames = int(len(x) / 24000 * 24000 / (1024 // 4) / 1)  # 占位，下面直接用时长判断
    dur = len(x) / 24000
    if dur >= 6.0:
        p = dict(taps=12, delay=2, iters=3, floor_db=12.0, denoise_db=12.0, wmode="none")
    elif dur >= 3.0:
        p = dict(taps=10, delay=2, iters=3, floor_db=10.0, denoise_db=10.0, wmode="none")
    else:
        p = dict(taps=8, delay=2, iters=2, floor_db=9.0, denoise_db=9.0, wmode="none")
    y = DR.dereverb_wav(x, 24000, **p)
    raw = os.path.join(OUT_DIR, "_tmp.f32")
    wav = os.path.join(OUT_DIR, "_tmp.wav")
    open(raw, "wb").write(y.astype(np.float32).tobytes())
    subprocess.run([A.FFMPEG, "-y", "-v", "error", "-f", "f32le", "-ar", "24000", "-ac", "1",
                    "-i", raw, "-c:a", "pcm_f32le", wav], check=True)
    out = os.path.join(OUT_DIR, vid + ".mp3")
    meas = render_mp3(wav, len(y) / 24000, out)
    d = A.probe_dur(out)
    return {"id": vid, "dur": round(d, 2), "prev_dur": r["dur"], "input_i": meas["input_i"],
            "params": {k: v for k, v in p.items()}}


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    rows = []
    for i, vid in enumerate(sorted(REPORT)):
        out = os.path.join(OUT_DIR, vid + ".mp3")
        if os.path.exists(out):
            continue
        info = process(vid)
        rows.append(info)
        json.dump(rows, open(QC, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"[{i+1}/49] {vid}  {info['prev_dur']:.2f}->{info['dur']:.2f}s  "
              f"LUFS {info['input_i']}", flush=True)
    print("DONE", len(rows))


if __name__ == "__main__":
    main()
