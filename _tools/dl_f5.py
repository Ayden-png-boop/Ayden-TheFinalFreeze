# -*- coding: utf-8 -*-
"""断点续传下载 F5-TTS 模型（hf-mirror，绕系统代理）。"""
import os
import time

import requests

BASE = "https://modelscope.cn/models/AI-ModelScope/F5-TTS/resolve/master/F5TTS_v1_Base/"
DEST = r"D:\ai\models\F5TTS_v1_Base"
FILES = ["model_1250000.safetensors", "vocab.txt"]


def fetch(s, name):
    out = os.path.join(DEST, name)
    url = BASE + name
    while True:
        pos = os.path.getsize(out) if os.path.exists(out) else 0
        headers = {"Range": f"bytes={pos}-"} if pos else {}
        try:
            with s.get(url, stream=True, timeout=(20, 60), headers=headers) as r:
                if r.status_code == 416:
                    print("already complete", name)
                    return
                r.raise_for_status()
                total = pos + int(r.headers.get("content-length", 0))
                mode = "ab" if pos and r.status_code == 206 else "wb"
                if mode == "wb":
                    pos = 0
                done = pos
                with open(out, mode) as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
                        done += len(chunk)
                        if done // (100 << 20) != (done - len(chunk)) // (100 << 20):
                            print(f"{name} {done/1e6:.0f}/{total/1e6:.0f} MB", flush=True)
            if os.path.getsize(out) >= total:
                print("done", name, os.path.getsize(out))
                return
        except Exception as e:
            print("retry", name, type(e).__name__, os.path.getsize(out), flush=True)
            time.sleep(3)


def main():
    s = requests.Session()
    s.trust_env = False
    os.makedirs(DEST, exist_ok=True)
    for name in FILES:
        fetch(s, name)


if __name__ == "__main__":
    main()
