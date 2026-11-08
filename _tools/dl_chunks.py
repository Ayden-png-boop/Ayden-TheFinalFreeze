# -*- coding: utf-8 -*-
"""通用分块下载：每块独立重试到精确字节，最后拼接。适合不稳定镜像。

用法：python dl_chunks.py <url> <out> [chunk_mb]
"""
import os
import sys
import time

import requests

URL = sys.argv[1]
OUT = sys.argv[2]
CHUNK = int(float(sys.argv[3]) * (1 << 20)) if len(sys.argv) > 3 else (8 << 20)


def sess():
    s = requests.Session()
    s.trust_env = False
    return s


def main():
    s = sess()
    r0 = s.get(URL, headers={"Range": "bytes=0-0"}, timeout=30)
    total = int(r0.headers["content-range"].split("/")[-1])
    r0.close()
    print("total", total, flush=True)
    n = (total + CHUNK - 1) // CHUNK
    parts = []
    for i in range(n):
        start = i * CHUNK
        end = min(start + CHUNK - 1, total - 1)
        expect = end - start + 1
        part = OUT + f".ck{i:03d}"
        parts.append((part, expect))
        for attempt in range(10):
            cur = os.path.getsize(part) if os.path.exists(part) else 0
            if cur > expect:
                with open(part, "wb") as f:
                    f.truncate(0)
                cur = 0
            if cur == expect:
                break
            try:
                with s.get(URL, headers={"Range": f"bytes={start+cur}-{end}"},
                           stream=True, timeout=(15, 30)) as r:
                    if r.status_code not in (200, 206):
                        raise RuntimeError(f"status {r.status_code}")
                    with open(part, "ab") as f:
                        for c in r.iter_content(1 << 20):
                            f.write(c)
            except Exception as e:
                print(f"  ck{i} retry{attempt} {type(e).__name__}", flush=True)
                s = sess()
                time.sleep(1.5)
        ok = os.path.exists(part) and os.path.getsize(part) == expect
        print(f"  ck{i+1}/{n} {'ok' if ok else 'FAIL'}", flush=True)
        if not ok:
            raise SystemExit(f"chunk {i} failed")
    with open(OUT, "wb") as f:
        for part, size in parts:
            assert os.path.getsize(part) == size
            with open(part, "rb") as p:
                while True:
                    b = p.read(8 << 20)
                    if not b:
                        break
                    f.write(b)
    print("MERGED", os.path.getsize(OUT), flush=True)
    for part, _ in parts:
        try:
            os.remove(part)
        except OSError:
            pass


if __name__ == "__main__":
    main()
