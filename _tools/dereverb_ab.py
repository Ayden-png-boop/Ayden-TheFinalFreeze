# -*- coding: utf-8 -*-
"""A/B 调参：对 3 条样本跑不同力度的 WPE，输出对比指标与试听带。"""
import os
import sys
import subprocess
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voice_profile import load_wav
import vo_dereverb as DR
import apply_human_vo as A
from reverb_measure import gap_depth

BASE = r"C:\Users\-\Desktop\冰川信使海外版"
TMP = os.path.join(BASE, r"_tools\_dereverb_tmp")
os.makedirs(TMP, exist_ok=True)

REPORT = {r["id"]: r for r in __import__("json").load(
    open(os.path.join(BASE, r"_tools\_human_vo_report.json"), encoding="utf-8"))}


def decode(src, start, end):
    """源录音 -> 24k mono float64"""
    cmd = [A.FFMPEG, "-v", "error", "-i", src, "-ss", "%.3f" % start, "-to", "%.3f" % end,
           "-f", "f32le", "-acodec", "pcm_f32le", "-ac", "1", "-ar", "24000", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)


def render_mp3(wav_path, dur, out):
    meas = A.loudnorm_measure(wav_path, 0.0, dur)
    A.render(wav_path, 0.0, dur, meas, out)


def process_one(vid, params):
    r = REPORT[vid]
    src = os.path.join(A.SRC_DIR, r["src"])
    x = decode(src, r["start"], r["end"])
    y = DR.dereverb_wav(x, 24000, **params)
    wav = os.path.join(TMP, f"{vid}_p.wav")
    # 写 wav（f32le 裸流塞进 wav 容器）
    raw = os.path.join(TMP, f"{vid}_p.f32")
    open(raw, "wb").write(y.astype(np.float32).tobytes())
    subprocess.run([A.FFMPEG, "-y", "-v", "error", "-f", "f32le", "-ar", "24000", "-ac", "1",
                    "-i", raw, "-c:a", "pcm_f32le", wav], check=True)
    out = os.path.join(TMP, f"{vid}_p.mp3")
    render_mp3(wav, len(y) / 24000, out)
    return out


if __name__ == "__main__":
    TEST = ["VO-003", "VO-012", "VO-040"]
    SETS = {
        "轻": dict(taps=8, delay=3, iters=3, floor_db=9.0, blend=1.0),
        "中": dict(taps=10, delay=3, iters=3, floor_db=12.0, blend=1.0),
        "重": dict(taps=14, delay=2, iters=4, floor_db=16.0, blend=1.0),
    }
    rows = {}
    for vid in TEST:
        r = REPORT[vid]
        src = os.path.join(A.SRC_DIR, r["src"])
        x, sr = load_wav(os.path.join(A.OUT_DIR, vid + ".mp3"))
        d0, _ = gap_depth(x, sr)
        print(f"\n{vid} (线上现状) 深度 {d0:.1f}dB")
        for name, p in SETS.items():
            out = process_one(vid, p)
            xp, sr = load_wav(out)
            d1, _ = gap_depth(xp, sr)
            print(f"  {name}: 深度 {d1:.1f}dB (+{d1-d0:.1f})  时长 {len(xp)/sr:.2f}s "
                  f"(原 {r['dur']:.2f}s)  -> {os.path.basename(out)}")
