#!/bin/bash
# =================================================================
# NBA Analytics - Ubuntu Server Setup for mareknba.pl
# =================================================================
# Automatyczna instalacja wszystkiego co potrzebne
# Użyj: bash setup-ubuntu-mareknba.sh --yes (dla auto-potwierdzenia)
# =================================================================

set -e

# Sprawdź flagę --yes
AUTO_YES=false
if [[ "$1" == "--yes" || "$1" == "-y" ]]; then
    AUTO_YES=true
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║    🏀 NBA Analytics - Ubuntu Server Setup                ║"
echo "║    Domain: mareknba.pl                                    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Sprawdź czy to Ubuntu/Debian
if [ ! -f /etc/os-release ]; then
    echo "❌ Nie można wykryć systemu operacyjnego!"
    exit 1
fi

. /etc/os-release
echo "📋 System: $PRETTY_NAME"
echo ""

# Sprawdź sudo (tylko jeśli nie root)
if [ "$EUID" -ne 0 ] && ! sudo -v &>/dev/null; then
    echo "❌ Ten skrypt wymaga uprawnień sudo"
    exit 1
fi

# Ustaw SUDO prefix jeśli nie root
if [ "$EUID" -eq 0 ]; then
    SUDO=""
else
    SUDO="sudo"
fi

echo "════════════════════════════════════════════════════════════"
echo "ℹ️  Ten skrypt zainstaluje:"
echo "   ✓ Docker & Docker Compose"
echo "   ✓ Git"
echo "   ✓ Podstawowe narzędzia"
echo "   ✓ Firewall (UFW)"
echo "   ✓ Projekt NBA Analytics"
echo "════════════════════════════════════════════════════════════"
echo ""

if [ "$AUTO_YES" = false ]; then
    read -p "Czy kontynuować? (tak/nie): " confirm
    if [[ ! "$confirm" =~ ^(tak|t|yes|y)$ ]]; then
        echo "Anulowano."
        exit 0
    fi
else
    echo "🚀 Tryb automatyczny (--yes): Pomijam potwierdzenia"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "KROK 1/8: Aktualizacja systemu"
echo "════════════════════════════════════════════════════════════"
$SUDO apt update
$SUDO apt upgrade -y
echo "✅ System zaktualizowany"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "KROK 2/8: Instalacja podstawowych narzędzi"
echo "════════════════════════════════════════════════════════════"
$SUDO apt install -y \
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
echo "KROK 3/8: Instalacja Docker"
echo "════════════════════════════════════════════════════════════"

if command -v docker &> /dev/null; then
    echo "ℹ️  Docker już jest zainstalowany: $(docker --version)"
else
    echo "📦 Instalowanie Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    $SUDO sh get-docker.sh
    rm get-docker.sh
    
    # Dodaj użytkownika do grupy docker (tylko jeśli nie root)
    if [ "$EUID" -ne 0 ]; then
        $SUDO usermod -aG docker $USER
    fi
    
    echo "✅ Docker zainstalowany: $(docker --version)"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "KROK 4/8: Instalacja Docker Compose"
echo "════════════════════════════════════════════════════════════"

if docker compose version &> /dev/null; then
    $SUDO "ℹ️  Docker Compose już jest zainstalowany: $(docker compose version)"
else
    sudo apt install -y docker-compose-plugin
    echo "✅ Docker Compose zainstalowany: $(docker compose version)"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "KROK 5/8: Konfiguracja Firewall (UFW)"
ech$SUDO ufw status | grep -q "Status: active"; then
    echo "ℹ️  Firewall UFW już jest aktywny"
else
    echo "🔥 Konfiguracja firewall..."
    $SUDO ufw --force reset
    $SUDO ufw default deny incoming
    $SUDO ufw default allow outgoing
    $SUDO ufw allow 22/tcp comment 'SSH'
    $SUDO ufw allow 80/tcp comment 'HTTP'
    $SUDO ufw allow 443/tcp comment 'HTTPS'
    $SUDO ufw --force enable
    echo "✅ Firewall skonfigurowany"
fi

echo ""
echo "Otwarte porty:"
$SUDO ""
echo "Otwarte porty:"
sudo ufw status numbered

