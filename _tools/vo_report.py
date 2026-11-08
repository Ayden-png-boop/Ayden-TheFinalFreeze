# -*- coding: utf-8 -*-
"""生成配音完成度检查报告（HTML + CSV）。数据基于 ASR 逐条对齐结果。"""
import re, os, json, html

BASE = r"C:\Users\-\Desktop\冰川信使海外版"
SCRIPT = os.path.join(BASE, r"output\voice-script\配音脚本-英文.txt")
OUT_HTML = os.path.join(BASE, r"output\配音完成度检查-20261031.html")
OUT_CSV = os.path.join(BASE, r"output\配音缺口清单-20261031.csv")

# 人工核对后的映射：录音文件 -> VO 编号
MAP = {
    "10月20日 3(1).m4a": "VO-001", "10月20日 4(1).m4a": "VO-003", "10月20日 5.m4a": "VO-004",
    "10月20日 6.m4a": "VO-005", "10月20日 7.m4a": "VO-006", "10月20日 8.m4a": "VO-007",
    "10月21日.m4a": "VO-008", "10月21日 4.m4a": "VO-010", "10月21日 5.m4a": "VO-011",
    "10月22日.m4a": "VO-012", "10月22日 2.m4a": "VO-013", "10月22日 3.m4a": "VO-014",
    "10月22日 4.m4a": "VO-015", "10月22日 7.m4a": "VO-016", "10月22日 8(1).m4a": "VO-017",
    "10月22日 10.m4a": "VO-018", "10月22日 11.m4a": "VO-019", "10月22日 12.m4a": "VO-020",
    "10月22日 13.m4a": "VO-021", "10月22日 14.m4a": "VO-022",
    "10月27日.m4a": "VO-023", "10月27日 2.m4a": "VO-024", "10月27日 3.m4a": "VO-025",
    "10月27日 4.m4a": "VO-026", "10月27日 5.m4a": "VO-027", "10月27日 6.m4a": "VO-028",
    "10月27日 7(1).m4a": "VO-029", "10月27日 8(1).m4a": "VO-030", "10月27日 9(1).m4a": "VO-031",
    "10月27日 10(1).m4a": "VO-033", "10月27日 11(1).m4a": "VO-035", "10月27日 12(1).m4a": "VO-036",
    "10月27日 15(1).m4a": "VO-037", "10月27日 16(1).m4a": "VO-038", "10月27日 17(1).m4a": "VO-040",
    "10月27日 18(1).m4a": "VO-041", "10月27日 19(1).m4a": "VO-042", "10月27日 20(1).m4a": "VO-043",
    "10月27日 21(1).m4a": "VO-044", "10月27日 22(1).m4a": "VO-046", "10月27日 24(1).m4a": "VO-047",
    "10月27日 25.m4a": "VO-048", "10月27日 26.m4a": "VO-049", "10月27日 28.m4a": "VO-050",
    "10月27日 30.m4a": "VO-051", "10月27日 31.m4a": "VO-052", "10月27日 32.m4a": "VO-053",
    "10月27日 33.m4a": "VO-054", "10月27日 34.m4a": "VO-055",
}

# 需复听的条目
TODO = [
    ("VO-011", "脚本写 18 % more energy，录音听起来像 “80 more percent energy”，数值需复听确认。"),
    ("VO-038", "脚本写 92 % of their glaciers，录音听起来像 “90 %”，数值需复听确认。"),
    ("VO-030", "脚本写 Organise a peaceful protest，录音是 “Organize the people, protest”，措辞不一致。"),
    ("VO-053", "脚本写 Feign cooperation，录音开头听不清（疑似 “Thank cooperation”），需复听。"),
]


def load_script():
    rows, cur = [], ""
    for line in open(SCRIPT, encoding="utf-8"):
        s = line.strip()
        m = re.match(r"^【(第\d章[^】]*)】", s)
        if m:
            cur = m.group(1)
        m2 = re.match(r"^(VO-(\d+))\s+\[([^\]]+)\]\s*(.*)$", s)
        if m2:
            rows.append({"n": int(m2.group(2)), "id": m2.group(1), "ch": cur,
                         "role": m2.group(3), "text": m2.group(4)})
    return [r for r in rows if "不配音" not in r["role"]]


