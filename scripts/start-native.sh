#!/bin/bash
# =================================================================
# NBA Analytics - Native Start Script (without Docker)
# =================================================================

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║        🚀 Starting NBA Analytics (Native Mode)           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

PROJECT_DIR=$(pwd)
BACKEND_DIR="$PROJECT_DIR/backend"

# Sprawdź czy jesteśmy w katalogu projektu
if [ ! -f "package.json" ]; then
    echo "❌ Błąd: Uruchom skrypt w katalogu projektu!"
    exit 1
fi

# Sprawdź czy .env.production istnieje
if [ ! -f ".env.production" ]; then
    echo "⚠️  Brak pliku .env.production!"
    if [ -f ".env" ]; then
        cp .env .env.production
        echo "✅ Utworzono .env.production z .env"
    else
        echo "❌ Brak pliku konfiguracyjnego!"
        exit 1
    fi
fi

# Załaduj zmienne środowiskowe
set -a
source .env.production
set +a

DOMAIN_DISPLAY=${DOMAIN:-mareknba.pl}

echo "════════════════════════════════════════════════════════════"
echo "🔄 Zatrzymywanie starych procesów"
echo "════════════════════════════════════════════════════════════"

# Zatrzymaj stare procesy PM2
pm2 delete nba-backend 2>/dev/null || echo "   Brak starych procesów PM2"

echo "✅ Stare procesy zatrzymane"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "🚀 Uruchamianie Backend (FastAPI)"
echo "════════════════════════════════════════════════════════════"

cd "$BACKEND_DIR"

# Sprawdź czy venv istnieje
if [ ! -d "venv" ]; then
    echo "❌ Brak virtual environment! Uruchom najpierw setup-native-ubuntu.sh"
    exit 1
fi

# Uruchom backend z PM2 (zaciąga .env.production przez env_file)
pm2 start ecosystem.native.json --update-env

echo "✅ Backend uruchomiony przez PM2"

cd "$PROJECT_DIR"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "🌐 Uruchamianie Caddy (Web Server + SSL)"
echo "════════════════════════════════════════════════════════════"

# Restart Caddy
sudo systemctl restart caddy

if sudo systemctl is-active --quiet caddy; then
    echo "✅ Caddy działa"
else
    echo "❌ Caddy nie uruchomił się!"
    echo "Sprawdź logi: sudo journalctl -u caddy -n 50"
    exit 1
fi

# Zapisz konfigurację PM2
pm2 save

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              ✅ APLIKACJA URUCHOMIONA!                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 STATUS:"
echo ""

# Status PM2
pm2 status

echo ""
echo "🌍 APLIKACJA DOSTĘPNA:"
echo "   Local:  http://localhost"
echo "   Domain: https://${DOMAIN_DISPLAY}"
echo ""
echo "📋 PRZYDATNE KOMENDY:"
echo "   Status:    pm2 status"
echo "   Logi:      pm2 logs nba-backend"
echo "   Restart:   pm2 restart nba-backend"
echo "   Stop:      pm2 stop nba-backend"
echo "   Caddy:     sudo systemctl status caddy"
echo ""
echo "🔧 HEALTH CHECKS:"
echo "   Backend:   curl http://localhost:8000/health"
echo "   Caddy:     curl http://localhost/"
echo ""
