# -*- coding: utf-8 -*-
"""对用户自录配音做静音切分，估算每个文件里的"句数"，用于判断是否配完。"""
import subprocess, re, os, json, sys

FFMPEG = r"D:\ai\VideoLingo\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"D:\ai\VideoLingo\ffmpeg\bin\ffprobe.exe"

def dur(p):
    out = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", p], capture_output=True, text=True).stdout.strip()
    try:
        return float(out)
    except:
        return 0.0

def segments(p, noise="-35dB", d=0.35):
    r = subprocess.run([FFMPEG, "-hide_banner", "-nostats", "-i", p,
                        "-af", f"silencedetect=noise={noise}:d={d}", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    log = r.stderr
    D = dur(p)
    starts = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", log)]
    # 静音区间
    sil = []
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else D
        sil.append((s, e))
    # 语音区间 = 补集
    speech = []
    cur = 0.0
    for s, e in sil:
        if s - cur > 0.15:
            speech.append((cur, s))
        cur = max(cur, e)
    if D - cur > 0.15:
        speech.append((cur, D))
    return D, speech, sil

def main(folder):
    files = sorted([f for f in os.listdir(folder) if f.lower().endswith((".m4a", ".mp3", ".wav", ".aac"))])
    rows = []
    total_speech = 0.0
    total_seg = 0
    for f in files:
        p = os.path.join(folder, f)
        D, sp, sil = segments(p)
        sp_dur = sum(e - s for s, e in sp)
        total_speech += sp_dur
        total_seg += len(sp)
        rows.append({
            "file": f, "dur": round(D, 2), "speech_dur": round(sp_dur, 2),
            "segments": len(sp),
            "seg_lens": [round(e - s, 1) for s, e in sp][:40],
            "leading_sil": round(sp[0][0], 2) if sp else round(D, 2),
            "trailing_sil": round(D - sp[-1][1], 2) if sp else 0,
        })
    print(f"files={len(files)}  total_dur={sum(r['dur'] for r in rows):.1f}s  speech={total_speech:.1f}s  speech_segments={total_seg}")
    for r in rows:
        print(f"{r['file']:<24} dur={r['dur']:>6.1f} speech={r['speech_dur']:>6.1f} segs={r['segments']:>2} "
              f"lead={r['leading_sil']:>5.2f} tail={r['trailing_sil']:>5.2f} lens={r['seg_lens']}")
    with open(os.path.join(folder, "_vad_report.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\-\Desktop\冰川信使海外版\mp3")
