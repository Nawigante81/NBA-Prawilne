# 🏀 NBA Analytics - Native Ubuntu Deployment (NO DOCKER)

## ⚠️ Dla serwerów OpenVZ/Virtuozzo gdzie Docker nie działa

Jeśli widzisz błąd: `permission denied` przy `docker run` - Twój serwer nie wspiera pełnej konteneryzacji. Ten przewodnik pokazuje jak uruchomić aplikację **bezpośrednio na Ubuntu**.

---

## 🚀 QUICK START (3 komendy!)

### 1. Pobierz projekt (jeśli jeszcze nie masz)
```bash
cd ~
git clone https://github.com/Nawigante81/MarekNBAnalitics--chuj-wi.git nba-analytics
cd nba-analytics
```

### 2. Automatyczna instalacja wszystkiego
```bash
curl -fsSL https://raw.githubusercontent.com/Nawigante81/MarekNBAnalitics--chuj-wi/main/setup-native-ubuntu.sh | bash
```

**LUB lokalnie:**
```bash
chmod +x setup-native-ubuntu.sh
./setup-native-ubuntu.sh
```

### 3. Uruchom aplikację
```bash
chmod +x start-native.sh
./start-native.sh
```

**GOTOWE!** 🎉

---

## 📦 CO INSTALUJE SKRYPT?

- ✅ **Node.js 20** - Frontend
- ✅ **Python 3.11** - Backend
- ✅ **Redis** - Cache
- ✅ **Caddy** - Web server + SSL (automatyczny)
- ✅ **PM2** - Process manager (auto-restart)

---

## 🌍 Po instalacji

Aplikacja dostępna na:
- **http://localhost** - Lokalnie na serwerze
- **https://mareknba.pl** - Z internetu (po propagacji DNS)

**SSL automatyczny** - Caddy pobiera certyfikat od Let's Encrypt!

---

## 📊 Zarządzanie

### Status
```bash
pm2 status              # Status backendu
sudo systemctl status caddy  # Status Caddy
```

### Logi
```bash
pm2 logs nba-backend    # Logi backend
sudo journalctl -u caddy -f  # Logi Caddy
```

### Restart
```bash
pm2 restart nba-backend
sudo systemctl restart caddy
```

### Stop
```bash
./stop-native.sh
# LUB
pm2 stop nba-backend
sudo systemctl stop caddy
```

### Update z Git
```bash
cd ~/nba-analytics
git pull
npm run build           # Rebuild frontend
pm2 restart nba-backend # Restart backend
sudo systemctl restart caddy
```

---

## 🔧 Struktura

```
~/nba-analytics/
├── dist/                    # Frontend (zbudowany)
├── backend/
│   ├── venv/               # Python virtual environment
│   ├── main.py             # Backend FastAPI
│   ├── logs/               # Logi aplikacji
│   └── ecosystem.native.json  # PM2 config
├── Caddyfile.native        # Caddy config
├── .env.production         # Konfiguracja
├── setup-native-ubuntu.sh  # Instalacja
├── start-native.sh         # Start
└── stop-native.sh          # Stop
```

---

## ⚙️ Konfiguracja

Edytuj `.env.production`:
```bash
nano .env.production
```

Ważne zmienne:
```bash
DOMAIN=mareknba.pl
VITE_SUPABASE_URL=...
VITE_SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_KEY=...
VITE_ODDS_API_KEY=...
```

Po zmianach:
```bash
pm2 restart nba-backend
```

---

## 🔥 Firewall

Sprawdź czy porty są otwarte:
```bash
sudo ufw status

# Powinny być otwarte:
22/tcp   # SSH
80/tcp   # HTTP
443/tcp  # HTTPS
```

---

## 🆘 Troubleshooting

### Backend nie odpowiada
```bash
pm2 logs nba-backend
pm2 restart nba-backend
```

### Caddy nie działa
```bash
sudo journalctl -u caddy -n 50
sudo systemctl restart caddy
```

### SSL nie działa
```bash
# Sprawdź DNS
nslookup mareknba.pl

# Sprawdź logi Caddy
sudo journalctl -u caddy | grep -i certificate
```

### Redis problem
```bash
sudo systemctl status redis-server
sudo systemctl restart redis-server
```

### Port 8000 zajęty
```bash
# Sprawdź co używa portu
sudo netstat -tulpn | grep :8000

# Zabij proces
pm2 delete nba-backend
pm2 start backend/ecosystem.native.json
```

---

## 💾 Backup

```bash
# Backup konfiguracji
cp .env.production .env.production.backup

# Backup logów
tar -czf logs-backup-$(date +%Y%m%d).tar.gz backend/logs/
```

---

## 🔄 Autostart po restarcie serwera

**PM2** (już skonfigurowane):
```bash
pm2 startup  # Konfiguruje autostart
pm2 save     # Zapisuje aktualną konfigurację
```

**Caddy** (już włączone):
```bash
sudo systemctl enable caddy
```

Po restarcie serwera wszystko uruchomi się automatycznie!

---

## 📊 Monitoring zasobów

```bash
# CPU/RAM/Disk
htop

# PM2 monitoring
pm2 monit

# Disk space
df -h
```

---

## ✅ Checklist

- [ ] Zainstalowano wszystkie zależności (setup-native-ubuntu.sh)
- [ ] Frontend zbudowany (npm run build)
- [ ] Backend działa (pm2 status)
- [ ] Caddy działa (systemctl status caddy)
- [ ] Redis działa (systemctl status redis-server)
- [ ] DNS skonfigurowany (mareknba.pl → IP serwera)
- [ ] SSL działa (https://mareknba.pl)
- [ ] Autostart skonfigurowany (pm2 startup)

---

## 💰 Zalety vs Docker

| Feature | Docker | Native |
|---------|--------|--------|
| Działa na OpenVZ | ❌ NIE | ✅ TAK |
| Zużycie RAM | Wyższe | Niższe |
| Szybkość | Wolniejsze | Szybsze |
| Łatwość update | Łatwiejsze | Średnia |
| Izolacja | Lepsza | Słabsza |

---

## 🎯 Wymagania systemowe

- **OS**: Ubuntu 20.04+ / Debian 11+
- **RAM**: Min 2GB (zalecane 4GB)
- **CPU**: Min 1 core (zalecane 2+)
- **Disk**: Min 10GB wolnego miejsca
- **Network**: Otwarte porty 80, 443

---

**Dokumentacja pełna:** [SELF_HOSTING_GUIDE.md](SELF_HOSTING_GUIDE.md)

*Ostatnia aktualizacja: 19 stycznia 2026*
