# 🚀 Kompletna Instrukcja Uruchomienia Projektu NBA Analytics

## Wymagania wstępne

### ✅ Co musisz mieć zainstalowane:
1. **Python 3.8+** - [Pobierz tutaj](https://www.python.org/downloads/)
2. **Node.js 18+** - [Pobierz tutaj](https://nodejs.org/)
3. **Git** (opcjonalnie) - [Pobierz tutaj](https://git-scm.com/)

### Sprawdź wersje (PowerShell):
```powershell
python --version   # Powinno pokazać Python 3.8 lub wyżej
node --version     # Powinno pokazać v18 lub wyżej
npm --version      # Powinno pokazać 9 lub wyżej
```

---

## Krok 1: Przygotowanie bazy danych (Supabase)

### 1.1 Utwórz konto Supabase (DARMOWE)
1. Idź do: https://supabase.com
2. Kliknij **"Start your project"**
3. Zaloguj się przez GitHub (lub email)
4. Kliknij **"New Project"**
5. Wypełnij:
   - **Name**: `NBA-Analytics`
   - **Database Password**: Zapisz gdzieś (będzie potrzebne)
   - **Region**: Wybierz najbliższy (np. Europe West)
6. Kliknij **"Create new project"** (czekaj 2-3 minuty)

### 1.2 Skopiuj klucze API
1. W Supabase Dashboard, kliknij **Settings** (ikona koła zębatego) → **API**
2. Skopiuj:
   - **Project URL** (np. `https://xxxxx.supabase.co`)
   - **anon public** key (długi string zaczynający się od `eyJ...`)
   - **service_role** key (w sekcji "Service role")

### 1.3 Utwórz strukturę bazy danych
1. W Supabase Dashboard, kliknij **SQL Editor** w lewym menu
2. Kliknij **"New Query"**
3. **Otwórz plik** w projekcie: `supabase_setup_complete_all_tables.sql`
4. **Skopiuj całą zawartość** (Ctrl+A, Ctrl+C)
5. **Wklej do SQL Editor** w Supabase (Ctrl+V)
6. Kliknij **"Run"** (lub Ctrl+Enter)
7. ✅ Poczekaj ~10 sekund - zobaczysz wynik z 4 tabelami

**Weryfikacja:**
- Kliknij **Table Editor** → Powinieneś widzieć 4 tabele:
  - ✅ `teams` (30 wierszy)
  - ✅ `games` (pusta)
  - ✅ `odds` (pusta)
  - ✅ `player_game_stats` (pusta)

---

## Krok 2: Konfiguracja projektu

### 2.1 Sprawdź plik .env
Otwarty plik `.env` w głównym folderze projektu powinien zawierać:

```env
# Supabase Configuration
VITE_SUPABASE_URL=https://twoj-projekt.supabase.co
VITE_SUPABASE_ANON_KEY=twoj-anon-key-tutaj
SUPABASE_SERVICE_KEY=twoj-service-key-tutaj

# The Odds API (opcjonalnie - dla live odds)
ODDS_API_KEY=twoj-odds-api-key

# Opcje (można zostawić domyślne)
AUTO_SCRAPE_ON_START=false
ENABLE_SCHEDULER=false
```

**Uwaga:** Zamień `twoj-projekt`, `twoj-anon-key`, `twoj-service-key` na wartości z Supabase!

### 2.2 Sprawdź plik backend/.env
Skopiuj ten sam plik do folderu `backend/`:

```powershell
Copy-Item .env backend/.env
```

---

## Krok 3: Instalacja zależności

### 3.1 Zainstaluj zależności Python (Backend)
```powershell
cd backend
pip install -r requirements.txt
```

**To może potrwać 2-3 minuty.** Zobaczyz instalację pakietów jak:
- fastapi
- uvicorn
- supabase
- pandas
- numpy
- beautifulsoup4

**Jeśli wystąpią błędy:**
```powershell
# Spróbuj z pip3
pip3 install -r requirements.txt

# Lub zaktualizuj pip
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3.2 Wróć do głównego folderu
```powershell
cd ..
```

### 3.3 Zainstaluj zależności Node.js (Frontend)
```powershell
npm install
```

**To może potrwać 3-5 minut.** Instaluje ~300MB zależności.

**Jeśli wystąpią błędy:**
```powershell
# Wyczyść cache i spróbuj ponownie
rm -r node_modules
rm package-lock.json
npm install
```

---

## Krok 4: Import danych historycznych (424k wierszy)

### 4.1 Sprawdź czy pliki CSV są na miejscu
```powershell
ls "nba historia"
```

Powinieneś zobaczyć:
- ✅ `regular_season_box_scores_2010_2024_part_1.csv`
- ✅ `regular_season_box_scores_2010_2024_part_2.csv`
- ✅ `regular_season_box_scores_2010_2024_part_3.csv`

### 4.2 Uruchom import
```powershell
cd backend
python import_historical_data.py
```

**Co się stanie:**
1. Script połączy się z Supabase
2. Sprawdzi czy tabela `player_game_stats` istnieje
3. Zacznie importować dane w batches po 1000 wierszy
4. Zobaczysz progress:
   ```
   📂 Wczytywanie pliku: nba historia/regular_season_box_scores_2010_2024_part_1.csv
      Znaleziono 141,493 wierszy
      ✅ Batch 1/142: 1000 wierszy zaimportowano
      ✅ Batch 2/142: 1000 wierszy zaimportowano
      ...
   ```

**Czas trwania: ~5-10 minut** (zależy od internetu)

**Jeśli wystąpi błąd "Table does not exist":**
- Wróć do Kroku 1.3 i upewnij się, że uruchomiłeś SQL w Supabase

**Jeśli wystąpi błąd "Permission denied":**
- Sprawdź czy w `.env` masz `SUPABASE_SERVICE_KEY` (nie tylko ANON_KEY)

### 4.3 Weryfikacja importu
Po zakończeniu, w Supabase Dashboard:
1. Kliknij **Table Editor** → `player_game_stats`
2. Powinieneś zobaczyć **424,478 wierszy**

Lub sprawdź w SQL Editor:
```sql
SELECT COUNT(*) FROM player_game_stats;
-- Wynik: 424478
```

### 4.4 Wróć do głównego folderu
```powershell
cd ..
```

---

## Krok 5: Uruchomienie projektu

### Opcja A: Uruchomienie ręczne (2 terminale)

#### Terminal 1 - Backend (FastAPI)
```powershell
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Powinieneś zobaczyć:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
[OK] Starting application with Supabase (Service Role)
INFO:     Application startup complete.
```

**Backend działa na: http://localhost:8000**

**Testuj API:**
- Otwórz w przeglądarce: http://localhost:8000/docs
- Zobaczysz Swagger UI z dokumentacją API

#### Terminal 2 - Frontend (React)
**Otwórz NOWY terminal PowerShell** (zostaw backend działający!)

```powershell
npm run dev
```

**Powinieneś zobaczyć:**
```
  VITE v5.4.2  ready in 1234 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

**Frontend działa na: http://localhost:5173**

**Otwórz w przeglądarce:** http://localhost:5173

---

### Opcja B: Uruchomienie przez skrypty (Windows)

#### Krok 1: Uruchom backend
Otwórz PowerShell w folderze projektu:
```powershell
cd backend
python -m uvicorn main:app --reload
```

#### Krok 2: Uruchom frontend (nowy terminal)
```powershell
npm run dev
```

---

## Krok 6: Testowanie funkcji analitycznych

### 6.1 Testuj Prop Bet Analyzer

**W przeglądarce, idź do:**
```
http://localhost:8000/api/analytics/prop-bet?player_name=LeBron James&stat_type=points&line=25.5&games=20
```

**Powinieneś zobaczyć JSON z:**
```json
{
  "player": "LeBron James",
  "stat_type": "points",
  "line": 25.5,
  "prediction": 27.3,
  "hit_rate": 65.0,
  "value": "OVER",
  "confidence": 65.0,
  "recommendation": "LEAN OVER. Avg 27.3 vs 25.5. 65.0% hit rate."
}
```

### 6.2 Testuj Form Tracker

```
http://localhost:8000/api/analytics/form?player_name=Stephen Curry&games=15
```

### 6.3 Testuj Matchup Analyzer

```
http://localhost:8000/api/analytics/matchup/player?player_name=Kevin Durant&opponent=LAL
```

### 6.4 Testuj Injury Impact

```
http://localhost:8000/api/analytics/injury-impact?team=GSW&missing_player=Stephen Curry
```

---

## Krok 7: Używanie komponentów React

### 7.1 Otwórz src/App.tsx

Dodaj importy na górze:
```tsx
import { PropBetAnalyzer } from './components/PropBetAnalyzer';
import { FormTracker } from './components/FormTracker';
```

### 7.2 Dodaj komponenty do render

Gdzieś w return:
```tsx
<div className="container mx-auto px-4 py-8 space-y-8">
  <h1 className="text-4xl font-bold text-center mb-8">
    🏀 NBA Analytics & Betting System
  </h1>
  
  <PropBetAnalyzer />
  <FormTracker />
  
  {/* Twoje inne komponenty */}
</div>
```

### 7.3 Zapisz i sprawdź

Frontend powinien się automatycznie odświeżyć (hot reload).
Zobaczysz nowe sekcje:
- 🎯 Prop Bet Analyzer
- 📈 Player Form Tracker

---

## 🎯 Kompletny checklist uruchomienia

### Przed pierwszym uruchomieniem:
- [ ] Python 3.8+ zainstalowany
- [ ] Node.js 18+ zainstalowany
- [ ] Konto Supabase utworzone
- [ ] Projekt Supabase utworzony
- [ ] SQL setup uruchomiony (`supabase_setup_complete_all_tables.sql`)
- [ ] Klucze API w `.env` i `backend/.env`
- [ ] `pip install -r requirements.txt` wykonane
- [ ] `npm install` wykonane
- [ ] Dane historyczne zaimportowane (`python import_historical_data.py`)

### Przy każdym uruchomieniu:
1. [ ] Terminal 1: `cd backend` → `uvicorn main:app --reload`
2. [ ] Terminal 2: `npm run dev`
3. [ ] Otwórz http://localhost:5173
4. [ ] Backend API: http://localhost:8000/docs

---

## 🐛 Troubleshooting - Najczęstsze problemy

### Problem 1: "Python nie jest rozpoznawany"
**Rozwiązanie:**
1. Zainstaluj Python z https://www.python.org/downloads/
2. Podczas instalacji **ZAZNACZ "Add Python to PATH"**
3. Restart PowerShell

### Problem 2: "uvicorn: command not found"
**Rozwiązanie:**
```powershell
pip install uvicorn
# Lub
python -m uvicorn main:app --reload
```

### Problem 3: "npm: command not found"
**Rozwiązanie:**
1. Zainstaluj Node.js z https://nodejs.org/
2. Restart PowerShell

### Problem 4: "Port 8000 is already in use"
**Rozwiązanie:**
```powershell
# Znajdź proces
netstat -ano | findstr :8000

# Zabij proces (zmień PID na właściwy)
taskkill /PID 12345 /F

# Lub użyj innego portu
uvicorn main:app --reload --port 8001
```

### Problem 5: "Cannot connect to database"
**Rozwiązanie:**
1. Sprawdź czy klucze w `.env` są poprawne
2. Sprawdź czy używasz `SUPABASE_SERVICE_KEY` (nie tylko ANON_KEY)
3. Sprawdź połączenie internetowe
4. Sprawdź czy projekt Supabase nie jest wstrzymany (free tier)

### Problem 6: "Table player_game_stats does not exist"
**Rozwiązanie:**
1. Wróć do Supabase Dashboard → SQL Editor
2. Uruchom ponownie `supabase_setup_complete_all_tables.sql`

### Problem 7: "Import failed: Rate limit exceeded"
**Rozwiązanie:**
1. Zmień `batch_size` w `import_historical_data.py` z 1000 na 500
2. Zwiększ `time.sleep(0.1)` na `time.sleep(0.3)`

### Problem 8: "Module 'analytics' not found"
**Rozwiązanie:**
```powershell
cd backend
# Sprawdź czy plik istnieje
ls analytics.py

# Jeśli nie ma, coś poszło nie tak - plik powinien być w backend/
```

### Problem 9: "Recharts module not found"
**Rozwiązanie:**
```powershell
npm install recharts
```

### Problem 10: Frontend nie łączy się z backendem
**Rozwiązanie:**
1. Sprawdź czy backend działa: http://localhost:8000/docs
2. W komponencie zmień URL na: `http://localhost:8000` (bez końcowego `/`)
3. Sprawdź CORS - backend powinien mieć w `main.py`:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],
       ...
   )
   ```

---

## 📚 Przydatne komendy

### Backend (w folderze backend/)
```powershell
# Uruchom serwer
uvicorn main:app --reload

# Uruchom z debugiem
uvicorn main:app --reload --log-level debug

# Testuj endpoint
curl http://localhost:8000/health

# Zobacz logi
# (logi są w terminalu gdzie uruchomiłeś uvicorn)
```

### Frontend (w głównym folderze)
```powershell
# Uruchom dev server
npm run dev

# Build do produkcji
npm run build

# Preview produkcji
npm run preview

# Uruchom testy
npm test

# Check TypeScript
npm run typecheck
```

### Baza danych (Supabase SQL Editor)
```sql
-- Sprawdź liczbę wierszy
SELECT COUNT(*) FROM player_game_stats;

-- Sprawdź zakres dat
SELECT MIN(game_date), MAX(game_date) FROM player_game_stats;

-- Top 10 scorers
SELECT player_name, COUNT(*) as games, AVG(points) as ppg
FROM player_game_stats
GROUP BY player_name
HAVING COUNT(*) > 50
ORDER BY ppg DESC
LIMIT 10;

-- Sprawdź statystyki gracza
SELECT * FROM player_game_stats
WHERE player_name = 'LeBron James'
ORDER BY game_date DESC
LIMIT 10;
```

---

## 🎓 Następne kroki

Po uruchomieniu projektu:

1. **Przeczytaj dokumentację:**
   - `ANALYTICS_FEATURES.md` - Opis wszystkich funkcji analitycznych
   - `HISTORICAL_DATA_IMPORT.md` - Więcej o danych historycznych
   - http://localhost:8000/docs - API dokumentacja

2. **Testuj funkcje:**
   - Spróbuj różnych graczy w Prop Bet Analyzer
   - Zobacz trendy w Form Tracker
   - Sprawdź matchupy przed prawdziwymi meczami

3. **Customizuj:**
   - Dodaj własne komponenty React
   - Modyfikuj kolory w Tailwind
   - Dodaj nowe endpointy API

4. **Rozwijaj:**
   - Dodaj więcej funkcji z listy w `ANALYTICS_FEATURES.md`
   - Integruj z The Odds API (live odds)
   - Dodaj email notifications

---

## 📞 Potrzebujesz pomocy?

**Zasoby:**
- 📄 Dokumentacja projektu: `README.md`
- 🎯 Funkcje analityczne: `ANALYTICS_FEATURES.md`
- 📊 Dane historyczne: `HISTORICAL_DATA_IMPORT.md`
- 🔧 Supabase setup: `SUPABASE_SETUP.md`

**API Dokumentacja:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## ✅ Gotowe!

Jeśli wszystko działa, powinieneś mieć:
- ✅ Backend API na http://localhost:8000
- ✅ Frontend React na http://localhost:5173
- ✅ 424,478 wierszy danych historycznych w bazie
- ✅ 4 funkcje analityczne działające
- ✅ Interaktywne komponenty React

**Miłego korzystania z NBA Analytics! 🏀📊**
