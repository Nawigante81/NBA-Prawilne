# 🚀 NBA Analytics - OVH Deployment Guide

Kompletny przewodnik wdrożenia projektu NBA Analytics na hostingu OVH.

---

## 📋 KROK 1: Wybór i przygotowanie serwera OVH

### Opcja A: VPS OVH (ZALECANA) ⭐
**Minimalne wymagania:**
- **RAM**: 4GB (zalecane 8GB)
- **Procesor**: 2 vCPU
- **Dysk**: 40GB SSD
- **System**: Ubuntu 22.04 LTS lub Debian 12

**Polecane plany OVH VPS:**
- **VPS Starter** (2 vCPU, 4GB RAM, 80GB SSD) - ~40 PLN/mies
- **VPS Value** (2 vCPU, 8GB RAM, 160GB SSD) - ~80 PLN/mies

**Jak zamówić:**
1. Wejdź na: https://www.ovhcloud.com/pl/vps/
2. Wybierz plan VPS
3. System operacyjny: **Ubuntu 22.04**
4. Dodatkowe opcje: **włącz Backup** (opcjonalnie)
5. Finalizuj zamówienie

### Opcja B: Dedykowany Serwer OVH
Jeśli masz już serwer dedykowany - używamy tej samej konfiguracji co VPS.

### ❌ Hosting WWW OVH (NIE ZALECANE)
Współdzielony hosting (z cPanel) **nie obsługuje Docker** i wymaga znacznej przeróbki projektu.

---

## 📋 KROK 2: Zakup domeny

### 2.1 Gdzie kupić domenę?
**OVH Domains:**
1. https://www.ovhcloud.com/pl/domains/
2. Wybierz domenę (np. `nba-analytics.pl`, `your-name-nba.com`)
3. Cena: ~15-60 PLN/rok

**Alternatywy:**
- **Cloudflare** (~10 USD/rok) - bez marży
- **Namecheap** - popularna opcja
- **home.pl** - polski dostawca

### 2.2 Konfiguracja DNS (po zakupie serwera)
W panelu domeny ustaw rekordy DNS:
```
A     @              <IP_TWOJEGO_VPS>     TTL: 3600
A     www            <IP_TWOJEGO_VPS>     TTL: 3600
AAAA  @              <IPv6_TWOJEGO_VPS>   TTL: 3600 (opcjonalnie)
```

**Przykład:**
- Domena: `nba-analytics.com`
- IP VPS: `51.68.45.123`
- Rekord A: `nba-analytics.com` → `51.68.45.123`

---

## 📋 KROK 3: Pierwsze logowanie do VPS

### 3.1 Otrzymasz email od OVH z danymi:
```
IP: 51.68.45.xxx
User: ubuntu (lub root dla Debian)
Password: xxxxxxxxxxxxx
```

### 3.2 Zaloguj się przez SSH:

**Windows (PowerShell):**
```powershell
ssh ubuntu@51.68.45.xxx
# Wpisz hasło z emaila
```

**Windows (PuTTY):**
1. Pobierz PuTTY: https://www.putty.org/
2. Host: `51.68.45.xxx`
3. Port: `22`
4. Connection type: SSH
5. Kliknij Open, podaj login i hasło

### 3.3 Zmień hasło (ważne!):
```bash
passwd
# Wpisz nowe, silne hasło (2 razy)
```

---

## 📋 KROK 4: Instalacja Docker i wymagań

Skopiuj i uruchom poniższy skrypt **na serwerze VPS**:

```bash
#!/bin/bash
# Skrypt instalacyjny dla OVH VPS - Ubuntu 22.04/Debian 12

echo "🚀 NBA Analytics - OVH VPS Setup"
echo "================================="

# Aktualizacja systemu
echo "📦 Aktualizacja systemu..."
sudo apt update && sudo apt upgrade -y

# Instalacja podstawowych narzędzi
echo "🔧 Instalacja narzędzi..."
sudo apt install -y curl wget git nano htop ufw

# Instalacja Docker
echo "🐳 Instalacja Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Instalacja Docker Compose
echo "🐳 Instalacja Docker Compose..."
sudo apt install -y docker-compose-plugin

# Konfiguracja Firewall
echo "🔥 Konfiguracja firewall..."
sudo ufw allow 22/tcp     # SSH
sudo ufw allow 80/tcp     # HTTP
sudo ufw allow 443/tcp    # HTTPS
sudo ufw --force enable

# Utworzenie katalogu projektu
echo "📁 Tworzenie katalogu projektu..."
mkdir -p ~/nba-analytics
cd ~/nba-analytics

echo "✅ Instalacja zakończona!"
echo ""
echo "⚠️  WAŻNE: Wyloguj się i zaloguj ponownie, aby Docker działał:"
echo "    exit"
echo "    ssh ubuntu@<TWOJE_IP>"
```

