# -*- coding: utf-8 -*-
"""测量用户录音的音色基线：基频中位数、语速（词/秒）、响度。"""
import os, json, subprocess, wave, tempfile
import numpy as np

FFMPEG = r"D:\ai\VideoLingo\ffmpeg\bin\ffmpeg.exe"
SRC = r"C:\Users\-\Desktop\冰川信使海外版\mp3"
ASR = r"C:\Users\-\Desktop\冰川信使海外版\_tools\_vo_asr.json"


def load_wav(path, sr=16000):
    tmp = os.path.join(tempfile.gettempdir(), "_f0.wav")
    subprocess.run([FFMPEG, "-y", "-v", "error", "-i", path, "-ac", "1", "-ar", str(sr), tmp],
                   check=True)
    with wave.open(tmp, "rb") as w:
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return data, sr


def median_f0(x, sr):
    frame, hop = int(sr * 0.04), int(sr * 0.02)
    lo, hi = int(sr / 320), int(sr / 75)
    f0s = []
    for i in range(0, len(x) - frame, hop):
        seg = x[i:i + frame]
        if np.sqrt(np.mean(seg ** 2)) < 0.01:
            continue
        seg = seg - seg.mean()
        ac = np.correlate(seg, seg, mode="full")[frame - 1:]
        if ac[0] <= 0:
            continue
        ac = ac / ac[0]
        if lo >= len(ac) - 1:
            continue
        lag = lo + int(np.argmax(ac[lo:min(hi, len(ac) - 1)]))
        peak = ac[lag]
        if peak < 0.35:
            continue
        f0s.append(sr / lag)
    if not f0s:
        return 0.0, 0.0
    return float(np.median(f0s)), float(np.percentile(np.array(f0s), [10, 90]).mean())


def rms_db(x):
    r = np.sqrt(np.mean(x ** 2)) + 1e-9
    return 20 * np.log10(r)


def main():
    asr = {r["file"]: r for r in json.load(open(ASR, encoding="utf-8"))}
    rows = []
    for f in sorted(os.listdir(SRC)):
        if not f.lower().endswith(".m4a"):
            continue
        x, sr = load_wav(os.path.join(SRC, f))
        f0, _ = median_f0(x, sr)
        rec = asr.get(f, {})
        words = sum(len(s["text"].split()) for s in rec.get("segments", []))
        # 有效语音时长（用最早开始到最晚结束，减去大静音近似）
        segs = rec.get("segments", [])
        span = (segs[-1]["end"] - segs[0]["start"]) if segs else 0
        rows.append({"file": f, "f0": round(f0, 1), "words": words,
                     "span": round(span, 2), "wps": round(words / span, 2) if span else 0,
                     "db": round(rms_db(x), 1)})
    f0s = [r["f0"] for r in rows if r["f0"] > 0]
    wps = [r["wps"] for r in rows if r["wps"] > 0.5]
    print(f"files={len(rows)}  F0 median={np.median(f0s):.1f}Hz  range={min(f0s):.0f}-{max(f0s):.0f}")
    print(f"语速 median={np.median(wps):.2f} words/s ({np.median(wps)*60:.0f} wpm)")
    print(f"响度 median={np.median([r['db'] for r in rows]):.1f} dBFS")
    for r in rows:
        print(f"{r['file']:<22} f0={r['f0']:>6.1f} wps={r['wps']:>4.2f} words={r['words']:>3} db={r['db']:>6.1f}")
    json.dump(rows, open(r"C:\Users\-\Desktop\冰川信使海外版\_tools\_voice_profile.json", "w",
                         encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
