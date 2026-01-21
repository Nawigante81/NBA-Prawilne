# 🏠 NBA Analytics - Self-Hosting Guide
## Hosting na własnym serwerze - mareknba.pl

Przewodnik wdrożenia projektu na **własnym serwerze** z domeną **mareknba.pl**.

---

## 📋 INFORMACJE O SERWERZE

Powiedz mi więcej o swoim serwerze:

### 1. **Jaki system operacyjny?**
   - [ ] Ubuntu (wersja: ___)
   - [ ] Debian (wersja: ___)
   - [ ] CentOS/RHEL
   - [ ] Windows Server
   - [ ] Inny: ___

### 2. **Specyfikacja serwera:**
   - CPU: ___
   - RAM: ___
   - Dysk: ___

### 3. **Typ serwera:**
   - [ ] Dedykowany (w domu/biurze)
   - [ ] VPS/Cloud
   - [ ] NAS (Synology/QNAP/etc.)
   - [ ] Raspberry Pi
   - [ ] Inny: ___

### 4. **Połączenie internetowe:**
   - [ ] Stałe IP publiczne
   - [ ] Dynamiczne IP (będziesz potrzebować DynamicDNS)
   - [ ] Za routerem (potrzebujesz port forwarding)

### 5. **Co już masz?**
   - [ ] Docker zainstalowany
   - [ ] Docker Compose zainstalowany
   - [ ] Dostęp SSH do serwera
   - [ ] Serwer działa 24/7

---

## 🌍 KONFIGURACJA DNS DLA mareknba.pl

### Krok 1: Sprawdź swoje publiczne IP

**Na serwerze (Linux):**
```bash
curl ifconfig.me
```

**Lub w przeglądarce:**
- https://whatismyipaddress.com/

### Krok 2: Skonfiguruj DNS

Wejdź do panelu zarządzania domeną **mareknba.pl** i dodaj następujące rekordy:

```dns
Typ   Nazwa    Wartość                      TTL
A     @        <TWOJE_PUBLICZNE_IP>        3600
A     www      <TWOJE_PUBLICZNE_IP>        3600
```

**Przykład:**
```dns
A     @        203.0.113.45                3600
A     www      203.0.113.45                3600
```

### Krok 3: Sprawdź propagację DNS

```bash
# Na swoim komputerze lub serwerze
nslookup mareknba.pl
nslookup www.mareknba.pl

# Powinno zwrócić Twoje IP
```

**Propagacja DNS może zająć 5-60 minut.**

---

## 🔧 KONFIGURACJA ROUTERA (jeśli serwer jest w sieci lokalnej)

Jeśli Twój serwer jest za routerem (np. w domu), musisz przekierować porty:

### Port Forwarding w routerze:

```
Port zewnętrzny → IP serwera w LAN → Port wewnętrzny
80              → 192.168.1.100      → 80
443             → 192.168.1.100      → 443
```

**Kroki (różne dla każdego routera):**
1. Wejdź do panelu routera (np. 192.168.1.1)
2. Znajdź "Port Forwarding" lub "Virtual Server"
3. Dodaj reguły dla portów 80 i 443
4. Zapisz i zrestartuj router

### Dynamiczne IP?

Jeśli Twoje IP zmienia się, użyj **DynamicDNS**:
- **No-IP** (darmowy): https://www.noip.com/
- **DuckDNS** (darmowy): https://www.duckdns.org/
- **Cloudflare** (darmowy + proxy): https://cloudflare.com

---

## 🐳 INSTALACJA NA SERWERZE

### Ubuntu/Debian (ZALECANE)

#### Krok 1: Aktualizuj system
```bash
sudo apt update && sudo apt upgrade -y
```

#### Krok 2: Zainstaluj Docker
```bash
# Oficjalny skrypt Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Docker Compose
sudo apt install -y docker-compose-plugin

# Narzędzia
sudo apt install -y git curl wget nano

# Wyloguj się i zaloguj ponownie
exit
```

#### Krok 3: Konfiguruj Firewall
```bash
# UFW (jeśli używasz)
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable

# LUB iptables
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables-save | sudo tee /etc/iptables/rules.v4
```

---

## 📦 DEPLOYMENT PROJEKTU

### Metoda A: Sklonuj z GitHub (ZALECANA)

```bash
# Utwórz katalog
mkdir -p ~/nba-analytics
cd ~/nba-analytics

# Sklonuj repozytorium
git clone https://github.com/Nawigante81/MarekNBAnalitics--chuj-wi.git .

# Sprawdź pliki
ls -la
```

### Metoda B: Upload z lokalnego komputera

**Windows (PowerShell):**
```powershell
# Z katalogu projektu
cd "E:\VSCODE PROJEKT\MarekNBAnalitics-main"

# Upload przez SCP
scp -r * user@<IP_SERWERA>:~/nba-analytics/
```

**Lub użyj WinSCP/FileZilla:**
- Host: IP Twojego serwera
- Port: 22
- Upload wszystkie pliki

