# 🚀 Szybki start - OVH Hosting

Ten plik zawiera **tylko najważniejsze komendy** do wdrożenia projektu na OVH VPS.

Pełna dokumentacja: [OVH_DEPLOYMENT_GUIDE.md](OVH_DEPLOYMENT_GUIDE.md)

---

## ⚡ QUICK START (copy-paste)

### 1. Pierwsze logowanie do VPS

```bash
# Zaloguj się (zmień IP na swoje)
ssh ubuntu@51.68.45.xxx

# Zmień hasło
passwd
```

### 2. Instalacja Docker

```bash
# Skopiuj i wklej całość:
curl -fsSL https://get.docker.com -o get-docker.sh && \
sudo sh get-docker.sh && \
sudo usermod -aG docker $USER && \
sudo apt install -y docker-compose-plugin git ufw && \
sudo ufw allow 22/tcp && \
sudo ufw allow 80/tcp && \
sudo ufw allow 443/tcp && \
sudo ufw --force enable && \
echo "✅ Docker zainstalowany!"

# WYLOGUJ SIĘ i ZALOGUJ PONOWNIE!
exit
ssh ubuntu@51.68.45.xxx
```

### 3. Pobierz projekt

```bash
# Utwórz katalog i sklonuj repo
mkdir -p ~/nba-analytics
cd ~/nba-analytics
git clone https://github.com/Nawigante81/MarekNBAnalitics--chuj-wi.git .
```

### 4. Konfiguracja

```bash
# Skopiuj i edytuj config
cp .env .env.production
nano .env.production
```

**ZMIEŃ W PLIKU:**
```bash
DOMAIN=twoja-domena.com    # <-- TWOJA DOMENA!
```

**Zapisz:** `Ctrl+X`, `Y`, `Enter`

### 5. Uruchom!

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

### 6. Sprawdź

```bash
# Status
docker compose -f docker-compose.prod.yml ps

# Logi
docker compose -f docker-compose.prod.yml logs -f
```

---

## 🌍 Konfiguracja domeny

### W panelu domeny (OVH/Cloudflare/inny):

```
Typ   Nazwa    Wartość              TTL
A     @        51.68.45.xxx        3600
A     www      51.68.45.xxx        3600
```

**Zamień `51.68.45.xxx` na IP swojego VPS!**

### Sprawdź propagację DNS (na swoim komputerze):

```bash
nslookup twoja-domena.com
```

Po 5-60 minutach Caddy **automatycznie pobierze SSL**! ✅

---

## 📝 Przydatne komendy

```bash
# Status
docker compose -f docker-compose.prod.yml ps

# Logi (wszystkie)
docker compose -f docker-compose.prod.yml logs -f

# Logi (tylko backend)
docker compose -f docker-compose.prod.yml logs -f backend

# Restart
docker compose -f docker-compose.prod.yml restart

# Stop
docker compose -f docker-compose.prod.yml down

# Update z Git
git pull
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build

# Sprawdź zasoby
docker stats
```

---

## 🆘 Problemy?

### Docker permission denied
```bash
sudo usermod -aG docker $USER
exit
# Zaloguj się ponownie
```

### Port 80 zajęty
```bash
# Zatrzymaj Apache/Nginx
sudo systemctl stop apache2
sudo systemctl disable apache2
```

### Backend nie odpowiada
```bash
# Sprawdź logi
docker compose -f docker-compose.prod.yml logs backend

# Wejdź do kontenera
docker exec -it nba-backend bash
```

### SSL nie działa
```bash
# Sprawdź logi Caddy
docker compose -f docker-compose.prod.yml logs caddy

# Sprawdź DNS
nslookup twoja-domena.com

# DNS musi wskazywać na IP VPS!
```

---

## ✅ Checklist

- [ ] VPS zamówiony i dostępny
- [ ] Zalogowano przez SSH
- [ ] Docker zainstalowany
- [ ] Firewall skonfigurowany (UFW)
- [ ] Projekt sklonowany
- [ ] `.env.production` skonfigurowany z domeną
- [ ] Domena kupiona
- [ ] DNS skonfigurowany (rekordy A)
- [ ] `docker compose up -d` wykonany
- [ ] Aplikacja działa na http://IP
- [ ] SSL działa (po 5-60 min)

---

## 💰 Koszty (szacunkowe)

| Co | Koszt |
|----|-------|
| OVH VPS Starter | ~40 PLN/mies |
| Domena (.com) | ~60 PLN/rok |
| **RAZEM** | **~540 PLN/rok** |

**Darmowe:**
- Supabase ✅
- SSL (Let's Encrypt) ✅
- Odds API ✅

---

## 🎯 Po wdrożeniu

Aplikacja będzie dostępna na:
- `https://twoja-domena.com` - Frontend
- `https://twoja-domena.com/api/` - Backend API

**Raporty automatyczne:**
- 7:50 AM - Analiza wczorajsza
- 8:00 AM - Podsumowanie
- 11:00 AM - Dzisiejsze mecze

---

**Potrzebujesz pomocy?** Zobacz pełną dokumentację: [OVH_DEPLOYMENT_GUIDE.md](OVH_DEPLOYMENT_GUIDE.md)
