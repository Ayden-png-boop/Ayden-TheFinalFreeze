# -*- coding: utf-8 -*-
"""中文版配音生成：清洗脚本文本 -> edge-tts 合成 -> 统一响度 -21 LUFS / 24k mono 48kbps。

用法：
  python zh_gen.py --dry          只打印清洗对照
  python zh_gen.py --sample 12    抽样 12 条生成到 _zh_stage，用于核语速
  python zh_gen.py                全量生成到 _zh_stage
"""
import argparse
import asyncio
import json
import os
import re
import subprocess
import sys

BASE = r"C:\Users\-\Desktop\冰川信使海外版"
SCRIPT = os.path.join(BASE, r"output\voice-script\配音脚本-中文.txt")
STAGE = os.path.join(BASE, r"_tools\_zh_stage")
RAW = os.path.join(BASE, r"_tools\_zh_raw")
FFMPEG = r"D:\ai\VideoLingo\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"D:\ai\VideoLingo\ffmpeg\bin\ffprobe.exe"

VOICE = "zh-CN-XiaoxiaoNeural"
PITCH = "-53Hz"      # 2026-11-01 新录音基线 161.6Hz（mp3 旧基线 166.7Hz 用 -40Hz）
RATE = "-5%"
TARGET_I = -21.0
TARGET_TP = -1.5
TARGET_LRA = 11.0

for k in ("HTTPS_PROXY", "HTTP_PROXY", "https_proxy", "http_proxy"):
    os.environ.pop(k, None)

import edge_tts  # noqa: E402


# ---------------- 文本解析 ----------------

def load_script():
    rows, ch = [], ""
    with open(SCRIPT, encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            m = re.match(r"^【(第\d+章[^】]*)】", s)
            if m:
                ch = m.group(1)
            m2 = re.match(r"^(VO-(\d+))\s+\[([^\]]+)\]\s*(.*)$", s)
            if m2:
                rows.append({
                    "id": m2.group(1), "n": int(m2.group(2)), "ch": ch,
                    "role": m2.group(3), "text": m2.group(4).strip(),
                })
    return rows


EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U00002B00-\U00002BFF"
    "\U0001F1E6-\U0001F1FF\uFE0F\u2190-\u21FF\u2300-\u23FF]"
)

ABBR = {
    "QTE": "Q T E", "HUD": "H U D", "CEO": "C E O", "IPCC": "I P C C",
    "SOS": "S O S", "GPS": "G P S", "G20": "G二十", "AI": "A I",
    "GDP": "G D P", "CO2": "二氧化碳", "PM2.5": "P M 2.5",
}


_CN_DIGIT = "零一二三四五六七八九"


