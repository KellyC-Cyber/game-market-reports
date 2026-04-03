#!/usr/bin/env python3
"""
build_html_from_latest.py
Reads data from build_report_LATEST.py and build_weekly_LATEST.py
and generates HTML versions for GitHub Pages.
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from html_generator import generate_html
from datetime import datetime

# ── Import market data from existing build scripts ────────────────────────────
# We exec the build scripts in a controlled way to extract data variables
def extract_market_data(script_path):
    """Execute the build script and extract market data variables."""
    ns = {}
    with open(script_path) as f:
        src = f.read()
    
    # Only execute the data definition part (before wb = openpyxl...)
    # Find where openpyxl workbook operations start
    cutoff = src.find('\nwb = ')
    if cutoff == -1:
        cutoff = src.find('\nwb=')
    if cutoff > 0:
        data_src = src[:cutoff]
    else:
        data_src = src
    
    # Remove openpyxl imports for clean execution
    data_src = '\n'.join(
        line for line in data_src.split('\n')
        if not line.strip().startswith('from openpyxl') 
        and not line.strip().startswith('import openpyxl')
        and not 'Font(' in line
        and not 'PatternFill(' in line
        and not 'Alignment(' in line
        and not 'Border(' in line
        and not 'Side(' in line
        and not 'get_column_letter' in line
    )
    
    try:
        exec(compile(data_src, script_path, 'exec'), ns)
    except Exception as e:
        print(f"Warning: partial exec error ({e}), continuing...")
    
    return ns


def build_monthly_html():
    ns = extract_market_data("build_report_LATEST.py")
    
    markets = [
        {"name": "中国大陆", "pc_ranks": ns.get("cn_pc",[]), "mobile_ranks": ns.get("cn_mobile",[]),
         "mkt_rows": ns.get("cn_mkt",[]), "policy_rows": ns.get("cn_policy",[])},
        {"name": "美国",     "pc_ranks": ns.get("us_pc",[]), "mobile_ranks": ns.get("us_mobile",[]),
         "mkt_rows": ns.get("us_mkt",[]), "policy_rows": ns.get("us_policy",[])},
        {"name": "欧洲",     "pc_ranks": ns.get("eu_pc",[]), "mobile_ranks": ns.get("eu_mobile",[]),
         "mkt_rows": ns.get("eu_mkt",[]), "policy_rows": ns.get("eu_policy",[])},
        {"name": "日本",     "pc_ranks": ns.get("jp_pc",[]), "mobile_ranks": ns.get("jp_mobile",[]),
         "mkt_rows": ns.get("jp_mkt",[]), "policy_rows": ns.get("jp_policy",[])},
        {"name": "韩国",     "pc_ranks": ns.get("kr_pc",[]), "mobile_ranks": ns.get("kr_mobile",[]),
         "mkt_rows": ns.get("kr_mkt",[]), "policy_rows": ns.get("kr_policy",[])},
        {"name": "港台",     "pc_ranks": ns.get("tw_pc",[]), "mobile_ranks": ns.get("tw_mobile",[]),
         "mkt_rows": ns.get("tw_mkt",[]), "policy_rows": ns.get("tw_policy",[])},
        {"name": "东南亚",   "pc_ranks": ns.get("sea_pc",[]), "mobile_ranks": ns.get("sea_mobile",[]),
         "mkt_rows": ns.get("sea_mkt",[]), "policy_rows": ns.get("sea_policy",[])},
        {"name": "俄罗斯",   "pc_ranks": ns.get("ru_pc",[]), "mobile_ranks": ns.get("ru_mobile",[]),
         "mkt_rows": ns.get("ru_mkt",[]), "policy_rows": ns.get("ru_policy",[])},
    ]
    
    generate_html(
        title_main="全球游戏市场热点月报",
        title_sub="2026年3月",
        period="2026年3月1日 — 3月31日",
        report_type="📅 月度报告",
        markets=markets,
        output_path="docs/monthly.html",
    )


def build_weekly_html():
    ns = extract_market_data("build_weekly_LATEST.py")
    
    markets = [
        {"name": "中国大陆", "pc_ranks": ns.get("cn_pc",[]), "mobile_ranks": ns.get("cn_mobile",[]),
         "mkt_rows": ns.get("cn_mkt",[]), "policy_rows": ns.get("cn_policy",[])},
        {"name": "美国",     "pc_ranks": ns.get("us_pc",[]), "mobile_ranks": ns.get("us_mobile",[]),
         "mkt_rows": ns.get("us_mkt",[]), "policy_rows": ns.get("us_policy",[])},
        {"name": "欧洲",     "pc_ranks": ns.get("eu_pc",[]), "mobile_ranks": ns.get("eu_mobile",[]),
         "mkt_rows": ns.get("eu_mkt",[]), "policy_rows": ns.get("eu_policy",[])},
        {"name": "日本",     "pc_ranks": ns.get("jp_pc",[]), "mobile_ranks": ns.get("jp_mobile",[]),
         "mkt_rows": ns.get("jp_mkt",[]), "policy_rows": ns.get("jp_policy",[])},
        {"name": "韩国",     "pc_ranks": ns.get("kr_pc",[]), "mobile_ranks": ns.get("kr_mobile",[]),
         "mkt_rows": ns.get("kr_mkt",[]), "policy_rows": ns.get("kr_policy",[])},
        {"name": "港台",     "pc_ranks": ns.get("tw_pc",[]), "mobile_ranks": ns.get("tw_mobile",[]),
         "mkt_rows": ns.get("tw_mkt",[]), "policy_rows": ns.get("tw_policy",[])},
        {"name": "东南亚",   "pc_ranks": ns.get("sea_pc",[]), "mobile_ranks": ns.get("sea_mobile",[]),
         "mkt_rows": ns.get("sea_mkt",[]), "policy_rows": ns.get("sea_policy",[])},
        {"name": "俄罗斯",   "pc_ranks": ns.get("ru_pc",[]), "mobile_ranks": ns.get("ru_mobile",[]),
         "mkt_rows": ns.get("ru_mkt",[]), "policy_rows": ns.get("ru_policy",[])},
    ]
    
    generate_html(
        title_main="全球游戏市场热点周报",
        title_sub="2026年3月26日 — 4月1日",
        period="2026年3月26日 — 4月1日（第13周）",
        report_type="🗓️ 周报",
        markets=markets,
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
