# -*- coding: utf-8 -*-
"""生成中文版配音试听页（含「数字与缩写」筛选，便于复核读法）。"""
import csv
import json
import os
import re
import subprocess
import sys

BASE = r"C:\Users\-\Desktop\冰川信使海外版"
sys.path.insert(0, os.path.join(BASE, "_tools"))
import zh_gen as Z  # noqa: E402

ZH = os.path.join(BASE, r"output\voice-overs\zh")
OUT = os.path.join(BASE, r"output\配音试听-中文版-20261031.html")
CSV = os.path.join(BASE, r"output\中文配音对照表-20261031.csv")

SPECIAL = re.compile(r"[0-9%℃]|Q T E|H U D|C E O|I P C C|S O S|G二十")


def main():
    rows = [r for r in Z.load_script() if "不配音" not in r["role"]]
    data = []
    for r in rows:
        p = os.path.join(ZH, r["id"] + ".mp3")
        if not os.path.exists(p):
            continue
        say = Z.clean(r["text"])
        data.append({
            "id": r["id"], "ch": r["ch"], "role": r["role"], "text": r["text"], "say": say,
            "dur": round(Z.probe_dur(p), 2),
            "flag": bool(SPECIAL.search(say)),
        })
    chs = []
    for d in data:
        if d["ch"] not in chs:
            chs.append(d["ch"])
    total = sum(d["dur"] for d in data)

    html = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>配音试听 · 冰川信使 2040 中文版</title>
<style>
:root{--bg:#f6f8fa;--card:#fff;--line:#e3e8ef;--ink:#1b2430;--dim:#667085;
--ai:#6d33c8;--aibg:#f1eaff;--warn:#b45309;--warnbg:#fef3e2;--acc:#0e7490}
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
h2{font-size:13px;color:var(--dim);font-weight:600;letter-spacing:.5px;margin:26px 0 8px}
h2:first-child{margin-top:0}
.row{display:grid;grid-template-columns:64px 1fr 84px 62px 34px;gap:12px;align-items:center;
background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 13px;margin-bottom:6px;cursor:pointer;transition:.15s}
.row:hover{border-color:#c8d3e0;box-shadow:0 2px 8px rgba(16,40,70,.06)}
.row.on{border-color:var(--acc);box-shadow:0 0 0 2px rgba(14,116,144,.14)}
.id{font:12px/1.4 ui-monospace,Consolas,monospace;color:var(--dim)}
.tx{font-size:13.5px;line-height:1.5;color:var(--ink);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.row.open .tx{-webkit-line-clamp:unset}
.say{font-size:12px;color:var(--dim);margin-top:3px;display:none}
.row.open .say{display:block}
.role{font-size:12px;color:var(--dim);margin-top:2px}
.badge{font-size:11.5px;padding:2px 9px;border-radius:999px;text-align:center;white-space:nowrap}
.b-ai{background:var(--aibg);color:var(--ai)}
.b-warn{background:var(--warnbg);color:var(--warn)}
.dur{font:12px ui-monospace,Consolas,monospace;color:var(--dim);text-align:right}
.play{width:30px;height:30px;border-radius:50%;border:none;background:var(--acc);color:#fff;cursor:pointer;font-size:11px}
.bar{position:fixed;left:0;right:0;bottom:0;background:var(--card);border-top:1px solid var(--line);padding:10px 22px;display:flex;gap:14px;align-items:center;box-shadow:0 -4px 16px rgba(16,40,70,.06)}
.bar .now{font-size:13px;flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bar .now b{font-family:ui-monospace,Consolas,monospace;font-weight:600}
.bar button{border:1px solid var(--line);background:var(--card);border-radius:8px;padding:6px 12px;cursor:pointer;font-size:13px;color:var(--ink)}
.bar label{font-size:12.5px;color:var(--dim);display:flex;align-items:center;gap:5px;cursor:pointer}
.bar input[type=range]{width:170px;accent-color:var(--acc)}
</style></head><body>
<header>
  <h1>配音试听 · 冰川信使 2040 <span style="color:var(--dim);font-weight:400;font-size:14px">中文版 · 新音色</span></h1>
  <div class="meta"><b>__N__</b> 条 · 音色 zh-CN-XiaoxiaoNeural（压低 40Hz → 172Hz） · 总时长 <b>__TOT__</b></div>
  <div class="filters">
    <button data-f="all" class="on">全部</button>
    <button data-f="long">长句 ≥8s</button>
    <button data-f="flag">数字与缩写</button>
  </div>
</header>
<main id="list"></main>
<div class="bar">
  <button id="prev">上一句</button>
  <button id="toggle">播放</button>
  <button id="next">下一句</button>
  <div class="now" id="now">点任意一行开始试听，再点一次展开读法</div>
  <label><input type="checkbox" id="auto" checked>播完自动下一句</label>
  <input type="range" id="vol" min="0" max="100" value="100">
</div>
<audio id="au"></audio>
<script>
const DATA = __DATA__;
let filter = 'all', cur = -1;
const au = document.getElementById('au');
const list = document.getElementById('list');

function render(){
  list.innerHTML = '';
  let lastCh = null;
  DATA.forEach((d, i) => {
    if (filter === 'long' && d.dur < 8) return;
    if (filter === 'flag' && !d.flag) return;
    if (d.ch !== lastCh) {
      const h = document.createElement('h2'); h.textContent = d.ch; list.appendChild(h); lastCh = d.ch;
    }
    const row = document.createElement('div');
    row.className = 'row' + (i === cur ? ' on' : '');
    row.dataset.i = i;
    const badge = d.flag ? '<span class="badge b-warn">数字/缩写</span>' : '<span class="badge b-ai">新音色</span>';
    row.innerHTML = '<div class="id">' + d.id + '</div>' +
      '<div><div class="tx">' + d.text.replace(/</g,'&lt;') + '</div>' +
      '<div class="say">读法：' + d.say.replace(/</g,'&lt;') + '</div>' +
      '<div class="role">' + (d.role || '') + '</div></div>' +
      '<div>' + badge + '</div>' +
      '<div class="dur">' + d.dur.toFixed(2) + 's</div>' +
      '<button class="play">▶</button>';
    row.onclick = () => {
      if (i === cur) { row.classList.toggle('open'); return; }
      play(i);
    };
    list.appendChild(row);
  });
}

function play(i){
  if (i < 0 || i >= DATA.length) return;
  cur = i;
  const d = DATA[i];
  au.src = 'voice-overs/zh/' + d.id + '.mp3';
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
                .replace("__N__", str(len(data)))
                .replace("__TOT__", "%d 分 %02d 秒" % (int(total // 60), int(total % 60))))
    open(OUT, "w", encoding="utf-8").write(html)

    with open(CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["编号", "章节", "角色", "中文台词", "配音读法", "时长s"])
        for d in data:
            w.writerow([d["id"], d["ch"], d["role"], d["text"], d["say"], "%.2f" % d["dur"]])

    print("写出", OUT)
    print("写出", CSV)
    print("条数", len(data), "章节", len(chs), "总时长 %.1fs" % total,
          "数字/缩写条目", sum(1 for d in data if d["flag"]))


if __name__ == "__main__":
    main()
