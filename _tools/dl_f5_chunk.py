# -*- coding: utf-8 -*-
"""按 32MB 分块下载 F5-TTS 模型：每块独立重试到精确字节数，最后顺序拼接并校验头。"""
import json
import os
import struct
import time

import requests

URL = "https://modelscope.cn/models/AI-ModelScope/F5-TTS/resolve/master/F5TTS_v1_Base/model_1250000.safetensors"
OUT = r"D:\ai\models\F5TTS_v1_Base\model_1250000.safetensors"
TOTAL = 1348435761
CHUNK = 32 << 20


def s_new():
    s = requests.Session()
    s.trust_env = False
    return s


def get_range(s, start, end, part):
    """下载 [start,end] 到 part 文件，直到精确长度。"""
    expect = end - start + 1
    for attempt in range(6):
        cur = os.path.getsize(part) if os.path.exists(part) else 0
        if cur > expect:
            with open(part, "wb") as f:
                f.truncate(0)
            cur = 0
        if cur == expect:
            return True
        try:
            with s.get(URL, headers={"Range": f"bytes={start+cur}-{end}"},
                       stream=True, timeout=(20, 45)) as r:
                if r.status_code not in (200, 206):
                    raise RuntimeError(f"status {r.status_code}")
                with open(part, "ab") as f:
                    for c in r.iter_content(4 << 20):
                        f.write(c)
        except Exception as e:
            print(f"  chunk {start//CHUNK} retry {attempt}: {type(e).__name__}", flush=True)
            time.sleep(2)
    return os.path.getsize(part) == expect if os.path.exists(part) else False


def main():
    s = s_new()
    parts = []
    n = (TOTAL + CHUNK - 1) // CHUNK
    for i in range(n):
        start = i * CHUNK
        end = min(start + CHUNK - 1, TOTAL - 1)
        part = OUT + f".ck{i:03d}"
        parts.append((part, end - start + 1))
        ok = get_range(s, start, end, part)
        print(f"chunk {i+1}/{n} {'ok' if ok else 'FAIL'} {os.path.getsize(part)/1e6:.0f}MB", flush=True)
        if not ok:
            # 换新 session 再战
            s = s_new()
            ok = get_range(s, start, end, part)
            if not ok:
                raise SystemExit(f"chunk {i} failed")
            print(f"chunk {i+1} recovered", flush=True)
    with open(OUT, "wb") as f:
        for part, size in parts:
            assert os.path.getsize(part) == size, part
            with open(part, "rb") as p:
                while True:
                    buf = p.read(8 << 20)
                    if not buf:
                        break
                    f.write(buf)
    got = os.path.getsize(OUT)
    assert got == TOTAL, f"{got} != {TOTAL}"
    with open(OUT, "rb") as f:
        hlen = struct.unpack("<Q", f.read(8))[0]
        hdr = json.loads(f.read(hlen))
    dend = max(v["data_offsets"][1] for k, v in hdr.items() if k != "__metadata__")
    assert 8 + hlen + dend == TOTAL, "header mismatch"
    print("MERGED OK", got, "tensors", len([k for k in hdr if k != "__metadata__"]))
    for part, _ in parts:
        try:
            os.remove(part)
        except OSError:
            pass


if __name__ == "__main__":
    main()
