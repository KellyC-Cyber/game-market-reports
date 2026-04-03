#!/bin/bash
# push_reports.sh - called by cron after Excel generation
# Generates HTML then commits+pushes to GitHub Pages

WORKSPACE="/Users/user/.openclaw/workspace"
cd "$WORKSPACE"

echo "[$(date)] Generating HTML reports..."
python3 build_html_from_latest.py

echo "[$(date)] Committing and pushing to GitHub..."
git add docs/
git commit -m "auto: update reports $(date '+%Y-%m-%d %H:%M')" 2>/dev/null || echo "Nothing new to commit"
git push origin main

echo "[$(date)] Site updated: https://kellyc-cyber.github.io/game-market-reports/"
