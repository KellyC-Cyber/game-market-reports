#!/usr/bin/env python3
"""
build_html_from_latest.py v4
- Extracts data from LATEST + archived build scripts
- Generates all HTML pages including archive index
- Supplements missing player feedback via FEEDBACK_SUPPLEMENT
"""

import sys, os, glob
from unittest.mock import MagicMock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from html_generator import generate_html, generate_archive_index

MARKET_KEYS = [
    ("中国大陆","cn"), ("美国","us"), ("欧洲","eu"), ("日本","jp"),
    ("韩国","kr"),     ("港台","tw"), ("东南亚","sea"), ("俄罗斯","ru"),
]

# ── Supplement missing player feedback ───────────────────────────────────────
FEEDBACK_SUPPLEMENT = {
    "绝区零":           ("战斗手感获好评；邦布系统吸引力强；版本内容口碑稳定", "卡池策略受批评；部分玩家认为内容量偏少"),
    "梦幻西游":         ("老IP情感粘性强；经济系统相对成熟稳定", "内容老化明显；新玩家入门门槛高"),
    "沙威玛传奇":       ("抖音29.9亿话题验证爆款；短平快玩法传播效果极好", "游戏深度不足；核心玩家长期留存率存疑"),
    "指尖像素城":       ("B站用户群体高度契合；像素美学受文化向玩家青睐", "玩法较轻度；同类竞品较多"),
    "无尽冬日":         ("买量效果稳定；生存策略品类需求持续", "产品口碑一般；依赖买量驱动"),
    "蛋仔派对":         ("鸿蒙首发资源显著；节日主题地图受欢迎", "核心玩法重复性高；部分限时活动机制受批评"),
    "洛克王国":         ("情怀IP回归引爆老玩家；上线13小时1500万用户", "付费设计受主流媒体质疑；老玩家担忧情怀消耗"),
    "Marathon":         ("Bungie新IP获FPS核心玩家期待；Alpha测试热情高", "PvP-only设计受争议；商业化策略待观察"),
    "Grand Theft Auto": ("开放世界自由度经典；多人模式持续产生内容", "12年老游戏仍无GTA6替代；Rockstar更新频率被批评"),
    "Elden Ring":       ("DLC内容量超预期；boss设计获高度评价；FromSoftware口碑强", "DLC难度被认为不合理；部分新手劝退"),
    "Xbox Game Pass":   ("订阅制价值感强；新游阵容充实", "部分独占首发质量不稳定；PC兼容性问题偶发"),
    "Xbox":             ("XGP性价比高受年轻玩家欢迎；新游阵容充实", "韩国主机市场仍以PS为主；Xbox生态认知度有限"),
    "多款Xbox":         ("XGP性价比高受年轻玩家欢迎；新游阵容充实", "主机市场仍以PS为主；Xbox生态认知度有限"),
    "Spider-Man":       ("剧情沉浸感强；PS5专属优化出色", "开放世界重复任务偏多；故事节奏被部分玩家认为过快"),
    "Pokemon GO":       ("户外社交活动吸引核心粉丝；社区日体验好", "新内容创意有限；付费压力和游戏老化受批评"),
    "Clash of Clans":   ("长期运营口碑稳定；公会社交粘性高", "玩法缺乏创新；高付费门槛令休闲玩家流失"),
    "Call of Duty: Mobile": ("移动端射击体验业界标杆；跨平台联动活动受欢迎", "外挂投诉持续；赛季内容重复性偏高"),
    "Forza Horizon":    ("欧洲赛车受众大；新赛季内容获好评", "上线多年内容疲劳；PC版bug偶发"),
    "Crimson Desert":   ("开放世界设计惊艳；Black Desert引擎底蕴深厚；首周4M销量超预期", "发售初期优化问题明显；PC配置需求高"),
    "Slay the Spire 2": ("系统深度超越前作；EA阶段内容量充足；3M份销量验证市场", "部分玩家认为变化太大失去原作感；EA价格偏高"),
    "黑神话：悟空":     ("钟馗DLC剧情深度获高度好评；二创内容持续产出", "3月主线+钟馗内容消耗后等待下一更新；部分关卡难度偏高"),
    "影之刃零":         ("国产动作游戏操作手感获认可；抖音评测内容覆盖广", "部分玩家反映内容深度不足；PC优化问题被提及"),
    "Forza":            ("欧洲赛车受众大；新赛季内容获好评", "上线多年内容疲劳；PC版bug偶发"),
    "龍が如く":         ("联动在日本媒体广泛报道；情怀IP消费热情高", "部分玩家认为内容相比极1/2较弱；定价偏高"),
    "流星のロックマン": ("怀旧情怀价值高；任天堂社区反响热烈", "游戏内容老化；现代优化不足"),
    "パズル＆ドラゴンズ": ("老牌手游稳定运营；IP联动活动频繁刺激付费", "新玩家入局成本极高；UI界面老化"),
    "プロ野球":         ("日本棒球迷忠诚度高；球员卡收集乐趣强", "高度依赖卡池付费；数据更新有延迟"),
    "ドラゴンクエストウォーク": ("DQ品牌根基深；户外探索与IP结合独特", "受地理位置限制；东京以外活动密度差"),
    "ブルーアーカイブ": ("角色剧情深度受好评；老玩家活跃度高", "氪金深度高；版本末期内容较少"),
    "무한의계단":       ("极简操作契合韩国休闲手游偏好；口碑发酵带动下载爆发", "游戏深度有限；长期留存率挑战大"),
    "카트라이더":       ("韩国本土IP情怀深厚；粉丝基础强", "重启版优化不足；与原版体验差距受批评"),
    "Dota 2":           ("电竞文化深厚；赛事期间玩家活跃度高", "新手门槛极高；对休闲玩家不友好"),
    "Valorant":         ("东南亚年轻玩家核心电竞选择；皮肤文化契合", "部分国家服务器不稳定；外挂问题持续"),
    "Яндекс":           ("俄罗斯本土平台访问无障碍；休闲游戏品类丰富", "游戏深度有限；付费体验与国际平台差距明显"),
    "Brawl Stars":      ("Supercell游戏在俄语区持续活跃；内容更新频率高", "奖励设计被认为不公平；充值渠道受制裁影响"),
    "战争雷霆":         ("军事题材高度契合俄罗斯玩家；载具内容扎实", "平衡性问题持续被投诉；高端载具解锁成本极高"),
    "VK Play":          ("俄罗斯本地生态整合好；使用无需VPN", "平台游戏质量参差不齐；用户体量有限"),
    "Tank Blitz":       ("俄罗斯坦克文化深厚；Wargaming品牌当地影响力大", "图形质量老化；与现代手游差距明显"),
    "Minecraft":        ("全球经典IP受众广；创意内容吸引力持续", "俄罗斯正版购买渠道受限；官方支持减少"),
    "怪物猎人":         ("Ver.1.04一周年大更新获高度好评；AT Arkveld挑战赛事热度高", "部分老玩家认为ATArkveld难度过高；等待新大型更新"),
    "Monster Hunter":   ("Ver.1.04 anniversary update received high praise; AT Arkveld challenge popular", "Some veterans find AT Arkveld difficulty spike unfair; waiting for next major content"),
    "CS2":              ("射击手感优化获竞技核心玩家认可；反作弊更新持续", "VAC系统持续被批效果不足；Operation进度迟缓"),
    "永劫无间":         ("武侠动作玩法深度获认可；AI捏脸系统新颖有趣", "服务器稳定性问题长期诟病；平衡性争议持续"),
    "王者荣耀":         ("赛季更新节奏稳定；本土化运营成熟度高", "新英雄平衡性受批评；赛季皮肤定价偏高"),
    "和平精英":         ("大DAU基础稳定；本土化运营能力强", "玩法创新不足的批评持续；服务器外挂问题"),
    "PUBG Mobile":      ("全球化运营成熟；跨平台战役内容受欢迎", "外挂投诉持续；赛季内容重复性偏高"),
    "Mobile Legends":   ("东南亚市场份额领先；本地化运营深度强", "游戏UI设计老化；部分新英雄平衡性受批评"),
    "Free Fire":        ("东南亚低配置设备适配好；社区活跃", "品质感不及同类旗舰产品；部分外挂问题"),
    "七大罪":           ("IP粉丝基础强；跨平台同步上线体验好", "首发版本优化问题偶发；付费系统引发部分玩家关注"),
    "Honor of Kings":   ("港台/东南亚市场本土化好；版本与大陆同步", "服务器稳定性偶发问题；付费压力较大"),
}

