# -*- coding: utf-8 -*-
"""把去混响后的 49 条真人配音放进工程：
旧版(带房间混响)先备份到 _human_v1_backup，再覆盖 en/、public/voice/en、dist-national/voice/en。
不动 _aria_backup（那里是旧 Aria AI 音色的备份）。
"""
import hashlib
import os
import shutil

BASE = r"C:\Users\-\Desktop\冰川信使海外版"
STAGE = os.path.join(BASE, r"_tools\_human_vo_dry")
EN = os.path.join(BASE, r"output\voice-overs\en")
BK = os.path.join(EN, "_human_v1_backup")
PUB = os.path.join(BASE, r"glacier-messenger-h5\public\voice\en")
DIST = os.path.join(BASE, r"glacier-messenger-h5\dist-national\voice\en")


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
        if os.path.isdir(DIST):
            shutil.copy2(s, os.path.join(DIST, f))
        replaced += 1
    bad = [f for f in files
           if not (md5(os.path.join(STAGE, f)) == md5(os.path.join(EN, f)) == md5(os.path.join(PUB, f)))]
    print("备份", backed, "替换", replaced, "校验不一致", bad)
    print("en:", len([x for x in os.listdir(EN) if x.startswith("VO-")]),
          "public:", len([x for x in os.listdir(PUB) if x.startswith("VO-")]),
          "dist:", len([x for x in os.listdir(DIST) if x.startswith("VO-")]) if os.path.isdir(DIST) else 0,
          "备份:", len(os.listdir(BK)))


if __name__ == "__main__":
    main()
