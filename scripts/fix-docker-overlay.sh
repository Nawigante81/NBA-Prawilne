#!/bin/bash
# =================================================================
# NBA Analytics - Docker Overlay Fix
# =================================================================
# Naprawia problem z overlayfs w Docker/containerd
# =================================================================

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║       🔧 Docker OverlayFS Permission Fix                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Sprawdź czy działa jako root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Ten skrypt musi być uruchomiony jako root"
    echo "   Użyj: sudo bash fix-docker-overlay.sh"
    exit 1
fi

echo "🔍 Diagnoza problemu..."
echo ""

# Sprawdź kernel i overlayfs
echo "📋 Informacje systemowe:"
echo "   Kernel: $(uname -r)"
echo "   OS: $(lsb_release -d | cut -f2)"
echo ""

# Sprawdź czy overlay module jest załadowany
if lsmod | grep -q overlay; then
    echo "✅ Moduł overlay jest załadowany"
else
    echo "⚠️  Moduł overlay nie jest załadowany - ładuję..."
    modprobe overlay
    if lsmod | grep -q overlay; then
        echo "✅ Moduł overlay załadowany"
    else
        echo "❌ Nie można załadować modułu overlay"
        echo "   Twój kernel może nie obsługiwać overlayfs"
    fi
fi

# Sprawdź typ systemu plików
ROOT_FS=$(df -T / | tail -1 | awk '{print $2}')
echo "   System plików root: $ROOT_FS"

# Sprawdź czy to wirtualizacja
if systemd-detect-virt &>/dev/null; then
    VIRT=$(systemd-detect-virt)
    echo "   Wirtualizacja: $VIRT"
    
    if [[ "$VIRT" == "openvz" || "$VIRT" == "lxc" ]]; then
        echo ""
        echo "⚠️  Wykryto $VIRT - overlayfs może nie działać!"
        echo "   Zmieniam storage driver na vfs..."
        NEED_VFS=true
    fi
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "🔧 ROZWIĄZANIA"
echo "════════════════════════════════════════════════════════════"
echo ""

# Rozwiązanie 1: Zatrzymaj Docker i wyczyść
echo "1️⃣  Zatrzymuję Docker..."
systemctl stop docker containerd || true
sleep 2

# Rozwiązanie 2: Wyczyść stare dane
echo "2️⃣  Czyszczę stare dane containerd..."
rm -rf /var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/* || true
rm -rf /var/lib/containerd/tmpmounts/* || true

# Rozwiązanie 3: Sprawdź i napraw uprawnienia
echo "3️⃣  Naprawiam uprawnienia..."
chmod 755 /var/lib/containerd
chmod 755 /var/lib/docker
chown -R root:root /var/lib/containerd
chown -R root:root /var/lib/docker

# Rozwiązanie 4: Konfiguracja Docker daemon
echo "4️⃣  Konfiguruję Docker daemon..."
mkdir -p /etc/docker

# Sprawdź czy potrzebujemy vfs
if [ "$NEED_VFS" = true ]; then
    cat > /etc/docker/daemon.json <<EOF
{
  "storage-driver": "vfs",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF
    echo "   ✅ Ustawiono storage driver: vfs (wolniejszy ale stabilny)"
else
    cat > /etc/docker/daemon.json <<EOF
{
  "storage-driver": "overlay2",
  "storage-opts": [
    "overlay2.override_kernel_check=true"
  ],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF
    echo "   ✅ Ustawiono storage driver: overlay2"
fi

# Rozwiązanie 5: Restart Docker
echo "5️⃣  Uruchamiam Docker..."
systemctl daemon-reload
systemctl start docker

sleep 3

# Sprawdź status
if systemctl is-active --quiet docker; then
    echo "   ✅ Docker działa"
else
    echo "   ❌ Docker nie uruchomił się"
    echo ""
    echo "Sprawdź logi:"
    echo "  journalctl -xeu docker"
    exit 1
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ NAPRAWIONO!"
echo "════════════════════════════════════════════════════════════"
echo ""

# Pokaż informacje o storage driver
STORAGE_DRIVER=$(docker info 2>/dev/null | grep "Storage Driver" | awk '{print $3}')
echo "📊 Docker Info:"
echo "   Storage Driver: $STORAGE_DRIVER"
echo ""

echo "🧪 TEST:"
echo "   Testuję Docker pull..."
if docker pull hello-world; then
    echo "   ✅ Docker pull działa!"
    docker run --rm hello-world
    echo ""
    echo "   ✅ Docker run działa!"
    docker rmi hello-world >/dev/null 2>&1
else
    echo "   ❌ Nadal są problemy"
    echo ""
    echo "Spróbuj alternatywnego storage driver:"
    echo "  1. Edytuj: nano /etc/docker/daemon.json"
    echo "  2. Zmień 'storage-driver' na 'vfs'"
    echo "  3. Restart: systemctl restart docker"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "🚀 NASTĘPNE KROKI"
echo "════════════════════════════════════════════════════════════"
echo "cd ~/nba-analytics"
echo "./deploy-mareknba.sh"
echo ""
