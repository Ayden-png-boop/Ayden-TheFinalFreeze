# -*- coding: utf-8 -*-
"""把 staging 的 49 条真人配音放进工程：原文件备份 → 覆盖 en/ → 同步 public/voice/en。"""
import hashlib
import json
import os
import shutil

BASE = r"C:\Users\-\Desktop\冰川信使海外版"
STAGE = os.path.join(BASE, r"_tools\_human_vo")
EN = os.path.join(BASE, r"output\voice-overs\en")
BK = os.path.join(EN, "_aria_backup")
PUB = os.path.join(BASE, r"glacier-messenger-h5\public\voice\en")


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def main():
    os.makedirs(BK, exist_ok=True)
    files = sorted(f for f in os.listdir(STAGE) if f.startswith("VO-") and f.endswith(".mp3"))
    assert len(files) == 49, len(files)
    backed = replaced = 0
    for f in files:
        s = os.path.join(STAGE, f)
        d = os.path.join(EN, f)
        b = os.path.join(BK, f)
        if os.path.exists(d) and not os.path.exists(b):
            shutil.copy2(d, b)
            backed += 1
        shutil.copy2(s, d)
        shutil.copy2(s, os.path.join(PUB, f))
        replaced += 1
    # 校验
    bad = [f for f in files if not (md5(os.path.join(STAGE, f)) == md5(os.path.join(EN, f)) == md5(os.path.join(PUB, f)))]
    print("备份", backed, "替换", replaced, "校验不一致", bad)
    print("en 目录文件数", len([x for x in os.listdir(EN) if x.startswith("VO-")]),
          "public 目录文件数", len([x for x in os.listdir(PUB) if x.startswith("VO-")]))
    print("备份目录文件数", len(os.listdir(BK)))


if __name__ == "__main__":
    main()
