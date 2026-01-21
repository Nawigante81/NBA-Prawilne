# Instrukcja aplikacji NBA Analytics

Poniższa instrukcja opisuje wszystkie zakładki i funkcje w aplikacji, sposób działania oraz źródła danych. Dokument jest oparty o aktualny kod frontendu i backendu.

## 1) Jak działa całość (w skrócie)
- Frontend: React + Vite (`src/`).
- Backend: FastAPI (`backend/main.py`).
- Baza danych: Supabase (tabele w `supabase/migrations/`).
- Dane zewnętrzne: The Odds API (kursy), Basketball-Reference (drużyny i składy), NBA Stats (wyniki).
- Dane historyczne: import z CSV w `nba historia/` do tabeli `player_game_stats`.
- Strefa czasowa: większość dziennych zestawień jest liczona w strefie America/Chicago.

## 2) Szybki start (dla użytkownika aplikacji)
1. Upewnij się, że backend działa i ma połączenie z Supabase (wskaźnik na dole po prawej).
2. Otwórz aplikację w przeglądarce (frontend).
3. Wybierz zakładkę z lewego menu.
4. Jeśli widzisz `Brak danych`, sprawdź połączenie z backendem lub wykonanie importu danych historycznych.

## 3) Źródła danych i pipeline
### 3.1 Supabase – główne tabele
- `teams`: lista drużyn NBA.
- `games`: mecze na dziś (z The Odds API).
- `odds`: kursy z wielu bukmacherów (The Odds API).
- `players`: składy drużyn (Basketball-Reference).
- `player_game_stats`: historyczne boxscore (CSV 2010–2024).
- `game_results`: wyniki meczów (NBA Stats scoreboard).
- `team_betting_stats`: cache statystyk ATS/OU.
- `reports`: zapisane raporty (jeśli generowane i zapisywane).

### 3.2 Skąd pochodzą dane
- **The Odds API** → `games`, `odds` (pliki: `backend/scrapers.py`).
- **Basketball-Reference** → `teams`, `players` (składy, ID zawodników do zdjęć).
- **NBA Stats** → `game_results` (wyniki i statusy meczów).
- **CSV historyczne** → `player_game_stats` (import przez `backend/import_historical_data.py`).

### 3.3 Co się dzieje, gdy brak danych
- Frontend nie „wymyśla” danych. Jeśli Supabase jest niedostępne, większość widoków pokaże `Brak danych`.
- Wskaźnik statusu na dole po prawej pokaże: offline / online bez danych / online z danymi.

## 4) Elementy wspólne interfejsu
### 4.1 Pasek górny (Header)
- **Nazwa sekcji**: zmienia się wraz z zakładką.
- **Ostatnia aktualizacja**: czas odświeżenia (America/Chicago).
- **Język**: przełącznik języka UI.
- **Status Live Data**: informacja „live data”.
- **Odśwież**: ręcznie sprawdza stan backendu.
- **Powiadomienia / Ustawienia / Profil**: obecnie puste (placeholdery).

### 4.2 Pasek boczny (Sidebar)
- Nawigacja po zakładkach.
- „League Status”: liczba dzisiejszych meczów + godzina pierwszego meczu (z `/api/games/today`).

### 4.3 Wskaźnik statusu backendu
- Dół po prawej: status backendu i Supabase (`/health`).

## 5) Zakładki i funkcje

### 5.1 Dashboard (Panel główny)
**Cel**: szybki przegląd dzisiejszych meczów, wartościowych kursów oraz wejście do analizy drużyn.

**Źródła danych**:
- `/api/games/today` → lista dzisiejszych meczów.
- `/api/odds/{game_id}` → kursy do wzbogacenia meczów.
- `/api/focus-teams/today` → „focus teams” (edge z kursów).
- `/api/teams/analysis` → analizy sezonowe drużyn.

