# -*- coding: utf-8 -*-
"""把 staging 的新中文配音放进工程：原 zh 文件备份 → 覆盖 → 同步 public/voice/zh 与 dist-national/voice/zh。"""
import hashlib
import os
import shutil

BASE = r"C:\Users\-\Desktop\冰川信使海外版"
STAGE = os.path.join(BASE, r"_tools\_f5_stage")
ZH = os.path.join(BASE, r"output\voice-overs\zh")
BK = os.path.join(ZH, "_backup_xiaoxiao53")
PUB = os.path.join(BASE, r"glacier-messenger-h5\public\voice\zh")
DIST = os.path.join(BASE, r"glacier-messenger-h5\dist-national\voice\zh")


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def main():
    files = sorted(f for f in os.listdir(STAGE) if f.startswith("VO-") and f.endswith(".mp3"))
    print("待替换", len(files))
    assert len(files) == 115, len(files)
    os.makedirs(BK, exist_ok=True)
    for d in (PUB, DIST):
        os.makedirs(d, exist_ok=True)

    backed = 0
    for f in files:
        s = os.path.join(STAGE, f)
        d = os.path.join(ZH, f)
        b = os.path.join(BK, f)
        if os.path.exists(d) and not os.path.exists(b):
            shutil.copy2(d, b)
            backed += 1
        shutil.copy2(s, d)
        shutil.copy2(s, os.path.join(PUB, f))
        shutil.copy2(s, os.path.join(DIST, f))

    bad = [f for f in files
           if not (md5(os.path.join(STAGE, f)) == md5(os.path.join(ZH, f))
                   == md5(os.path.join(PUB, f)) == md5(os.path.join(DIST, f)))]
    print("备份", backed, "替换", len(files), "校验不一致", bad)
    for name, p in (("output/zh", ZH), ("public/zh", PUB), ("dist/zh", DIST)):
        print(f"  {name}: {len([x for x in os.listdir(p) if x.startswith('VO-')])} 个")


if __name__ == "__main__":
    main()
