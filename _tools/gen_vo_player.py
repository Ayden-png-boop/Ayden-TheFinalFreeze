# -*- coding: utf-8 -*-
"""生成本地配音试听页：按章节列 115 条，标注真人/AI，点一条播一条。"""
import json
import os
import re

BASE = r"C:\Users\-\Desktop\冰川信使海外版"
SCRIPT = os.path.join(BASE, r"output\voice-script\配音脚本-英文.txt")
EN = os.path.join(BASE, r"output\voice-overs\en")
REPORT = os.path.join(BASE, r"_tools\_human_vo_report.json")
OUT = os.path.join(BASE, r"output\配音试听-20261031.html")

MAYBE = {"VO-011", "VO-038", "VO-030", "VO-053", "VO-016"}


def load_script():
    rows, ch = [], "番外 · 界面与提示文案"
    for line in open(SCRIPT, encoding="utf-8"):
        s = line.strip()
        m = re.match(r"^【(.+)】$", s)
        if m:
            ch = m.group(1)
            continue
        m = re.match(r"^(VO-\d+)\s+\[([^\]]+)\]\s*(.*)$", s)
        if not m:
            continue
        if "不配音" in m.group(2):
            continue
        rows.append({"id": m.group(1), "role": m.group(2), "text": m.group(3), "ch": ch})
    return rows