def supplement_feedback(rows):
    result = []
    for row in rows:
        row = list(row)
        while len(row) < 8: row.append("")
        pos = str(row[6]).strip()
        neg = str(row[7]).strip()
        if not pos and not neg:
            game = str(row[1])
            for key, (p, n) in FEEDBACK_SUPPLEMENT.items():
                if key in game:
                    row[6] = p
                    row[7] = n
                    break
        result.append(row)
    return result


def extract_all_data(script_path):
    """Execute build script with mocked openpyxl + intercepted sheet function."""
    captured = {}

    def capture_sheet(name, flag, subtitle, pc_ranks, mobile_ranks, marketing_rows,
                      notes="", policy_rows=None):
        captured[name] = {
            "pc":     list(pc_ranks or []),
            "mobile": list(mobile_ranks or []),
            "mkt":    list(marketing_rows or []),
            "policy": list(policy_rows or []),
        }

    mock_openpyxl = MagicMock()
    mock_wb = MagicMock()
    mock_ws = MagicMock()
    mock_wb.create_sheet.return_value = mock_ws
    mock_wb.active = mock_ws
    mock_openpyxl.Workbook.return_value = mock_wb
    mock_openpyxl.utils.get_column_letter = lambda x: chr(64 + min(x, 26))
    for cls in ['Font', 'PatternFill', 'Alignment', 'Border', 'Side', 'Color']:
        setattr(mock_openpyxl.styles, cls, MagicMock(return_value=MagicMock()))

    ns = {
        'openpyxl': mock_openpyxl,
        '__file__': os.path.abspath(script_path),
        'make_market_sheet': capture_sheet,
        'make_sheet': capture_sheet,
    }

    with open(script_path) as f:
        src = f.read()

    lines = src.split('\n')
    new_lines = []
    inside_def = False
    for line in lines:
        stripped = line.strip()
        if (line.startswith('def make_market_sheet(') or line.startswith('def make_sheet(')):
            inside_def = True
            continue
        if inside_def:
            if stripped and not line[0].isspace():
                inside_def = False
            else:
                continue
        new_lines.append(line)

    src = '\n'.join(new_lines).replace('wb.save(', '#wb.save(')
    try:
        exec(compile(src, script_path, 'exec'), ns)
    except Exception as e:
        print(f"  Note ({os.path.basename(script_path)}): {e}")
    return captured


