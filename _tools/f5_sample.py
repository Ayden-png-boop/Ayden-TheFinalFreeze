# -*- coding: utf-8 -*-
"""F5-TTS 零样本克隆试听样张：用用户 14.4s 录音做音色参考，生成 4 条台词。

用法：python f5_sample.py [ids]
"""
import os
import sys

BASE = r"C:\Users\-\Desktop\冰川信使海外版"
sys.path.insert(0, os.path.join(BASE, "_tools"))
from zh_gen import clean, load_script, loudnorm_measure, post  # noqa: E402

REF_WAV = os.path.join(BASE, r"_tools\ref_clone.wav")
REF_TEXT = "雪暴冰刃的尾巴焦躁地拍打着地面，黄牛镇的青铜鼻环在月光下泛着冷光。"
CKPT = r"D:\ai\models\F5TTS_v1_Base\model_1250000.safetensors"
VOCAB = r"D:\ai\models\F5TTS_v1_Base\vocab.txt"
OUT = os.path.join(BASE, r"_tools\_f5")

IDS = sys.argv[1].split(",") if len(sys.argv) > 1 else ["VO-001", "VO-030", "VO-060", "VO-090"]

for k in ("HTTPS_PROXY", "HTTP_PROXY", "https_proxy", "http_proxy", "ALL_PROXY", "all_proxy"):
    os.environ.pop(k, None)
os.environ["NO_PROXY"] = "*"
os.environ["HF_HUB_OFFLINE"] = "1"

import torchaudio  # noqa: E402
from f5_tts.api import F5TTS  # noqa: E402

print("loading model ...", flush=True)
f5 = F5TTS(model="F5TTS_v1_Base", ckpt_file=CKPT, vocab_file=VOCAB, ode_method="euler", vocoder_local_path=r"D://ai//models//vocos-mel-24khz")
print("model ready", flush=True)

rows = {r["id"]: r for r in load_script()}
os.makedirs(OUT, exist_ok=True)

for vid in IDS:
    text = clean(rows[vid]["text"])
    # F5-TTS 生成文本里不要长停顿符号
    text = text.replace("…", "。").replace("，", "，")
    raw = os.path.join(OUT, f"{vid}_raw.wav")
    f5.infer(
        ref_file=REF_WAV, ref_text=REF_TEXT, gen_text=text,
        file_wave=raw, speed=1.0, seed=None, show_info=print,
    )
    m = loudnorm_measure(raw)
    post(raw, os.path.join(OUT, f"{vid}.mp3"), m)
    print("ok", vid, text[:20], flush=True)
print("ALL DONE")