**Funkcje**:
- **Karty statystyk**: kliknięcie przenosi do szczegółów:
  - Scheduled games (zaplanowane mecze),
  - Tracked teams (drużyny z najlepszym edge),
  - Season overview (statystyki sezonowe),
  - Value opportunities (edge > 0).
- **Today’s Games**: lista meczów z najlepszymi kursami ML/spread/total.
- **View Odds**: przenosi do zakładki Odds z zaznaczonym meczem.
- **Team Analysis**: otwiera widok All Teams z preselektowaną drużyną.
- **Export CSV / PDF**: dostępny w widokach „Scheduled”, „Tracked”, „Season”, „Value”.

**Jak liczone są dane**:
- Kursy ML są pobierane z `odds` i wybierany jest najlepszy kurs (najwyższy decimal) dla drużyny.
- Edge = `p_consensus * best_price - 1`, gdzie p_consensus to no‑vig z kursów wielu bukmacherów.

### 5.2 Reports (Raporty)
**Cel**: codzienne raporty analityczne (7:50, 8:00, 11:00 czasu Chicago).

**Źródła danych**:
- `/api/reports` → zapisane raporty z tabeli `reports`.
- `/api/reports/750am`, `/api/reports/800am`, `/api/reports/1100am` → generowanie raportów.

**Funkcje**:
- **Lista raportów**: wybór raportu z lewej strony.
- **Generate Now**: generuje raporty na żądanie.
- **Sekcje raportu**: zwijane/rozwijane bloki danych.
- **Eksport PDF**: generowany lokalnie w przeglądarce.

**Uwaga**: jeśli backend działa w trybie „mock” lub nie zapisuje raportów, lista może być pusta.

### 5.3 Teams (All Teams)
**Cel**: pełny przegląd drużyn, filtracja i szczegółowy panel drużyny.

**Źródła danych**:
- `/api/teams/analysis` → zestawienie drużyn z wyliczeniami z `player_game_stats`.

**Funkcje**:
- Widok **grid** lub **table**.
- Filtry: konferencja, dywizja, sortowanie.
- Wyszukiwarka po nazwie/skrótach.
- Panel szczegółów drużyny (po kliknięciu): record, win%, Off/Def Rtg, ATS/OU, key players.

**Uwaga**: „key players” to realne nazwiska z tabeli `players` (nie są generowane sztucznie).

### 5.4 Betting Recommendations
**Cel**: lista rekomendowanych zakładów ML + narzędzia bankroll.

**Źródła danych**:
- `/api/betting-recommendations` → obliczane z tabel `games` + `odds`.

**Funkcje**:
- Kategorie: All / Featured / General / Value.
- **Value Bets**: top 5 pozycji z dodatnim edge.
- **Kelly Calculator**: oblicza sugerowany % bankrolla (Quarter Kelly).
- **Bankroll input**: pozwala przeliczać stawkę.

**Jak liczone są rekomendacje**:
- Consensus prob: no‑vig z kursów wielu bukmacherów.
- Edge = `p_consensus * best_price - 1`.

### 5.5 Odds (Live Odds)
**Cel**: porównanie kursów u bukmacherów.

**Źródła danych**:
- `/api/games/today` + `/api/odds/{game_id}`.

**Funkcje**:
- Lista meczów, możliwość zaznaczenia jednego.
- Tabela bukmacherów z ML / spread / total.
- „Best odds” dla ML/spread/total.
- Przycisk Refresh.

**Uwaga**: alerty ruchów kursów są obecnie puste (backend nie dostarcza ruchów).

### 5.6 Players (Players Browser)
**Cel**: przegląd zawodników, porównania i szczegóły.

**Źródła danych**:
- `/api/players` → lista graczy (z filtrami).
- `/api/teams` → lista drużyn do filtra.
- `/api/players/{id}` → szczegóły + statystyki sezonowe i ostatnie mecze z `player_game_stats`.

**Funkcje**:
- Filtry: drużyna, pozycja, wyszukiwarka.
- Karty zawodników + dodawanie do porównania.
- Porównanie do 4 zawodników.
- Modal szczegółów: statystyki sezonu, trendy, bio.