### Zapisz skrypt i uruchom:
```bash
# Skopiuj cały skrypt powyżej
nano setup-ovh.sh

# Wklej (Ctrl+Shift+V w terminalu)
# Zapisz (Ctrl+X, Y, Enter)

# Uruchom
chmod +x setup-ovh.sh
./setup-ovh.sh

# WYLOGUJ SIĘ I ZALOGUJ PONOWNIE
exit
ssh ubuntu@<TWOJE_IP>
```

---

## 📋 KROK 5: Upload projektu na serwer

### Metoda A: Git (ZALECANA)

**Na serwerze VPS:**
```bash
cd ~/nba-analytics

# Sklonuj repozytorium
git clone https://github.com/Nawigante81/MarekNBAnalitics--chuj-wi.git .

# Sprawdź czy pliki są na miejscu
ls -la
```

### Metoda B: SCP/SFTP (bez Git)

**Na swoim komputerze (Windows PowerShell):**
```powershell
# Z katalogu projektu
cd "E:\VSCODE PROJEKT\MarekNBAnalitics-main"

# Upload wszystkich plików
scp -r * ubuntu@<IP_VPS>:~/nba-analytics/

# Lub użyj WinSCP: https://winscp.net/
```

---

## 📋 KROK 6: Konfiguracja środowiska

### 6.1 Na serwerze VPS:
```bash
cd ~/nba-analytics

# Skopiuj przykładową konfigurację
cp .env .env.production

# Edytuj konfigurację
nano .env.production
```

### 6.2 Wypełnij dane w `.env.production`:

```bash
# =================================================================
# DOMENA (ZMIEŃ NA SWOJĄ!)
# =================================================================
DOMAIN=your-domain.com              # WPISZ SWOJĄ DOMENĘ!

# =================================================================
# API CONFIGURATION
# =================================================================
VITE_API_BASE_URL=                  # ZOSTAW PUSTE (Caddy przekieruje)

# =================================================================
# SUPABASE CONFIGURATION
# =================================================================
VITE_SUPABASE_URL=https://vzuvsgfjutrwkbwpetwc.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ6dXZzZ2ZqdXRyd2tid3BldHdjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjcxODIxMzYsImV4cCI6MjA4Mjc1ODEzNn0.oqLHr6LnPun4RjNLrSuaOx2qaL1fL9kv0gZzQinGF04
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ6dXZzZ2ZqdXRyd2tid3BldHdjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NzE4MjEzNiwiZXhwIjoyMDgyNzU4MTM2fQ.K667JDCJxJ84vVD_kpozSxDIWSOhQThOZXiy3NVM-Ek

# =================================================================
# ODDS API CONFIGURATION
# =================================================================
VITE_ODDS_API_KEY=b17a3b658c04d085f4d39ca56c71e8ad

# =================================================================
# APPLICATION SETTINGS
# =================================================================
VITE_APP_TIMEZONE=America/Chicago
VITE_REFRESH_INTERVAL=30000
ENABLE_SCHEDULER=true
AUTO_SCRAPE_ON_START=false
VITE_DEV_MODE=false
VITE_DEBUG=false

# User agent
BASKETBALL_REFERENCE_USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
```

**Zapisz:** `Ctrl+X`, `Y`, `Enter`

---

## 📋 KROK 7: Konfiguracja Caddy dla domeny

### 7.1 Sprawdź plik Caddyfile:
```bash
cat Caddyfile.docker
```

### 7.2 Jeśli trzeba, dostosuj:
```bash
nano Caddyfile.docker
```

Powinien wyglądać tak:
```
{$DOMAIN:localhost} {
    # Health endpoint
    handle /health {
        respond "OK" 200
    }

    # Backend API
    handle /api/* {
        reverse_proxy backend:8000
    }

    # Frontend
    handle {
        reverse_proxy frontend:8080
    }

    # Access log
    log {
        output file /var/log/caddy/access.log
        format json
    }
}
```

---

## 📋 KROK 8: Uruchomienie aplikacji

### 8.1 Build i uruchomienie:
```bash
cd ~/nba-analytics

# Uruchom w trybie produkcyjnym
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

### 8.2 Sprawdź status:
```bash
# Status kontenerów
docker compose -f docker-compose.prod.yml ps

# Logi
docker compose -f docker-compose.prod.yml logs -f

# Sprawdź czy działa
curl http://localhost/health
```

### 8.3 Oczekiwany output:
```
NAME                IMAGE                   STATUS
nba-backend         nba-backend:latest      Up
nba-frontend        nba-frontend:latest     Up
nba-caddy           caddy:2-alpine          Up
nba-redis           redis:7-alpine          Up
```

---

## 📋 KROK 9: Testowanie aplikacji

### 9.1 Przez HTTP (zanim skonfigurujesz domenę):
```bash
# Z serwera
curl http://localhost/health
curl http://localhost/api/health

