#!/usr/bin/env python3
"""
HTML Report Generator for 全球游戏市场热点报告
Generates a beautiful, responsive HTML page from report data.
Called by build_report_LATEST.py and build_weekly_LATEST.py after Excel generation.
"""

import json
from datetime import datetime

# ── Color palette (matches Excel theme) ──────────────────────────────────────
COLORS = {
    "navy":   "#1B2A4A",
    "sky":    "#2E86AB",
    "orange": "#E76F51",
    "purple": "#7B2D8B",
    "rust":   "#B7410E",
    "mint":   "#52B788",
    "gold":   "#F4A261",
    "white":  "#FFFFFF",
    "lt":     "#F8F9FA",
    "mid":    "#6C757D",
    "dark":   "#212529",
}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  :root {{
    --navy: #1B2A4A; --sky: #2E86AB; --orange: #E76F51;
    --purple: #7B2D8B; --rust: #B7410E; --mint: #52B788;
    --gold: #F4A261; --bg: #0F1923; --surface: #1a2535;
    --surface2: #243044; --text: #E8EDF3; --muted: #8896A8;
    --border: rgba(255,255,255,0.08);
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
    background: var(--bg); color: var(--text);
    line-height: 1.6; font-size: 14px;
  }}

  /* ── Header ── */
  .site-header {{
    background: linear-gradient(135deg, var(--navy) 0%, #0d1f3c 100%);
    border-bottom: 1px solid var(--border);
    padding: 0 24px;
    position: sticky; top: 0; z-index: 100;
    display: flex; align-items: center; justify-content: space-between;
    height: 56px;
  }}
  .site-header .logo {{ color: var(--sky); font-weight: 700; font-size: 15px; letter-spacing: 0.5px; }}
  .site-header .nav {{ display: flex; gap: 4px; }}
  .site-header .nav a {{
    color: var(--muted); text-decoration: none; padding: 6px 12px;
    border-radius: 6px; font-size: 13px; transition: all .15s;
  }}
  .site-header .nav a:hover, .site-header .nav a.active {{
    background: rgba(46,134,171,.2); color: var(--sky);
  }}

  /* ── Hero ── */
  .hero {{
    background: linear-gradient(160deg, #1B2A4A 0%, #0d1f3c 60%, #0F1923 100%);
    padding: 48px 24px 36px; text-align: center;
    border-bottom: 1px solid var(--border);
  }}
  .hero .badge {{
    display: inline-block; background: rgba(46,134,171,.2);
    color: var(--sky); border: 1px solid rgba(46,134,171,.4);
    border-radius: 20px; padding: 4px 14px; font-size: 12px; margin-bottom: 16px;
  }}
  .hero h1 {{ font-size: clamp(22px,4vw,36px); font-weight: 700; letter-spacing: -0.5px; }}
  .hero h1 span {{ color: var(--sky); }}
  .hero .meta {{ color: var(--muted); font-size: 13px; margin-top: 10px; }}
  .hero .meta strong {{ color: var(--text); }}

  /* ── Market Nav ── */
  .market-nav {{
    background: var(--surface); border-bottom: 1px solid var(--border);
    padding: 0 24px; display: flex; gap: 4px; overflow-x: auto;
    scrollbar-width: none; position: sticky; top: 56px; z-index: 90;
  }}
  .market-nav::-webkit-scrollbar {{ display: none; }}
  .market-nav a {{
    color: var(--muted); text-decoration: none; padding: 12px 16px;
    white-space: nowrap; font-size: 13px; border-bottom: 2px solid transparent;
    transition: all .15s; display: flex; align-items: center; gap: 6px;
  }}
  .market-nav a:hover {{ color: var(--text); }}
  .market-nav a.active {{ color: var(--sky); border-bottom-color: var(--sky); }}

  /* ── Overview Cards ── */
  .section {{ padding: 32px 24px; max-width: 1400px; margin: 0 auto; }}
  .section-title {{
    font-size: 18px; font-weight: 700; color: var(--text);
    margin-bottom: 20px; display: flex; align-items: center; gap: 10px;
  }}
  .section-title::after {{
    content: ''; flex: 1; height: 1px; background: var(--border);
  }}
  .cards-grid {{
    display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 16px; margin-bottom: 32px;
  }}
  .card {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 12px; padding: 20px; transition: all .2s;
  }}
  .card:hover {{ border-color: rgba(46,134,171,.4); transform: translateY(-2px); }}
  .card .card-header {{ display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }}
  .card .flag {{ font-size: 24px; }}
  .card .market-name {{ font-weight: 600; font-size: 15px; }}
  .card .market-sub {{ color: var(--muted); font-size: 12px; }}

  /* ── Market Sheet ── */
  .market-sheet {{ display: none; }}
  .market-sheet.active {{ display: block; }}

  /* ── Section Headers ── */
  .sh {{
    display: flex; align-items: center; gap: 12px;
    padding: 14px 18px; border-radius: 10px; margin-bottom: 16px;
    font-weight: 700; font-size: 14px; margin-top: 28px;
  }}
  .sh-pc    {{ background: rgba(46,134,171,.15);  color: #6ec8e8; border-left: 3px solid var(--sky); }}
  .sh-mob   {{ background: rgba(231,111,81,.15);  color: #f4a07a; border-left: 3px solid var(--orange); }}
  .sh-mkt   {{ background: rgba(123,45,139,.15);  color: #c77de0; border-left: 3px solid var(--purple); }}
  .sh-pol   {{ background: rgba(183,65,14,.15);   color: #e88a5a; border-left: 3px solid var(--rust); }}

  /* ── Tables ── */
  .tbl-wrap {{ overflow-x: auto; border-radius: 10px; border: 1px solid var(--border); margin-bottom: 8px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  thead tr {{ background: var(--navy); }}
  thead th {{
    padding: 10px 14px; text-align: left; font-weight: 600;
    color: rgba(255,255,255,.85); white-space: nowrap; font-size: 12px;
  }}
  tbody tr {{ background: var(--surface); border-bottom: 1px solid var(--border); }}
  tbody tr:nth-child(even) {{ background: var(--surface2); }}
  tbody tr:hover {{ background: rgba(46,134,171,.1); }}
  tbody td {{ padding: 10px 14px; vertical-align: top; }}
  .rank-badge {{
    display: inline-block; background: var(--sky); color: white;
    border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: 700;
    white-space: nowrap;
  }}
  .game-name {{ font-weight: 600; color: var(--text); }}
  .game-type {{ color: var(--muted); font-size: 11px; }}
  .content-cell {{ max-width: 320px; color: #c8d3df; line-height: 1.5; }}
  .feedback-pos {{ color: #6fcf97; font-size: 12px; }}
  .feedback-neg {{ color: #eb5757; font-size: 12px; }}
  .dim-badge {{
    display: inline-block; border-radius: 4px; padding: 2px 8px;
    font-size: 11px; font-weight: 600; white-space: nowrap;
  }}
  .dim-ugc  {{ background:rgba(82,183,136,.2); color:#52B788; }}
  .dim-kol  {{ background:rgba(244,162,97,.2); color:#F4A261; }}
  .dim-ch   {{ background:rgba(46,134,171,.2); color:#6ec8e8; }}
  .dim-co   {{ background:rgba(123,45,139,.2); color:#c77de0; }}
  .dim-med  {{ background:rgba(231,111,81,.2); color:#f4a07a; }}
  .dim-oth  {{ background:rgba(108,117,125,.2); color:#adb5bd; }}
  .pol-type {{ font-size: 11px; color: var(--muted); }}
  .pol-risk {{ color: #eb5757; font-size: 12px; }}
  .pol-good {{ color: #6fcf97; font-size: 12px; }}

  /* ── Footer ── */
  footer {{
    text-align: center; padding: 32px 24px;
    color: var(--muted); font-size: 12px; border-top: 1px solid var(--border);
  }}
  footer a {{ color: var(--sky); text-decoration: none; }}

  @media (max-width: 768px) {{
    .site-header {{ padding: 0 16px; }}
    .section {{ padding: 20px 16px; }}
    .hero {{ padding: 32px 16px 24px; }}
  }}
</style>
</head>
<body>

<header class="site-header">
  <div class="logo">🎮 KL游戏·全球市场情报</div>
  <nav class="nav">
    <a href="index.html" id="nav-weekly">周报</a>
    <a href="monthly.html" id="nav-monthly">月报</a>
  </nav>
</header>

<div class="hero">
  <div class="badge">{report_type}</div>
  <h1>{title_main}<br><span>{title_sub}</span></h1>
  <div class="meta">分析周期：<strong>{period}</strong> &nbsp;|&nbsp; 生成时间：<strong>{generated}</strong></div>
</div>

<nav class="market-nav" id="marketNav">
{market_nav_items}
</nav>

<main>
{overview_section}
{market_sections}
</main>

<footer>
  <p>本报告由 KL游戏市场情报系统 自动生成 · 数据来源：官方平台/权威媒体/第三方数据平台</p>
  <p style="margin-top:6px">如有数据疑问请联系市场团队 · <a href="#">查看历史报告</a></p>
</footer>

<script>
// Market tab switching
const nav = document.getElementById('marketNav');
nav.querySelectorAll('a').forEach(a => {{
  a.addEventListener('click', e => {{
    e.preventDefault();
    const target = a.dataset.market;
    nav.querySelectorAll('a').forEach(x => x.classList.remove('active'));
    a.classList.add('active');
    document.querySelectorAll('.market-sheet').forEach(s => s.classList.remove('active'));
    const sheet = document.getElementById('sheet-' + target);
    if (sheet) sheet.classList.add('active');
    // Scroll to top of main
    window.scrollTo({{top: document.querySelector('.hero').offsetHeight + 56 + 48, behavior:'smooth'}});
  }});
}});
// Activate first
const first = nav.querySelector('a');
if (first) first.click();

// Active nav link
const page = location.pathname.split('/').pop() || 'index.html';
document.querySelectorAll('.nav a').forEach(a => {{
  if (a.href.includes(page)) a.classList.add('active');
}});
</script>
</body>
</html>"""


def dim_class(dim):
    if "UGC" in dim: return "dim-ugc"
    if "网红" in dim or "KOL" in dim: return "dim-kol"
    if "渠道" in dim or "平台" in dim: return "dim-ch"
    if "异业" in dim: return "dim-co"
    if "媒体" in dim: return "dim-med"
    return "dim-oth"

def esc(s):
    if not s: return ""
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

MARKET_FLAGS = {
    "中国大陆":"🇨🇳","美国":"🇺🇸","欧洲":"🇪🇺","日本":"🇯🇵",
    "韩国":"🇰🇷","港台":"🇭🇰🇹🇼","东南亚":"🌏","俄罗斯":"🇷🇺"
}

def render_rank_table(rows, cols):
    if not rows: return "<p style='color:var(--muted);padding:16px'>暂无数据</p>"
    html = ['<div class="tbl-wrap"><table><thead><tr>']
    for c in cols:
        html.append(f'<th>{esc(c)}</th>')
    html.append('</tr></thead><tbody>')
    for row in rows:
        html.append('<tr>')
        for j, cell in enumerate(row):
            cell = str(cell) if cell else ""
            if j == 0:
                html.append(f'<td><span class="rank-badge">{esc(cell)}</span></td>')
            elif j == 1:
                html.append(f'<td><div class="game-name">{esc(cell)}</div><div class="game-type">{esc(row[2]) if len(row)>2 else ""}</div></td>')
            elif j == 2:
                continue  # merged into col 1
            elif j == 5:
                html.append(f'<td class="content-cell">{esc(cell)}</td>')
            elif j == 6:
                html.append(f'<td class="feedback-pos">{esc(cell)}</td>')
            elif j == 7:
                html.append(f'<td class="feedback-neg">{esc(cell)}</td>')
            else:
                html.append(f'<td>{esc(cell)}</td>')
        html.append('</tr>')
    html.append('</tbody></table></div>')
    return ''.join(html)

def render_mkt_table(rows):
    if not rows: return "<p style='color:var(--muted);padding:16px'>暂无数据</p>"
    html = ['<div class="tbl-wrap"><table><thead><tr>',
            '<th>游戏</th><th>类型</th><th>营销维度</th><th>具体动作</th><th>平台</th><th>爆点数据</th><th>正面反馈</th><th>负面反馈</th>',
            '</tr></thead><tbody>']
    for row in rows:
        while len(row) < 8: row = list(row) + [""]
        html.append('<tr>')
        html.append(f'<td class="game-name">{esc(row[0])}</td>')
        html.append(f'<td><span class="game-type">{esc(row[1])}</span></td>')
        html.append(f'<td><span class="dim-badge {dim_class(row[2])}">{esc(row[2])}</span></td>')
        html.append(f'<td class="content-cell">{esc(row[3])}</td>')
        html.append(f'<td>{esc(row[4])}</td>')
        html.append(f'<td class="content-cell">{esc(row[5])}</td>')
        html.append(f'<td class="feedback-pos">{esc(row[6])}</td>')
        html.append(f'<td class="feedback-neg">{esc(row[7])}</td>')
        html.append('</tr>')
    html.append('</tbody></table></div>')
    return ''.join(html)

def render_policy_table(rows):
    if not rows: return "<p style='color:var(--muted);padding:16px'>暂无数据</p>"
    html = ['<div class="tbl-wrap"><table><thead><tr>',
            '<th>政策/热闻标题</th><th>来源</th><th>类型</th><th>事件详情</th><th>行业影响</th><th>风险信号</th>',
            '</tr></thead><tbody>']
    for row in rows:
        while len(row) < 6: row = list(row) + [""]
        risk = row[5] if len(row)>5 else ""
        risk_cls = "pol-risk" if risk else ""
        html.append('<tr>')
        html.append(f'<td class="game-name">{esc(row[0])}</td>')
        html.append(f'<td class="pol-type">{esc(row[1])}</td>')
        html.append(f'<td><span class="dim-badge dim-oth">{esc(row[2])}</span></td>')
        html.append(f'<td class="content-cell">{esc(row[3])}</td>')
        html.append(f'<td class="content-cell">{esc(row[4])}</td>')
        html.append(f'<td class="{risk_cls}">{esc(risk)}</td>')
        html.append('</tr>')
    html.append('</tbody></table></div>')
    return ''.join(html)


def generate_html(
    title_main, title_sub, period, report_type,
    markets,   # list of dicts: {name, flag, pc_ranks, mobile_ranks, mkt_rows, policy_rows}
    output_path,
    is_weekly=False
):
    # Market nav
    nav_items = []
    for m in markets:
        flag = MARKET_FLAGS.get(m['name'], '🌐')
        nav_items.append(
            f'<a href="#" data-market="{esc(m["name"])}">{flag} {esc(m["name"])}</a>'
        )

    # Overview section
    overview_cards = []
    for m in markets:
        flag = MARKET_FLAGS.get(m['name'], '🌐')
        top_game = m['pc_ranks'][0][1] if m['pc_ranks'] else "—"
        top_mobile = m['mobile_ranks'][0][1] if m['mobile_ranks'] else "—"
        mkt_count = len(m['mkt_rows'])
        overview_cards.append(f"""
        <div class="card" onclick="document.querySelector('[data-market=\\'{m['name']}\\']').click()">
          <div class="card-header">
            <span class="flag">{flag}</span>
            <div><div class="market-name">{esc(m['name'])}</div>
            <div class="market-sub">PC榜首：{esc(top_game)} · 手游榜首：{esc(top_mobile)}</div></div>
          </div>
          <div style="color:var(--muted);font-size:12px">本期营销案例 <strong style="color:var(--gold)">{mkt_count}</strong> 条</div>
        </div>""")

    overview_html = f"""
<section class="section">
  <div class="section-title">📊 各市场快览</div>
  <div class="cards-grid">{''.join(overview_cards)}</div>
</section>"""

    # Market detail sections
    market_sections = []
    PC_COLS   = ["名次","游戏名称","类型","开发商","平台","游戏内容分析","正面反馈","负面反馈"]
    MOB_COLS  = ["名次","游戏名称","类型","开发商","商店/榜单","游戏内容分析","正面反馈","负面反馈"]

    for m in markets:
        flag = MARKET_FLAGS.get(m['name'], '🌐')
        market_sections.append(f"""
<div class="market-sheet" id="sheet-{esc(m['name'])}">
  <section class="section">
    <div class="sh sh-pc">🖥️ 一、PC / 主机热门游戏榜单（当期 TOP5）</div>
    {render_rank_table(m['pc_ranks'], PC_COLS)}

    <div class="sh sh-mob">📱 二、手游热门游戏榜单（iOS · Google · 地区头部商店 畅销+下载 TOP10）</div>
    {render_rank_table(m['mobile_ranks'], MOB_COLS)}

    <div class="sh sh-mkt">📣 三、重点营销热点详情</div>
    {render_mkt_table(m['mkt_rows'])}

    <div class="sh sh-pol">⚖️ 四、区域产业政策热闻</div>
    {render_policy_table(m['policy_rows'])}
  </section>
</div>""")

    html = HTML_TEMPLATE.format(
        title=f"{title_main} {title_sub}",
        title_main=esc(title_main),
        title_sub=esc(title_sub),
        period=esc(period),
        report_type=esc(report_type),
        generated=datetime.now().strftime("%Y-%m-%d %H:%M"),
        market_nav_items="\n".join(nav_items),
        overview_section=overview_html,
        market_sections="\n".join(market_sections),
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML generated: {output_path}")
    return output_path


if __name__ == "__main__":
    print("HTML generator module loaded. Import and call generate_html() to use.")