**Zdjęcia zawodników**:
- Basketball‑Reference (po ID) lub fallback do avatarów.

### 5.7 Analytics
**Cel**: narzędzia analityczne oparte o historyczne dane boxscore.

**Źródła danych**:
- `player_game_stats` (import z CSV) przez endpointy `/api/analytics/*`.

**Zakładki**:
1. **Overview** – szybkie karty nawigacyjne.
2. **Props (Prop Bet Analyzer)** – `/api/analytics/prop-bet`:
   - Parametry: player, stat, linia, liczba gier, opcjonalny przeciwnik.
   - Wynik: OVER/UNDER/NO VALUE, confidence, hit rate, trend.
3. **Form (Form Tracker)** – `/api/analytics/form`:
   - Trend formy, rolling averages, wykresy.
4. **Matchup**:
   - Team vs Team: `/api/analytics/matchup/team`.
   - Player vs Opponent: `/api/analytics/matchup/player`.
5. **Injury Impact** – `/api/analytics/injury-impact`:
   - Analiza wpływu braku zawodnika na drużynę i beneficjentów.

### 5.8 Bulls Analysis
**Cel**: specjalistyczna analiza Chicago Bulls.

**Źródła danych**:
- `/api/bulls-analysis`:
  - `games` + `odds` → najbliższy mecz Bulls.
  - `player_game_stats` → statystyki sezonowe i trendy.
  - `team_betting_stats` → ATS/OU, jeśli dostępne.
- `/api/teams/CHI/players` → fallback roster, gdy brak pełnej analizy.

**Funkcje**:
- Team overview: record, ATS, OU, last 5.
- Player analysis: średnie PTS/REB/AST, FG%, FT%, minuty (top 8 graczy z ostatnich 7 meczów).
- Next game: opponent, linia spread i total (mediana z bukmacherów).
- Trends: pace, off/def rating, 3PT%, FT% (porównanie last7 vs prev7).
- Risk factors: back‑to‑back, home court (tylko jeśli dane są aktualne).

## 6) Warto wiedzieć
- **Brak danych** najczęściej oznacza brak importu CSV lub brak połączenia z Supabase.
- **Raporty** mogą być puste, jeśli nie są zapisywane w tabeli `reports`.
- **Dane historyczne** są wymagane do zakładek Analytics.
- **Strefa czasowa**: raporty i „dzisiejsze mecze” liczone są w America/Chicago.

## 7) Skrót endpointów API (frontend)
- `GET /health`
- `GET /api/teams`
- `GET /api/teams/analysis`
- `GET /api/teams/{team}/players`
- `GET /api/games/today`
- `GET /api/odds/{game_id}`
- `GET /api/focus-teams/today`
- `GET /api/players`
- `GET /api/players/{id}`
- `GET /api/reports` + `/api/reports/*`
- `GET /api/betting-recommendations`
- `GET /api/bulls-analysis`
- `GET /api/analytics/prop-bet`
- `GET /api/analytics/form`
- `GET /api/analytics/matchup/team`
- `GET /api/analytics/matchup/player`
- `GET /api/analytics/injury-impact`


## 8) Konfiguracja komputera (Windows 10)
Poniżej minimalna i zalecana konfiguracja Windows 10, aby uruchomić aplikację lokalnie.

### 8.1 Wymagania sprzętowe
Minimalne:
- CPU: 2 rdzenie
- RAM: 8 GB
- Dysk: 10 GB wolnego miejsca
- Internet: stabilne połączenie (API + Supabase)

Zalecane:
- CPU: 4 rdzenie
- RAM: 16 GB
- Dysk: SSD, 20 GB wolnego miejsca

### 8.2 Wymagania systemowe
- Windows 10 64-bit (aktualne poprawki systemowe)
- PowerShell 5.1+ (standardowo w Windows 10)
- Ustawiona poprawna data i godzina systemu (ważne dla zapytań do API)

