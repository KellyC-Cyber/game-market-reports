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
    """PC/Console: 5 cards. Click to expand content+feedback."""
    if not rows: return '<p class="empty">暂无数据</p>'
    html = ['<div class="pc-grid">']
    for i, row in enumerate(rows):
        while len(row) < 8: row = list(row) + [""]
        rank, name, typ, dev, platform, content, pos_fb, neg_fb = [str(c) if c else "" for c in row[:8]]
        rank_num = re.sub(r'[^0-9]', '', rank) or rank[:3]
        plat_short = platform.split('/')[0].split('·')[0].strip() if platform else ""
        cid = f"pc-detail-{i}"
        has_detail = bool(content or pos_fb or neg_fb)
        detail_html = ""
        if has_detail:
            detail_html = f'<div class="collapsible" id="{cid}">'
            if content: detail_html += f'<div class="pc-content">{text_to_bullets(content)}</div>'
            if pos_fb or neg_fb:
                detail_html += '<div class="pc-feedback">'
                if pos_fb: detail_html += f'<div class="fb-pos mini"><span class="fb-label">👍</span>{text_to_bullets(pos_fb)}</div>'
                if neg_fb: detail_html += f'<div class="fb-neg mini"><span class="fb-label">👎</span>{text_to_bullets(neg_fb)}</div>'
                detail_html += '</div>'
            detail_html += '</div>'
        toggle = f' onclick="toggleDetail(\'{cid}\')" class="pc-card expandable"' if has_detail else ' class="pc-card"'
        html.append(f'''
<div{toggle}>
  <div class="pc-rank">#{rank_num}</div>
  <div class="pc-name">{esc(name)}</div>
  <div class="pc-chips">
    <span class="chip chip-type">{esc(typ)}</span>
    {'<span class="chip chip-plat">'+esc(plat_short)+'</span>' if plat_short else ''}
  </div>
  {'<div class="pc-dev">'+esc(dev)+'</div>' if dev else ''}
  {'<div class="expand-hint">点击展开详情</div>' if has_detail else ''}
  {detail_html}
</div>''')
    html.append('</div>')
    return ''.join(html)

def render_rank_cards(rows):
    """Mobile rank cards: click to expand content+feedback."""
    if not rows: return '<p class="empty">暂无数据</p>'
    html = ['<div class="mob-list">']
    for i, row in enumerate(rows):
        while len(row) < 8: row = list(row) + [""]
        rank, name, typ, dev, platform, content, pos_fb, neg_fb = [str(c) if c else "" for c in row[:8]]
        rank_clean = re.sub(r'^(畅销|下载)#?', '', rank).strip()
        cid = f"mob-detail-{id(rows)}-{i}"
        has_detail = bool(content or pos_fb or neg_fb)
        detail_html = ""
        if has_detail:
            detail_html = f'<div class="collapsible" id="{cid}">'
            if content: detail_html += f'<div class="mob-content">{text_to_bullets(content)}</div>'
            if pos_fb or neg_fb:
                detail_html += '<div class="mob-feedback">'
                if pos_fb: detail_html += f'<div class="fb-pos mini"><span class="fb-label">👍</span>{text_to_bullets(pos_fb)}</div>'
                if neg_fb: detail_html += f'<div class="fb-neg mini"><span class="fb-label">👎</span>{text_to_bullets(neg_fb)}</div>'
                detail_html += '</div>'
            detail_html += '</div>'
        toggle = f'onclick="toggleDetail(\'{cid}\')" ' if has_detail else ''
        expandable = 'expandable' if has_detail else ''
        html.append(f'''
<div class="mob-card {expandable}" {toggle}>
  <span class="mob-rank">{esc(rank_clean)}</span>
  <div class="mob-main">
    <div class="mob-name">{esc(name)}</div>
    <div class="mob-chips">
      <span class="chip chip-type">{esc(typ)}</span>
      {'<span class="chip chip-plat">'+esc(platform)+'</span>' if platform else ''}
      {'<span class="chip chip-dev">'+esc(dev)+'</span>' if dev else ''}
    </div>
    {detail_html}
  </div>
  {'<span class="expand-arrow">›</span>' if has_detail else ''}
</div>''')
    html.append('</div>')
    return ''.join(html)

