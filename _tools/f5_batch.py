# -*- coding: utf-8 -*-
"""F5-TTS 零样本克隆：用用户录音音色生成全部中文配音。

策略：
  1. 每条先用 speed=1.0 生成，测时长；
  2. 与现用版本（_zh_stage，已与画面节奏对齐）时长比较，偏差 >12% 则按比例重生成一次；
  3. 统一 loudnorm -21 LUFS / 24kHz mono 48kbps 输出到 _f5_stage。

用法：python f5_batch.py [--only VO-001,VO-002] [--sample N]
"""
import argparse
import os
import subprocess
import sys
import time

BASE = r"C:\Users\-\Desktop\冰川信使海外版"
sys.path.insert(0, os.path.join(BASE, "_tools"))
from zh_gen import clean, load_script, loudnorm_measure, post  # noqa: E402

REF_WAV = os.path.join(BASE, r"_tools\ref_clone.wav")
REF_TEXT = "雪暴冰刃的尾巴焦躁地拍打着地面，黄牛镇的青铜鼻环在月光下泛着冷光。"
CKPT = r"D:\ai\models\F5TTS_v1_Base\model_1250000.safetensors"
VOCAB = r"D:\ai\models\F5TTS_v1_Base\vocab.txt"
VOCODER = r"D:\ai\models\vocos-mel-24khz"
OUT = os.path.join(BASE, r"_tools\_f5_stage")
OLD = os.path.join(BASE, r"_tools\_zh_stage")
FFPROBE = r"D:\ai\VideoLingo\ffmpeg\bin\ffprobe.exe"

for k in ("HTTPS_PROXY", "HTTP_PROXY", "https_proxy", "http_proxy", "ALL_PROXY", "all_proxy"):
    os.environ.pop(k, None)
os.environ["NO_PROXY"] = "*"

from f5_tts.api import F5TTS  # noqa: E402


def dur(p):
    r = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", p], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--sample", type=int, default=0)
    a = ap.parse_args()

    rows = [r for r in load_script() if "不配音" not in r["role"]]
    if a.only:
        want = set(a.only.split(","))
        rows = [r for r in rows if r["id"] in want]
    if a.sample:
        rows = rows[: a.sample]

    os.makedirs(OUT, exist_ok=True)
    print(f"loading model, {len(rows)} lines ...", flush=True)
    f5 = F5TTS(model="F5TTS_v1_Base", ckpt_file=CKPT, vocab_file=VOCAB,
               vocoder_local_path=VOCODER)
    print("model ready", flush=True)

    done = 0
    for r in rows:
        vid = r["id"]
        text = clean(r["text"]).replace("…", "。")
        raw = os.path.join(OUT, f"{vid}_raw.wav")
        old_d = dur(os.path.join(OLD, vid + ".mp3"))
        t0 = time.time()
        try:
            f5.infer(ref_file=REF_WAV, ref_text=REF_TEXT, gen_text=text,
                     file_wave=raw, speed=1.0, seed=0,
                     show_info=lambda *x, **k: None, progress=None)
            d1 = dur(raw)
            if old_d > 0 and d1 > 0 and abs(d1 - old_d) / old_d > 0.12:
                sp = max(0.85, min(1.45, d1 / old_d))
                f5.infer(ref_file=REF_WAV, ref_text=REF_TEXT, gen_text=text,
                         file_wave=raw, speed=sp, seed=0,
                         show_info=lambda *x, **k: None, progress=None)
                d2 = dur(raw)
                print(f"  {vid} speed->{sp:.2f} {d1:.2f}->{d2:.2f}s (target {old_d:.2f})", flush=True)
            m = loudnorm_measure(raw)
            post(raw, os.path.join(OUT, vid + ".mp3"), m)
            done += 1
            print(f"{done}/{len(rows)} {vid} {dur(os.path.join(OUT, vid + '.mp3')):.2f}s "
                  f"({time.time()-t0:.1f}s) {text[:14]}", flush=True)
        except Exception as e:
            print(f"FAIL {vid} {type(e).__name__} {str(e)[:60]}", flush=True)
    print("ALL DONE", done)


if __name__ == "__main__":
    main()