### 8.3 Wymagane oprogramowanie
1) Node.js (LTS)
- Wersja: 18.x lub 20.x
- NPM: zainstalowany razem z Node.js

2) Python
- Wersja: 3.10+ (zalecane 3.11)
- Pip: zainstalowany razem z Pythonem

3) Git
- Do pobrania i aktualizacji repozytorium

Opcjonalnie:
- Docker Desktop (jeśli chcesz uruchamiać aplikację w kontenerach)

### 8.4 Konfiguracja środowiska
1) Skonfiguruj pliki `.env`:
- Frontend korzysta z wartości `VITE_*` (np. `VITE_API_BASE_URL`, `VITE_SUPABASE_URL`).
- Backend czyta `.env` w katalogu głównym (np. `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`).

2) Uzupełnij klucze API:
- `ODDS_API_KEY` (The Odds API) – potrzebny do kursów.
- Supabase: `SUPABASE_URL` + `SUPABASE_SERVICE_KEY` lub `VITE_SUPABASE_ANON_KEY`.

### 8.5 Uruchomienie aplikacji lokalnie (zalecany tryb)
1) Backend (FastAPI):
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2) Frontend (Vite):
```powershell
cd ..
npm install
npm run dev
```

3) Otwórz aplikację:
- Domyślnie: `http://localhost:5173`

### 8.6 Import danych historycznych (dla Analytics)
Aby Analytics działał poprawnie, potrzebny jest import CSV:
```powershell
cd backend
python import_historical_data.py
```
Uwaga: import może potrwać kilkanaście minut i wymaga więcej RAM.

### 8.7 Firewall i porty
Upewnij się, że lokalne porty nie są blokowane:
- `8000` (backend)
- `5173` (frontend)

### 8.8 Najczęstsze problemy
- `Brak danych`: brak połączenia z Supabase lub brak importu CSV.
- `CORS`: sprawdź `VITE_API_BASE_URL` i czy backend działa.
- `Błędy kursów`: brak lub niepoprawny `ODDS_API_KEY`.\n## 8.9 Szybka sciaga (uruchomienie .bat)
- Pierwsze uruchomienie: dwuklik `setup.bat` (instalacja zaleznosci).
- Kolejne uruchomienia: dwuklik `start.bat`.
- Zatrzymanie: `stop.bat` (jesli potrzebne).
- Wymagane: poprawnie wypelnione `.env` i dostep do internetu.
- Aplikacja: `http://localhost:5173`.
## 9) Disclaimer
System służy celom analitycznym/edukacyjnym. Nie stanowi porady finansowej.

---

Jeśli chcesz, mogę dodać kolejną wersję instrukcji w formie PDF albo skróconej „ściągi” dla użytkownika końcowego.



## 10) Instalacja wymaganych programow (Windows 10)
Poniżej kroki instalacji podstawowych narzedzi potrzebnych do uruchomienia aplikacji.

### 10.1 Node.js (NPM)
- Wejdz na: https://nodejs.org/
- Pobierz wersje LTS (18.x lub 20.x)
- Zainstaluj standardowo (Next, Next, Finish)
- Sprawdz w PowerShell:
```powershell
node -v
npm -v
```

### 10.2 Python
- Wejdz na: https://www.python.org/downloads/
- Pobierz wersje 3.11.x
- Zaznacz opcje: "Add Python to PATH"
- Zainstaluj standardowo
- Sprawdz w PowerShell:
```powershell
python --version
pip --version
```

### 10.3 Git
- Wejdz na: https://git-scm.com/download/win
- Pobierz i zainstaluj standardowo
- Sprawdz w PowerShell:
```powershell
git --version
```

### 10.4 (Opcjonalnie) Docker Desktop
- Wejdz na: https://www.docker.com/products/docker-desktop/
- Zainstaluj jesli chcesz uruchamiac aplikacje w kontenerach

### 10.5 Weryfikacja
Po instalacji wszystkich narzedzi uruchom ponownie komputer i sprawdz wersje w PowerShell.
