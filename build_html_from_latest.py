#!/usr/bin/env python3
"""
build_html_from_latest.py v2
Uses mock interception to capture ALL data including policy_rows from inline calls.
"""

import sys, os
from unittest.mock import MagicMock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from html_generator import generate_html

MARKET_KEYS = [
    ("中国大陆","cn"), ("美国","us"), ("欧洲","eu"), ("日本","jp"),
    ("韩国","kr"),     ("港台","tw"), ("东南亚","sea"), ("俄罗斯","ru"),
]

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
        'make_sheet': capture_sheet,   # weekly uses make_sheet
    }

    with open(script_path) as f:
        src = f.read()

    # Remove def make_market_sheet / def make_sheet so injected mocks are used
    lines = src.split('\n')
    new_lines = []
    inside_def = False
    for line in lines:
        stripped = line.strip()
        if (line.startswith('def make_market_sheet(') or
                line.startswith('def make_sheet(')):
            inside_def = True
            continue
        if inside_def:
            if stripped and not line[0].isspace():
                inside_def = False
            else:
                continue
        new_lines.append(line)

    src = '\n'.join(new_lines)
    src = src.replace('wb.save(', '#wb.save(')

    try:
        exec(compile(src, script_path, 'exec'), ns)
    except Exception as e:
        print(f"  Note: {e}")

    return captured


def build_markets(captured):
    markets = []
    for name, _ in MARKET_KEYS:
        d = captured.get(name, {})
        markets.append({
            "name":         name,
            "pc_ranks":     d.get("pc", []),
            "mobile_ranks": d.get("mobile", []),
            "mkt_rows":     d.get("mkt", []),
            "policy_rows":  d.get("policy", []),
        })
    return markets


def build_monthly_html():
    captured = extract_all_data("build_report_LATEST.py")
    for name, _ in MARKET_KEYS:
        d = captured.get(name, {})
        print(f"  {name}: pc={len(d.get('pc',[]))} mob={len(d.get('mobile',[]))} mkt={len(d.get('mkt',[]))} pol={len(d.get('policy',[]))}")
    generate_html(
        title_main="全球游戏市场热点月报",
        title_sub="2026年3月",
        period="2026年3月1日 — 3月31日",
        report_type="📅 月度报告",
        markets=build_markets(captured),
        output_path="docs/monthly.html",
    )


def build_weekly_html():
    captured = extract_all_data("build_weekly_LATEST.py")
    for name, _ in MARKET_KEYS:
        d = captured.get(name, {})
        print(f"  {name}: pc={len(d.get('pc',[]))} mob={len(d.get('mobile',[]))} mkt={len(d.get('mkt',[]))} pol={len(d.get('policy',[]))}")
    generate_html(
        title_main="全球游戏市场热点周报",
        title_sub="2026年3月26日 — 4月1日",
        period="2026年3月26日 — 4月1日（第13周）",
        report_type="🗓️ 周报",
        markets=build_markets(captured),
        output_path="docs/index.html",
        is_weekly=True,
    )


if __name__ == "__main__":
    os.makedirs("docs", exist_ok=True)
    print("=== Building weekly HTML ===")
    build_weekly_html()
    print("=== Building monthly HTML ===")
    build_monthly_html()
    print("✅ Done. Files in docs/")
