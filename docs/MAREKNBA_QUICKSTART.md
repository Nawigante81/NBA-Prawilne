# 🚀 NBA Analytics - mareknba.pl Quick Start

## ⚡ Instalacja na serwerze Ubuntu (COPY-PASTE)

### 1. Zaloguj się do serwera
```bash
ssh twoj_user@IP_SERWERA
```

### 2. Uruchom instalację (jedna komenda!)
```bash
curl -fsSL https://raw.githubusercontent.com/Nawigante81/MarekNBAnalitics--chuj-wi/main/setup-ubuntu-mareknba.sh | bash
```

**LUB pobierz i uruchom lokalnie:**
```bash
wget https://raw.githubusercontent.com/Nawigante81/MarekNBAnalitics--chuj-wi/main/setup-ubuntu-mareknba.sh
chmod +x setup-ubuntu-mareknba.sh
./setup-ubuntu-mareknba.sh
```

### 3. Co zainstaluje skrypt?
- ✅ Docker & Docker Compose
- ✅ Git i narzędzia
- ✅ Firewall (UFW) - porty 80, 443
- ✅ Projekt NBA Analytics
- ✅ Optymalizacja systemu

### 4. Po instalacji - WAŻNE!
```bash
# WYLOGUJ SIĘ I ZALOGUJ PONOWNIE!
exit
ssh twoj_user@IP_SERWERA

# Przejdź do projektu
cd ~/nba-analytics

# Uruchom aplikację
./deploy-mareknba.sh
# Wybierz opcję 1
```

---

## 🌍 Konfiguracja DNS (przed lub po instalacji)

W panelu domeny **mareknba.pl** ustaw:

```
Typ   Nazwa    Wartość               TTL
A     @        <IP_TWOJEGO_SERWERA>  3600
A     www      <IP_TWOJEGO_SERWERA>  3600
```

**Sprawdź swoje IP:**
```bash
curl ifconfig.me
```

**Sprawdź propagację DNS:**
```bash
nslookup mareknba.pl
```

---

## 🔧 Port Forwarding (jeśli serwer za routerem)

Jeśli serwer jest w sieci domowej:

1. Wejdź do routera (np. `192.168.1.1`)
2. Znajdź **Port Forwarding** / **Virtual Server**
3. Dodaj reguły:
   - Port **80** → IP serwera w LAN → Port **80**
   - Port **443** → IP serwera w LAN → Port **443**
4. Zapisz i zrestartuj router

**Sprawdź czy porty są otwarte:**
https://www.yougetsignal.com/tools/open-ports/

---

## 📋 Przydatne komendy

```bash
# Status
cd ~/nba-analytics
docker compose -f docker-compose.prod.yml ps

# Logi
docker compose -f docker-compose.prod.yml logs -f

# Restart
docker compose -f docker-compose.prod.yml restart

# Stop
docker compose -f docker-compose.prod.yml down

# Health check
curl http://localhost/health
curl http://localhost/api/health

# Zasoby
docker stats
htop
```

---

## 🎯 Po uruchomieniu

Aplikacja dostępna na:
- 🌍 **https://mareknba.pl** (po propagacji DNS)
- 🏥 **https://mareknba.pl/health**
- 🔧 **https://mareknba.pl/api/health**

**Raporty automatyczne (Chicago time):**
- **7:50 AM** - Analiza wczorajsza
- **8:00 AM** - Podsumowanie poranne
- **11:00 AM** - Dzisiejsze mecze

---

## 🔥 Troubleshooting

### Docker permission denied
```bash
sudo usermod -aG docker $USER
exit
# Zaloguj ponownie
```

### SSL nie działa
```bash
# Sprawdź DNS
nslookup mareknba.pl

# Sprawdź logi Caddy
docker compose -f docker-compose.prod.yml logs caddy

# Sprawdź czy porty są otwarte (z innego komputera)
telnet TWOJE_IP 80
telnet TWOJE_IP 443
```

### Backend nie odpowiada
```bash
docker compose -f docker-compose.prod.yml logs backend
docker compose -f docker-compose.prod.yml restart backend
```

### Brak miejsca na dysku
```bash
df -h
docker system prune -a -f
```

---

## 📚 Pełna dokumentacja

- **[SELF_HOSTING_GUIDE.md](SELF_HOSTING_GUIDE.md)** - Kompletny przewodnik
- **[deploy-mareknba.sh](deploy-mareknba.sh)** - Skrypt deployment

---

## ✅ Checklist

- [ ] Serwer Ubuntu gotowy
- [ ] Zainstalowany Docker (automatycznie)
- [ ] Firewall skonfigurowany (automatycznie)
- [ ] DNS skonfigurowany (mareknba.pl → IP)
- [ ] Port forwarding (jeśli potrzebne)
- [ ] Projekt sklonowany (automatycznie)
- [ ] Aplikacja uruchomiona
- [ ] SSL działa (Caddy automatycznie)

---

**Potrzebujesz pomocy?** Zobacz [SELF_HOSTING_GUIDE.md](SELF_HOSTING_GUIDE.md)
