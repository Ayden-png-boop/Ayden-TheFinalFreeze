# -*- coding: utf-8 -*-
"""多线程分段续传下载 F5-TTS 模型（hf-mirror，绕系统代理）。

把「主文件已有字节之后」的剩余区间切成 N 段并行下载到 .partN，
全部到齐后按序拼接回主文件并校验总大小。
"""
import os
import threading
import time

import requests

URL = "https://modelscope.cn/models/AI-ModelScope/F5-TTS/resolve/master/F5TTS_v1_Base/model_1250000.safetensors"
OUT = r"D:\ai\models\F5TTS_v1_Base\model_1250000.safetensors"
N = 8

lock = threading.Lock()


def worker(s, idx, start, end):
    part = OUT + f".part{idx}"
    pos = os.path.getsize(part) if os.path.exists(part) else 0
    cur = start + pos
    while cur <= end:
        headers = {"Range": f"bytes={cur}-{end}"}
        try:
            with s.get(URL, stream=True, timeout=(20, 45), headers=headers) as r:
                r.raise_for_status()
                with open(part, "ab") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
                        cur += len(chunk)
        except Exception as e:
            time.sleep(2)
        with lock:
            print(f"part{idx}: {(cur - start)/1e6:.0f}/{(end - start + 1)/1e6:.0f} MB", flush=True)


def main():
    s = requests.Session()
    s.trust_env = False
    r0 = s.get(URL, headers={"Range": "bytes=0-0"}, timeout=30)
    cr = r0.headers.get("content-range", "")  # bytes 0-0/1348123456
    total = int(cr.split("/")[-1])
    r0.close()
    print("total", total)
    have = os.path.getsize(OUT) if os.path.exists(OUT) else 0
    # 校验已有文件：通过先下载尾段并比对（简单起见信任顺序追加，最后按大小校验）
    remain = total - have
    print("have", have, "remain", remain)
    if remain <= 0:
        print("complete")
        return
    seg = remain // N
    ranges = []
    b = have
    for i in range(N):
        e = have + seg * (i + 1) - 1 if i < N - 1 else total - 1
        ranges.append((b, e))
        b = e + 1
    threads = [threading.Thread(target=worker, args=(s, i, a, b2), daemon=True)
               for i, (a, b2) in enumerate(ranges)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    # 拼接
    with open(OUT, "ab") as f:
        for i in range(N):
            part = OUT + f".part{i}"
            size = os.path.getsize(part)
            expect = ranges[i][1] - ranges[i][0] + 1
            assert size == expect, f"part{i} size {size} != {expect}"
            with open(part, "rb") as p:
                while True:
                    buf = p.read(1 << 22)
                    if not buf:
                        break
                    f.write(buf)
    got = os.path.getsize(OUT)
    assert got == total, f"{got} != {total}"
    for i in range(N):
        os.remove(OUT + f".part{i}")
    print("MERGED OK", got)


if __name__ == "__main__":
    main()