# Z przeglądarki
http://<IP_VPS>/
```

### 9.2 Przez HTTPS (po skonfigurowaniu DNS):
Po ~5-10 minutach od ustawienia DNS:
```
https://your-domain.com/
https://your-domain.com/health
https://your-domain.com/api/health
```

**Caddy automatycznie pobierze certyfikat SSL od Let's Encrypt!** 🎉

---

## 📋 KROK 10: Monitorowanie i zarządzanie

### 10.1 Podstawowe komendy:
```bash
cd ~/nba-analytics

# Status
docker compose -f docker-compose.prod.yml ps

# Logi (wszystkie kontenery)
docker compose -f docker-compose.prod.yml logs -f

# Logi (konkretny kontener)
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend
docker compose -f docker-compose.prod.yml logs -f caddy

# Restart
docker compose -f docker-compose.prod.yml restart

# Stop
docker compose -f docker-compose.prod.yml down

# Restart po zmianach
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build
```

### 10.2 Aktualizacja kodu:
```bash
cd ~/nba-analytics

# Pobierz najnowszy kod
git pull

# Restart z nowym build
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build
```

### 10.3 Backup:
```bash
# Backup bazy danych (Supabase robi to automatycznie)
# Backup logów
tar -czf backup-logs-$(date +%Y%m%d).tar.gz backend/logs/

# Backup konfiguracji
cp .env.production .env.production.backup
```

---

## 🔧 TROUBLESHOOTING

### Problem: "Permission denied" przy Docker
```bash
# Dodaj użytkownika do grupy docker
sudo usermod -aG docker $USER

# Wyloguj się i zaloguj ponownie
exit
ssh ubuntu@<IP>
```

### Problem: "Port 80/443 already in use"
```bash
# Sprawdź co używa portów
sudo netstat -tulpn | grep :80
sudo netstat -tulpn | grep :443

# Zatrzymaj inne usługi (np. Apache/Nginx)
sudo systemctl stop apache2
sudo systemctl disable apache2
```

### Problem: Domena nie działa
```bash
# Sprawdź DNS (z lokalnego komputera)
nslookup your-domain.com

# Sprawdź czy Caddy działa
docker compose -f docker-compose.prod.yml logs caddy

# Sprawdź certyfikaty
docker exec -it nba-caddy caddy list-modules
```

### Problem: Backend nie odpowiada
```bash
# Sprawdź logi backend
docker compose -f docker-compose.prod.yml logs backend

# Wejdź do kontenera
docker exec -it nba-backend bash

# Sprawdź healthcheck
curl http://localhost:8000/health
```

### Problem: Brak pamięci
```bash
# Sprawdź zużycie
free -h
df -h

# Wyczyść nieużywane obrazy/kontenery
docker system prune -a
```

---

## 📊 Monitoring i alerty

### OVH Monitoring
1. Wejdź do panelu OVH
2. Wybierz swój VPS
3. Zakładka "Monitoring"
4. Ustaw alerty dla CPU/RAM/Disk

### Logi aplikacji
```bash
# Logi backend w czasie rzeczywistym
tail -f ~/nba-analytics/backend/logs/app.log

# Logi Caddy
docker exec -it nba-caddy tail -f /var/log/caddy/access.log
```

---

## 💰 SZACUNKOWE KOSZTY

| Usługa | Koszt miesięczny | Roczny |
|--------|------------------|--------|
| OVH VPS Starter (4GB) | ~40 PLN | ~480 PLN |
| Domena (.com) | - | ~60 PLN |
| **TOTAL** | **~40 PLN** | **~540 PLN** |

**Darmowe usługi w projekcie:**
- Supabase (Free tier) ✅
- Let's Encrypt SSL ✅
- The Odds API (Free tier) ✅

---

## ✅ CHECKLIST PRZED URUCHOMIENIEM

- [ ] Zamówiłeś VPS OVH
- [ ] Zalogowałeś się przez SSH
- [ ] Zainstalowałeś Docker
- [ ] Skonfigurowałeś firewall (UFW)
- [ ] Zakupiłeś domenę
- [ ] Skonfigurowałeś DNS (rekordy A)
- [ ] Sklonowałeś projekt na serwer
- [ ] Skonfigurowałeś `.env.production` z domeną
- [ ] Uruchomiłeś `docker compose up -d`
- [ ] Aplikacja odpowiada na http://IP
- [ ] DNS propagacja zakończona (10-60 min)
- [ ] HTTPS działa (Caddy pobrał certyfikat)

---

## 🆘 POTRZEBUJESZ POMOCY?

1. **OVH Support**: https://help.ovhcloud.com/
2. **GitHub Issues**: Otwórz issue w repozytorium
3. **Logi**: Zawsze dołącz logi przy zgłaszaniu problemu

---

## 🎉 GOTOWE!

Twoja aplikacja NBA Analytics powinna działać na:
- **https://your-domain.com** - Frontend
- **https://your-domain.com/api/** - Backend API

**Raporty generują się automatycznie:**
- 7:50 AM - Analiza poprzedniego dnia
- 8:00 AM - Podsumowanie poranne
- 11:00 AM - Scouting na dzisiejsze gry

---

*Ostatnia aktualizacja: 18 stycznia 2026*