def main():
    script = load_script()
    done = set(MAP.values())
    chs = []
    for r in script:
        if not chs or chs[-1][0] != r["ch"]:
            chs.append([r["ch"], []])
        chs[-1][1].append(r)
    total = len(script)
    ndone = len(done)
    missing = [r for r in script if r["id"] not in done]

    # CSV
    with open(OUT_CSV, "w", encoding="utf-8-sig") as f:
        f.write("编号,章节,角色,英文台词,状态\n")
        for r in script:
            st = "已录" if r["id"] in done else "待录"
            f.write('"%s","%s","%s","%s","%s"\n' % (r["id"], r["ch"], r["role"],
                                                    r["text"].replace('"', "'"), st))

    # HTML
    pct = ndone / total * 100
    ch_rows = ""
    for ch, items in chs:
        d = sum(1 for i in items if i["id"] in done)
        n = len(items)
        ratio = d / n * 100
        ch_rows += f"""
        <tr>
          <td class="ch">{html.escape(ch)}</td>
          <td class="num">{n}</td>
          <td class="num">{d}</td>
          <td class="num">{n - d}</td>
          <td class="bar-cell"><div class="bar"><i style="width:{ratio:.0f}%"></i></div></td>
        </tr>"""

    miss_rows = ""
    for ch, items in chs:
        left = [i for i in items if i["id"] not in done]
        if not left:
            continue
        miss_rows += f'<tr class="grp"><td colspan="3">{html.escape(ch)}　·　还差 {len(left)} 条</td></tr>'
        for i in left:
            text = i["text"]
            tag = "界面文案" if 95 <= i["n"] <= 117 else ("短句" if len(text.split()) <= 6 else "")
            miss_rows += (f'<tr><td class="vid">{i["id"]}</td><td class="txt">{html.escape(text)}</td>'
                          f'<td class="tag">{tag}</td></tr>')

    todo_rows = "".join(f'<tr><td class="vid">{v}</td><td class="txt">{html.escape(t)}</td></tr>' for v, t in TODO)

    doc = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>冰川信使海外版 · 配音完成度检查</title>
