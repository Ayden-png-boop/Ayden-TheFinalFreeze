# -*- coding: utf-8 -*-
"""量化混响：用语音间隙的「回声填充深度」对比真人录音与 AI 干声。

dry 录音在语音间隙里能量会跌到噪底（深度大）；
带房间混响时尾音灌进间隙（深度浅）。同一指标对比即可判混响强度。
"""
import os
import sys
import glob
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voice_profile import load_wav


def gap_depth(x, sr):
    """返回 (间隙中位深度dB, 有效间隙数)。深度 = 语音峰值电平 - 间隙中部电平。"""
    w = int(0.02 * sr)
    h = int(0.01 * sr)
    n = 1 + max(0, (len(x) - w) // h)
    e = np.array([np.sqrt(np.mean(x[i * h:i * h + w] ** 2)) for i in range(n)])
    db = 20 * np.log10(e + 1e-9)
    peak = np.percentile(db, 95)
    if peak < -45:
        return None, 0
    speech = db > peak - 20
    gaps = []
    i = 0
    L = len(db)
    while i < L:
        if not speech[i]:
            j = i
            while j < L and not speech[j]:
                j += 1
            if (j - i) * 0.01 >= 0.15 and i > 0 and j < L:
                mid = (i + j) // 2
                seg = db[max(i, mid - 2):mid + 3]
                gaps.append(peak - float(np.median(seg)))
            i = j
        else:
            i += 1
    if not gaps:
        return None, 0
    return float(np.median(gaps)), len(gaps)


def report(pattern, label):
    files = sorted(glob.glob(pattern))
    ds, gs = [], []
    for f in files:
        x, sr = load_wav(f)
        d, g = gap_depth(x, sr)
        if d is not None:
            ds.append(d)
            gs.append(g)
    if not ds:
        print(f"{label:<24} 无数据")
        return
    print(f"{label:<24} n={len(ds):3d}  间隙深度中位 {np.median(ds):5.1f}dB "
          f"(P25 {np.percentile(ds,25):4.1f} / P75 {np.percentile(ds,75):4.1f})  间隙数中位 {np.median(gs):.0f}")


if __name__ == "__main__":
    BASE = r"C:\Users\-\Desktop\冰川信使海外版"
    report(os.path.join(BASE, r"_tools\_human_vo\VO-*.mp3"), "真人录音(线上版)")
    report(os.path.join(BASE, r"output\voice-overs\en\_aria_backup\VO-*.mp3"), "AI 干声(参照)")
    report(os.path.join(BASE, r"mp3\*.m4a"), "原始 m4a")
