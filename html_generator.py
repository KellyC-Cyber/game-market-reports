#!/usr/bin/env python3
"""
html_generator.py  v2
Beautiful card-based HTML report generator.
Features:
- Card layout (no wide tables)
- iOS/Android tab switch for mobile rankings
- Text auto-formatted into bullet points
- All content visible without horizontal scroll
- Policy section with timeline cards
"""

from datetime import datetime
import re

# ── Text helpers ──────────────────────────────────────────────────────────────
def esc(s):
    if not s: return ""
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def text_to_bullets(s):
    """Split Chinese text at ；。\n into bullet points."""
    if not s: return ""
    s = str(s)
    parts = re.split(r'[；。\n]+', s)
    parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 1]
    if len(parts) <= 1:
        return f'<span class="text-cell">{esc(s)}</span>'
    items = ''.join(f'<li>{esc(p)}</li>' for p in parts)
    return f'<ul class="bullet-list">{items}</ul>'

def text_inline(s):
    """Short inline text, no bullets."""
    return esc(str(s)) if s else "—"

MARKET_FLAGS = {
    "中国大陆":"🇨🇳","美国":"🇺🇸","欧洲":"🇪🇺","日本":"🇯🇵",
    "韩国":"🇰🇷","港台":"🇭🇰","东南亚":"🌏","俄罗斯":"🇷🇺"
}

DIM_STYLES = {
    "UGC":  ("#D1FAE5","#065F46","📹"),
    "网红":  ("##FEF9C3","#713F12","🌟"),
    "KOL":  ("#FEF9C3","#713F12","🌟"),
    "渠道":  ("#DBEAFE","#1E40AF","📲"),
    "平台":  ("#DBEAFE","#1E40AF","📲"),
    "异业":  ("#EDE9FE","#5B21B6","🤝"),
    "媒体":  ("#FFEDD5","#9A3412","📰"),
    "其他":  ("#F1F5F9","#475569","•"),
}

def dim_style(dim):
    for k, (bg, color, icon) in DIM_STYLES.items():
        if k in str(dim): return bg, color, icon
    return "#F1F5F9","#475569","•"

POLICY_TYPE_STYLES = {
    "版号": ("#DBEAFE","#1E40AF"),
    "监管": ("#FEE2E2","#991B1B"),
    "政策": ("#D1FAE5","#065F46"),
    "舆论": ("#FEF9C3","#713F12"),
    "产业": ("#EDE9FE","#5B21B6"),
}
def policy_type_style(t):
    for k,(bg,c) in POLICY_TYPE_STYLES.items():
        if k in str(t): return bg,c
    return "#F1F5F9","#475569"

# ── Rank card renderer ────────────────────────────────────────────────────────
def render_rank_cards(rows):
    if not rows: return '<p class="empty">暂无数据</p>'
    html = ['<div class="rank-cards">']
    for row in rows:
        while len(row) < 8: row = list(row) + [""]
        rank, name, typ, dev, platform, content, pos_fb, neg_fb = [str(c) if c else "" for c in row[:8]]
        # platform chips
        plat_chips = ''.join(
            f'<span class="chip chip-plat">{esc(p.strip())}</span>'
            for p in re.split(r'[/·,、]', platform) if p.strip()
        ) if platform else ''
        html.append(f'''
<div class="rank-card">
  <div class="rank-card-header">
    <span class="rank-num">{esc(rank)}</span>
    <div class="rank-info">
      <div class="rank-name">{esc(name)}</div>
      <div class="rank-meta">
        <span class="chip chip-type">{esc(typ)}</span>
        {plat_chips}
        {'<span class="chip chip-dev">'+esc(dev)+'</span>' if dev else ''}
      </div>
    </div>
  </div>
  {f'<div class="rank-content">{text_to_bullets(content)}</div>' if content else ''}
  <div class="rank-feedback">
    {f'<div class="fb-pos"><span class="fb-label">👍 正面</span>{text_to_bullets(pos_fb)}</div>' if pos_fb else ''}
    {f'<div class="fb-neg"><span class="fb-label">👎 负面</span>{text_to_bullets(neg_fb)}</div>' if neg_fb else ''}
  </div>
</div>''')
    html.append('</div>')
    return ''.join(html)