# ── Mobile tab renderer (畅销/下载 only) ─────────────────────────────────────
def render_mobile_tabs(rows, sheet_id):
    if not rows: return '<p class="empty">暂无数据</p>'
    hot_rows = [r for r in rows if '畅销' in str(r[0])]
    dl_rows  = [r for r in rows if '下载' in str(r[0])]
    tabs = [("all", f"全部  {len(rows)}", rows)]
    if hot_rows: tabs.append(("hot", f"畅销榜  {len(hot_rows)}", hot_rows))
    if dl_rows:  tabs.append(("dl",  f"下载榜  {len(dl_rows)}",  dl_rows))
    html = [f'<div class="tab-group" id="mob-tabs-{sheet_id}">']
    html.append('<div class="tabs">')
    for i, (tid, label, _) in enumerate(tabs):
        active = 'active' if i == 0 else ''
        html.append(f'<button class="tab-btn {active}" onclick="switchTab(this,\'{sheet_id}-{tid}\')">{label}</button>')
    html.append('</div>')
    for i, (tid, _, tab_rows) in enumerate(tabs):
        display = '' if i == 0 else 'style="display:none"'
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
  <div class="mkt-actions collapsible" id="mkt-{abs(hash(game))}">{"".join(action_blocks)}</div>
  {'<div class="mkt-feedback collapsible" id="mktfb-'+str(abs(hash(game)))+'">'+'<div class="fb-pos"><span class="fb-label">👍 正面</span>'+text_to_bullets(all_pos)+'</div><div class="fb-neg"><span class="fb-label">👎 负面</span>'+text_to_bullets(all_neg)+'</div></div>' if all_pos or all_neg else ''}
  <div class="mkt-toggle" onclick="toggleMkt(this,'{abs(hash(game))}')">展开详情 ›</div>
</div>''')
    html.append('</div>')
    return ''.join(html)

# ── Policy cards ──────────────────────────────────────────────────────────────
def render_policy_cards(rows):
    if not rows: return '<p class="empty">暂无政策热闻数据</p>'
    # Type → short label for vertical text
    TYPE_LABELS = {'版号': '版号', '监管': '监管', '政策利好': '利好', '产业': '产业', '舆论': '舆论', '其他': '其他'}
    html = ['<div class="gazette-body-wrap"><div class="policy-gazette">']
    for i, row in enumerate(rows):
        while len(row) < 6: row = list(row) + [""]
        title, source, typ, detail, impact, risk = [str(c) if c else "" for c in row[:6]]
        typ_short = TYPE_LABELS.get(typ, typ[:2] if typ else '—')
        html.append(f'''
<div class="gazette-entry">
  <div class="gazette-left">
    <span class="gazette-num">{str(i+1).zfill(2)}</span>
    <span class="gazette-type-vert">{esc(typ_short)}</span>
  </div>
  <div class="gazette-body">
    <div class="gazette-headline">{esc(title)}</div>
    {'<div class="gazette-byline">'+esc(source)+'</div>' if source else ''}
    {'<div class="gazette-detail">'+text_to_bullets(detail)+'</div>' if detail else ''}
    {'<div class="gazette-impact">'+text_to_bullets(impact)+'</div>' if impact else ''}
    {'<div class="gazette-risk">⚠ 风险信号：'+text_to_bullets(risk)+'</div>' if risk else ''}
  </div>
