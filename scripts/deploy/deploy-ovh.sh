#!/bin/bash
# =================================================================
# NBA Analytics - OVH Deployment Script
# =================================================================
# Uruchamia aplikację na serwerze OVH VPS w trybie produkcyjnym
# =================================================================

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║        🏀 NBA Analytics - OVH Production Deploy           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Sprawdź czy jesteśmy w katalogu projektu
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "❌ Błąd: Nie znaleziono pliku docker-compose.prod.yml"
    echo "   Upewnij się, że jesteś w katalogu projektu!"
    exit 1
fi

# Sprawdź czy .env.production istnieje
if [ ! -f ".env.production" ]; then
    echo "⚠️  Plik .env.production nie istnieje!"
    echo ""
    echo "Tworzę z szablonu .env..."
    
    if [ -f ".env" ]; then
        cp .env .env.production
        echo "✅ Utworzono .env.production z .env"
    else
        echo "❌ Nie znaleziono pliku .env!"
        echo ""
        echo "Musisz utworzyć plik .env.production z następującymi zmiennymi:"
        echo "  DOMAIN=twoja-domena.com"
        echo "  VITE_SUPABASE_URL=..."
        echo "  VITE_SUPABASE_ANON_KEY=..."
        echo "  itd."
        exit 1
    fi
fi

# Sprawdź czy DOMAIN jest ustawiona
if ! grep -q "^DOMAIN=" .env.production || grep -q "^DOMAIN=$" .env.production || grep -q "^DOMAIN=localhost" .env.production; then
    echo "⚠️  UWAGA: Zmienna DOMAIN nie jest ustawiona lub jest localhost!"
    echo ""
    echo "Aby Caddy mógł pobrać certyfikat SSL, musisz ustawić domenę:"
    echo "  nano .env.production"
    echo "  # Ustaw: DOMAIN=twoja-domena.com"
    echo ""
    read -p "Czy chcesz kontynuować mimo to? (tak/nie): " confirm
    if [[ ! "$confirm" =~ ^(tak|t|yes|y)$ ]]; then
        echo "Anulowano."
        exit 0
    fi
fi

# Sprawdź czy Docker działa
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker nie działa!"
    echo ""
    echo "Sprawdź instalację Docker:"
    echo "  sudo systemctl status docker"
    echo "  sudo systemctl start docker"
    exit 1
fi

echo "════════════════════════════════════════════════════════════"
echo "📋 PRE-DEPLOYMENT CHECKS"
echo "════════════════════════════════════════════════════════════"

# Wyświetl konfigurację
echo "📁 Katalog: $(pwd)"
echo "🐋 Docker: $(docker --version)"
echo "🐋 Compose: $(docker compose version)"
echo "🌐 IP serwera: $(hostname -I | awk '{print $1}')"

# Pokaż domenę (jeśli ustawiona)
DOMAIN=$(grep "^DOMAIN=" .env.production | cut -d '=' -f2)
if [ -n "$DOMAIN" ] && [ "$DOMAIN" != "localhost" ]; then
    echo "🌍 Domena: $DOMAIN"
else
    echo "🌍 Domena: Nie ustawiona (tylko HTTP)"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "🔧 DEPLOYMENT OPTIONS"
echo "════════════════════════════════════════════════════════════"
echo "1) Fresh deployment (zatrzymaj stare, zbuduj nowe, uruchom)"
echo "2) Quick restart (szybki restart bez rebuildu)"
echo "3) Update from Git (pull + rebuild + restart)"
echo "4) Stop application"
echo "5) View logs"
echo "6) Status check"
echo "0) Cancel"
echo ""
read -p "Wybierz opcję [1-6, 0]: " choice