# ── Mobile tab renderer ───────────────────────────────────────────────────────
def render_mobile_tabs(rows, sheet_id):
    if not rows: return '<p class="empty">暂无数据</p>'
    
    ios_rows = [r for r in rows if any(x in str(r[4] if len(r)>4 else '') for x in ['iOS','App Store','ios'])]
    and_rows = [r for r in rows if any(x in str(r[4] if len(r)>4 else '') for x in ['Google','Play','Android','android','安卓'])]
    other_rows = [r for r in rows if r not in ios_rows and r not in and_rows]
    
    tabs = [("all", f"全部 ({len(rows)})", rows)]
    if ios_rows:    tabs.append(("ios",     f"🍎 iOS ({len(ios_rows)})",         ios_rows))
    if and_rows:    tabs.append(("android", f"🤖 Android ({len(and_rows)})",     and_rows))
    if other_rows:  tabs.append(("other",   f"📱 其他 ({len(other_rows)})",       other_rows))

    html = [f'<div class="tab-group" id="mob-tabs-{sheet_id}">']
    html.append('<div class="tabs">')
    for i, (tid, label, _) in enumerate(tabs):
        active = 'active' if i==0 else ''
        html.append(f'<button class="tab-btn {active}" data-tab="{sheet_id}-{tid}" onclick="switchTab(this,\'{sheet_id}-{tid}\')">{label}</button>')
    html.append('</div>')
    
    for i, (tid, _, tab_rows) in enumerate(tabs):
        display = '' if i==0 else 'style="display:none"'
        html.append(f'<div class="tab-panel" id="panel-{sheet_id}-{tid}" {display}>')
        html.append(render_rank_cards(tab_rows))
        html.append('</div>')
    html.append('</div>')
    return ''.join(html)

# ── Marketing cards ───────────────────────────────────────────────────────────
def render_mkt_cards(rows):
    if not rows: return '<p class="empty">暂无数据</p>'
    html = ['<div class="mkt-cards">']
    for row in rows:
        while len(row) < 8: row = list(row) + [""]
        game, typ, dim, action, platform, kpi, pos_fb, neg_fb = [str(c) if c else "" for c in row[:8]]
        bg, color, icon = dim_style(dim)
        html.append(f'''
<div class="mkt-card">
  <div class="mkt-card-top">
    <div class="mkt-left">
      <div class="mkt-game">{esc(game)}</div>
      <span class="chip chip-type">{esc(typ)}</span>
    </div>
    <span class="dim-badge" style="background:{bg};color:{color}">{icon} {esc(dim)}</span>
  </div>
  <div class="mkt-body">
    <div class="mkt-row"><span class="mkt-label">具体动作</span><div>{text_to_bullets(action)}</div></div>
    {'<div class="mkt-row"><span class="mkt-label">平台</span><div>'+esc(platform)+'</div></div>' if platform else ''}
    {'<div class="mkt-row"><span class="mkt-label">爆点数据</span><div class="kpi-text">'+text_to_bullets(kpi)+'</div></div>' if kpi else ''}
  </div>
  <div class="mkt-feedback">
    {f'<div class="fb-pos"><span class="fb-label">👍 正面</span>{text_to_bullets(pos_fb)}</div>' if pos_fb else ''}
    {f'<div class="fb-neg"><span class="fb-label">👎 负面</span>{text_to_bullets(neg_fb)}</div>' if neg_fb else ''}
  </div>
</div>''')
    html.append('</div>')
    return ''.join(html)

# ── Policy cards ──────────────────────────────────────────────────────────────
def render_policy_cards(rows):
    if not rows: return '<p class="empty">暂无政策热闻数据</p>'
    html = ['<div class="policy-list">']
    for row in rows:
        while len(row) < 6: row = list(row) + [""]
        title, source, typ, detail, impact, risk = [str(c) if c else "" for c in row[:6]]
        bg, color = policy_type_style(typ)
        risk_html = f'<div class="policy-risk">⚠️ 风险信号：{text_to_bullets(risk)}</div>' if risk else ''
        html.append(f'''
<div class="policy-card">
  <div class="policy-card-header">
    <span class="policy-type-badge" style="background:{bg};color:{color}">{esc(typ)}</span>
    <div class="policy-title">{esc(title)}</div>
    {'<span class="policy-source">📌 '+esc(source)+'</span>' if source else ''}
  </div>
  {'<div class="policy-detail">'+text_to_bullets(detail)+'</div>' if detail else ''}
  {'<div class="policy-impact">💡 影响分析：'+text_to_bullets(impact)+'</div>' if impact else ''}
  {risk_html}
</div>''')
    html.append('</div>')
    return ''.join(html)

