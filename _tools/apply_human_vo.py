# -*- coding: utf-8 -*-
"""把 mp3/*.m4a 里的真人录音切成 49 条 VO，统一响度与格式，输出到 staging。

规则：
  1) VAD 切出语音段（-40dB / 0.22s），丢弃 < 0.4s 的噪声段；
  2) 若首段 < 0.7s 且与后段间隔 > 0.6s，视为句首杂音丢弃；
  3) 其余段合并成一条（句内停顿保留）；
  4) 两端各留 0.12s / 0.18s 余量，loudnorm 两遍归一到 -21 LUFS / -1.5 dBTP；
  5) silenceremove 去首尾静音，输出 24kHz 单声道 48kbps mp3（与工程现有规格一致）。
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vo_vad_check import segments  # noqa: E402
import gen_fill_en as G  # noqa: E402
import vo_match_en as V  # noqa: E402

BASE = r"C:\Users\-\Desktop\冰川信使海外版"
SRC_DIR = os.path.join(BASE, "mp3")
OUT_DIR = os.path.join(BASE, r"_tools\_human_vo")
REPORT = os.path.join(BASE, r"_tools\_human_vo_report.json")
FFMPEG = r"D:\ai\VideoLingo\ffmpeg\bin\ffmpeg.exe"

# 自动匹配未过阈值的 4 条（已人工核对内容一致）
MANUAL = {
    "VO-016": "10月22日 7.m4a",
    "VO-019": "10月22日 11.m4a",
    "VO-030": "10月27日 8(1).m4a",
    "VO-052": "10月27日 31.m4a",
}

TARGET_I = -21.0
TARGET_TP = -1.5
TARGET_LRA = 11.0

# 人工修正：VO-001 录音里 "Everest Alarm" 念了两遍（1.0s 语音 + 0.3s 停顿 + 0.9s 语音），
# 取第二遍，避免开场标题重复。
OVERRIDE = {"VO-001": (1.62, 2.80)}


def build_map():
    cov = json.load(open(os.path.join(BASE, r"_tools\_vo_coverage_en.json"), encoding="utf-8"))["matches"]
    m = {}
    for vid, info in cov.items():
        if vid in G.DONE:
            m[vid] = info["file"]
    for vid, f in MANUAL.items():
        m[vid] = f
    missing = sorted(set(G.DONE) - set(m))
    assert not missing, f"仍有未定位的已录条目: {missing}"
    # 一个文件只对应一条
    dup = {}
    for vid, f in m.items():
        dup.setdefault(f, []).append(vid)
    for f, vids in dup.items():
        assert len(vids) == 1, f"{f} 被分配给多条: {vids}"
    return m


def pick_span(path):
    """返回 (start, end, 说明)"""
    dur, segs, _ = segments(path, noise="-40dB", d=0.22)
    segs = [(s, e) for s, e in segs if e - s >= 0.4]
    assert segs, "没有检测到语音"
    note = []
    if len(segs) >= 2 and (segs[0][1] - segs[0][0]) < 0.7 and (segs[1][0] - segs[0][1]) > 0.6:
        note.append("丢弃句首短杂音%.2fs" % (segs[0][1] - segs[0][0]))
        segs = segs[1:]
    if len(segs) == 1:
        note.append("单段")
    else:
        note.append("合并%d段" % len(segs))
    start = max(0.0, segs[0][0] - 0.06)
    end = min(dur, segs[-1][1] + 0.10)
    return start, end, "; ".join(note)


def loudnorm_measure(path, start, end):
    af = "loudnorm=I=%s:TP=%s:LRA=%s:print_format=json" % (TARGET_I, TARGET_TP, TARGET_LRA)
    cmd = [FFMPEG, "-hide_banner", "-nostats", "-i", path, "-ss", "%.3f" % start, "-to", "%.3f" % end,
           "-af", af, "-f", "null", "-"]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    txt = r.stderr
    i = txt.rfind("{")
    j = txt.rfind("}")
    data = json.loads(txt[i:j + 1])
    return data


def render(path, start, end, meas, out):
    # 边界已由 VAD 给出，这里不再做二次静音裁剪（silenceremove 会误伤轻辅音起句）
    af = (
        "loudnorm=I=%s:TP=%s:LRA=%s:measured_I=%s:measured_TP=%s:measured_LRA=%s:"
        "measured_thresh=%s:offset=%s:linear=true,"
        "aresample=24000"
    ) % (
        TARGET_I, TARGET_TP, TARGET_LRA,
        meas["input_i"], meas["input_tp"], meas["input_lra"],
        meas["input_thresh"], meas["target_offset"],
    )
    cmd = [FFMPEG, "-y", "-v", "error", "-i", path, "-ss", "%.3f" % start, "-to", "%.3f" % end,
           "-af", af, "-ac", "1", "-ar", "24000", "-c:a", "libmp3lame", "-b:a", "48k", out]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-400:])


def probe_dur(path):
    r = subprocess.run([FFMPEG.replace("ffmpeg.exe", "ffprobe.exe"), "-v", "error",
                        "-show_entries", "format=duration", "-of", "csv=p=0", path],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    m = build_map()
    print("待处理", len(m), "条")
    rows = []
    for vid in sorted(m):
        src = os.path.join(SRC_DIR, m[vid])
        if vid in OVERRIDE:
            start, end = OVERRIDE[vid]
            note = "人工指定(取第二遍)"
        else:
            start, end, note = pick_span(src)
        meas = loudnorm_measure(src, start, end)
        out = os.path.join(OUT_DIR, vid + ".mp3")
        render(src, start, end, meas, out)
        dur = probe_dur(out)
        rows.append({"id": vid, "src": m[vid], "start": round(start, 2), "end": round(end, 2),
                     "orig_i": float(meas["input_i"]), "dur": round(dur, 2), "note": note})
        print(f"{vid}  {m[vid]:<20} {start:6.2f}-{end:6.2f}  原始{meas['input_i']:>6}LUFS  "
              f"输出{dur:5.2f}s  {note}")
    json.dump(rows, open(REPORT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n合计 %.1fs" % sum(r["dur"] for r in rows))


if __name__ == "__main__":
    main()