<style>
  :root {{
    --ink:#1d1d1f; --sub:#6b6b70; --line:#e3e1dc; --bg:#f6f5f2; --card:#ffffff;
    --accent:#2f6b58; --warn:#a8442a;
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink);
    font-family:"PingFang SC","Microsoft YaHei","Segoe UI",system-ui,sans-serif;
    line-height:1.65; -webkit-font-smoothing:antialiased; }}
  .wrap {{ max-width:900px; margin:0 auto; padding:56px 32px 80px; }}
  h1 {{ font-size:27px; font-weight:600; letter-spacing:.02em; margin:0 0 6px; }}
  .lead {{ color:var(--sub); font-size:14px; margin:0 0 36px; }}
  .kpis {{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:40px; }}
  .kpi {{ background:var(--card); border:1px solid var(--line); border-radius:3px; padding:18px 20px; }}
  .kpi .v {{ font-size:30px; font-weight:600; letter-spacing:-.01em; }}
  .kpi .l {{ font-size:12px; color:var(--sub); margin-top:2px; }}
  .kpi.hi .v {{ color:var(--accent); }}
  .kpi.miss .v {{ color:var(--warn); }}
  h2 {{ font-size:15px; font-weight:600; margin:44px 0 12px; letter-spacing:.04em; }}
  h2 span {{ color:var(--sub); font-weight:400; margin-left:8px; font-size:12px; }}
  table {{ width:100%; border-collapse:collapse; background:var(--card);
    border:1px solid var(--line); font-size:13.5px; }}
  th {{ text-align:left; font-weight:500; color:var(--sub); font-size:12px;
    padding:10px 14px; border-bottom:1px solid var(--line); background:#fbfaf8; }}
  td {{ padding:10px 14px; border-bottom:1px solid #efedE8; vertical-align:top; }}
  tr:last-child td {{ border-bottom:none; }}
  td.num {{ text-align:right; width:64px; font-variant-numeric:tabular-nums; }}
  td.ch {{ width:230px; }}
  .bar {{ height:5px; background:#eceae5; border-radius:3px; overflow:hidden; }}
  .bar i {{ display:block; height:100%; background:var(--accent); }}
  .bar-cell {{ width:180px; }}
  tr.grp td {{ background:#fbfaf8; font-weight:600; font-size:12.5px; color:var(--accent);
    padding:9px 14px; }}
  td.vid {{ width:92px; font-variant-numeric:tabular-nums; color:var(--sub); white-space:nowrap; }}
  td.tag {{ width:88px; color:var(--sub); font-size:12px; white-space:nowrap; }}
  td.txt {{ line-height:1.5; }}
  .note {{ background:var(--card); border:1px solid var(--line); border-left:3px solid var(--accent);
    padding:16px 20px; font-size:13.5px; margin-top:14px; }}
  .note p {{ margin:6px 0; }}
  .note b {{ font-weight:600; }}
  .foot {{ margin-top:44px; color:var(--sub); font-size:12px; line-height:1.8;
    border-top:1px solid var(--line); padding-top:16px; }}
</style></head>
<body><div class="wrap">
  <h1>冰川信使海外版 · 英文配音完成度检查</h1>
  <p class="lead">检查对象：mp3 文件夹内 {len(MAP)} 个录音文件　·　对照底本：英文配音脚本（115 条需配音条目）　·　检查日期 2026-10-31</p>

  <div class="kpis">
    <div class="kpi"><div class="v">{total}</div><div class="l">脚本需配音条目</div></div>
    <div class="kpi hi"><div class="v">{ndone}</div><div class="l">已录（条）</div></div>
    <div class="kpi miss"><div class="v">{len(missing)}</div><div class="l">未录（条）</div></div>
    <div class="kpi"><div class="v">{pct:.0f}%</div><div class="l">整体完成度</div></div>
  </div>

  <h2>逐章进度</h2>
  <table>
    <tr><th>章节</th><th class="num">需录</th><th class="num">已录</th><th class="num">缺</th><th>进度</th></tr>
    {ch_rows}
  </table>

  <h2>结论<span>一句话</span></h2>
  <div class="note">
    <p><b>没配完。</b>{len(MAP)} 个录音文件逐一与脚本对齐后，覆盖第 1 至第 5 章共 {ndone} 条；缺口 {len(missing)} 条。</p>
    <p>其中第 1–5 章只差 4 条零散短句与章标题（VO-009、VO-032、VO-039、VO-045）；<b>第 6、7、8 章及结尾界面文案（VO-056 至 VO-117，共 62 条）尚未录制</b>。</p>
    <p>按剩余 62 条正文估算，还需约 5 分半到 6 分半的成品语音。</p>
  </div>

  <h2>待补录清单<span>共 {len(missing)} 条，可直接照此录制</span></h2>
  <table>
    <tr><th>编号</th><th>英文台词</th><th>类型</th></tr>
    {miss_rows}
  </table>

  <h2>已录但建议复听<span>{len(TODO)} 条</span></h2>
  <table>
    <tr><th>编号</th><th>问题</th></tr>
    {todo_rows}
  </table>

  <h2>文件命名提醒</h2>
  <div class="note">
    <p>现有文件是录音软件默认名（“10月20日 4(1).m4a”这类），没有编号，批次内还有跳号（10月22日 缺 5、6、9；10月27日 缺 13、14、23、27、29），只能靠语音识别逐条比对才能定位，导入工程时极易错位。</p>
    <p>建议补录时直接按编号命名，例如 <b>VO-056.m4a</b>。录完我可以一次性完成：转 mp3、统一响度、按编号落位到 voice-overs/en，并替换现有 AI 音轨。</p>
  </div>

  <div class="foot">
    核对方式：本地语音识别（faster-whisper large-v3）逐文件转写后与英文脚本做词级对齐，匹配得分低于阈值的条目按上下文人工复核。<br>
    配音脚本底本：output/voice-script/配音脚本-英文.txt　·　完整体检数据：_tools/_vo_coverage_en.json
  </div>
</div></body></html>"""
    open(OUT_HTML, "w", encoding="utf-8").write(doc)
    print("written", OUT_HTML)
    print("written", OUT_CSV)
    print(f"total={total} done={ndone} missing={len(missing)} pct={pct:.1f}")


if __name__ == "__main__":
    main()
