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
import os

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
def render_pc_cards(rows):
    """PC/Console: 5 cards in a horizontal row, clean and compact."""
    if not rows: return '<p class="empty">暂无数据</p>'
    html = ['<div class="pc-grid">']
    for row in rows:
        while len(row) < 8: row = list(row) + [""]
        rank, name, typ, dev, platform, content, pos_fb, neg_fb = [str(c) if c else "" for c in row[:8]]
        # Extract rank number
        rank_num = re.sub(r'[^0-9]', '', rank) or rank[:3]
        plat_short = platform.split('/')[0].split('·')[0].strip() if platform else ""
        html.append(f'''
<div class="pc-card">
  <div class="pc-rank">#{rank_num}</div>
  <div class="pc-name">{esc(name)}</div>
  <div class="pc-chips">
    <span class="chip chip-type">{esc(typ)}</span>
    {'<span class="chip chip-plat">'+esc(plat_short)+'</span>' if plat_short else ''}
  </div>
  {'<div class="pc-dev">🏢 '+esc(dev)+'</div>' if dev else ''}
  {'<div class="pc-content">'+text_to_bullets(content)+'</div>' if content else ''}
  {'<div class="pc-feedback">' + (f'<div class="fb-pos mini"><span class="fb-label">👍</span>{text_to_bullets(pos_fb)}</div>' if pos_fb else '') + (f'<div class="fb-neg mini"><span class="fb-label">👎</span>{text_to_bullets(neg_fb)}</div>' if neg_fb else '') + '</div>' if (pos_fb or neg_fb) else ''}
</div>''')
    html.append('</div>')
    return ''.join(html)

def render_rank_cards(rows):
    """Generic vertical rank cards (used by mobile tab panels)."""
    if not rows: return '<p class="empty">暂无数据</p>'
    html = ['<div class="mob-list">']
    for row in rows:
        while len(row) < 8: row = list(row) + [""]
        rank, name, typ, dev, platform, content, pos_fb, neg_fb = [str(c) if c else "" for c in row[:8]]
        rank_clean = re.sub(r'^(畅销|下载)#?', '', rank).strip()
        html.append(f'''
<div class="mob-card">
  <div class="mob-left">
    <span class="mob-rank">{esc(rank_clean)}</span>
    <div>
      <div class="mob-name">{esc(name)}</div>
      <div class="mob-chips">
        <span class="chip chip-type">{esc(typ)}</span>
        {'<span class="chip chip-plat">'+esc(platform)+'</span>' if platform else ''}
        {'<span class="chip chip-dev">'+esc(dev)+'</span>' if dev else ''}
      </div>
    </div>
  </div>
  {'<div class="mob-content">'+text_to_bullets(content)+'</div>' if content else ''}
  {'<div class="mob-feedback">' + (f'<div class="fb-pos mini"><span class="fb-label">👍</span>{text_to_bullets(pos_fb)}</div>' if pos_fb else '') + (f'<div class="fb-neg mini"><span class="fb-label">👎</span>{text_to_bullets(neg_fb)}</div>' if neg_fb else '') + '</div>' if (pos_fb or neg_fb) else ''}
</div>''')
    html.append('</div>')
    return ''.join(html)

# ── Mobile tab renderer ───────────────────────────────────────────────────────
def render_mobile_tabs(rows, sheet_id):
    if not rows: return '<p class="empty">暂无数据</p>'

    def has(row, *kws):
        t = str(row[0]) + str(row[4] if len(row)>4 else '')
        return any(k in t for k in kws)

    # Split by 畅销 / 下载
    hot_rows  = [r for r in rows if '畅销' in str(r[0])]
    dl_rows   = [r for r in rows if '下载' in str(r[0])]
    # Split by platform
    ios_rows  = [r for r in rows if any(x in str(r[4] if len(r)>4 else '') for x in ['iOS','App Store'])]
    and_rows  = [r for r in rows if any(x in str(r[4] if len(r)>4 else '') for x in ['Google','Play','Android','安卓'])]

    tabs = [("all", f"全部 {len(rows)}", rows)]
    if hot_rows:  tabs.append(("hot",     f"💰 畅销榜 {len(hot_rows)}", hot_rows))
    if dl_rows:   tabs.append(("dl",      f"⬇️ 下载榜 {len(dl_rows)}",  dl_rows))
    if ios_rows:  tabs.append(("ios",     f"🍎 iOS {len(ios_rows)}",    ios_rows))
    if and_rows:  tabs.append(("android", f"🤖 Android {len(and_rows)}", and_rows))

    html = [f'<div class="tab-group" id="mob-tabs-{sheet_id}">']
    html.append('<div class="tabs">')
    for i, (tid, label, _) in enumerate(tabs):
        active = 'active' if i==0 else ''
        html.append(f'<button class="tab-btn {active}" onclick="switchTab(this,\'{sheet_id}-{tid}\')">{label}</button>')
    html.append('</div>')
    for i, (tid, _, tab_rows) in enumerate(tabs):
        display = '' if i==0 else 'style="display:none"'
        html.append(f'<div class="tab-panel" id="panel-{sheet_id}-{tid}" {display}>')
        html.append(render_rank_cards(tab_rows))
        html.append('</div>')
    html.append('</div>')
    return ''.join(html)

