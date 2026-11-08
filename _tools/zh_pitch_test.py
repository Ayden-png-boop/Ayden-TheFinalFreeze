# -*- coding: utf-8 -*-
"""测试 XiaoxiaoNeural 不同 pitch 档位的基频与时长，判断下压幅度是否自然可用。"""
import asyncio, os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voice_profile import load_wav, median_f0
for k in ("HTTPS_PROXY", "HTTP_PROXY", "https_proxy", "http_proxy"):
    os.environ.pop(k, None)
import edge_tts

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_zh_pick")
os.makedirs(OUT, exist_ok=True)
TEST = "晨光照在冰棱上折射出冷冽的蓝，忽然一声冰裂声撕裂寂静。"
FFPROBE = r"D:\ai\VideoLingo\ffmpeg\bin\ffprobe.exe"


def dur(p):
    r = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", p], capture_output=True, text=True)
    return float(r.stdout.strip())


async def main():
    for voice in ["zh-CN-XiaoxiaoNeural", "zh-CN-XiaoyiNeural"]:
        for pitch in ["-20Hz", "-30Hz", "-40Hz", "-50Hz"]:
            p = os.path.join(OUT, f"{voice}_{pitch}.mp3")
            try:
                await edge_tts.Communicate(TEST, voice, pitch=pitch).save(p)
            except Exception as e:
                print(voice, pitch, "FAIL", type(e).__name__)
                continue
            x, sr = load_wav(p)
            f0, _ = median_f0(x, sr)
            d = dur(p)
            print(f"{voice:<26} pitch={pitch:<6} F0={f0:6.1f}Hz  {d:5.2f}s  {26/d:4.2f}字/秒")
            await asyncio.sleep(0.3)


asyncio.run(main())
