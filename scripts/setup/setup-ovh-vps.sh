#!/bin/bash
# =================================================================
# NBA Analytics - OVH VPS Automated Setup Script
# =================================================================
# Ten skrypt przygotowuje serwer OVH VPS do uruchomienia aplikacji
# Wspiera: Ubuntu 22.04, Ubuntu 20.04, Debian 11, Debian 12
# =================================================================

set -e  # Przerwij przy błędzie

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     🏀 NBA Analytics - OVH VPS Setup                      ║"
echo "║     Automated installation for production deployment      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Sprawdź czy skrypt jest uruchomiony na serwerze (nie lokalnie)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
    echo "❌ Ten skrypt należy uruchomić NA SERWERZE OVH VPS, nie lokalnie na Windows!"
    echo ""
    echo "Instrukcje:"
    echo "1. Zaloguj się do VPS: ssh ubuntu@<IP_VPS>"
    echo "2. Skopiuj ten skrypt na serwer"
    echo "3. Uruchom: bash setup-ovh-vps.sh"
    exit 1
fi

# Sprawdź system operacyjny
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
    echo "📋 Wykryto system: $OS $VER"
else
    echo "❌ Nie można wykryć systemu operacyjnego"
    exit 1
fi

# Sprawdź czy użytkownik ma sudo
if ! sudo -v &>/dev/null; then
    echo "❌ Ten skrypt wymaga uprawnień sudo"
    exit 1
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "KROK 1/7: Aktualizacja systemu"
echo "════════════════════════════════════════════════════════════"
sudo apt update
sudo apt upgrade -y
echo "✅ System zaktualizowany"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "KROK 2/7: Instalacja podstawowych narzędzi"
echo "════════════════════════════════════════════════════════════"
sudo apt install -y \
    curl \
    wget \
    git \
    nano \
    htop \
    net-tools \
    ca-certificates \
    gnupg \
    lsb-release \
    ufw \
    unzip
echo "✅ Narzędzia zainstalowane"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "KROK 3/7: Instalacja Docker"
echo "════════════════════════════════════════════════════════════"

# Sprawdź czy Docker już jest zainstalowany
if command -v docker &> /dev/null; then
    echo "ℹ️  Docker już jest zainstalowany ($(docker --version))"
else
    echo "📦 Instalowanie Docker..."
    
    # Oficjalny skrypt instalacyjny Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh
    
    # Dodaj użytkownika do grupy docker
    sudo usermod -aG docker $USER
    
    echo "✅ Docker zainstalowany: $(docker --version)"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "KROK 4/7: Instalacja Docker Compose"
echo "════════════════════════════════════════════════════════════"

# Instalacja Docker Compose plugin
if docker compose version &> /dev/null; then
    echo "ℹ️  Docker Compose już jest zainstalowany ($(docker compose version))"
else
    sudo apt install -y docker-compose-plugin
    echo "✅ Docker Compose zainstalowany: $(docker compose version)"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "KROK 5/7: Konfiguracja Firewall (UFW)"
echo "════════════════════════════════════════════════════════════"

# Sprawdź czy UFW jest aktywny
if sudo ufw status | grep -q "Status: active"; then
    echo "ℹ️  Firewall UFW już jest aktywny"
else
    echo "🔥 Konfiguracja firewall..."
    sudo ufw --force reset
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow 22/tcp comment 'SSH'
    sudo ufw allow 80/tcp comment 'HTTP'
    sudo ufw allow 443/tcp comment 'HTTPS'
    sudo ufw --force enable
    echo "✅ Firewall skonfigurowany"
fi

echo ""
sudo ufw status numbered

echo ""
echo "════════════════════════════════════════════════════════════"
echo "KROK 6/7: Utworzenie struktury katalogów"
echo "════════════════════════════════════════════════════════════"

# Katalog projektu
PROJECT_DIR="$HOME/nba-analytics"
mkdir -p "$PROJECT_DIR"
mkdir -p "$PROJECT_DIR/backend/logs"
mkdir -p "$PROJECT_DIR/logs"

echo "✅ Katalogi utworzone w: $PROJECT_DIR"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "KROK 7/7: Optymalizacja systemu dla Docker"
echo "════════════════════════════════════════════════════════════"

# Zwiększ limity systemowe dla Docker
if ! grep -q "fs.inotify.max_user_watches" /etc/sysctl.conf; then
    echo "fs.inotify.max_user_watches=524288" | sudo tee -a /etc/sysctl.conf
    echo "fs.inotify.max_user_instances=512" | sudo tee -a /etc/sysctl.conf
    sudo sysctl -p
    echo "✅ Limity systemowe zwiększone"
else
    echo "ℹ️  Limity systemowe już skonfigurowane"
fi

# Włącz automatyczne uruchamianie Docker przy starcie systemu
sudo systemctl enable docker
echo "✅ Docker będzie uruchamiany automatycznie"

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                  ✅ INSTALACJA ZAKOŃCZONA                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 PODSUMOWANIE:"
echo "   ├─ System: $OS $VER"
echo "   ├─ Docker: $(docker --version)"
echo "   ├─ Docker Compose: $(docker compose version)"
echo "   ├─ Katalog projektu: $PROJECT_DIR"
echo "   └─ Firewall: Aktywny (porty 22, 80, 443)"
echo ""
echo "⚠️  WAŻNE - WYMAGANE KROKI:"
echo ""
echo "1️⃣  WYLOGUJ SIĘ i ZALOGUJ PONOWNIE, aby Docker działał:"
echo "    exit"
echo "    ssh $(whoami)@$(hostname -I | awk '{print $1}')"
echo ""
echo "2️⃣  Przejdź do katalogu projektu:"
echo "    cd ~/nba-analytics"
echo ""
echo "3️⃣  Sklonuj repozytorium (lub upload plików):"
echo "    git clone https://github.com/Nawigante81/MarekNBAnalitics--chuj-wi.git ."
echo ""
echo "4️⃣  Skonfiguruj środowisko:"
echo "    cp .env .env.production"
echo "    nano .env.production"
echo "    # Ustaw DOMAIN=twoja-domena.com"
echo ""
echo "5️⃣  Uruchom aplikację:"
echo "    docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build"
echo ""
echo "📚 Szczegółowa dokumentacja: OVH_DEPLOYMENT_GUIDE.md"
echo ""
