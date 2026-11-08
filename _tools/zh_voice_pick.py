# -*- coding: utf-8 -*-
"""中文音色筛选：对候选 zh-CN 女声合成同一句，测基频与字速，挑最接近用户录音音色（166.7Hz）的。"""
import asyncio, os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voice_profile import load_wav, median_f0
import numpy as np

for k in ("HTTPS_PROXY", "HTTP_PROXY", "https_proxy", "http_proxy"):
    os.environ.pop(k, None)

import edge_tts

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_zh_pick")
os.makedirs(OUT, exist_ok=True)

TEST = "晨光照在冰棱上折射出冷冽的蓝，忽然一声冰裂声撕裂寂静。"
NCHAR = 26

CAND = [
    "zh-CN-XiaoxiaoNeural",
    "zh-CN-XiaoyiNeural",
    "zh-CN-XiaochenNeural",
    "zh-CN-XiaohanNeural",
    "zh-CN-XiaomengNeural",
    "zh-CN-XiaomoNeural",
    "zh-CN-XiaoruiNeural",
    "zh-CN-XiaoxuanNeural",
    "zh-CN-XiaoyanNeural",
    "zh-CN-XiaozhenNeural",
    "zh-CN-XiaoxiaoMultilingualNeural",
    "zh-CN-XiaochenMultilingualNeural",
]

FFPROBE = r"D:\ai\VideoLingo\ffmpeg\bin\ffprobe.exe"


def dur(p):
    r = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", p], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except Exception:
        return 0.0


async def main():
    rows = []
    for v in CAND:
        p = os.path.join(OUT, v + ".mp3")
        try:
            await edge_tts.Communicate(TEST, v).save(p)
        except Exception as e:
            print(f"{v:<42} FAIL {type(e).__name__}")
            continue
        x, sr = load_wav(p)
        f0, _ = median_f0(x, sr)
        d = dur(p)
        cps = NCHAR / max(d, 1e-6)
        rows.append((v, f0, d, cps))
        print(f"{v:<42} F0={f0:6.1f}Hz  {d:5.2f}s  {cps:4.2f}字/秒")
        await asyncio.sleep(0.3)
    print("\n目标 F0 = 166.7Hz（你的英文录音中位）")
    for v, f0, d, cps in sorted(rows, key=lambda r: abs(r[1] - 166.7)):
        print(f"  {abs(f0-166.7):6.1f}Hz差  {v:<42} {f0:6.1f}Hz {cps:4.2f}字/秒")


asyncio.run(main())
