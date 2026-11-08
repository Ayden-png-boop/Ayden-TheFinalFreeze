# -*- coding: utf-8 -*-
"""生成「现用 vs F5 音色克隆」A/B 试听页，音频一并复制到页面同级目录。"""
import os
import shutil
import subprocess
import sys

BASE = r"C:\Users\-\Desktop\冰川信使海外版"
sys.path.insert(0, os.path.join(BASE, "_tools"))
import zh_gen as Z  # noqa: E402

OLD = os.path.join(BASE, r"_tools\_zh_stage")
NEW = os.path.join(BASE, r"_tools\_f5_stage")
TAG = "20261101"
OUTDIR = os.path.join(BASE, "output", f"配音对比-F5克隆-{TAG}")
HTML = os.path.join(BASE, "output", f"配音对比-F5克隆-{TAG}.html")
FFPROBE = r"D:\ai\VideoLingo\ffmpeg\bin\ffprobe.exe"


def dur(p):
    r = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", p], capture_output=True, text=True)
    try:
        return round(float(r.stdout.strip()), 2)
    except ValueError:
        return 0.0


def main():
    rows = [r for r in Z.load_script() if "不配音" not in r["role"]]
    for sub in ("old", "new"):
        os.makedirs(os.path.join(OUTDIR, sub), exist_ok=True)

    data = []
    for r in rows:
        o = os.path.join(OLD, r["id"] + ".mp3")
        n = os.path.join(NEW, r["id"] + ".mp3")
        if not (os.path.exists(o) and os.path.exists(n)):
            continue
        shutil.copy2(o, os.path.join(OUTDIR, "old", r["id"] + ".mp3"))
        shutil.copy2(n, os.path.join(OUTDIR, "new", r["id"] + ".mp3"))
        do, dn = dur(o), dur(n)
        data.append({
            "id": r["id"], "ch": r["ch"], "role": r["role"], "text": r["text"],
            "say": Z.clean(r["text"]), "do": do, "dn": dn,
            "ratio": (dn / do) if do else 0,
        })

    chs = []
    for d in data:
        if d["ch"] not in chs:
            chs.append(d["ch"])

    groups = []
    for ch in chs:
        items = [d for d in data if d["ch"] == ch]
        groups.append((ch, items))

    def rows_html(items):
        out = []
        for d in items:
            warn = " warn" if d["ratio"] and abs(d["ratio"] - 1) > 0.15 else ""
            out.append(f"""<div class="row{warn}" data-id="{d['id']}">
  <div class="id">{d['id']}</div>
  <div class="body">
    <div class="text">{d['text']}</div>
    <div class="meta-line">{d['role']} · 现用 {d['do']}s · 克隆 {d['dn']}s · 比例 {d['ratio']:.2f}</div>
  </div>
  <div class="acts">
    <button class="p old" data-src="配音对比-F5克隆-{TAG}/old/{d['id']}.mp3">现用</button>
    <button class="p new" data-src="配音对比-F5克隆-{TAG}/new/{d['id']}.mp3">克隆</button>
  </div>
</div>""")
        return "\n".join(out)

    body = []
    for ch, items in groups:
        body.append(f'<h2>{ch}</h2>\n' + rows_html(items))

    total_old = sum(d["do"] for d in data)
    total_new = sum(d["dn"] for d in data)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>中文配音 A/B · 现用 vs 音色克隆</title>
<style>
:root{{--bg:#f6f8fa;--card:#fff;--line:#e3e8ef;--ink:#1b2430;--dim:#667085;--old:#0e7490;--new:#6d33c8;--warn:#b45309;--warnbg:#fef8ef}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif;padding-bottom:90px}}
header{{position:sticky;top:0;z-index:10;background:rgba(246,248,250,.95);backdrop-filter:blur(8px);border-bottom:1px solid var(--line);padding:15px 22px}}
h1{{margin:0 0 6px;font-size:18px}}
.meta{{color:var(--dim);font-size:13px}}
.meta b{{color:var(--ink)}}
main{{max-width:1040px;margin:0 auto;padding:16px 20px}}
h2{{font-size:13px;color:var(--dim);letter-spacing:.4px;margin:24px 0 8px;font-weight:600}}
.row{{display:grid;grid-template-columns:70px 1fr 148px;gap:12px;align-items:center;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 14px;margin-bottom:6px}}
.row.warn{{background:var(--warnbg);border-color:#f0d9b5}}
.id{{font:600 13px/1 ui-monospace,Consolas,monospace;color:var(--dim)}}
.text{{font-size:15px}}
.meta-line{{color:var(--dim);font-size:12px;margin-top:3px}}
.acts{{display:flex;gap:8px;justify-content:flex-end}}
button.p{{border:1px solid var(--line);background:#fff;border-radius:8px;padding:7px 12px;font-size:13px;cursor:pointer;min-width:62px}}
button.p.old{{color:var(--old);border-color:#bfe0e8}}
button.p.new{{color:var(--new);border-color:#d9c8f5}}
button.p:hover{{filter:brightness(.97)}}
button.p.playing{{background:var(--ink);color:#fff;border-color:var(--ink)}}
footer{{position:fixed;left:0;right:0;bottom:0;background:#fff;border-top:1px solid var(--line);padding:10px 22px;display:flex;gap:16px;align-items:center;font-size:13px;color:var(--dim)}}
footer b{{color:var(--ink)}}
</style></head><body>
<header>
  <h1>中文配音 A/B 试听</h1>
  <div class="meta">现用 = 晓晓变调（pitch −53Hz） · 克隆 = F5-TTS 用您录音做音色参考 · 共 <b>{len(data)}</b> 条 · 现用总时长 <b>{total_old:.0f}s</b> / 克隆总时长 <b>{total_new:.0f}s</b></div>
</header>
<main>
{''.join(body)}
</main>
<footer><span>点击「现用 / 克隆」即时播放，可连续点按做 A/B 对比</span><span id="now"></span></footer>
<audio id="player" preload="none"></audio>
<script>
const p = document.getElementById('player');
let cur = null;
document.querySelectorAll('button.p').forEach(b => {{
  b.addEventListener('click', () => {{
    document.querySelectorAll('button.p').forEach(x => x.classList.remove('playing'));
    b.classList.add('playing');
    p.src = b.dataset.src;
    p.play();
    const row = b.closest('.row');
    document.getElementById('now').textContent = '正在播放：' + row.dataset.id + (b.classList.contains('new') ? ' · 克隆' : ' · 现用');
    cur = b;
  }});
}});
p.addEventListener('ended', () => {{ if (cur) cur.classList.remove('playing'); }});
</script>
</body></html>"""
    with open(HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print("page:", HTML, len(data), "rows")


if __name__ == "__main__":
    main()
