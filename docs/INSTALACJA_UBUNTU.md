# 🏀 NBA Analytics - Instrukcja Instalacji Ubuntu 24.04

## 📋 Spis treści
- [Wymagania](#wymagania)
- [Architektura systemu](#architektura-systemu)
- [Instalacja krok po kroku](#instalacja-krok-po-kroku)
- [Konfiguracja](#konfiguracja)
- [Uruchomienie](#uruchomienie)
- [Zarządzanie aplikacją](#zarządzanie-aplikacją)
- [Rozwiązywanie problemów](#rozwiązywanie-problemów)

---

## 🔧 Wymagania

### System
- **OS:** Ubuntu 24.04 LTS (lub nowszy)
- **RAM:** Minimum 2GB (zalecane 4GB+)
- **Dysk:** 10GB wolnej przestrzeni
- **Sieć:** Połączenie internetowe

### Uprawnienia
- Dostęp **root** lub użytkownik z prawami **sudo**

---

## 🏗️ Architektura systemu

```
┌─────────────────────────────────────────────────────────┐
│                    NBA Analytics                         │
│                                                          │
│  Frontend (React + Vite)     Backend (FastAPI)          │
│  http://192.168.100.128:8080 http://192.168.100.128:8000│
│         ↓                            ↓                   │
│    serve (PM2)                  uvicorn (PM2)            │
│                                      ↓                   │
│                              Supabase Database           │
│                       https://vzuvsgfjutrwkbwpetwc       │
│                            .supabase.co                  │
└─────────────────────────────────────────────────────────┘
```

### Komponenty:
- **Frontend:** React 18 + Vite + TypeScript + Tailwind CSS
- **Backend:** Python 3.12 + FastAPI + uvicorn
- **Database:** Supabase PostgreSQL (zewnętrzna, cloud)
- **Cache:** Redis (opcjonalny, dla wydajności)
- **Process Manager:** PM2 (auto-restart, monitoring)
- **Web Server:** serve (statyczne pliki frontendu)

**Uwaga:** Aplikacja NIE używa Docker ani Caddy - jest to natywna instalacja Ubuntu.

---

## 📦 Instalacja krok po kroku

### KROK 1: Przygotowanie systemu

```bash
# Zaloguj się jako root lub użyj sudo
sudo su

# Zaktualizuj system
apt update && apt upgrade -y

# Zainstaluj Git (jeśli nie ma)
apt install -y git
```

---

### KROK 2: Pobierz projekt z GitHub

```bash
# Przejdź do katalogu domowego
cd ~

# Sklonuj projekt
git clone https://github.com/Nawigante81/MarekNBAnalitics--chuj-wi.git nba-analytics

# Wejdź do katalogu projektu
cd nba-analytics

# Sprawdź czy pliki są na miejscu
ls -la
```

**Oczekiwany output:** Powinieneś zobaczyć pliki: `package.json`, `setup-native-ubuntu.sh`, `start-simple.sh`, itp.

---

### KROK 3: Automatyczna instalacja wszystkich zależności

```bash
# Uruchom skrypt instalacyjny
bash setup-native-ubuntu.sh
```

**Instalacja zajmie 10-15 minut** i automatycznie zainstaluje:

#### Krok 1/6: Node.js 20
- Node.js 20.x (najnowsza LTS)
- npm (package manager)

#### Krok 2/6: Python 3.12
- Python 3.12.x
- python3-venv (virtual environments)
- python3-pip (package manager)
- python3-dev (headers dla kompilacji)

#### Krok 3/6: Redis (opcjonalnie)
- Redis 7.x (cache dla backendu)
- Automatyczny fallback jeśli systemd nie działa (OpenVZ)

#### Krok 4/6: PM2
- PM2 (process manager dla Node.js i Python)
- Automatyczne restartowanie procesów

#### Krok 5/6: Frontend
- Instalacja zależności npm
- Build produkcyjny Vite
- Utworzenie katalogu `dist/`

#### Krok 6/6: Backend
- Utworzenie Python virtual environment
- Instalacja wszystkich zależności Python
- Chromium + ChromeDriver (web scraping)
- Playwright + system dependencies
- Instalacja `serve` globalnie

---

### KROK 4: Weryfikacja instalacji

Po zakończeniu skryptu powinieneś zobaczyć:

```
╔════════════════════════════════════════════════════════════╗
║              ✅ KONFIGURACJA ZAKOŃCZONA!                   ║
╚════════════════════════════════════════════════════════════╝

📊 ZAINSTALOWANO:
   ├─ Node.js: v20.x.x
   ├─ Python: 3.12.x
   ├─ Redis: 7.x.x
   ├─ PM2: x.x.x
   ├─ Serve: installed
   └─ Frontend: /root/nba-analytics/dist
```

Sprawdź ręcznie:

```bash
# Wersje zainstalowanych narzędzi
node -v        # Powinno być v20.x.x
python3 -V     # Powinno być Python 3.12.x
pm2 -v         # Powinno być zainstalowane
redis-cli ping # Powinno zwrócić PONG (lub błąd - to OK)
```

---

## ⚙️ Konfiguracja

### Konfiguracja Supabase (Baza danych)

Aplikacja używa **Supabase** jako zewnętrznej bazy danych PostgreSQL.

**URL Supabase:** `https://vzuvsgfjutrwkbwpetwc.supabase.co`

Konfiguracja jest już zapisana w pliku `.env.production`:

```env
# Supabase - Baza danych (Cloud PostgreSQL)
VITE_SUPABASE_URL=https://vzuvsgfjutrwkbwpetwc.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Backend Supabase (pełne uprawnienia)
SUPABASE_URL=https://vzuvsgfjutrwkbwpetwc.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Struktura danych w Supabase:**
- Tabele: `games`, `teams`, `players`, `player_game_stats`, `odds`, `scraped_data`
- RLS (Row Level Security) skonfigurowane
- Automatyczne timestampy
- Indexes dla wydajności

**Nie musisz nic konfigurować** - wszystko jest gotowe!

---

### Konfiguracja adresu IP

Domyślnie aplikacja jest skonfigurowana na IP: **192.168.100.128**

Jeśli Twój serwer ma inny IP, edytuj `.env.production`:

```bash
nano .env.production
```

Zmień linię:
```env
DOMAIN=192.168.100.128
VITE_API_BASE_URL=http://192.168.100.128:8000
```

Na swój IP (np. `192.168.1.100`).

Następnie przebuduj frontend:
```bash
npm run build
```

---

## 🚀 Uruchomienie

### Uruchom aplikację

```bash
# Upewnij się że jesteś w katalogu projektu
cd ~/nba-analytics

# Nadaj uprawnienia wykonywania (jednorazowo)
chmod +x start-simple.sh stop-simple.sh

# Uruchom aplikację
bash start-simple.sh
```

**Output:**
```
╔════════════════════════════════════════════════════════════╗
║        🚀 Starting NBA Analytics (Simple Mode)           ║
╚════════════════════════════════════════════════════════════╝

🔄 Zatrzymywanie starych procesów
✅ Stare procesy zatrzymane

🚀 Uruchamianie Backend (FastAPI) na porcie 8000
✅ Backend uruchomiony przez PM2 (uvicorn + .env.production)

🌐 Uruchamianie Frontend na porcie 8080
✅ Frontend uruchomiony na porcie 8080

╔════════════════════════════════════════════════════════════╗
║              ✅ APLIKACJA URUCHOMIONA!                     ║
╚════════════════════════════════════════════════════════════╝
```

---

### Sprawdź status

```bash
# Status wszystkich procesów PM2
pm2 status
```

**Oczekiwany output:**
```
┌────┬────────────────┬─────────┬─────────┬──────────┬────────┬──────┬───────────┐
│ id │ name           │ mode    │ pid     │ uptime   │ ↺      │ cpu  │ mem       │
├────┼────────────────┼─────────┼─────────┼──────────┼────────┼──────┼───────────┤
│ 0  │ nba-backend    │ fork    │ 12345   │ 5m       │ 0      │ 2%   │ 150.0 MB  │
│ 1  │ nba-frontend   │ fork    │ 12346   │ 5m       │ 0      │ 0%   │ 50.0 MB   │
└────┴────────────────┴─────────┴─────────┴──────────┴────────┴──────┴───────────┘
```

Oba procesy powinny mieć status **online** i pid > 0.

---

### Uruchomienie ręczne backendu (diagnostyka)

Jeśli backend nie startuje, uruchom go ręcznie z poprawnym załadowaniem `.env.production`:

```bash
cd ~/nba-analytics
export $(grep -v '^#' .env.production | xargs)
cd backend
source venv/bin/activate
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info
```

Jeśli pojawi się błąd **Missing SUPABASE_URL** — oznacza to, że `.env.production` nie został załadowany.

---

### Testuj aplikację

```bash
# Test backendu (health check)
curl http://localhost:8000/health

# Powinno zwrócić:
{"status":"healthy","timestamp":"2026-01-19T..."}

# Test frontendu
curl http://localhost:8080

# Powinno zwrócić kod HTML
```

---

### Otwórz w przeglądarce

**Z serwera:**
- Frontend: http://localhost:8080
- Backend API: http://localhost:8000

**Z innych urządzeń w sieci lokalnej:**
- Frontend: http://192.168.100.128:8080
- Backend API: http://192.168.100.128:8000

Otwórz przeglądarkę i wejdź na adres **http://192.168.100.128:8080** 🎉

---

## 🔧 Zarządzanie aplikacją

### Podstawowe komendy

```bash
# Zatrzymaj aplikację
bash stop-simple.sh

# Uruchom ponownie
bash start-simple.sh

# Status procesów
pm2 status

# Logi wszystkich procesów
pm2 logs

# Logi tylko backendu
pm2 logs nba-backend

# Logi tylko frontendu
pm2 logs nba-frontend

# Restart wszystkiego
pm2 restart all

# Restart tylko backendu
pm2 restart nba-backend

# Zatrzymaj tylko jeden proces
pm2 stop nba-frontend
```

---

### Monitoring w czasie rzeczywistym

```bash
# Dashboard PM2 (CPU, RAM, logi)
pm2 monit

# Dashboard w przeglądarce (opcjonalnie)
pm2 web
```

---

### Automatyczne uruchamianie po restarcie

```bash
# Zapisz aktualną konfigurację PM2
pm2 save

# Włącz autostart po restarcie systemu
pm2 startup

# Skopiuj i uruchom komendę którą PM2 wyświetli
```

---

## 📂 Struktura katalogów

```
~/nba-analytics/
├── backend/
│   ├── venv/                 # Python virtual environment
│   ├── logs/                 # Logi backendu
│   ├── main.py              # Główny plik FastAPI
│   ├── requirements.txt     # Zależności Python
│   └── ecosystem.native.json # Konfiguracja PM2 dla backendu
├── dist/                    # Zbudowany frontend (produkcja)
├── src/                     # Kod źródłowy frontendu
├── .env.production          # Konfiguracja produkcyjna
├── package.json             # Zależności Node.js
├── setup-native-ubuntu.sh   # Skrypt instalacyjny
├── start-simple.sh          # Skrypt uruchamiający
└── stop-simple.sh           # Skrypt zatrzymujący
```

---

## 🔍 Rozwiązywanie problemów

### Backend nie startuje

**Sprawdź logi:**
```bash
pm2 logs nba-backend --lines 50
```

**Typowe problemy:**

1. **Brak modułów Python:**
```bash
cd ~/nba-analytics/backend
source venv/bin/activate
pip install -r requirements.txt
```

2. **Błąd połączenia z Supabase:**
- Sprawdź `.env.production` - czy SUPABASE_URL i klucze są poprawne
- Sprawdź połączenie: `curl https://vzuvsgfjutrwkbwpetwc.supabase.co`

3. **Błąd: Missing SUPABASE_URL lub SUPABASE_SERVICE_ROLE_KEY:**
- Upewnij się, że `.env.production` jest ładowany (PM2 używa `env_file`)
- Ręcznie: `export $(grep -v '^#' .env.production | xargs)`

4. **Port 8000 zajęty:**
```bash
sudo lsof -i :8000
# Zabij proces: kill -9 <PID>
```

---

### Frontend nie startuje

**Sprawdź logi:**
```bash
pm2 logs nba-frontend --lines 50
```

**Typowe problemy:**

1. **Brak katalogu dist/:**
```bash
cd ~/nba-analytics
npm run build
```

2. **Port 8080 zajęty:**
```bash
sudo lsof -i :8080
# Zabij proces: kill -9 <PID>
```

3. **Brak 'serve':**
```bash
npm install -g serve
```

---

### Redis nie działa

Redis jest **opcjonalny** - aplikacja będzie działać bez niego (trochę wolniej).

**Jeśli chcesz uruchomić Redis:**
```bash
sudo systemctl start redis-server
sudo systemctl enable redis-server
redis-cli ping  # Powinno zwrócić PONG
```

---

### Aktualizacja aplikacji

```bash
cd ~/nba-analytics

# Zatrzymaj aplikację
bash stop-simple.sh

# Pobierz nową wersję
git pull

# Zainstaluj nowe zależności (jeśli są)
npm install
cd backend
source venv/bin/activate
pip install -r requirements.txt
cd ..

# Przebuduj frontend
npm run build

# Uruchom ponownie
bash start-simple.sh
```

---

## 📊 Dostęp do danych

### Supabase Dashboard

Dostęp do bazy danych przez panel Supabase:

**URL:** https://supabase.com/dashboard/project/vzuvsgfjutrwkbwpetwc

Możesz tam:
- Przeglądać tabele
- Edytować dane
- Uruchamiać SQL queries
- Monitorować logi
- Zarządzać użytkownikami

---

### API Endpoints

Backend udostępnia REST API:

```bash
# Health check
GET http://192.168.100.128:8000/health

# Pobierz dzisiejsze mecze
GET http://192.168.100.128:8000/api/games/today

# Pobierz statystyki drużyny
GET http://192.168.100.128:8000/api/teams/{team_id}/stats

# Pobierz gracza
GET http://192.168.100.128:8000/api/players/{player_id}

# Pobierz kursy bukmacherskie
GET http://192.168.100.128:8000/api/odds/latest
```

Pełna dokumentacja API: http://192.168.100.128:8000/docs

---

## 🛡️ Bezpieczeństwo

### Firewall (opcjonalnie)

Jeśli aplikacja ma być dostępna tylko w sieci lokalnej:

```bash
# Zainstaluj UFW
apt install -y ufw

# Zezwól na SSH (ważne!)
ufw allow 22/tcp

# Zezwól na porty aplikacji tylko z lokalnej sieci
ufw allow from 192.168.100.0/24 to any port 8000
ufw allow from 192.168.100.0/24 to any port 8080

# Włącz firewall
ufw enable

# Sprawdź status
ufw status
```

---

### Zmiana kluczy Supabase (zaawansowane)

Jeśli chcesz użyć własnej bazy Supabase:

1. Utwórz nowy projekt na https://supabase.com
2. Skopiuj URL i klucze API
3. Edytuj `.env.production`:
```bash
nano .env.production
```
4. Zmień wartości:
```env
VITE_SUPABASE_URL=https://twoj-projekt.supabase.co
VITE_SUPABASE_ANON_KEY=twoj_anon_key
SUPABASE_URL=https://twoj-projekt.supabase.co
SUPABASE_SERVICE_ROLE_KEY=twoj_service_role_key
```
5. Przebuduj i uruchom:
```bash
npm run build
bash start-simple.sh
```

---

## 📞 Wsparcie

**Problem z instalacją?**
- Sprawdź logi: `pm2 logs`
- Sprawdź status: `pm2 status`
- Zrestartuj: `bash stop-simple.sh && bash start-simple.sh`

**GitHub Issues:** https://github.com/Nawigante81/MarekNBAnalitics--chuj-wi/issues

---

## 📝 Podsumowanie

✅ **Instalacja:** `bash setup-native-ubuntu.sh`  
✅ **Uruchomienie:** `bash start-simple.sh`  
✅ **Dostęp:** http://192.168.100.128:8080  
✅ **Baza danych:** Supabase (automatyczna konfiguracja)  
✅ **Monitoring:** `pm2 status` i `pm2 logs`  

**Aplikacja działa bez Docker i bez Caddy - prosta, natywna instalacja Ubuntu!** 🚀

---

*Ostatnia aktualizacja: 19 stycznia 2026*
