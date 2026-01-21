#!/bin/bash
# =================================================================
# NBA Analytics - Stop Script (Simple Mode)
# =================================================================

echo "🛑 Zatrzymywanie NBA Analytics..."

# Zatrzymaj wszystkie procesy PM2
pm2 delete all 2>/dev/null || echo "Brak procesów do zatrzymania"

echo "✅ Aplikacja zatrzymana"
