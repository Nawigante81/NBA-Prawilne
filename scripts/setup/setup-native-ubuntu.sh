#!/bin/bash
# =================================================================
# NBA Analytics - Non-Docker Deployment for mareknba.pl
# =================================================================
# Uruchamia aplikację bezpośrednio na Ubuntu (bez Dockera)
# Dla serwerów OpenVZ/Virtuozzo gdzie Docker nie działa
# =================================================================

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   🏀 NBA Analytics - Native Ubuntu Deployment            ║"
echo "║   Simple Mode: Backend + Frontend (NO Caddy/SSL)         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Ustaw katalog projektu
PROJECT_DIR="$HOME/nba-analytics"
BACKEND_DIR="$PROJECT_DIR/backend"

# Sprawdź czy katalog projektu istnieje
if [ ! -d "$PROJECT_DIR" ]; then
    echo "📁 Katalog projektu nie istnieje, klonuję z GitHub..."
    cd "$HOME"
    git clone https://github.com/Nawigante81/MarekNBAnalitics--chuj-wi.git nba-analytics
    echo "✅ Projekt sklonowany do: $PROJECT_DIR"
elif [ ! -f "$PROJECT_DIR/package.json" ]; then
    echo "❌ Błąd: $PROJECT_DIR istnieje ale nie zawiera projektu!"
    exit 1
else
    echo "✅ Znaleziono projekt w: $PROJECT_DIR"
    cd "$PROJECT_DIR"
    echo "📥 Aktualizuję kod z GitHub..."
    git pull || echo "⚠️  Nie można zaktualizować (to OK jeśli projekt nie jest z git)"
fi

cd "$PROJECT_DIR"

# Sprawdź czy działa jako root lub z sudo
if [ "$EUID" -ne 0 ]; then 
    SUDO="sudo"
else
    SUDO=""
fi

echo "📁 Katalog projektu: $PROJECT_DIR"
echo ""

# Zainstaluj podstawowe narzędzia
echo "📦 Instalowanie podstawowych narzędzi..."
$SUDO apt-get update
$SUDO apt-get install -y curl wget git build-essential

echo ""
echo "════════════════════════════════════════════════════════════"
echo "KROK 1/6: Instalacja Node.js 20"
echo "════════════════════════════════════════════════════════════"

if command -v node &> /dev/null && node -v | grep -q "v20"; then
    echo "✅ Node.js 20 już zainstalowany: $(node -v)"
else
    echo "📦 Instalowanie Node.js 20..."
    curl -fsSL https://deb.nodesource.com/setup_20.x -o /tmp/nodesource_setup.sh
    if [ "$EUID" -eq 0 ]; then
        bash /tmp/nodesource_setup.sh
        apt-get install -y nodejs
    else
        sudo bash /tmp/nodesource_setup.sh
        sudo apt-get install -y nodejs
    fi
    rm -f /tmp/nodesource_setup.sh
    echo "✅ Node.js zainstalowany: $(node -v)"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "KROK 2/6: Instalacja Python 3"
echo "════════════════════════════════════════════════════════════"

# Sprawdź wersję Python
PYTHON_VERSION=$(python3 --version 2>/dev/null | awk '{print $2}' | cut -d. -f1,2)
PYTHON_CMD="python3"

if command -v python3 &> /dev/null; then
    echo "✅ Python już zainstalowany: $(python3 --version)"
    
    # Sprawdź czy jest wystarczająco nowy (>=3.9)
    PYTHON_MAJOR=$(python3 --version | awk '{print $2}' | cut -d. -f1)
    PYTHON_MINOR=$(python3 --version | awk '{print $2}' | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 9 ]; then
        echo "✅ Wersja Python jest OK (wymaga >=3.9)"
    else
        echo "⚠️  Python jest za stary, instaluję nowszą wersję..."
        $SUDO apt-get update
        $SUDO apt-get install -y python3 python3-venv python3-dev python3-pip
    fi
else
    echo "📦 Instalowanie Python..."
    $SUDO apt-get update
    $SUDO apt-get install -y python3 python3-venv python3-dev python3-pip
    echo "✅ Python zainstalowany: $(python3 --version)"
fi

# Upewnij się że venv i pip są zainstalowane
echo "📦 Instalowanie python3-venv i pip..."
$SUDO apt-get install -y python3-venv python3-pip python3-dev

# Upewnij się że pip jest zainstalowany
if ! command -v pip3 &> /dev/null; then
    echo "📦 Instalowanie pip..."
    $SUDO apt-get install -y python3-pip
fi

echo "✅ Python: $(python3 --version)"
echo "✅ Pip: $(pip3 --version | awk '{print $2}')"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "KROK 3/6: Instalacja Redis (Opcjonalne - dla cache)"
echo "════════════════════════════════════════════════════════════"

if command -v redis-server &> /dev/null; then
    echo "✅ Redis już zainstalowany: $(redis-server --version | head -1)"
else
    echo "📦 Instalowanie Redis..."
    $SUDO apt-get install -y redis-server
    echo "✅ Redis zainstalowany"
fi

# Sprawdź czy Redis już działa
if redis-cli ping &>/dev/null; then
    echo "✅ Redis już działa"