---

## ⚙️ KONFIGURACJA

### Plik .env.production jest już gotowy!

```bash
cd ~/nba-analytics

# Sprawdź konfigurację
cat .env.production
```

Powinien zawierać:
```bash
DOMAIN=mareknba.pl
VITE_API_BASE_URL=
# ... reszta konfiguracji
```

**Jeśli trzeba coś zmienić:**
```bash
nano .env.production
```

---

## 🚀 URUCHOMIENIE

### Krok 1: Build i start
```bash
cd ~/nba-analytics

# Uruchom w trybie produkcyjnym
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

### Krok 2: Sprawdź status
```bash
# Status kontenerów
docker compose -f docker-compose.prod.yml ps

# Logi (Ctrl+C aby wyjść)
docker compose -f docker-compose.prod.yml logs -f
```

### Krok 3: Testuj

**Lokalnie na serwerze:**
```bash
curl http://localhost/health
curl http://localhost/api/health
```

**Z przeglądarki (po propagacji DNS):**
```
https://mareknba.pl
https://mareknba.pl/health
https://mareknba.pl/api/health
```

**Caddy automatycznie pobierze certyfikat SSL od Let's Encrypt!** ✅

---

## 🔄 AUTOSTART (opcjonalnie)

Aby aplikacja uruchamiała się automatycznie po restarcie serwera:

### Metoda 1: Docker restart policy (już skonfigurowane)

W `docker-compose.prod.yml` mamy:
```yaml
restart: unless-stopped
```

Docker automatycznie uruchomi kontenery przy starcie systemu!

### Metoda 2: Systemd service (backup)

Jeśli chcesz dodatkową kontrolę:

```bash
sudo nano /etc/systemd/system/nba-analytics.service
```

Wklej:
```ini
[Unit]
Description=NBA Analytics Docker Compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/YOUR_USER/nba-analytics
ExecStart=/usr/bin/docker compose -f docker-compose.prod.yml --env-file .env.production up -d
ExecStop=/usr/bin/docker compose -f docker-compose.prod.yml down
User=YOUR_USER

[Install]
WantedBy=multi-user.target
```

**Zamień `YOUR_USER` na swojego użytkownika!**

Aktywuj:
```bash
sudo systemctl daemon-reload
sudo systemctl enable nba-analytics.service
sudo systemctl start nba-analytics.service

# Status
sudo systemctl status nba-analytics.service
```

---

## 📊 MONITOROWANIE

### Podstawowe komendy:

```bash
cd ~/nba-analytics

# Status
docker compose -f docker-compose.prod.yml ps

# Logi (wszystkie)
docker compose -f docker-compose.prod.yml logs -f

# Logi (konkretny kontener)
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend
docker compose -f docker-compose.prod.yml logs -f caddy

# Restart
docker compose -f docker-compose.prod.yml restart

# Restart konkretnego kontenera
docker compose -f docker-compose.prod.yml restart backend

# Stop
docker compose -f docker-compose.prod.yml down

# Zasoby (CPU/RAM)
docker stats
```

### Health Checks:

```bash
# Backend
curl http://localhost:8000/health

# Frontend przez Caddy
curl http://localhost/health

# Redis
docker exec nba-redis redis-cli ping
```

---

## 🔄 AKTUALIZACJA

### Pull z GitHub i restart:

```bash
cd ~/nba-analytics

# Backup konfiguracji
cp .env.production .env.production.backup

# Pobierz zmiany
git pull

# Przywróć config (gdyby został nadpisany)
cp .env.production.backup .env.production

# Restart z rebuildem
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

### Lub użyj skryptu deploy-ovh.sh:

```bash
chmod +x deploy-ovh.sh
./deploy-ovh.sh
# Wybierz opcję 3: Update from Git
```

---

## 🛡️ BEZPIECZEŃSTWO

### 1. Firewall
```bash
# Sprawdź status
sudo ufw status

# Powinny być otwarte tylko porty: 22, 80, 443
```

### 2. Regularne aktualizacje
```bash
# Co tydzień/miesiąc
sudo apt update && sudo apt upgrade -y
docker system prune -f
```

### 3. Backup
```bash
# Backup konfiguracji
tar -czf backup-$(date +%Y%m%d).tar.gz .env.production docker-compose.prod.yml

# Backup logów
tar -czf logs-backup-$(date +%Y%m%d).tar.gz backend/logs/
```

### 4. Monitoring logów
```bash
# Sprawdzaj co jakiś czas
tail -f backend/logs/app.log
docker compose -f docker-compose.prod.yml logs --tail=100 backend
```

---

## 🔧 TROUBLESHOOTING

### Problem: SSL nie działa po kilku minutach

```bash
# Sprawdź logi Caddy
docker compose -f docker-compose.prod.yml logs caddy

# Sprawdź czy DNS wskazuje na Twój serwer
nslookup mareknba.pl

# Sprawdź czy porty 80/443 są dostępne z internetu
# (z innego komputera lub: https://www.yougetsignal.com/tools/open-ports/)

# Jeśli za routerem, sprawdź port forwarding!
```

