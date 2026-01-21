#!/bin/bash
# =================================================================
# NBA Analytics - Quick Deploy for Self-Hosted Server
# Domain: mareknba.pl
# =================================================================

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     🏀 NBA Analytics - mareknba.pl Deployment            ║"
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
    echo "   Tworzę z szablonu..."
    
    if [ -f ".env" ]; then
        cp .env .env.production
        echo "✅ Utworzono .env.production"
    else
        echo "❌ Nie znaleziono pliku .env!"
        exit 1
    fi
fi

# Sprawdź czy DOMAIN jest ustawiona
DOMAIN=$(grep "^DOMAIN=" .env.production | cut -d '=' -f2 || echo "")
if [ -z "$DOMAIN" ] || [ "$DOMAIN" = "localhost" ]; then
    echo "⚠️  Ustawiam domenę na mareknba.pl..."
    
    if grep -q "^DOMAIN=" .env.production; then
        sed -i 's/^DOMAIN=.*/DOMAIN=mareknba.pl/' .env.production
    else
        echo "" >> .env.production
        echo "DOMAIN=mareknba.pl" >> .env.production
    fi
    
    echo "✅ Domena ustawiona: mareknba.pl"
fi

# Sprawdź czy VITE_API_BASE_URL jest pusta (dla produkcji)
if grep -q "^VITE_API_BASE_URL=http" .env.production; then
    echo "⚠️  Czyszczę VITE_API_BASE_URL dla produkcji..."
    sed -i 's/^VITE_API_BASE_URL=.*/VITE_API_BASE_URL=/' .env.production
    echo "✅ API URL skonfigurowany dla Caddy proxy"
fi

# Sprawdź czy Docker działa
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker nie działa!"
    echo ""
    echo "Zainstaluj Docker:"
    echo "  curl -fsSL https://get.docker.com -o get-docker.sh"
    echo "  sudo sh get-docker.sh"
    exit 1
fi

echo "════════════════════════════════════════════════════════════"
echo "📋 PRE-DEPLOYMENT INFO"
echo "════════════════════════════════════════════════════════════"
echo "📁 Katalog: $(pwd)"
echo "🐋 Docker: $(docker --version)"
echo "🐋 Compose: $(docker compose version)"
echo "🌐 IP serwera: $(hostname -I | awk '{print $1}' || echo 'N/A')"
echo "🌍 Domena: mareknba.pl"
echo ""

# Menu
echo "════════════════════════════════════════════════════════════"
echo "🚀 DEPLOYMENT OPTIONS"
echo "════════════════════════════════════════════════════════════"
echo "1) 🆕 Fresh deployment (stop, build, start)"
echo "2) 🔄 Quick restart (no rebuild)"
echo "3) 📥 Update from Git (pull + rebuild)"
echo "4) ⏹️  Stop application"
echo "5) 📋 View logs"
echo "6) 📊 Status check"
echo "7) 🧹 Cleanup (remove unused images)"
echo "0) ❌ Cancel"
echo ""
read -p "Wybierz opcję [0-7]: " choice

case $choice in
    1)
        echo ""
        echo "🚀 Fresh Deployment dla mareknba.pl..."
        echo "════════════════════════════════════════════════════════════"
        
        echo "⏹️  Zatrzymuję stare kontenery..."
        docker compose -f docker-compose.prod.yml down || true
        
        echo "🧹 Czyszczę stare obrazy..."
        docker image prune -f || true
        
        echo "🏗️  Buduję i uruchamiam..."
        docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
        
        echo ""
        echo "✅ Deployment zakończony!"
        echo ""
        echo "Aplikacja dostępna na:"
        echo "  🌍 https://mareknba.pl"
        echo "  🏥 https://mareknba.pl/health"
        echo "  🔧 https://mareknba.pl/api/health"
        ;;
        
    2)
        echo ""
        echo "🔄 Quick Restart..."
        docker compose -f docker-compose.prod.yml restart
        echo "✅ Zrestartowano!"
        ;;
        
    3)
        echo ""
        echo "📥 Update from Git..."
        echo "════════════════════════════════════════════════════════════"
        
        if [ ! -d ".git" ]; then
            echo "❌ To nie jest repozytorium git!"
            exit 1
        fi
        
        echo "💾 Backup konfiguracji..."
        cp .env.production .env.production.backup
        
        echo "📥 Pobieranie zmian..."
        git pull
        
        echo "✅ Przywracam konfigurację..."
        if [ -f ".env.production.backup" ]; then
            mv .env.production.backup .env.production
        fi
        
        echo "🏗️  Rebuild i restart..."
        docker compose -f docker-compose.prod.yml down
        docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
        
        echo "✅ Update zakończony!"
        ;;
        
    4)
        echo ""
        echo "⏹️  Zatrzymuję aplikację..."
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
        
        if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
            echo "✅ Backend: OK"
        else
            echo "❌ Backend: NOT RESPONDING"
        fi
        
        if curl -f -s http://localhost/health > /dev/null 2>&1; then
            echo "✅ Caddy: OK"
        else
            echo "⚠️  Caddy: NOT RESPONDING"
        fi
        
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
        echo "🐋 Docker Stats"
        echo "════════════════════════════════════════════════════════════"
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
        ;;
        
    7)
        echo ""
        echo "🧹 Cleanup..."
        echo "════════════════════════════════════════════════════════════"
        docker system prune -a -f
        echo "✅ Oczyszczono!"
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
echo "🌍 APPLICATION URLS"
echo "════════════════════════════════════════════════════════════"
echo "Frontend:    https://mareknba.pl"
echo "API:         https://mareknba.pl/api/health"
echo "Health:      https://mareknba.pl/health"
echo ""
echo "📚 Documentation: SELF_HOSTING_GUIDE.md"
echo "════════════════════════════════════════════════════════════"
echo ""
