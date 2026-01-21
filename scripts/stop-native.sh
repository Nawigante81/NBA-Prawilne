#!/bin/bash
# =================================================================
# NBA Analytics - Native Stop Script
# =================================================================

echo "⏹️  Zatrzymywanie NBA Analytics..."

# Stop PM2 processes
pm2 stop nba-backend 2>/dev/null || echo "Backend już zatrzymany"

# Stop Caddy
sudo systemctl stop caddy

echo "✅ Aplikacja zatrzymana"
echo ""
echo "Status:"
pm2 status