case $choice in
    1)
        echo ""
        echo "🚀 Fresh Deployment..."
        echo "════════════════════════════════════════════════════════════"
        
        # Zatrzymaj stare kontenery
        echo "⏹️  Zatrzymuję stare kontenery..."
        docker compose -f docker-compose.prod.yml down || true
        
        # Wyczyść nieużywane obrazy (opcjonalnie)
        echo "🧹 Czyszczę nieużywane obrazy..."
        docker image prune -f || true
        
        # Build i uruchom
        echo "🏗️  Buduję i uruchamiam kontenery..."
        docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
        
        echo ""
        echo "✅ Deployment zakończony!"
        ;;
        
    2)
        echo ""
        echo "🔄 Quick Restart..."
        echo "════════════════════════════════════════════════════════════"
        docker compose -f docker-compose.prod.yml restart
        echo "✅ Zrestartowano!"
        ;;
        
    3)
        echo ""
        echo "📥 Update from Git..."
        echo "════════════════════════════════════════════════════════════"
        
        # Sprawdź czy to repozytorium git
        if [ ! -d ".git" ]; then
            echo "❌ To nie jest repozytorium git!"
            exit 1
        fi
        
        # Backup .env.production
        echo "💾 Backup konfiguracji..."
        cp .env.production .env.production.backup
        
        # Pull z gita
        echo "📥 Pobieranie zmian z GitHub..."
        git pull
        
        # Przywróć .env.production (gdyby został nadpisany)
        if [ -f ".env.production.backup" ]; then
            mv .env.production.backup .env.production
            echo "✅ Przywrócono konfigurację"
        fi
        
        # Restart z rebuildem
        echo "🏗️  Rebuild i restart..."
        docker compose -f docker-compose.prod.yml down
        docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
        
        echo "✅ Update zakończony!"
        ;;
        
    4)
        echo ""
        echo "⏹️  Stopping application..."
        docker compose -f docker-compose.prod.yml down
        echo "✅ Zatrzymano!"
        ;;
        
    5)
        echo ""
        echo "📋 Application Logs (Ctrl+C aby wyjść)"
        echo "════════════════════════════════════════════════════════════"
        docker compose -f docker-compose.prod.yml logs -f
        ;;
        
    6)
        echo ""
        echo "📊 Application Status"
        echo "════════════════════════════════════════════════════════════"
        docker compose -f docker-compose.prod.yml ps
        
        echo ""
        echo "🏥 Health Checks"
        echo "════════════════════════════════════════════════════════════"
        
        # Sprawdź backend
        if curl -f -s http://localhost:8000/health > /dev/null; then
            echo "✅ Backend: OK (http://localhost:8000/health)"
        else
            echo "❌ Backend: NOT RESPONDING"
        fi
        
        # Sprawdź frontend przez Caddy
        if curl -f -s http://localhost/health > /dev/null; then
            echo "✅ Caddy: OK (http://localhost/health)"
        else
            echo "⚠️  Caddy: NOT RESPONDING"
        fi
        
        # Sprawdź Redis
        if docker exec nba-redis redis-cli ping > /dev/null 2>&1; then
            echo "✅ Redis: OK"
        else
            echo "❌ Redis: NOT RESPONDING"
        fi
        
        echo ""
        echo "💾 Disk Usage"
        echo "════════════════════════════════════════════════════════════"
        df -h / | tail -1
        
        echo ""
        echo "🐋 Docker Resources"
        echo "════════════════════════════════════════════════════════════"
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
        ;;
        
    0)
        echo "Anulowano."
        exit 0
        ;;
        
    *)
        echo "❌ Nieprawidłowa opcja!"
        exit 1
        ;;
esac

echo ""
echo "════════════════════════════════════════════════════════════"
echo "📚 USEFUL COMMANDS"
echo "════════════════════════════════════════════════════════════"
echo "Status:   docker compose -f docker-compose.prod.yml ps"
echo "Logs:     docker compose -f docker-compose.prod.yml logs -f"
echo "Stop:     docker compose -f docker-compose.prod.yml down"
echo "Restart:  docker compose -f docker-compose.prod.yml restart"
echo ""

# Jeśli domena jest ustawiona, pokaż URL
if [ -n "$DOMAIN" ] && [ "$DOMAIN" != "localhost" ]; then
    echo "🌍 APPLICATION URLS:"
    echo "   https://$DOMAIN"
    echo "   https://$DOMAIN/api/health"
    echo "   https://$DOMAIN/health"
else
    SERVER_IP=$(hostname -I | awk '{print $1}')
    echo "🌍 APPLICATION URLS (HTTP only - no domain):"
    echo "   http://$SERVER_IP"
    echo "   http://$SERVER_IP/api/health"
fi

echo ""