else
    echo "🔄 Próbuję uruchomić Redis..."
    
    # METODA 1: Systemctl (normalny Linux)
    if $SUDO systemctl start redis-server 2>/dev/null; then
        $SUDO systemctl enable redis-server 2>/dev/null
        sleep 2
        if redis-cli ping &>/dev/null; then
            echo "✅ Redis działa (systemctl)"
        else
            echo "⚠️  Redis przez systemctl nie odpowiada"
        fi
    else
        # METODA 2: Bezpośrednie uruchomienie (dla OpenVZ)
        echo "⚠️  Systemctl nie działa (OpenVZ/Virtuozzo), uruchamiam bezpośrednio..."
        
        # Zatrzymaj stare procesy
        pkill -9 redis-server 2>/dev/null || true
        sleep 1
        
        # Utwórz katalog dla Redis
        mkdir -p /var/run/redis
        mkdir -p /var/log/redis
        
        # Uruchom Redis jako daemon bez systemd
        nohup redis-server --daemonize no --port 6379 --bind 127.0.0.1 --protected-mode yes > /var/log/redis/redis.log 2>&1 &
        sleep 2
        
        # Sprawdź czy działa
        if redis-cli ping &>/dev/null; then
            echo "✅ Redis działa (daemon mode)"
        else
            echo ""
            echo "⚠️  ═══════════════════════════════════════════════════════"
            echo "⚠️  Redis nie uruchomił się - to OK dla OpenVZ!"
            echo "⚠️  Aplikacja będzie działać BEZ cache (trochę wolniej)"
            echo "⚠️  ═══════════════════════════════════════════════════════"
            echo ""
        fi
    fi
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "KROK 4/6: Instalacja PM2 (Process Manager)"
echo "════════════════════════════════════════════════════════════"

if command -v pm2 &> /dev/null; then
    echo "✅ PM2 już zainstalowany: $(pm2 --version)"
else
    echo "📦 Instalowanie PM2..."
    $SUDO npm install -g pm2
    echo "✅ PM2 zainstalowany: $(pm2 --version)"
fi

# Skonfiguruj PM2 startup
$SUDO pm2 startup systemd -u $(whoami) --hp $(eval echo ~$(whoami)) || true

echo ""
echo "════════════════════════════════════════════════════════════"
echo "KROK 5/6: Budowanie Frontendu"
echo "═════════════════════════════════════════════════════════"

echo "📦 Instalowanie zależności frontend..."
npm install

echo "🏗️  Budowanie frontend..."
npm run build

if [ ! -d "dist" ]; then
    echo "❌ Błąd: Nie udało się zbudować frontendu"
    exit 1
fi

echo "✅ Frontend zbudowany w: $PROJECT_DIR/dist"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "KROK 6/6: Konfiguracja Backendu"
echo "════════════════════════════════════════════════════════════"

# Instaluj zależności systemowe dla web scrapingu
echo "📦 Instalowanie chromium dla web scrapingu..."
VIRT_TYPE=$(systemd-detect-virt -c 2>/dev/null || true)
if [ "$VIRT_TYPE" = "lxc" ] || [ "$VIRT_TYPE" = "openvz" ] || [ "$VIRT_TYPE" = "systemd-nspawn" ]; then
    echo "⚠️  Pomijam chromium (snap nie dziala w: $VIRT_TYPE)"
else
    $SUDO apt-get install -y chromium-browser chromium-chromedriver wget unzip || echo "⚠️  Chromium - pominięto"
fi

cd "$BACKEND_DIR"

# Utwórz katalogi dla logów
echo "📁 Tworzę katalogi..."
mkdir -p logs

# Utwórz virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Tworzę Python virtual environment..."
    python3 -m venv venv
fi

echo "📦 Instalowanie zależności Python..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Zainstaluj playwright browsers i systemowe zależności
echo "📦 Instalowanie Playwright browsers i zależności systemowych..."
playwright install chromium 2>/dev/null || echo "⚠️  Playwright browsers - pominięto"
$SUDO playwright install-deps 2>/dev/null || echo "⚠️  Playwright system deps - pominięto (zainstaluj ręcznie: sudo playwright install-deps)"

echo "✅ Backend skonfigurowany"

# Wróć do głównego katalogu
cd "$PROJECT_DIR"

# Zainstaluj serve globalnie dla frontendu
echo "📦 Instalowanie 'serve' dla frontendu..."
$SUDO npm install -g serve

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              ✅ KONFIGURACJA ZAKOŃCZONA!                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 ZAINSTALOWANO:"
echo "   ├─ Node.js: $(node -v)"
echo "   ├─ Python: $(python3 --version | awk '{print $2}')"
echo "   ├─ Redis: $(redis-server --version | head -1 | awk '{print $3}')"
echo "   ├─ PM2: $(pm2 --version)"
echo "   ├─ Serve: $(npm list -g serve --depth=0 2>/dev/null | grep serve || echo 'installed')"
echo "   └─ Frontend: $PROJECT_DIR/dist"
echo ""
echo "════════════════════════════════════════════════════════════"
echo "🚀 URUCHOMIENIE APLIKACJI"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Użyj skryptu: ./start-simple.sh"
echo ""
echo "Aplikacja będzie dostępna:"
echo "   Frontend: http://192.168.100.128:8080"
echo "   Backend:  http://192.168.100.128:8000"
echo ""
echo "Przydatne komendy:"
echo "   pm2 status         - Status procesów"
echo "   pm2 logs           - Logi aplikacji"
echo "   ./stop-simple.sh   - Zatrzymaj aplikację"
echo ""
