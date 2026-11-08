# -*- coding: utf-8 -*-
"""为未录制的英文配音条目生成 AI 语音（edge-tts，音色与语速对齐用户自录基线）。

基线（由 49 条自录样本测得）：
  - 基频中位 166.7 Hz  -> 最接近的音色 en-US-EmmaNeural (168.4 Hz)
  - 净语速比 Emma 默认慢约 1.45 倍 -> rate = -25%
  - 输出响度对齐现有 AI 音轨 -21 LUFS / mp3 24k mono 48kbps
"""
import asyncio, os, sys, json, subprocess, time, re

sys.path.insert(0, r"C:\Users\-\Desktop\冰川信使海外版\_tools")
os.environ["HTTPS_PROXY"] = os.environ["HTTP_PROXY"] = "http://127.0.0.1:52957"
os.environ["https_proxy"] = os.environ["http_proxy"] = "http://127.0.0.1:52957"
import edge_tts  # noqa: E402

BASE = r"C:\Users\-\Desktop\冰川信使海外版"
SCRIPT = os.path.join(BASE, r"output\voice-script\配音脚本-英文.txt")
VO_DIR = os.path.join(BASE, r"output\voice-overs\en")
BACKUP = os.path.join(VO_DIR, "_aria_backup")
RAW = os.path.join(BASE, r"_tools\_gen_raw")
REPORT = os.path.join(BASE, r"output\voice-overs\_fill_report_en.json")
FFMPEG = r"D:\ai\VideoLingo\ffmpeg\bin\ffmpeg.exe"

VOICE = "en-US-EmmaNeural"
RATE = "-25%"

# 用户已录的 49 条
DONE = set("""VO-001 VO-003 VO-004 VO-005 VO-006 VO-007 VO-008 VO-010 VO-011
VO-012 VO-013 VO-014 VO-015 VO-016 VO-017 VO-018 VO-019 VO-020 VO-021 VO-022
VO-023 VO-024 VO-025 VO-026 VO-027 VO-028 VO-029 VO-030 VO-031 VO-033 VO-035 VO-036
VO-037 VO-038 VO-040 VO-041 VO-042 VO-043 VO-044 VO-046 VO-047 VO-048 VO-049 VO-050
VO-051 VO-052 VO-053 VO-054 VO-055""".split())


def load_script():
    rows, cur = [], ""
    for line in open(SCRIPT, encoding="utf-8"):
        s = line.strip()
        m = re.match(r"^【(第\d章[^】]*)】", s)
        if m:
            cur = m.group(1)
        m2 = re.match(r"^(VO-(\d+))\s+\[([^\]]+)\]\s*(.*)$", s)
        if m2 and "不配音" not in m2.group(3):
            rows.append({"id": m2.group(1), "n": int(m2.group(2)), "ch": cur,
                         "role": m2.group(3), "text": m2.group(4)})
    return rows


def clean_text(t):
    """去掉给演员看的舞台提示、emoji 与方括号补注"""
    t = re.sub(r"\([^)]*\)", " ", t)          # 括号内的动作提示
    t = re.sub(r"（[^）]*）", " ", t)
    t = re.sub(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]", " ", t)  # emoji
    t = t.replace("—", ", ").replace("≥", " at least ")
    t = t.replace("°C", " degrees Celsius").replace("°", " degrees ")
    t = re.sub(r"[\u2212-](?=\d)", " minus ", t)
    t = re.sub(r"(\d)\s*%", r"\1 percent", t)
    t = re.sub(r"\s+,", ",", t)
    t = re.sub(r"\s+", " ", t).strip(" ,")
    return t


async def synth(text, path, tries=5):
    for i in range(tries):
        try:
            await edge_tts.Communicate(text, VOICE, rate=RATE).save(path)
            if os.path.getsize(path) > 3000:
                return True
        except Exception as e:
            print(f"    retry {i+1} {type(e).__name__}", flush=True)
        await asyncio.sleep(2 + i * 3)
    return False


def post(raw, out):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    r = subprocess.run([FFMPEG, "-y", "-v", "error", "-i", raw,
                        "-af", "loudnorm=I=-21:TP=-1.5:LRA=11",
                        "-ac", "1", "-ar", "24000", "-c:a", "libmp3lame", "-b:a", "48k", out],
                       capture_output=True, text=True)
    return r.returncode == 0


async def main():
    os.makedirs(RAW, exist_ok=True)
    os.makedirs(BACKUP, exist_ok=True)
    script = load_script()
    todo = [r for r in script if r["id"] not in DONE]
    print(f"需生成 {len(todo)} 条 / 脚本共 {len(script)} 条", flush=True)

    t0 = time.time()
    ok, failed, skipped = [], [], []
    for i, r in enumerate(todo, 1):
        out = os.path.join(VO_DIR, r["id"] + ".mp3")
        if os.path.exists(out) and os.path.getsize(out) > 3000 and os.path.exists(
                os.path.join(BACKUP, r["id"] + ".mp3")):
            skipped.append(r["id"])
            continue
        text = clean_text(r["text"])
        raw = os.path.join(RAW, r["id"] + ".mp3")
        if not await synth(text, raw):
            failed.append(r["id"])
            print(f"[{i}/{len(todo)}] {r['id']} FAILED", flush=True)
            continue
        if os.path.exists(out) and not os.path.exists(os.path.join(BACKUP, r["id"] + ".mp3")):
            subprocess.run(["cp", out, os.path.join(BACKUP, r["id"] + ".mp3")])
        if not post(raw, out):
            failed.append(r["id"])
            print(f"[{i}/{len(todo)}] {r['id']} ffmpeg FAILED", flush=True)
            continue
        ok.append(r["id"])
        if i % 5 == 0 or i == len(todo):
            print(f"[{i}/{len(todo)}] {r['id']} ok  ({time.time()-t0:.0f}s)", flush=True)
        await asyncio.sleep(0.35)

    print(f"\n完成 {len(ok)} / 跳过 {len(skipped)} / 失败 {len(failed)}  用时 {time.time()-t0:.0f}s")
    if failed:
        print("失败：", " ".join(failed))
    json.dump({"voice": VOICE, "rate": RATE, "generated": ok, "failed": failed,
               "skipped": skipped, "at": time.strftime("%Y-%m-%d %H:%M:%S")},
              open(REPORT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    asyncio.run(main())
