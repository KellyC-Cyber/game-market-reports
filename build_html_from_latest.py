#!/usr/bin/env python3
"""
build_html_from_latest.py
Reads data from build_report_LATEST.py and build_weekly_LATEST.py
and generates HTML versions for GitHub Pages.
"""

import sys, os
from unittest.mock import MagicMock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from html_generator import generate_html


def extract_market_data(script_path):
    """Execute the build script with mocked openpyxl to extract data variables."""
    mock_openpyxl = MagicMock()
    mock_wb = MagicMock()
    mock_ws = MagicMock()
    mock_wb.create_sheet.return_value = mock_ws
    mock_wb.active = mock_ws
    mock_openpyxl.Workbook.return_value = mock_wb
    mock_openpyxl.utils.get_column_letter = lambda x: chr(64 + min(x, 26))
    for cls in ['Font','PatternFill','Alignment','Border','Side','Color']:
        setattr(mock_openpyxl.styles, cls, MagicMock(return_value=MagicMock()))

    ns = {
        'openpyxl': mock_openpyxl,
        '__file__': os.path.abspath(script_path),
    }
    with open(script_path) as f:
        src = f.read()

    # Prevent file writes
    src = src.replace('wb.save(', '#wb.save(')

    try:
        exec(compile(src, script_path, 'exec'), ns)
    except Exception as e:
        print(f"  Warning: {e}")
    return ns


MARKET_KEYS = [
    ("中国大陆", "cn"),
    ("美国",     "us"),
    ("欧洲",     "eu"),
    ("日本",     "jp"),
    ("韩国",     "kr"),
    ("港台",     "tw"),
    ("东南亚",   "sea"),
    ("俄罗斯",   "ru"),
]


def build_markets(ns):
    markets = []
    for name, key in MARKET_KEYS:
        markets.append({
            "name":         name,
            "pc_ranks":     ns.get(f"{key}_pc",    []),
            "mobile_ranks": ns.get(f"{key}_mobile", []),
            "mkt_rows":     ns.get(f"{key}_mkt",   []),
            "policy_rows":  ns.get(f"{key}_policy", []),
        })
    return markets


def build_monthly_html():
    ns = extract_market_data("build_report_LATEST.py")
    generate_html(
        title_main="全球游戏市场热点月报",
        title_sub="2026年3月",
        period="2026年3月1日 — 3月31日",
        report_type="📅 月度报告",
        markets=build_markets(ns),
        output_path="docs/monthly.html",
    )


def build_weekly_html():
    ns = extract_market_data("build_weekly_LATEST.py")
    generate_html(
        title_main="全球游戏市场热点周报",
        title_sub="2026年3月26日 — 4月1日",
        period="2026年3月26日 — 4月1日（第13周）",
        report_type="🗓️ 周报",
        markets=build_markets(ns),
        output_path="docs/index.html",
        is_weekly=True,
    )


if __name__ == "__main__":
    os.makedirs("docs", exist_ok=True)
    print("Building weekly HTML...")
    build_weekly_html()
    print("Building monthly HTML...")
    build_monthly_html()
    print("✅ Done. Files in docs/")