def num2cn(s):
    """0-999 的整数与一位小数转中文读法，用于百分号后。"""
    if "." in s:
        a, b = s.split(".", 1)
        return num2cn(a) + "点" + "".join(_CN_DIGIT[int(c)] for c in b)
    n = int(s)
    if n < 10:
        return _CN_DIGIT[n]
    if n < 20:
        return "十" + (_CN_DIGIT[n % 10] if n % 10 else "")
    if n < 100:
        return _CN_DIGIT[n // 10] + "十" + (_CN_DIGIT[n % 10] if n % 10 else "")
    if n == 100:
        return "一百"
    if n < 1000:
        rest = n % 100
        head = _CN_DIGIT[n // 100] + "百"
        if rest == 0:
            return head
        if rest < 10:
            return head + "零" + _CN_DIGIT[rest]
        return head + num2cn(rest)
    return s


def clean(text):
    t = text
    t = EMOJI.sub("", t)
    # 圆括号内的表演提示 / 画面说明不朗读（「（可选）」属界面语义，保留）
    t = t.replace("（可选）", "，可选").replace("(可选)", "，可选")
    t = re.sub(r"（[^）]*）", "", t)
    t = re.sub(r"\([^)]*\)", "", t)
    # 破折号、省略号
    t = t.replace("——", "，").replace("—", "，").replace("–", "，")
    t = t.replace("……", "…").replace("...", "…")
    # 百分号（先负号/加号，再普通）；数字转中文读法，避免 TTS 念成英文
    t = re.sub(r"[−–-]\s*(\d+(?:\.\d+)?)\s*%", lambda m: "负百分之" + num2cn(m.group(1)), t)
    t = re.sub(r"\+\s*(\d+(?:\.\d+)?)\s*%", lambda m: "增加百分之" + num2cn(m.group(1)), t)
    t = re.sub(r"(\d+(?:\.\d+)?)\s*%", lambda m: "百分之" + num2cn(m.group(1)), t)
    # 比较符、单位
    t = re.sub(r"≥\s*(\d+(?:\.\d+)?)", r"大于等于\1", t)
    t = re.sub(r"≤\s*(\d+(?:\.\d+)?)", r"小于等于\1", t)
    t = t.replace("℃", "摄氏度").replace("°C", "摄氏度").replace("°", "度")
    # 英文缩写（前后不接英文字母时替换）
    for k in sorted(ABBR, key=len, reverse=True):
        t = re.sub(r"(?<![A-Za-z])" + re.escape(k) + r"(?![A-Za-z])", ABBR[k], t)
    # 数字与量词之间的空格
    t = re.sub(r"(\d)\s+([年月日号米秒分个座台条次天周倍度千百万元])", r"\1\2", t)
    # 符号
    t = re.sub(r"\s*\+\s*", "和", t).replace("=", "等于")
    t = t.replace("：", "，").replace(":", "，")
    t = t.replace("、", "，")
    # 收尾：标点整理
    t = re.sub(r"\s*，\s*", "，", t)
    t = re.sub(r"[，,]{2,}", "，", t)
    t = re.sub(r"。\s*，", "。", t)
    t = re.sub(r"([！？…])[，。]+", r"\1", t)
    # 引号、书名号紧跟的多余句号：「…！」」。 → 「…！」」
    t = re.sub(r"""([！？…])["”'\u2019]\s*[，。]+""", r"\1\"", t)
    # 汉字与汉字 / 汉字与数字之间的多余空格
    t = re.sub(r"(?<=[\u4e00-\u9fa5]) +(?=[\u4e00-\u9fa5\d])", "", t)
    t = re.sub(r"(?<=[\d%]) +(?=[\u4e00-\u9fa5])", "", t)
    t = re.sub(r"([\u4e00-\u9fa5])\s+([，。！？的地得])", r"\1\2", t)
    t = re.sub(r"\s+", " ", t).strip()
    t = t.strip("，, ")
    t = re.sub(r"，([。！？…])", r"\1", t)
    t = re.sub(r"，$", "。", t)
    # 结尾是引号/书名号时不再补句号（前面已有 ！？… 收束）
    if t and t[-1] not in "。！？…" and not t.endswith(('"', "”", "」", "』", "》")):
        t += "。"
    return t


# ---------------- 合成 ----------------

def probe_dur(p):
    r = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", p], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def loudnorm_measure(src):
    r = subprocess.run(
        [FFMPEG, "-hide_banner", "-nostats", "-i", src,
         "-af", "loudnorm=I=%s:TP=%s:LRA=%s:print_format=json" % (TARGET_I, TARGET_TP, TARGET_LRA),
         "-f", "null", "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S)
    d = json.loads(m.group(0))
    return {k: d[k] for k in ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset")}


def post(raw, out, meas):
    af = (
        "loudnorm=I=%s:TP=%s:LRA=%s:measured_I=%s:measured_TP=%s:measured_LRA=%s:"
        "measured_thresh=%s:offset=%s:linear=true,"
        "aresample=24000"
    ) % (TARGET_I, TARGET_TP, TARGET_LRA, meas["input_i"], meas["input_tp"],
         meas["input_lra"], meas["input_thresh"], meas["target_offset"])
    subprocess.run(
        [FFMPEG, "-y", "-v", "error", "-i", raw, "-af", af,
         "-ac", "1", "-ar", "24000", "-c:a", "libmp3lame", "-b:a", "48k", out],
        check=True)
    return probe_dur(out)


async def synth(text, out_raw, retry=3):
    for i in range(retry):
        try:
            await edge_tts.Communicate(text, VOICE, pitch=PITCH, rate=RATE).save(out_raw)
            if os.path.exists(out_raw) and os.path.getsize(out_raw) > 1200:
                return True
        except Exception as e:
            if i == retry - 1:
                print("  synth fail", type(e).__name__, text[:30])
        await asyncio.sleep(1.0 + i)
    return False


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--only", default="")
    a = ap.parse_args()

    rows = [r for r in load_script() if "不配音" not in r["role"]]
    for r in rows:
        r["say"] = clean(r["text"])

    if a.dry:
        for r in rows:
            if r["say"].replace("。", "") != r["text"]:
                print(f'{r["id"]}\n  ORIG {r["text"]}\n  SAY  {r["say"]}')
        print("\n合计", len(rows), "条，清洗后有变化",
              sum(1 for r in rows if r["say"].replace("。", "") != r["text"]), "条")
        return

    os.makedirs(STAGE, exist_ok=True)
    os.makedirs(RAW, exist_ok=True)
    if a.sample:
        rows = rows[: a.sample]
    if a.only:
        want = set(a.only.split(","))
        rows = [r for r in rows if r["id"] in want]

    done, total, total_dur = 0, len(rows), 0.0
    for r in rows:
        raw = os.path.join(RAW, r["id"] + ".mp3")
        out = os.path.join(STAGE, r["id"] + ".mp3")
        if not await synth(r["say"], raw):
            continue
        try:
            meas = loudnorm_measure(raw)
            d = post(raw, out, meas)
        except Exception as e:
            print(r["id"], "post fail", e)
            continue
        total_dur += d
        done += 1
        if done % 15 == 0:
            print(f"  {done}/{total} 累计 {total_dur:.0f}s", flush=True)
        await asyncio.sleep(0.25)
    print(f"DONE {done}/{total} 总时长 {total_dur:.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