def dur_of(p):
    import subprocess
    r = subprocess.run([r"D:\ai\VideoLingo\ffmpeg\bin\ffprobe.exe", "-v", "error",
                        "-show_entries", "format=duration", "-of", "csv=p=0", p],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


def main():
    rows = load_script()
    hum = {r["id"]: r for r in json.load(open(REPORT, encoding="utf-8"))}
    data = []
    for r in rows:
        p = os.path.join(EN, r["id"] + ".mp3")
        if not os.path.exists(p):
            continue
        h = hum.get(r["id"])
        data.append({
            "id": r["id"], "ch": r["ch"], "role": r["role"], "text": r["text"],
            "kind": "human" if h else "ai",
            "src": ("%s [%.2f-%.2f]" % (h["src"], h["start"], h["end"])) if h else "en-US-EmmaNeural · −25%",
            "dur": round(dur_of(p), 2),
            "flag": r["id"] in MAYBE,
        })
    chs = []
    for d in data:
        if d["ch"] not in chs:
            chs.append(d["ch"])
    total = sum(d["dur"] for d in data)
    n_h = sum(1 for d in data if d["kind"] == "human")

    html = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>配音试听 · 冰川信使 2040</title>
<style>
:root{--bg:#f6f8fa;--card:#fff;--line:#e3e8ef;--ink:#1b2430;--dim:#667085;
--human:#0f766e;--humanbg:#e6f4f1;--ai:#6d33c8;--aibg:#f1eaff;--warn:#b45309;--warnbg:#fef3e2;--acc:#0e7490}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif;padding-bottom:120px}
header{position:sticky;top:0;z-index:10;background:rgba(246,248,250,.94);backdrop-filter:blur(8px);border-bottom:1px solid var(--line);padding:16px 22px 12px}
h1{margin:0 0 8px;font-size:18px;letter-spacing:.3px}
.meta{color:var(--dim);font-size:13px}
.meta b{color:var(--ink);font-weight:600}
.filters{display:flex;gap:8px;margin-top:12px;flex-wrap:wrap}
.filters button{border:1px solid var(--line);background:var(--card);color:var(--dim);padding:5px 13px;border-radius:999px;cursor:pointer;font-size:13px}
.filters button.on{background:var(--acc);border-color:var(--acc);color:#fff}
main{padding:18px 22px;max-width:1000px;margin:0 auto}
h2{font-size:13px;color:var(--dim);font-weight:600;letter-spacing:.5px;margin:26px 0 8px;text-transform:none}
h2:first-child{margin-top:0}
.row{display:grid;grid-template-columns:64px 1fr 92px 62px 34px;gap:12px;align-items:center;
background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 13px;margin-bottom:6px;cursor:pointer;transition:.15s}
.row:hover{border-color:#c8d3e0;box-shadow:0 2px 8px rgba(16,40,70,.06)}
.row.on{border-color:var(--acc);box-shadow:0 0 0 2px rgba(14,116,144,.14)}
.id{font:12px/1.4 ui-monospace,Consolas,monospace;color:var(--dim)}
.tx{font-size:13.5px;line-height:1.5;color:var(--ink);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.row.open .tx{-webkit-line-clamp:unset}
.role{font-size:12px;color:var(--dim);margin-top:2px}
.badge{font-size:11.5px;padding:2px 9px;border-radius:999px;text-align:center;white-space:nowrap}
.b-human{background:var(--humanbg);color:var(--human)}
.b-ai{background:var(--aibg);color:var(--ai)}
.b-warn{background:var(--warnbg);color:var(--warn)}
.dur{font:12px ui-monospace,Consolas,monospace;color:var(--dim);text-align:right}
.play{width:30px;height:30px;border-radius:50%;border:none;background:var(--acc);color:#fff;cursor:pointer;font-size:11px}
.play.pause{background:#94a3b8}
.bar{position:fixed;left:0;right:0;bottom:0;background:var(--card);border-top:1px solid var(--line);padding:10px 22px;display:flex;gap:14px;align-items:center;box-shadow:0 -4px 16px rgba(16,40,70,.06)}
.bar .now{font-size:13px;flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bar .now b{font-family:ui-monospace,Consolas,monospace;font-weight:600}
.bar button{border:1px solid var(--line);background:var(--card);border-radius:8px;padding:6px 12px;cursor:pointer;font-size:13px;color:var(--ink)}
.bar button:hover{border-color:#c8d3e0}
.bar label{font-size:12.5px;color:var(--dim);display:flex;align-items:center;gap:5px;cursor:pointer}
.bar input[type=range]{width:170px;accent-color:var(--acc)}
.hide{display:none!important}
</style></head><body>
<header>
  <h1>配音试听 · 冰川信使 2040 <span style="color:var(--dim);font-weight:400;font-size:14px">英文版</span></h1>
  <div class="meta"><b>__N__</b> 条 · 真人 <b>__NH__</b> · AI <b>__NA__</b> · 总时长 <b>__TOT__</b></div>
  <div class="filters">
    <button data-f="all" class="on">全部</button>
    <button data-f="human">我的录音</button>
    <button data-f="ai">AI 补全</button>
    <button data-f="flag">待复核</button>
  </div>
</header>
<main id="list"></main>
<div class="bar">
  <button id="prev">上一句</button>
  <button id="toggle">播放</button>
  <button id="next">下一句</button>
  <div class="now" id="now">点任意一行开始试听</div>
  <label><input type="checkbox" id="auto" checked>播完自动下一句</label>
  <input type="range" id="vol" min="0" max="100" value="100">
</div>
<audio id="au"></audio>
<script>
const DATA = __DATA__;
const CHS = __CHS__;
let filter = 'all', cur = -1;
const au = document.getElementById('au');
const list = document.getElementById('list');

function render(){
  list.innerHTML = '';
  let lastCh = null;
  DATA.forEach((d, i) => {
    if (filter !== 'all' && filter !== 'flag' && d.kind !== filter) return;
    if (filter === 'flag' && !d.flag) return;
    if (d.ch !== lastCh) {
      const h = document.createElement('h2'); h.textContent = d.ch; list.appendChild(h); lastCh = d.ch;
    }
    const row = document.createElement('div');
    row.className = 'row' + (i === cur ? ' on' : '');
    row.dataset.i = i;
    const badge = d.flag ? '<span class="badge b-warn">待复核</span>'
      : (d.kind === 'human' ? '<span class="badge b-human">我的录音</span>' : '<span class="badge b-ai">AI</span>');
    row.innerHTML = '<div class="id">' + d.id + '</div>' +
      '<div><div class="tx">' + d.text.replace(/</g,'&lt;') + '</div>' +
      '<div class="role">' + (d.role || '') + (d.kind === 'human' ? ' · ' + d.src : ' · ' + d.src) + '</div></div>' +
      '<div>' + badge + '</div>' +
      '<div class="dur">' + d.dur.toFixed(2) + 's</div>' +
      '<button class="play">▶</button>';
    row.onclick = (e) => { play(i); };
    list.appendChild(row);
  });
}

function play(i){
  if (i < 0 || i >= DATA.length) return;
  cur = i;
  const d = DATA[i];
  au.src = 'voice-overs/en/' + d.id + '.mp3';
  au.play().catch(()=>{});
  document.getElementById('now').innerHTML = '<b>' + d.id + '</b> ' + (d.role||'') + ' · ' + d.text.slice(0, 60);
  document.querySelectorAll('.row').forEach(r => r.classList.toggle('on', +r.dataset.i === i));
  const el = document.querySelector('.row[data-i="' + i + '"]');
  if (el) el.scrollIntoView({block:'nearest', behavior:'smooth'});
}

au.onended = () => {
  document.getElementById('toggle').textContent = '播放';
  if (document.getElementById('auto').checked) play(cur + 1);
};
document.getElementById('toggle').onclick = () => {
  if (au.paused) { if (!au.src) play(0); else au.play(); } else au.pause();
};
au.onplay = () => document.getElementById('toggle').textContent = '暂停';
au.onpause = () => document.getElementById('toggle').textContent = '播放';
document.getElementById('prev').onclick = () => play(Math.max(0, cur - 1));
document.getElementById('next').onclick = () => play(Math.min(DATA.length - 1, cur + 1));
document.getElementById('vol').oninput = e => au.volume = e.target.value / 100;
document.querySelectorAll('.filters button').forEach(b => b.onclick = () => {
  document.querySelectorAll('.filters button').forEach(x => x.classList.remove('on'));
  b.classList.add('on'); filter = b.dataset.f; render();
});
render();
</script></body></html>"""

    html = (html.replace("__DATA__", json.dumps(data, ensure_ascii=False))
                .replace("__CHS__", json.dumps(chs, ensure_ascii=False))
                .replace("__N__", str(len(data)))
                .replace("__NH__", str(n_h))
                .replace("__NA__", str(len(data) - n_h))
                .replace("__TOT__", "%d 分 %02d 秒" % (int(total // 60), int(total % 60))))
    open(OUT, "w", encoding="utf-8").write(html)
    print("写出", OUT, len(data), "条", n_h, "真人", len(data) - n_h, "AI", "总时长 %.1fs" % total)


if __name__ == "__main__":
    main()