# ── Overview card ─────────────────────────────────────────────────────────────
def render_overview_cards(markets):
    html = ['<div class="overview-grid">']
    for m in markets:
        flag = MARKET_FLAGS.get(m['name'], '🌐')
        top_pc = m['pc_ranks'][0][1] if m['pc_ranks'] else "—"
        top_mob = m['mobile_ranks'][0][1] if m['mobile_ranks'] else "—"
        mkt_count = len(m['mkt_rows'])
        pol_count = len(m['policy_rows'])
        name_js = m['name'].replace("'","\\'")
        html.append(f'''
<div class="overview-card" onclick="activateMarket('{name_js}')">
  <div class="ov-flag">{flag}</div>
  <div class="ov-name">{esc(m['name'])}</div>
  <div class="ov-stats">
    <div class="ov-stat"><span>🖥️ PC榜首</span><strong>{esc(top_pc)}</strong></div>
    <div class="ov-stat"><span>📱 手游榜首</span><strong>{esc(top_mob)}</strong></div>
    <div class="ov-stat"><span>📣 营销案例</span><strong>{mkt_count}条</strong></div>
    <div class="ov-stat"><span>⚖️ 政策热闻</span><strong>{pol_count}条</strong></div>
  </div>
</div>''')
    html.append('</div>')
    return ''.join(html)