# ── Marketing cards (merged by game, sorted by action count) ─────────────────
def render_mkt_cards(rows):
    if not rows: return '<p class="empty">暂无数据</p>'

    # Group by game name
    from collections import OrderedDict
    groups = OrderedDict()
    for row in rows:
        while len(row) < 8: row = list(row) + [""]
        game = str(row[0]) if row[0] else "—"
        if game not in groups: groups[game] = []
        groups[game].append(row)

    # Sort: most actions first
    sorted_groups = sorted(groups.items(), key=lambda x: -len(x[1]))

    html = ['<div class="mkt-cards">']
    for game, game_rows in sorted_groups:
        # Use first row for top-level info
        typ = str(game_rows[0][1]) if len(game_rows[0])>1 else ""
        # Collect all feedbacks
        all_pos = '; '.join(str(r[6]) for r in game_rows if len(r)>6 and str(r[6]).strip())
        all_neg = '; '.join(str(r[7]) for r in game_rows if len(r)>7 and str(r[7]).strip())

        # Build action blocks
        action_blocks = []
        for r in game_rows:
            dim  = str(r[2]) if len(r)>2 else ""
            act  = str(r[3]) if len(r)>3 else ""
            plat = str(r[4]) if len(r)>4 else ""
            kpi  = str(r[5]) if len(r)>5 else ""
            bg, color, icon = dim_style(dim)
            parts = []
            if act:  parts.append(f'<div class="ab-action">{text_to_bullets(act)}</div>')
            if plat: parts.append(f'<div class="ab-meta"><span class="ab-label">平台</span>{esc(plat)}</div>')
            if kpi:  parts.append(f'<div class="ab-meta kpi-text"><span class="ab-label">爆点</span>{text_to_bullets(kpi)}</div>')
            action_blocks.append(f'<div class="action-block"><span class="dim-badge" style="background:{bg};color:{color}">{icon} {esc(dim)}</span>{"".join(parts)}</div>')

        multi = len(game_rows) > 1
        counter = f'<span class="action-count">{len(game_rows)}个动作</span>' if multi else ''

        html.append(f'''
<div class="mkt-card">
  <div class="mkt-card-top">
    <div class="mkt-left">
      <div class="mkt-game">{esc(game)} {counter}</div>
      <span class="chip chip-type">{esc(typ)}</span>
    </div>
  </div>
  <div class="mkt-actions">{"".join(action_blocks)}</div>
  {'<div class="mkt-feedback"><div class="fb-pos"><span class="fb-label">👍 正面</span>'+text_to_bullets(all_pos)+'</div><div class="fb-neg"><span class="fb-label">👎 负面</span>'+text_to_bullets(all_neg)+'</div></div>' if all_pos or all_neg else ''}
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
.page-section { padding: 16px 20px; max-width: 1300px; margin: 0 auto; }
.market-sheet { display: none; }
.market-sheet.active { display: block; }

/* ── Section header ── */
.sec-header {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 14px; border-radius: 6px;
  font-weight: 700; font-size: 13px; margin: 16px 0 10px;
}
.sec-pc     { background: var(--sky-lt);    color: #1D4ED8; border-left: 3px solid var(--sky); }
.sec-mob    { background: var(--orange-lt); color: #C2410C; border-left: 3px solid var(--orange); }
.sec-mkt    { background: var(--purple-lt); color: #6D28D9; border-left: 3px solid var(--purple); }
.sec-pol    { background: var(--rust-lt);   color: #92400E; border-left: 3px solid var(--rust); }

/* ── PC Grid (5 across) ── */
.pc-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 8px;
  margin-bottom: 4px;
}
@media (max-width: 1100px) { .pc-grid { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 700px)  { .pc-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 460px)  { .pc-grid { grid-template-columns: 1fr; } }
.pc-card {
  background: white; border: 1px solid var(--border);
  border-radius: var(--radius); padding: 12px 10px;
  display: flex; flex-direction: column; gap: 4px;
  transition: all .2s; border-top: 3px solid var(--sky);
}
.pc-card:hover { border-color: var(--border-focus); box-shadow: var(--shadow-md); transform: translateY(-2px); }
.pc-rank { font-size: 24px; font-weight: 800; color: var(--sky); line-height: 1; letter-spacing: -1px; }
.pc-name { font-weight: 700; font-size: 13px; color: var(--navy); line-height: 1.3; }
.pc-chips { display: flex; flex-wrap: wrap; gap: 3px; }
.pc-dev { font-size: 11px; color: var(--text-muted); }
.pc-content { font-size: 11px; color: #475569; border-top: 1px solid var(--border); padding-top: 5px; margin-top: 2px; }
.pc-feedback { padding-top: 4px; display: flex; flex-direction: column; gap: 3px; }

/* ── Mobile list ── */
.mob-list { display: flex; flex-direction: column; gap: 6px; }
.mob-card {
  background: white; border: 1px solid var(--border);
  border-radius: 8px; padding: 10px 12px;
  border-left: 3px solid var(--orange);
}
.mob-left { display: flex; align-items: flex-start; gap: 8px; margin-bottom: 4px; }
.mob-rank {
  background: var(--orange); color: white; border-radius: 5px;
  padding: 2px 8px; font-size: 12px; font-weight: 700; flex-shrink: 0; min-width: 28px; text-align: center;
}
.mob-name { font-weight: 600; font-size: 13px; color: var(--navy); margin-bottom: 2px; }
.mob-chips { display: flex; flex-wrap: wrap; gap: 3px; }
.mob-content { font-size: 11px; color: #475569; border-left: 2px solid var(--border); padding-left: 7px; margin: 3px 0; }
.mob-feedback { display: grid; grid-template-columns: 1fr 1fr; gap: 4px; margin-top: 4px; }
@media (max-width: 500px) { .mob-feedback { grid-template-columns: 1fr; } }

/* ── Feedback mini ── */
.fb-pos.mini, .fb-neg.mini { padding: 4px 7px; font-size: 11px; }
.fb-pos.mini .fb-label, .fb-neg.mini .fb-label { display: inline; margin-right: 4px; }
.fb-pos { background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: var(--radius-sm); padding: 6px 8px; font-size: 11px; }
.fb-neg { background: #FFF1F2; border: 1px solid #FECDD3; border-radius: var(--radius-sm); padding: 6px 8px; font-size: 11px; }
.fb-label { font-weight: 600; display: block; margin-bottom: 2px; font-size: 10px; }
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
.mkt-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(380px,1fr)); gap: 10px; }
@media (max-width: 820px) { .mkt-cards { grid-template-columns: 1fr; } }
.mkt-card {
  background: white; border: 1px solid var(--border); border-radius: var(--radius); padding: 12px 14px;
  border-top: 3px solid var(--purple);
}
.mkt-card-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 6px; margin-bottom: 8px; }
.mkt-left { flex: 1; min-width: 0; }
.mkt-game { font-weight: 700; font-size: 14px; color: var(--navy); margin-bottom: 3px; display: flex; align-items: center; gap: 6px; }
.action-count { background: var(--purple-lt); color: var(--purple); border-radius: 10px; padding: 1px 7px; font-size: 11px; font-weight: 600; }
.dim-badge { flex-shrink: 0; border-radius: 5px; padding: 2px 8px; font-size: 11px; font-weight: 600; }
/* Action blocks inside mkt card */
.mkt-actions { display: flex; flex-direction: column; gap: 6px; }
.action-block {
  background: var(--surface2); border-radius: 6px; padding: 8px 10px;
  display: flex; flex-direction: column; gap: 4px;
}
.action-block .dim-badge { align-self: flex-start; margin-bottom: 2px; }
.ab-action { font-size: 12px; color: #334155; }
.ab-meta { font-size: 11px; color: var(--text-muted); display: flex; gap: 4px; align-items: flex-start; }
.ab-label { font-weight: 600; flex-shrink: 0; color: #64748B; min-width: 28px; }
.kpi-text { color: #0369A1 !important; font-weight: 500; }
.mkt-feedback { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-top: 8px; }
@media (max-width: 500px) { .mkt-feedback { grid-template-columns: 1fr; } }

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
  const tab = document.querySelector('.mkt-tab[data-market="' + name + '"]');
  const sheet = document.getElementById('sheet-' + name);
  if (tab) tab.classList.add('active');
  if (sheet) sheet.classList.add('active');
  const bar = document.querySelector('.market-tabs-bar');
  if (bar) window.scrollTo({top: bar.offsetTop - 54, behavior:'smooth'});
}
function switchTab(btn, panelId) {
  const group = btn.closest('.tab-group');
  group.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  group.querySelectorAll('.tab-panel').forEach(p => p.style.display = 'none');
  btn.classList.add('active');
  const panel = document.getElementById('panel-' + panelId);
  if (panel) panel.style.display = 'block';
}
// Attach click handlers to market tabs
document.querySelectorAll('.mkt-tab').forEach(function(btn) {
  btn.addEventListener('click', function() {
    activateMarket(this.dataset.market);
  });
});
// Active nav link
const page = location.pathname.split('/').pop() || 'index.html';
document.querySelectorAll('.header-nav a').forEach(a => {
  if (a.getAttribute('href') === page || (page==='' && a.getAttribute('href')==='index.html'))
    a.classList.add('active');
});
// Activate first market
const firstTab = document.querySelector('.mkt-tab');
if (firstTab) activateMarket(firstTab.dataset.market);
"""

# ── Archive styles ────────────────────────────────────────────────────────────
ARCHIVE_CSS_EXTRA = """
/* ── Archive bar ── */
.archive-bar {
  background: #F8FAFC; border-bottom: 1px solid var(--border);
  padding: 8px 24px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
}
.archive-bar .ab-label { color: var(--text-muted); font-size: 12px; font-weight: 600; }
.archive-btn {
  background: white; border: 1px solid var(--border); border-radius: 16px;
  padding: 3px 12px; font-size: 12px; color: var(--text-muted);
  text-decoration: none; transition: all .15s; white-space: nowrap;
}
.archive-btn:hover { border-color: var(--sky); color: var(--sky); background: var(--sky-lt); }
.archive-btn.current { background: var(--sky); border-color: var(--sky); color: white; font-weight: 600; }
.archive-sep { color: var(--border); font-size: 16px; }
/* ── Archive index ── */
.archive-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px,1fr)); gap: 12px; }
.archive-card {
  background: white; border: 1px solid var(--border); border-radius: var(--radius);
  padding: 16px; text-decoration: none; display: block; transition: all .2s;
}
.archive-card:hover { border-color: var(--border-focus); box-shadow: var(--shadow-md); transform: translateY(-1px); }
.archive-card .ac-type { font-size: 11px; font-weight: 600; color: var(--text-muted); margin-bottom: 6px; }
.archive-card .ac-title { font-weight: 700; font-size: 14px; color: var(--navy); margin-bottom: 4px; }
.archive-card .ac-period { font-size: 12px; color: var(--text-muted); }
.archive-card .ac-badge { display: inline-block; margin-top: 8px; background: var(--sky-lt); color: var(--sky); border-radius: 4px; padding: 1px 8px; font-size: 11px; font-weight: 600; }
"""

def generate_archive_bar(archive_weekly, archive_monthly, current_file, is_weekly):
    """Generate a compact bar showing links to past reports."""
    if not archive_weekly and not archive_monthly:
        return ""
    parts = ['<div class="archive-bar">']
    if archive_weekly:
        parts.append('<span class="ab-label">📅 往期周报：</span>')
        for item in archive_weekly:
            cls = "archive-btn current" if item['file'] == current_file else "archive-btn"
            parts.append(f'<a href="{esc(item["file"])}" class="{cls}">{esc(item["label"])}</a>')
    if archive_weekly and archive_monthly:
        parts.append('<span class="archive-sep">|</span>')
    if archive_monthly:
        parts.append('<span class="ab-label">📊 往期月报：</span>')
        for item in archive_monthly:
            cls = "archive-btn current" if item['file'] == current_file else "archive-btn"
            parts.append(f'<a href="{esc(item["file"])}" class="{cls}">{esc(item["label"])}</a>')
    parts.append('<a href="archive.html" class="archive-btn" style="margin-left:auto">🗂️ 全部存档</a>')
    parts.append('</div>')
    return ''.join(parts)


def generate_archive_index(archive_weekly, archive_monthly, output_path):
    """Generate docs/archive.html — full archive index."""
    cards = []
    for item in (archive_monthly or []):
        cards.append(f'''<a href="{esc(item['file'])}" class="archive-card">
  <div class="ac-type">📊 月度报告</div>
  <div class="ac-title">{esc(item['title'])}</div>
  <div class="ac-period">{esc(item['period'])}</div>
  <span class="ac-badge">月报</span>
</a>''')
    for item in (archive_weekly or []):
        cards.append(f'''<a href="{esc(item['file'])}" class="archive-card">
  <div class="ac-type">📅 周报</div>
  <div class="ac-title">{esc(item['title'])}</div>
  <div class="ac-period">{esc(item['period'])}</div>
  <span class="ac-badge" style="background:#FFF7ED;color:#C2410C">周报</span>
</a>''')

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>报告存档 - KL全球游戏市场情报</title>
<style>{CSS}{ARCHIVE_CSS_EXTRA}</style>
</head>
<body>
<header class="site-header">
  <div class="logo">🎮 <span>KL</span> 全球游戏市场情报</div>
  <nav class="header-nav">
    <a href="index.html">最新周报</a>
    <a href="monthly.html">最新月报</a>
    <a href="archive.html" class="active">存档</a>
  </nav>
</header>
<div class="hero">
  <div class="hero-badge">🗂️ 报告存档</div>
  <h1>往期报告<br><em>全部周报 · 月报</em></h1>
  <div class="hero-meta">点击卡片查看历史报告</div>
</div>
<div class="page-section">
  <div style="font-weight:700;font-size:16px;color:var(--navy);margin-bottom:14px">📁 所有报告（最新在前）</div>
  <div class="archive-grid">
    {''.join(cards)}
  </div>
</div>
<footer>KL游戏市场情报系统 · <a href="index.html" style="color:var(--sky)">返回最新周报</a></footer>
</body>
</html>"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Archive index generated: {output_path}")


def generate_html(
    title_main, title_sub, period, report_type,
    markets, output_path, is_weekly=False,
    archive_weekly=None, archive_monthly=None
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
        mob_id = sid.replace('大陆','cn').replace('美国','us').replace('欧洲','eu').replace('日本','jp').replace('韩国','kr').replace('港台','tw').replace('东南亚','sea').replace('俄罗斯','ru')
        sheets.append(f"""
<div class="market-sheet" id="sheet-{sid}">
  <div class="page-section">
    <div class="sec-header sec-pc">🖥️ 一、PC / 主机热门游戏榜单（TOP 5）</div>
    {render_pc_cards(m['pc_ranks'])}

    <div class="sec-header sec-mob">📱 二、手游热门游戏榜单（畅销 + 下载 TOP 10）</div>
    {render_mobile_tabs(m['mobile_ranks'], mob_id)}

    <div class="sec-header sec-mkt">📣 三、重点营销热点详情</div>
    {render_mkt_cards(m['mkt_rows'])}

    <div class="sec-header sec-pol">⚖️ 四、区域产业政策热闻</div>
    {render_policy_cards(m['policy_rows'])}
  </div>
</div>""")

    current_file = os.path.basename(output_path)
    archive_bar = generate_archive_bar(archive_weekly, archive_monthly, current_file, is_weekly)

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
<style>{CSS}{ARCHIVE_CSS_EXTRA}</style>
</head>
<body>
<header class="site-header">
  <div class="logo">🎮 <span>KL</span> 全球游戏市场情报</div>
  <nav class="header-nav">
    <a href="index.html">周报</a>
    <a href="monthly.html">月报</a>
    <a href="archive.html">🗂️ 存档</a>
  </nav>
</header>

<div class="hero">
  <div class="hero-badge">{esc(report_type)}</div>
  <h1>{esc(title_main)}<br><em>{esc(title_sub)}</em></h1>
  <div class="hero-meta">分析周期：<strong>{esc(period)}</strong> &nbsp;·&nbsp; 生成时间：<strong>{datetime.now().strftime("%Y-%m-%d %H:%M")}</strong></div>
</div>

{archive_bar}
{overview}

<div class="market-tabs-bar">
{market_tabs}
</div>

{''.join(sheets)}

<footer>
  本报告由 KL游戏市场情报系统自动生成 · 数据来源：官方平台 / 权威媒体 / 第三方数据平台<br>
  <a href="index.html" style="color:var(--sky)">📅 最新周报</a> &nbsp;·&nbsp;
  <a href="monthly.html" style="color:var(--sky)">📊 最新月报</a> &nbsp;·&nbsp;
  <a href="archive.html" style="color:var(--sky)">🗂️ 报告存档</a>
</footer>

<script>{JS}</script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML generated: {output_path}")
    return output_path


if __name__ == "__main__":
    print("html_generator v3 loaded.")