</div>''')
    html.append('</div></div>')
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
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=Jost:wght@300;400;500;600;700&display=swap');

:root {
  --gold: #C9A84C; --gold-lt: #F5EDD4; --gold-dk: #9A7A2E;
  --ivory: #F7F3EC; --ivory-dk: #EDE6D8;
  --black: #0D0B08; --charcoal: #1C1A17; --dark: #2A2620;
  --mid: #6B6458; --light: #A89E94; --white: #FDFAF5;
  --border: #D4C8A8; --border-lt: #EAE0C8;
  --bg: var(--ivory); --surface: var(--white); --surface2: var(--ivory-dk);
  --shadow: 0 2px 8px rgba(13,11,8,.10);
  --shadow-md: 0 4px 16px rgba(13,11,8,.14);
  --radius: 2px; --radius-sm: 1px;
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body {
  font-family: 'Jost', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: var(--ivory); color: var(--charcoal); font-size: 15px; line-height: 1.7;
}
/* ── Site header ── */
.site-header {
  background: var(--black); height: 56px; padding: 0 28px;
  display: flex; align-items: center; justify-content: space-between;
  position: sticky; top: 0; z-index: 200;
  border-bottom: 2px solid var(--gold-dk);
}
.site-header * { color: var(--gold) !important; }
.logo { font-family: 'Cormorant Garamond', serif; font-weight: 700; font-size: 18px; letter-spacing: 3px; text-transform: uppercase; }
.logo span { color: var(--white) !important; font-weight: 300; }
.header-nav { display: flex; }
.header-nav a {
  color: var(--light) !important; text-decoration: none; padding: 8px 16px;
  font-size: 10px; letter-spacing: 2.5px; text-transform: uppercase; font-weight: 500;
  border-left: 1px solid rgba(201,168,76,.2); transition: all .15s;
}
.header-nav a:first-child { border-left: none; }
.header-nav a:hover, .header-nav a.active { color: var(--gold) !important; background: rgba(201,168,76,.1); }
/* ── Hero ── */
.hero {
  background: var(--black); padding: 44px 28px 36px; text-align: center;
  position: relative; overflow: hidden; border-bottom: 3px solid var(--gold);
}
.hero::before {
  content: ''; position: absolute; inset: 0;
  background: repeating-linear-gradient(-45deg, transparent, transparent 20px, rgba(201,168,76,.03) 20px, rgba(201,168,76,.03) 21px);
}
.hero-badge {
  display: inline-block; border: 1px solid var(--gold-dk);
  color: var(--gold); font-size: 10px; letter-spacing: 3px;
  text-transform: uppercase; padding: 4px 18px; margin-bottom: 14px;
}
.hero h1 {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(26px,4vw,46px); font-weight: 600; color: var(--white);
  letter-spacing: 2px; line-height: 1.2;
}
.hero h1 em { color: var(--gold); font-style: normal; }
.hero-meta { margin-top: 10px; color: var(--light); font-size: 12px; letter-spacing: 1px; }
.hero-meta strong { color: var(--gold-lt); }
/* ── Market tabs ── */
.market-tabs-bar {
  background: var(--charcoal); border-bottom: 2px solid var(--gold-dk);
  display: flex; overflow-x: auto; scrollbar-width: none;
  position: sticky; top: 56px; z-index: 100;
}
.market-tabs-bar::-webkit-scrollbar { display: none; }
.mkt-tab {
  background: none; border: none; cursor: pointer; padding: 12px 18px;
  color: var(--light); font-size: 10px; font-weight: 500; white-space: nowrap;
  letter-spacing: 2px; text-transform: uppercase; border-bottom: 2px solid transparent;
  margin-bottom: -2px; transition: all .15s; font-family: 'Jost', sans-serif;
}
.mkt-tab:hover { color: var(--gold-lt); }
.mkt-tab.active { color: var(--gold); border-bottom-color: var(--gold); font-weight: 600; }
/* ── Overview ── */
.overview-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px,1fr)); gap: 1px; border: 1px solid var(--border); background: var(--border); }
.overview-card { background: var(--white); padding: 14px; cursor: pointer; transition: background .15s; }
.overview-card:hover { background: var(--gold-lt); }
.ov-flag { font-size: 20px; margin-bottom: 5px; }
.ov-name { font-family: 'Cormorant Garamond', serif; font-weight: 600; font-size: 15px; color: var(--dark); margin-bottom: 7px; letter-spacing: .5px; }
.ov-stats { display: flex; flex-direction: column; gap: 2px; }
.ov-stat { display: flex; justify-content: space-between; font-size: 11px; }
.ov-stat span { color: var(--mid); } .ov-stat strong { color: var(--dark); }
/* ── Section ── */
.page-section { padding: 16px 22px; max-width: 1360px; margin: 0 auto; }
.market-sheet { display: none; } .market-sheet.active { display: block; }
.sec-header {
  display: flex; align-items: center; gap: 14px; padding: 0; margin: 18px 0 10px;
  font-family: 'Cormorant Garamond', serif; font-size: 15px; font-weight: 600;
  letter-spacing: 2.5px; text-transform: uppercase; color: var(--dark);
}
.sec-header::after { content: ''; flex: 1; height: 1px; background: var(--border); }
/* ── PC Grid ── */
.pc-grid { display: grid; grid-template-columns: repeat(5,1fr); gap: 1px; border: 1px solid var(--border); background: var(--border); }
@media (max-width: 1100px) { .pc-grid { grid-template-columns: repeat(3,1fr); } }
@media (max-width: 700px)  { .pc-grid { grid-template-columns: repeat(2,1fr); } }
.pc-card { background: var(--white); padding: 12px 11px; display: flex; flex-direction: column; gap: 4px; transition: background .15s; }
.pc-card:hover { background: var(--ivory); }
.pc-rank { font-family: 'Cormorant Garamond', serif; font-size: 34px; font-weight: 700; color: var(--gold); line-height: 1; }
.pc-name { font-weight: 600; font-size: 13px; color: var(--dark); line-height: 1.3; }
.pc-chips { display: flex; flex-wrap: wrap; gap: 2px; }
.pc-dev { font-size: 10px; color: var(--light); letter-spacing: .3px; }
.pc-content { font-size: 12px; color: var(--mid); border-top: 1px solid var(--border-lt); padding-top: 5px; margin-top: 2px; }
.pc-feedback { padding-top: 3px; display: flex; flex-direction: column; gap: 3px; }
/* ── Mobile list ── */
.mob-list { display: flex; flex-direction: column; gap: 1px; border: 1px solid var(--border); background: var(--border); }
.mob-card { background: var(--white); padding: 8px 12px; display: flex; align-items: flex-start; gap: 9px; transition: background .15s; }
.mob-card:hover { background: var(--ivory); }
.mob-rank { background: var(--gold); color: var(--black); font-family: 'Cormorant Garamond', serif; font-size: 15px; font-weight: 700; min-width: 30px; text-align: center; padding: 2px 5px; flex-shrink: 0; }
.mob-main { flex: 1; min-width: 0; }
.mob-name { font-weight: 600; font-size: 13px; color: var(--dark); }
.mob-chips { display: flex; flex-wrap: wrap; gap: 2px; margin-top: 2px; }
.mob-content { font-size: 12px; color: var(--mid); margin-top: 3px; }
.mob-feedback { display: grid; grid-template-columns: 1fr 1fr; gap: 3px; margin-top: 4px; }
@media (max-width: 500px) { .mob-feedback { grid-template-columns: 1fr; } }
/* ── Chips ── */
.chip { display: inline-block; border-radius: 0; padding: 2px 7px; font-size: 11px; font-weight: 500; letter-spacing: .5px; text-transform: uppercase; }
.chip-type { background: var(--ivory-dk); color: var(--mid); border: 1px solid var(--border); }
.chip-plat { background: transparent; color: var(--light); border: 1px solid var(--border-lt); }
.chip-dev  { background: transparent; color: var(--gold-dk); border: 1px solid rgba(201,168,76,.3); }
/* ── Mobile tabs ── */
.tabs { display: flex; gap: 0; margin-bottom: 8px; border: 1px solid var(--border); width: fit-content; }
.tab-btn { background: var(--white); border: none; border-right: 1px solid var(--border); padding: 5px 14px; font-size: 10px; letter-spacing: 2px; text-transform: uppercase; cursor: pointer; font-family: 'Jost', sans-serif; color: var(--mid); transition: all .15s; }
.tab-btn:last-child { border-right: none; }
.tab-btn:hover { background: var(--ivory-dk); color: var(--dark); }
.tab-btn.active { background: var(--gold); color: var(--black); font-weight: 600; }
/* ── Marketing cards ── */
.mkt-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px,1fr)); gap: 1px; background: var(--border); border: 1px solid var(--border); }
@media (max-width: 720px) { .mkt-cards { grid-template-columns: 1fr; } }
.mkt-card { background: var(--white); padding: 12px 14px; }
.mkt-card-top { margin-bottom: 8px; }
.mkt-game { font-family: 'Cormorant Garamond', serif; font-weight: 600; font-size: 17px; color: var(--dark); letter-spacing: .5px; display: flex; align-items: center; gap: 8px; margin-bottom: 2px; }
.action-count { background: var(--gold); color: var(--black); font-family: 'Jost', sans-serif; font-size: 10px; font-weight: 600; letter-spacing: 1px; padding: 1px 6px; text-transform: uppercase; }
.dim-badge { display: inline-block; border-radius: 0; padding: 2px 7px; font-size: 10px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; }
.mkt-actions { display: flex; flex-direction: column; gap: 5px; }
.action-block { background: var(--ivory); border-left: 2px solid var(--gold); padding: 7px 9px; display: flex; flex-direction: column; gap: 3px; }
.action-block .dim-badge { align-self: flex-start; margin-bottom: 2px; }
.ab-action { font-size: 13px; color: var(--charcoal); }
.ab-meta { font-size: 12px; color: var(--mid); display: flex; gap: 5px; align-items: flex-start; }
.ab-label { font-weight: 600; flex-shrink: 0; color: var(--gold-dk); min-width: 28px; }
.kpi-text { color: var(--dark) !important; font-weight: 500; }
.mkt-feedback { display: grid; grid-template-columns: 1fr 1fr; gap: 5px; margin-top: 7px; }
@media (max-width: 500px) { .mkt-feedback { grid-template-columns: 1fr; } }
/* ── Feedback ── */
.fb-pos, .fb-neg { border-radius: 0; padding: 6px 9px; font-size: 12px; }
.fb-pos { background: #F5FBF5; border-left: 2px solid #5A9A5A; }
.fb-neg { background: #FBF5F5; border-left: 2px solid #9A5A5A; }
.fb-pos.mini, .fb-neg.mini { padding: 4px 7px; }
.fb-pos.mini .fb-label, .fb-neg.mini .fb-label { display: inline; margin-right: 4px; }
.fb-label { font-weight: 600; display: block; margin-bottom: 2px; font-size: 10px; letter-spacing: .5px; text-transform: uppercase; }
.fb-pos .fb-label { color: #3A7A3A; } .fb-neg .fb-label { color: #7A3A3A; }
/* ── Policy ── */
.policy-list { display: flex; flex-direction: column; gap: 1px; border: 1px solid var(--border); background: var(--border); }
.policy-card { background: var(--white); padding: 10px 14px; }
.policy-card-header { display: flex; flex-wrap: wrap; align-items: flex-start; gap: 7px; margin-bottom: 5px; }
.policy-type-badge { border-radius: 0; padding: 2px 7px; font-size: 10px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; flex-shrink: 0; }
.policy-title { font-weight: 600; font-size: 14px; color: var(--dark); flex: 1; }
.policy-source { color: var(--light); font-size: 11px; width: 100%; }
.policy-detail { font-size: 13px; color: var(--charcoal); border-left: 2px solid var(--gold); padding-left: 8px; margin: 4px 0; }
.policy-impact { font-size: 12px; color: var(--mid); border-left: 2px solid var(--border); padding-left: 8px; margin: 4px 0; }
.policy-risk { font-size: 12px; color: #7A3A3A; background: #FBF5F5; border-left: 2px solid #9A5A5A; padding: 5px 8px; margin-top: 4px; }
/* ── Bullets ── */
.bullet-list { padding-left: 14px; font-size: 12px; } .bullet-list li { margin-bottom: 2px; }
.text-cell { font-size: 13px; } .empty { color: var(--light); font-size: 12px; padding: 10px 0; font-style: italic; }


/* ── Marketing section prominence ── */
.mkt-section-wrap {
  background: var(--charcoal);
  border-top: 2px solid var(--gold);
  border-bottom: 2px solid var(--gold);
  padding: 18px 22px;
  margin: 18px -22px;
}
.mkt-section-wrap .sec-header {
  color: var(--gold) !important;
}
.mkt-section-wrap .sec-header::after {
  background: var(--gold-dk);
}
.mkt-section-wrap .mkt-cards {
  background: var(--gold-dk);
  border-color: var(--gold-dk);
}
.mkt-section-wrap .mkt-card {
  background: #1E1B16;
  color: var(--ivory);
}
.mkt-section-wrap .mkt-game { color: var(--gold-lt); }
.mkt-section-wrap .action-block { background: #2A2620; border-left-color: var(--gold); }
.mkt-section-wrap .ab-action { color: var(--ivory-dk); }
.mkt-section-wrap .ab-meta { color: var(--light); }
.mkt-section-wrap .ab-label { color: var(--gold-dk); }
.mkt-section-wrap .mkt-toggle { color: var(--gold-dk); border-top-color: rgba(201,168,76,.2); }
.mkt-section-wrap .mkt-toggle:hover { color: var(--gold); }
.mkt-section-wrap .chip-type { background: rgba(201,168,76,.15); color: var(--gold-lt); border-color: rgba(201,168,76,.3); }
.mkt-section-wrap .dim-badge { border: 1px solid rgba(201,168,76,.3); }
.mkt-section-wrap .fb-pos { background: rgba(90,154,90,.1); border-left-color: #5A9A5A; color: #9FCCA0; }
.mkt-section-wrap .fb-neg { background: rgba(154,90,90,.1); border-left-color: #9A5A5A; color: #CCAAAA; }
.mkt-section-wrap .fb-label { color: inherit; }
.mkt-section-wrap .action-count { background: var(--gold); color: var(--black); }
@media (max-width: 768px) { .mkt-section-wrap { margin: 14px -14px; padding: 14px 14px; } }

/* ── Policy section - gazette style ── */
.policy-gazette { display: flex; flex-direction: column; gap: 0; }
.gazette-entry {
  display: grid; grid-template-columns: 80px 1fr;
  gap: 0; border-bottom: 1px solid var(--border-lt);
  transition: background .15s;
}
.gazette-entry:last-child { border-bottom: none; }
.gazette-entry:hover { background: var(--ivory); }
.gazette-left {
  background: var(--dark); padding: 14px 10px;
  display: flex; flex-direction: column; align-items: center;
  justify-content: flex-start; gap: 8px; border-right: 2px solid var(--gold);
}
.gazette-type-vert {
  writing-mode: vertical-rl; text-orientation: mixed;
  font-family: 'Cormorant Garamond', serif; font-size: 11px;
  font-weight: 700; letter-spacing: 3px; text-transform: uppercase;
  color: var(--gold); white-space: nowrap;
}
.gazette-num {
  font-family: 'Cormorant Garamond', serif; font-size: 22px;
  font-weight: 700; color: var(--gold-dk); line-height: 1;
}
.gazette-body { padding: 12px 16px; }
.gazette-headline {
  font-family: 'Cormorant Garamond', serif; font-weight: 600;
  font-size: 15px; color: var(--dark); letter-spacing: .3px;
  line-height: 1.4; margin-bottom: 4px;
}
.gazette-byline {
  font-size: 11px; color: var(--light); letter-spacing: 1px;
  text-transform: uppercase; margin-bottom: 8px;
}
.gazette-detail {
  font-size: 13px; color: var(--charcoal); margin-bottom: 6px;
  border-left: 2px solid var(--gold); padding-left: 10px; line-height: 1.6;
}
.gazette-impact {
  font-size: 12px; color: var(--mid); padding: 5px 8px;
  background: var(--ivory-dk); border-left: 2px solid var(--border);
  margin-bottom: 5px; font-style: italic;
}
.gazette-risk {
  font-size: 12px; color: #7A3A3A; background: #FBF5F5;
  border-left: 2px solid #9A5A5A; padding: 5px 9px;
}

/* ── Collapse / expand micro-interaction ── */
.collapsible { display: none; overflow: hidden; transition: none; }
.collapsible.open { display: block; animation: fadeIn .2s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: none; } }

.expandable { cursor: pointer; transition: background .15s; }
.expandable:hover { background: var(--ivory) !important; }
.expandable.is-open { background: var(--ivory) !important; }
.expand-hint { font-size: 10px; color: var(--light); letter-spacing: 1px; margin-top: 4px; text-transform: uppercase; }
.expand-arrow { font-size: 18px; color: var(--light); line-height: 1; flex-shrink: 0; transition: transform .2s; display: none; }
.mob-card .expand-arrow { display: block; }
.expand-arrow.open { transform: rotate(90deg); }

/* mkt toggle button */
.mkt-toggle {
  font-size: 10px; letter-spacing: 1.5px; text-transform: uppercase;
  color: var(--gold-dk); cursor: pointer; margin-top: 6px;
  padding: 4px 0; border-top: 1px solid var(--border-lt); transition: color .15s;
}
.mkt-toggle:hover { color: var(--gold); }
.mkt-toggle.open { color: var(--mid); }

/* Mobile card layout with arrow */
.mob-card { display: flex; align-items: flex-start; gap: 9px; }

/* ── Footer ── */
footer { text-align: center; padding: 22px; font-size: 11px; letter-spacing: 1px; text-transform: uppercase; border-top: 2px solid var(--gold-dk); background: var(--black); color: var(--light); margin-top: 28px; }
footer a { color: var(--gold); text-decoration: none; }
@media (max-width: 768px) { .site-header { padding: 0 16px; } .page-section { padding: 12px 14px; } .hero { padding: 28px 16px 22px; } .mkt-cards { grid-template-columns: 1fr; } }
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
function toggleDetail(id) {
  const el = document.getElementById(id);
  if (!el) return;
  const card = el.closest('.expandable');
  const hint = card && card.querySelector('.expand-hint');
  const arrow = card && card.querySelector('.expand-arrow');
  const isOpen = el.classList.toggle('open');
  if (hint) hint.style.display = isOpen ? 'none' : '';
  if (arrow) { arrow.textContent = isOpen ? '⌄' : '›'; arrow.classList.toggle('open', isOpen); }
  if (card) card.classList.toggle('is-open', isOpen);
}
function toggleMkt(btn, id) {
  const actions = document.getElementById('mkt-' + id);
  const fb = document.getElementById('mktfb-' + id);
  const isOpen = btn.classList.toggle('open');
  if (actions) actions.classList.toggle('open', isOpen);
  if (fb) fb.classList.toggle('open', isOpen);
  btn.textContent = isOpen ? '收起 ‹' : '展开详情 ›';
}
// Attach click handlers to market tabs
document.querySelectorAll('.mkt-tab').forEach(function(btn) {
  btn.addEventListener('click', function() { activateMarket(this.dataset.market); });
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
    <div class="sec-header"><span class="sec-icon" style="color:var(--gold)">◆</span> PC · 主机热门榜单</div>
    {render_pc_cards(m['pc_ranks'])}

    <div class="sec-header"><span class="sec-icon" style="color:var(--gold-dk)">◆</span> 手游热门榜单</div>
    {render_mobile_tabs(m['mobile_ranks'], mob_id)}

    <div class="mkt-section-wrap">
      <div class="sec-header"><span class="sec-icon" style="color:var(--gold)">◆</span> 营销热点详情</div>
      {render_mkt_cards(m['mkt_rows'])}
    </div>

    <div class="sec-header"><span class="sec-icon" style="color:var(--light)">◆</span> 区域产业政策</div>
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
  <div style="margin-top:14px;font-size:11px;letter-spacing:8px;color:var(--gold-dk)">✦ &nbsp; ✦ &nbsp; ✦</div>
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