# ── Main HTML template ────────────────────────────────────────────────────────
CSS = """
:root {
  --bg: #F0F4F8; --surface: #FFFFFF; --surface2: #F8FAFC;
  --navy: #1E3A5F; --sky: #2563EB; --sky-lt: #EFF6FF;
  --orange: #EA580C; --orange-lt: #FFF7ED;
  --purple: #7C3AED; --purple-lt: #F5F3FF;
  --rust: #B45309; --rust-lt: #FFFBEB;
  --mint: #059669; --mint-lt: #D1FAE5;
  --text: #1E293B; --text-muted: #64748B; --text-light: #94A3B8;
  --border: #E2E8F0; --border-focus: #93C5FD;
  --shadow: 0 1px 3px rgba(0,0,0,.08), 0 1px 2px rgba(0,0,0,.05);
  --shadow-md: 0 4px 12px rgba(0,0,0,.08);
  --radius: 10px; --radius-sm: 6px;
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body { font-family: -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;
  background: var(--bg); color: var(--text); font-size: 14px; line-height: 1.6; }

/* ── Site header ── */
.site-header {
  background: var(--navy); color: #FFFFFF; height: 52px;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 24px; position: sticky; top: 0; z-index: 200;
  box-shadow: 0 2px 8px rgba(0,0,0,.15);
}
.site-header * { color: inherit; }
.logo { font-weight: 700; font-size: 15px; letter-spacing: .3px; color: #FFFFFF; }
.logo span { color: #93C5FD; }
.header-nav { display: flex; gap: 4px; }
.header-nav a {
  color: rgba(255,255,255,.75) !important; text-decoration: none;
  padding: 6px 14px; border-radius: var(--radius-sm); font-size: 13px; transition: all .15s;
}
.header-nav a:hover, .header-nav a.active {
  background: rgba(255,255,255,.18); color: #FFFFFF !important;
}

/* ── Hero ── */
.hero {
  background: linear-gradient(135deg, #1E3A5F 0%, #1B4080 100%);
  color: #FFFFFF; padding: 40px 24px 32px; text-align: center;
}
.hero * { color: inherit; }
.hero-badge {
  display: inline-block; background: rgba(255,255,255,.15); border: 1px solid rgba(255,255,255,.3);
  border-radius: 20px; padding: 3px 14px; font-size: 12px; margin-bottom: 12px; color: #BAE6FD;
}
.hero h1 { font-size: clamp(20px,3.5vw,32px); font-weight: 700; line-height: 1.3; color: #FFFFFF; }
.hero h1 em { color: #93C5FD; font-style: normal; }
.hero-meta { margin-top: 8px; color: rgba(255,255,255,.75); font-size: 13px; }
.hero-meta strong { color: #FFFFFF; }

/* ── Market tabs ── */
.market-tabs-bar {
  background: white; border-bottom: 2px solid var(--border);
  display: flex; gap: 0; overflow-x: auto; scrollbar-width: none;
  position: sticky; top: 52px; z-index: 100; padding: 0 12px;
}
.market-tabs-bar::-webkit-scrollbar { display: none; }
.mkt-tab {
  background: none; border: none; cursor: pointer; padding: 12px 18px;
  color: var(--text-muted); font-size: 13px; font-weight: 500;
  white-space: nowrap; border-bottom: 2px solid transparent;
  margin-bottom: -2px; transition: all .15s; font-family: inherit;
}
.mkt-tab:hover { color: var(--text); }
.mkt-tab.active { color: var(--sky); border-bottom-color: var(--sky); font-weight: 600; }

/* ── Overview grid ── */
.overview-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(200px,1fr)); gap: 12px;
}
.overview-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
  padding: 16px; cursor: pointer; transition: all .2s;
}
.overview-card:hover { border-color: var(--border-focus); box-shadow: var(--shadow-md); transform: translateY(-2px); }
.ov-flag { font-size: 28px; margin-bottom: 6px; }
.ov-name { font-weight: 700; font-size: 15px; margin-bottom: 10px; color: var(--navy); }
.ov-stats { display: flex; flex-direction: column; gap: 4px; }
.ov-stat { display: flex; justify-content: space-between; font-size: 12px; }
.ov-stat span { color: var(--text-muted); }
.ov-stat strong { color: var(--text); }

/* ── Section ── */
.page-section { padding: 28px 24px; max-width: 1300px; margin: 0 auto; }
.market-sheet { display: none; }
.market-sheet.active { display: block; }

/* ── Section header ── */
.sec-header {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 16px; border-radius: var(--radius-sm);
  font-weight: 700; font-size: 13px; margin: 24px 0 14px;
}
.sec-pc     { background: var(--sky-lt);    color: #1D4ED8; border-left: 3px solid var(--sky); }
.sec-mob    { background: var(--orange-lt); color: #C2410C; border-left: 3px solid var(--orange); }
.sec-mkt    { background: var(--purple-lt); color: #6D28D9; border-left: 3px solid var(--purple); }
.sec-pol    { background: var(--rust-lt);   color: #92400E; border-left: 3px solid var(--rust); }

/* ── Rank cards ── */
.rank-cards { display: flex; flex-direction: column; gap: 10px; }
.rank-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 14px 16px; transition: border-color .15s;
}
.rank-card:hover { border-color: var(--border-focus); }
.rank-card-header { display: flex; align-items: flex-start; gap: 12px; margin-bottom: 8px; }
.rank-num {
  background: var(--sky); color: white; border-radius: 6px;
  padding: 2px 10px; font-size: 13px; font-weight: 700; flex-shrink: 0; margin-top: 3px;
}
.rank-name { font-weight: 600; font-size: 14px; color: var(--navy); margin-bottom: 4px; }
.rank-meta { display: flex; flex-wrap: wrap; gap: 4px; }
.rank-content { font-size: 12px; color: #334155; margin: 6px 0; border-left: 2px solid var(--border); padding-left: 10px; }
.rank-feedback { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 8px; }
@media (max-width: 600px) { .rank-feedback { grid-template-columns: 1fr; } }
.fb-pos, .fb-neg { border-radius: var(--radius-sm); padding: 8px 10px; font-size: 12px; }
.fb-pos { background: #F0FDF4; border: 1px solid #BBF7D0; }
.fb-neg { background: #FFF1F2; border: 1px solid #FECDD3; }
.fb-label { font-weight: 600; display: block; margin-bottom: 3px; font-size: 11px; }
.fb-pos .fb-label { color: #059669; }
.fb-neg .fb-label { color: #DC2626; }

/* ── Chips ── */
.chip {
  display: inline-block; border-radius: 4px; padding: 1px 8px; font-size: 11px; font-weight: 500;
}
.chip-type { background: #E0F2FE; color: #0369A1; }
.chip-plat { background: #F1F5F9; color: #475569; }
.chip-dev  { background: #FAF5FF; color: #7E22CE; }

/* ── Tabs (iOS/Android) ── */
.tab-group { }
.tabs { display: flex; gap: 6px; margin-bottom: 12px; flex-wrap: wrap; }
.tab-btn {
  background: var(--surface); border: 1px solid var(--border); border-radius: 20px;
  padding: 5px 14px; font-size: 12px; cursor: pointer; font-family: inherit;
  color: var(--text-muted); transition: all .15s;
}
.tab-btn:hover { border-color: var(--sky); color: var(--sky); }
.tab-btn.active { background: var(--sky); border-color: var(--sky); color: white; font-weight: 600; }

/* ── Marketing cards ── */
.mkt-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(400px,1fr)); gap: 12px; }
@media (max-width: 860px) { .mkt-cards { grid-template-columns: 1fr; } }
.mkt-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px 16px;
}
.mkt-card-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; margin-bottom: 10px; }
.mkt-left { flex: 1; min-width: 0; }
.mkt-game { font-weight: 700; font-size: 14px; color: var(--navy); margin-bottom: 4px; }
.dim-badge { flex-shrink: 0; border-radius: 6px; padding: 3px 10px; font-size: 11px; font-weight: 600; }
.mkt-body { font-size: 12px; color: #334155; border-top: 1px solid var(--border); padding-top: 8px; }
.mkt-row { display: flex; gap: 8px; margin-bottom: 6px; align-items: flex-start; }
.mkt-label { flex-shrink: 0; color: var(--text-muted); font-weight: 600; min-width: 56px; padding-top: 1px; }
.kpi-text { color: #0369A1; font-weight: 500; }
.mkt-feedback { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 8px; }
@media (max-width: 600px) { .mkt-feedback { grid-template-columns: 1fr; } }

/* ── Policy cards ── */
.policy-list { display: flex; flex-direction: column; gap: 10px; }
.policy-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px 16px;
  border-left: 3px solid var(--rust);
}
.policy-card-header { display: flex; flex-wrap: wrap; align-items: flex-start; gap: 8px; margin-bottom: 8px; }
.policy-type-badge { border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: 600; flex-shrink: 0; }
.policy-title { font-weight: 600; font-size: 14px; color: var(--navy); flex: 1; }
.policy-source { color: var(--text-muted); font-size: 11px; width: 100%; }
.policy-detail { font-size: 12px; color: #334155; margin: 6px 0; border-left: 2px solid var(--border); padding-left: 10px; }
.policy-impact { font-size: 12px; color: #0369A1; margin: 6px 0; border-left: 2px solid #93C5FD; padding-left: 10px; }
.policy-risk { font-size: 12px; color: #991B1B; background: #FEF2F2; border-radius: var(--radius-sm); padding: 6px 10px; margin-top: 6px; }

/* ── Bullet list ── */
.bullet-list { padding-left: 14px; font-size: 12px; }
.bullet-list li { margin-bottom: 2px; }
.text-cell { font-size: 12px; }
.empty { color: var(--text-muted); font-size: 13px; padding: 12px 0; }

/* ── Footer ── */
footer {
  text-align: center; padding: 28px 24px; color: var(--text-muted);
  font-size: 12px; border-top: 1px solid var(--border); background: white; margin-top: 32px;
}

@media (max-width: 768px) {
  .site-header { padding: 0 16px; }
  .page-section { padding: 16px; }
  .hero { padding: 28px 16px 24px; }
  .mkt-cards { grid-template-columns: 1fr; }
}
"""