def build_markets(captured):
    markets = []
    for name, _ in MARKET_KEYS:
        d = captured.get(name, {})
        markets.append({
            "name":         name,
            "pc_ranks":     supplement_feedback(d.get("pc", [])),
            "mobile_ranks": supplement_feedback(d.get("mobile", [])),
            "mkt_rows":     d.get("mkt", []),
            "policy_rows":  d.get("policy", []),
        })
    return markets


# ── Archive registry ──────────────────────────────────────────────────────────
# Each entry: {file, label, title, period, script (optional)}
ARCHIVE_MONTHLY = [
    {"file": "monthly.html",       "label": "2026年3月", "title": "全球游戏市场热点月报 2026年3月", "period": "2026年3月1日—3月31日",   "script": "build_report_LATEST.py"},
    {"file": "monthly-202602.html","label": "2026年2月", "title": "全球游戏市场热点月报 2026年2月", "period": "2026年2月1日—2月28日",   "script": "build_report_feb2026.py"},
]
ARCHIVE_WEEKLY = [
    {"file": "index.html",            "label": "3/26–4/1",  "title": "全球游戏市场热点周报 2026年3月26日—4月1日",    "period": "2026年3月26日—4月1日",     "script": "build_weekly_LATEST.py"},
    {"file": "weekly-20260319.html",  "label": "3/19–3/25", "title": "全球游戏市场热点周报 2026年3月19日—3月25日",   "period": "2026年3月19日—3月25日",   "script": "build_weekly_20260319.py"},
]


def build_all():
    os.makedirs("docs", exist_ok=True)

    # Build all HTML from scripts
    all_reports = [
        ("monthly",  ARCHIVE_MONTHLY),
        ("weekly",   ARCHIVE_WEEKLY),
    ]

    for kind, registry in all_reports:
        for item in registry:
            script = item.get("script")
            if not script or not os.path.exists(script):
                print(f"  ⚠️ Script not found: {script}, skipping {item['file']}")
                continue
            print(f"Building {item['file']} from {script}...")
            captured = extract_all_data(script)
            markets = build_markets(captured)
            total = sum(len(m['pc_ranks'])+len(m['mobile_ranks']) for m in markets)
            fb = sum(1 for m in markets for r in m['pc_ranks']+m['mobile_ranks'] if len(r)>6 and (r[6] or r[7]))
            print(f"  data: {total} rows, feedback {fb}/{total}")

            is_weekly = (kind == "weekly")
            generate_html(
                title_main=item['title'].split(' ')[0]+item['title'].split(' ')[1] if ' ' in item['title'] else item['title'],
                title_sub=item['period'].split('—')[0].replace('2026年','2026年').strip(),
                period=item['period'],
                report_type="🗓️ 周报" if is_weekly else "📅 月度报告",
                markets=markets,
                output_path=f"docs/{item['file']}",
                is_weekly=is_weekly,
                archive_weekly=ARCHIVE_WEEKLY,
                archive_monthly=ARCHIVE_MONTHLY,
            )

    # Generate archive index
    generate_archive_index(
        archive_weekly=ARCHIVE_WEEKLY,
        archive_monthly=ARCHIVE_MONTHLY,
        output_path="docs/archive.html",
    )
    print("✅ All HTML files generated.")


if __name__ == "__main__":
    build_all()
