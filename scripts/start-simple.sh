#!/bin/bash
# =================================================================
# NBA Analytics - Simple Start (without Caddy)
# Backend: http://localhost:8000
# Frontend: http://localhost:8080
# =================================================================

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     🚀 Starting NBA Analytics (Simple Mode - No Caddy)   ║"
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

DOMAIN_DISPLAY=${DOMAIN:-192.168.100.131}

echo "════════════════════════════════════════════════════════════"
echo "🔄 Zatrzymywanie starych procesów"
echo "════════════════════════════════════════════════════════════"

# Zatrzymaj stare procesy PM2
pm2 delete all 2>/dev/null || echo "   Brak starych procesów PM2"

echo "✅ Stare procesy zatrzymane"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "🚀 Uruchamianie Backend (FastAPI) na porcie 8000"
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
echo "🌐 Uruchamianie Frontend na porcie 8080"
echo "════════════════════════════════════════════════════════════"

# Sprawdź czy dist istnieje
if [ ! -d "dist" ]; then
    echo "⚠️  Brak folderu dist, buduję frontend..."
    npm run build
fi

# Zainstaluj serve jeśli nie ma
if ! command -v serve &> /dev/null; then
    echo "📦 Instalowanie serve..."
    npm install -g serve
fi

# Uruchom frontend przez serve z PM2
pm2 start --name nba-frontend "serve dist -l 8080"

echo "✅ Frontend uruchomiony na porcie 8080"

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
echo "   Frontend:  http://${DOMAIN_DISPLAY}:8080"
echo "   Backend:   http://${DOMAIN_DISPLAY}:8000"
echo "   Health:    http://${DOMAIN_DISPLAY}:8000/health"
echo ""
echo "📋 PRZYDATNE KOMENDY:"
echo "   Status:         pm2 status"
echo "   Logi backend:   pm2 logs nba-backend"
echo "   Logi frontend:  pm2 logs nba-frontend"
echo "   Restart:        pm2 restart all"
echo "   Stop:           pm2 stop all"
echo ""
echo "⚠️  UWAGA: Aplikacja dostępna w sieci lokalnej (HTTP)!"
echo "   Z innych komputerów: http://${DOMAIN_DISPLAY}:8080"
echo ""