JS = """
function activateMarket(name) {
  document.querySelectorAll('.mkt-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.market-sheet').forEach(s => s.classList.remove('active'));
  const tab = document.querySelector(`.mkt-tab[data-market="${name}"]`);
  const sheet = document.getElementById('sheet-' + name);
  if (tab) tab.classList.add('active');
  if (sheet) sheet.classList.add('active');
  window.scrollTo({top: document.querySelector('.market-tabs-bar').offsetTop - 60, behavior:'smooth'});
}
function switchTab(btn, panelId) {
  const group = btn.closest('.tab-group');
  group.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  group.querySelectorAll('.tab-panel').forEach(p => p.style.display = 'none');
  btn.classList.add('active');
  const panel = document.getElementById('panel-' + panelId);
  if (panel) panel.style.display = '';
}
// Active nav
const page = location.pathname.split('/').pop() || 'index.html';
document.querySelectorAll('.header-nav a').forEach(a => {
  if (a.getAttribute('href') === page || (page==='' && a.getAttribute('href')==='index.html'))
    a.classList.add('active');
});
// Activate first market tab
const firstTab = document.querySelector('.mkt-tab');
if (firstTab) activateMarket(firstTab.dataset.market);
"""


def generate_html(
    title_main, title_sub, period, report_type,
    markets, output_path, is_weekly=False
):
    # Market tabs
    market_tabs = ''.join(
        f'<button class="mkt-tab" data-market="{esc(m["name"])}">'
        f'{MARKET_FLAGS.get(m["name"],"🌐")} {esc(m["name"])}</button>'
        for m in markets
    )

    # Market sheets
    sheets = []
    for m in markets:
        sid = esc(m['name'])
        # Assign unique id per market for mobile tabs
        mob_id = sid.replace('大陆','cn').replace('美国','us').replace('欧洲','eu').replace('日本','jp').replace('韩国','kr').replace('港台','tw').replace('东南亚','sea').replace('俄罗斯','ru')
        sheets.append(f"""
<div class="market-sheet" id="sheet-{sid}">
  <div class="page-section">
    <div class="sec-header sec-pc">🖥️ 一、PC / 主机热门游戏榜单（TOP 5）</div>
    {render_rank_cards(m['pc_ranks'])}

    <div class="sec-header sec-mob">📱 二、手游热门游戏榜单（畅销 + 下载 TOP 10）</div>
    {render_mobile_tabs(m['mobile_ranks'], mob_id)}

    <div class="sec-header sec-mkt">📣 三、重点营销热点详情</div>
    {render_mkt_cards(m['mkt_rows'])}

    <div class="sec-header sec-pol">⚖️ 四、区域产业政策热闻</div>
    {render_policy_cards(m['policy_rows'])}
  </div>
</div>""")

    overview = f"""
<div class="page-section" id="overview">
  <div style="font-weight:700;font-size:16px;color:var(--navy);margin-bottom:14px">📊 各市场快览</div>
  {render_overview_cards(markets)}
</div>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title_main)} {esc(title_sub)}</title>
<style>{CSS}</style>
</head>
<body>
<header class="site-header">
  <div class="logo">🎮 <span>KL</span> 全球游戏市场情报</div>
  <nav class="header-nav">
    <a href="index.html">周报</a>
    <a href="monthly.html">月报</a>
  </nav>
</header>

<div class="hero">
  <div class="hero-badge">{esc(report_type)}</div>
  <h1>{esc(title_main)}<br><em>{esc(title_sub)}</em></h1>
  <div class="hero-meta">分析周期：<strong>{esc(period)}</strong> &nbsp;·&nbsp; 生成时间：<strong>{datetime.now().strftime("%Y-%m-%d %H:%M")}</strong></div>
</div>

{overview}

<div class="market-tabs-bar">
{market_tabs}
</div>

{''.join(sheets)}

<footer>
  本报告由 KL游戏市场情报系统自动生成 · 数据来源：官方平台 / 权威媒体 / 第三方数据平台<br>
  <a href="index.html" style="color:var(--sky)">📅 最新周报</a> &nbsp;·&nbsp; <a href="monthly.html" style="color:var(--sky)">📊 最新月报</a>
</footer>

<script>{JS}</script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML generated: {output_path}")
    return output_path


if __name__ == "__main__":
    print("html_generator v2 loaded.")
