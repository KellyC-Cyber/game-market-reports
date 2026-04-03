#!/bin/bash
# push_reports.sh
# Called by cron after each report generation.
# Builds HTML, commits, and pushes to GitHub Pages.

WORKSPACE="/Users/user/.openclaw/workspace"
cd "$WORKSPACE"

echo "[$(date)] Building HTML reports..."
python3 build_html_from_latest.py

echo "[$(date)] Committing and pushing..."
git add docs/
git commit -m "auto: update reports $(date '+%Y-%m-%d %H:%M')" 2>/dev/null || echo "Nothing new to commit"
git push origin main

echo "[$(date)] Done. Site updated."
