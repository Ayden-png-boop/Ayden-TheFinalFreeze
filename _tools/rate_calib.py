# -*- coding: utf-8 -*-
"""用已录的 3 条真实语速，反推 edge-tts 的 rate 参数。"""
import asyncio, os, sys, json
sys.path.insert(0, r"C:\Users\-\Desktop\冰川信使海外版\_tools")
os.environ["HTTPS_PROXY"] = os.environ["HTTP_PROXY"] = "http://127.0.0.1:52957"
os.environ["https_proxy"] = os.environ["http_proxy"] = "http://127.0.0.1:52957"
import edge_tts  # noqa: E402
from voice_profile import load_wav, median_f0  # noqa: E402

VOICE = "en-US-EmmaNeural"
OUT = r"C:\Users\-\Desktop\冰川信使海外版\_tools\_calib"
# (VO编号, 用户录音净语音秒数, 台词)
SAMPLES = [
    ("VO-010", 10.7, "The flock snaps into arrow formation — then is swallowed by a rose-coloured mass of humid heat. Visibility drops to three metres in an instant."),
    ("VO-013", 9.7, "Torn prayer flags crack in the cold wind; moonlight sifts through broken walls and lays mottled shadows across the ruins."),
    ("VO-035", 8.5, "Xueyi's flock threads between the skyscrapers of Dubai, where the mirrored glass throws back a lethal band of glare."),
]


def speech_sec(path):
    """用 ffmpeg silencedetect 取净语音秒数"""
    import subprocess, re
    r = subprocess.run([r"D:\ai\VideoLingo\ffmpeg\bin\ffmpeg.exe", "-hide_banner", "-nostats", "-i", path,
                        "-af", "silencedetect=noise=-35dB:d=0.3", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    x, sr = load_wav(path)
    D = len(x) / sr
    st = [float(v) for v in re.findall(r"silence_start: ([0-9.]+)", r.stderr)]
    en = [float(v) for v in re.findall(r"silence_end: ([0-9.]+)", r.stderr)]
    sil = [(st[i], en[i] if i < len(en) else D) for i in range(len(st))]
    sp = 0.0
    cur = 0.0
    for a, b in sil:
        if a - cur > 0.1:
            sp += a - cur
        cur = max(cur, b)
    if D - cur > 0.1:
        sp += D - cur
    return sp, D


async def main():
    os.makedirs(OUT, exist_ok=True)
    ratios = []
    for vid, user_sec, text in SAMPLES:
        p = os.path.join(OUT, vid + "_r0.mp3")
        await edge_tts.Communicate(text, VOICE).save(p)
        sp, D = speech_sec(p)
        ratio = user_sec / sp
        ratios.append(ratio)
        print(f"{vid}: 用户净{user_sec}s  vs  Emma净{sp:.2f}s -> 需放慢 x{ratio:.2f}")
        await asyncio.sleep(0.5)
    r = sum(ratios) / len(ratios)
    rate_pct = (1 / r - 1) * 100
    print(f"\n平均比例 x{r:.3f}  =>  rate ≈ {rate_pct:.0f}%")

asyncio.run(main())