echo ""
echo "════════════════════════════════════════════════════════════"
echo "KROK 6/8: Sprawdzenie IP serwera"
echo "════════════════════════════════════════════════════════════"

PUBLIC_IP=$(curl -s ifconfig.me || echo "Nie można pobrać")
LOCAL_IP=$(hostname -I | awk '{print $1}' || echo "N/A")

echo "🌐 IP lokalne (w sieci):  $LOCAL_IP"
echo "🌍 IP publiczne:          $PUBLIC_IP"
echo ""

if [ "$PUBLIC_IP" != "Nie można pobrać" ]; then
    echo "⚠️  WAŻNE - KONFIGURACJA DNS:"
    echo ""
    echo "W panelu zarządzania domeną mareknba.pl ustaw:"
    echo ""
    echo "  Typ   Nazwa    Wartość         TTL"
    echo "  ────────────────────────────────────"
    echo "  A     @        $PUBLIC_IP      3600"
    echo "  A     www      $PUBLIC_IP      3600"
    echo ""
fi

# Sprawdź czy IP publiczne jest takie samo jak lokalne
if [ "$PUBLIC_IP" = "$LOCAL_IP" ]; then
    echo "✅ Serwer ma bezpośrednie połączenie z internetem (stałe IP)"
    echo "   Nie potrzebujesz port forwardingu w routerze!"
else
    echo "⚠️  Serwer jest w sieci lokalnej (za routerem)"
    echo ""
    echo "MUSISZ skonfigurować PORT FORWARDING w routerze:"
    echo "  Port 80  (HTTP)  → $LOCAL_IP → Port 80"
    echo "  Port 443 (HTTPS) → $LOCAL_IP → Port 443"
    echo ""
    echo "Jak to zrobić:"
    echo "1. Wejdź do panelu routera (zwykle 192.168.1.1)"
    echo "2. Znajdź 'Port Forwarding' lub 'Virtual Server'"
    echo "3. Dodaj reguły dla portów 80 i 443 → $LOCAL_IP"
    echo "4. Zapisz i zrestartuj router"
fi

if [ "$AUTO_YES" = false ]; then
    read -p "Czy DNS i port forwarding są skonfigurowane? (tak/nie): " dns_ready
    if [[ ! "$dns_ready" =~ ^(tak|t|yes|y)$ ]]; then
        echo ""
        echo "⏸️  OK, skonfiguruj DNS i port forwarding (jeśli potrzebne),"
        echo "   a potem uruchom ponownie ten skrypt."
        echo ""
        echo "Możesz też kontynuować instalację, ale aplikacja nie będzie"
        echo "dostępna z internetu dopóki nie skonfigurujesz DNS."
        echo ""
        read -p "Kontynuować mimo to? (tak/nie): " continue_anyway
        if [[ ! "$continue_anyway" =~ ^(tak|t|yes|y)$ ]]; then
            echo "Anulowano. Uruchom ponownie gdy będziesz gotowy:"
            echo "  bash setup-ubuntu-mareknba.sh --yes"
            exit 0
        fi
    fi
else
    echo "🚀 Tryb automatyczny: Pomijam weryfikację DNS (skonfiguruj później)"  echo "  bash setup-ubuntu-mareknba.sh"
        exit 0
    fi
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echoif [ "$AUTO_YES" = false ]; then
        read -p "Czy chcesz go usunąć i sklonować na nowo? (tak/nie): " remove_dir
        if [[ "$remove_dir" =~ ^(tak|t|yes|y)$ ]]; then
            echo "Usuwam stary katalog..."
            rm -rf "$PROJECT_DIR"
        else
            echo "Używam istniejącego katalogu"
        fi
    else
        echo "🚀 Tryb automatyczny: ECT_DIR" ]; then
    echo "⚠️  Katalog $PROJECT_DIR już istnieje"
    read -p "Czy chcesz go usunąć i sklonować na nowo? (tak/nie): " remove_dir
    if [[ "$remove_dir" =~ ^(tak|t|yes|y)$ ]]; then
        echo "Usuwam stary katalog..."
        rm -rf "$PROJECT_DIR"
    else
        echo "Używam istniejącego katalogu"
    fi