### Problem: "Connection refused" z zewnątrz

```bash
# Sprawdź czy kontenery działają
docker compose -f docker-compose.prod.yml ps

# Sprawdź czy Caddy nasłuchuje
sudo netstat -tulpn | grep :80
sudo netstat -tulpn | grep :443

# Sprawdź router - czy port forwarding działa?
# Sprawdź firewall na serwerze
sudo ufw status
```

### Problem: Aplikacja wolno działa

```bash
# Sprawdź zasoby
docker stats
htop

# Sprawdź logi pod kątem błędów
docker compose -f docker-compose.prod.yml logs backend | grep -i error
```

### Problem: Backend nie odpowiada

```bash
# Restart backend
docker compose -f docker-compose.prod.yml restart backend

# Sprawdź logi
docker compose -f docker-compose.prod.yml logs backend

# Wejdź do kontenera
docker exec -it nba-backend bash
curl http://localhost:8000/health
```

---

## 📱 DOSTĘP ZDALNY

Po skonfigurowaniu możesz uzyskać dostęp do aplikacji:

### Z komputera:
- https://mareknba.pl

### Z telefonu:
- https://mareknba.pl

### Z pracy/kawiarni:
- https://mareknba.pl

**Działa wszędzie, gdzie masz internet!** 🌍

---

## ⚡ DYNAMICZNE IP? UŻYJ CLOUDFLARE

Jeśli Twoje IP zmienia się, najlepsze rozwiązanie:

### 1. Przenieś DNS do Cloudflare (DARMOWE)

1. Załóż konto: https://cloudflare.com
2. Dodaj domenę mareknba.pl
3. Cloudflare poda Ci nameservery
4. Zmień nameservery u rejestratora domeny
5. W Cloudflare dodaj rekord A: `@` → Twoje IP
6. Włącz pomarańczową chmurkę (proxy)

**Korzyści:**
- ✅ DDoS protection
- ✅ CDN (szybszy dostęp)
- ✅ Nie musisz aktualizować IP ręcznie
- ✅ SSL nawet jeśli certyfikat nie działa

### 2. Lub użyj DynamicDNS

**DuckDNS (najprostszy):**
```bash
# Zainstaluj
mkdir -p ~/duckdns
cd ~/duckdns
nano duck.sh
```

Wklej (zamień TOKEN i SUBDOMAIN):
```bash
#!/bin/bash
echo url="https://www.duckdns.org/update?domains=mareknba&token=YOUR_TOKEN&ip=" | curl -k -o ~/duckdns/duck.log -K -
```

Uruchom co 5 minut:
```bash
chmod +x duck.sh
crontab -e
# Dodaj:
*/5 * * * * ~/duckdns/duck.sh >/dev/null 2>&1
```

---

## 💰 KOSZTY

| Co | Koszt |
|----|-------|
| Domena mareknba.pl | Już masz! ✅ |
| Własny serwer | 0 PLN/mies (energia: ~10-50 PLN) |
| Supabase | Darmowe ✅ |
| SSL (Let's Encrypt) | Darmowe ✅ |
| Odds API | Darmowe (limit) ✅ |
| **RAZEM** | **~10-50 PLN/mies (prąd)** |

**Oszczędność vs VPS:** ~40 PLN/mies = 480 PLN/rok!

---

## ✅ CHECKLIST

- [ ] Serwer gotowy i dostępny
- [ ] Docker zainstalowany
- [ ] Docker Compose zainstalowany
- [ ] Firewall skonfigurowany
- [ ] Port forwarding w routerze (jeśli potrzebne)
- [ ] DNS skonfigurowany (mareknba.pl → IP serwera)
- [ ] Projekt sklonowany na serwer
- [ ] `.env.production` skonfigurowany
- [ ] `docker compose up -d` wykonany
- [ ] Aplikacja działa lokalnie (http://localhost)
- [ ] DNS propagacja zakończona (5-60 min)
- [ ] HTTPS działa (https://mareknba.pl)
- [ ] Autostart skonfigurowany

---

## 🎉 GOTOWE!

Twoja aplikacja NBA Analytics działa na:
- **https://mareknba.pl** - Frontend
- **https://mareknba.pl/api/** - Backend API

**Raporty automatyczne (czas Chicago):**
- 7:50 AM - Analiza wczorajsza
- 8:00 AM - Podsumowanie
- 11:00 AM - Dzisiejsze mecze

---

## 🆘 POTRZEBUJESZ POMOCY?

Napisz:
- System operacyjny serwera
- Typ połączenia (stałe IP / za routerem / dynamic IP)
- Co już zainstalowałeś
- Treść błędu (logi)

---

*Ostatnia aktualizacja: 19 stycznia 2026*
*Domena: mareknba.pl*
