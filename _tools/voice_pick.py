# -*- coding: utf-8 -*-
"""在 edge-tts 英文音色中挑出与用户录音音高/语速最接近的一个。"""
import asyncio, os, sys, json, wave, subprocess, tempfile
import numpy as np

sys.path.insert(0, r"C:\Users\-\Desktop\冰川信使海外版\_tools")
from voice_profile import load_wav, median_f0

PROXY = "http://127.0.0.1:52957"
os.environ["HTTPS_PROXY"] = PROXY
os.environ["HTTP_PROXY"] = PROXY
os.environ["https_proxy"] = PROXY
os.environ["http_proxy"] = PROXY
import edge_tts  # noqa: E402

SENT = ("The flock snaps into arrow formation, then is swallowed by a rose-coloured "
        "mass of humid heat. Visibility drops to three metres in an instant.")
TARGET_F0 = 167.0
TARGET_WPM = 125.0

CANDIDATES = [
    "en-US-AriaNeural", "en-US-JennyNeural", "en-US-MichelleNeural", "en-US-AvaNeural",
    "en-US-EmmaNeural", "en-US-AnaNeural", "en-GB-SoniaNeural", "en-GB-LibbyNeural",
    "en-AU-NatashaNeural", "en-US-GuyNeural", "en-US-DavisNeural", "en-US-JasonNeural",
    "en-US-TonyNeural", "en-US-BrandonNeural", "en-US-ChristopherNeural", "en-US-EricNeural",
    "en-US-RogerNeural", "en-US-SteffanNeural", "en-US-AndrewNeural", "en-US-BrianNeural",
    "en-GB-RyanNeural", "en-GB-ThomasNeural", "en-AU-WilliamNeural",
]
OUTDIR = r"C:\Users\-\Desktop\冰川信使海外版\_tools\_voice_test"


async def synth(text, voice, path, rate="+0%"):
    c = edge_tts.Communicate(text, voice, rate=rate)
    await c.save(path)


def analyze(path):
    x, sr = load_wav(path)
    f0, _ = median_f0(x, sr)
    d = len(x) / sr
    return f0, d


async def main():
    os.makedirs(OUTDIR, exist_ok=True)
    words = len(SENT.split())
    res = []
    for v in CANDIDATES:
        p = os.path.join(OUTDIR, v + ".mp3")
        try:
            await synth(SENT, v, p)
        except Exception as e:
            print(f"{v:<26} FAIL {type(e).__name__}")
            continue
        f0, d = analyze(p)
        wpm = words / d * 60
        score = abs(f0 - TARGET_F0) / TARGET_F0 * 100
        res.append({"voice": v, "f0": round(f0, 1), "dur": round(d, 2), "wpm": round(wpm), "score": round(score, 1)})
        print(f"{v:<26} f0={f0:>6.1f}Hz dur={d:>5.2f}s wpm={wpm:>4.0f}")
        await asyncio.sleep(0.4)
    res.sort(key=lambda r: r["score"])
    print("\n=== 最接近 ===")
    for r in res[:6]:
        print(r)
    json.dump(res, open(os.path.join(OUTDIR, "_rank.json"), "w", encoding="utf-8"), indent=1)


asyncio.run(main())