fi

if [ ! -d "$PROJECT_DIR" ]; then
    echo "📥 Klonowanie repozytorium..."
    git clone https://github.com/Nawigante81/MarekNBAnalitics--chuj-wi.git "$PROJECT_DIR"
    echo "✅ Projekt sklonowany do: $PROJECT_DIR"
else
    echo "✅ Projekt już istnieje w: $PROJECT_DIR"
fi

cd "$PROJECT_DIR"$SUDO tee -a /etc/sysctl.conf
    echo "fs.inotify.max_user_instances=512" | $SUDO tee -a /etc/sysctl.conf
    $SUDO sysctl -p
    echo "✅ Limity systemowe zwiększone"
else
    echo "ℹ️  Limity systemowe już skonfigurowane"
fi

# Włącz autostart Docker
$SUDOecho "fs.inotify.max_user_watches=524288" | sudo tee -a /etc/sysctl.conf
    echo "fs.inotify.max_user_instances=512" | sudo tee -a /etc/sysctl.conf
    sudo sysctl -p
    echo "✅ Limity systemowe zwiększone"
else
    echo "ℹ️  Limity systemowe już skonfigurowane"
fi

# Włącz autostart Docker
sudo systemctl enable docker
echo "✅ Docker będzie uruchamiany automatycznie"

# Utwórz katalogi dla logów
mkdir -p "$PROJECT_DIR/backend/logs"
mkdir -p "$PROJECT_DIR/logs"

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              ✅ INSTALACJA ZAKOŃCZONA!                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 PODSUMOWANIE:"
echo "   ├─ System: $PRETTY_NAME"
echo "   ├─ Docker: $(docker --version)"
echo "   ├─ Docker Compose: $(docker compose version)"
if [ "$EUID" -ne 0 ]; then
    echo "1️⃣  WYLOGUJ SIĘ i ZALOGUJ PONOWNIE (ważne dla Docker!):"
    echo "    exit"
    echo "    ssh $(whoami)@$LOCAL_IP"
    echo ""
else
    echo "1️⃣  Jesteś zalogowany jako root - możesz od razu kontynuować"
    echo ""
fi  └─ Firewall: Aktywny (porty 22, 80, 443)"
echo ""
echo "════════════════════════════════════════════════════════════"
echo "⚠️  WYMAGANE KROKI PO INSTALACJI:"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "1️⃣  WYLOGUJ SIĘ i ZALOGUJ PONOWNIE (ważne dla Docker!):"
echo "    exit"
echo "    ssh $(whoami)@$LOCAL_IP"
echo ""
echo "2️⃣  Przejdź do katalogu projektu:"
echo "    cd ~/nba-analytics"
echo ""
echo "3️⃣  Sprawdź konfigurację:"
echo "    cat .env.production"
echo "    # Powinna być: DOMAIN=mareknba.pl"
echo ""
echo "4️⃣  Uruchom aplikację:"
echo "    chmod +x deploy-mareknba.sh"
echo "    ./deploy-mareknba.sh"
echo "    # Wybierz opcję 1 (Fresh deployment)"
echo ""
echo "    LUB ręcznie:"
echo "    docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build"
echo ""
echo "5️⃣  Sprawdź status:"
echo "    docker compose -f docker-compose.prod.yml ps"
echo "    docker compose -f docker-compose.prod.yml logs -f"
echo ""
echo "6️⃣  Testuj lokalnie:"
echo "    curl http://localhost/health"
echo ""
echo "7️⃣  Po propagacji DNS (5-60 minut):"
echo "    https://mareknba.pl"
echo ""
echo "════════════════════════════════════════════════════════════"
echo "📚 DOKUMENTACJA:"
echo "════════════════════════════════════════════════════════════"
echo "   SELF_HOSTING_GUIDE.md  - Pełny przewodnik"
echo "   deploy-mareknba.sh     - Skrypt deployment"
echo ""
echo "🆘 W razie problemów sprawdź logi:"
echo "   docker compose -f docker-compose.prod.yml logs -f"
echo ""
