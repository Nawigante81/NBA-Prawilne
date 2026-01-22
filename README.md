# 🏀 NBA Analysis & Betting Intelligence Platform

**Zaawansowana platforma analityczna i inteligencja zakładowa NBA**

Profesjonalny system analityczny NBA ze szczególnym naciskiem na Chicago Bulls. Platforma zapewnia przetwarzanie danych w czasie rzeczywistym, zaawansowaną analizę statystyczną, automatyczne generowanie raportów oraz inteligentne rekomendacje zakładów z wykorzystaniem optymalizacji Kelly Criterion.

![NBA Analysis Dashboard](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![TypeScript](https://img.shields.io/badge/TypeScript-5.5+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green)
![React](https://img.shields.io/badge/React-18.3+-blue)
![Python](https://img.shields.io/badge/Python-3.11+-yellow)

## 📋 Spis treści

1. [O projekcie](#-o-projekcie)
2. [Architektura systemu](#️-architektura-systemu)
3. [Zasada działania](#-zasada-działania)
4. [Kluczowe funkcjonalności](#-kluczowe-funkcjonalności)
5. [Stack technologiczny](#-stack-technologiczny)
6. [Struktura projektu](#-struktura-projektu)
7. [Szybki start](#-szybki-start)
8. [Instalacja i konfiguracja](#-instalacja-i-konfiguracja)
9. [API Endpoints](#-api-endpoints)
10. [Źródła danych](#-źródła-danych)
11. [Przepływ danych](#-przepływ-danych)
12. [Deployment](#-deployment)
13. [Rozwój i testy](#-rozwój-i-testy)
14. [Troubleshooting](#-troubleshooting)
15. [Roadmap](#-roadmap)

---

## 🎯 O projekcie

### Czym jest NBA-Prawilne?

NBA-Prawilne to kompleksowa, produkcyjna platforma analityczna stworzona dla profesjonalnych analityków i entuzjastów zakładów sportowych NBA. System łączy:

- **Automatyczny scraping danych** z wielu źródeł (NBA Stats API, Basketball-Reference, The Odds API)
- **Zaawansowane algorytmy analityczne** wykorzystujące matematykę zakładową (Kelly Criterion, Expected Value, CLV)
- **System jakości danych** z 13+ bramkami walidacyjnymi zapewniającymi najwyższą jakość rekomendacji
- **Trzy codzienne raporty** generowane automatycznie o określonych godzinach (stref czasowa Chicago)
- **Szczegółową analizę Chicago Bulls** z podziałem na poszczególnych graczy
- **Dashboard interaktywny** zbudowany w React z wizualizacjami i wykresami na żywo

### Dla kogo?

- **Analitycy sportowi** potrzebujący narzędzi do głębokiej analizy statystycznej
- **Profesjonalni typerzy** szukający przewagi matematycznej (edge) w zakładach
- **Entuzjaści NBA** chcący lepiej rozumieć zespoły i graczy
- **Data Scientists** zainteresowani analizą danych sportowych

### Główne problemy, które rozwiązuje:

1. **Automatyzacja zbierania danych** - eliminuje ręczne wyszukiwanie statystyk
2. **Kontrola budżetu API** - zarządzanie limitami wywołań zewnętrznych API
3. **Jakość rekomendacji** - system bramek jakości zapobiega złym zakładom
4. **Śledzenie wartości** - monitorowanie Closing Line Value (CLV) dla mierzenia edge
5. **Zarządzanie ryzykiem** - Kelly Criterion dla optymalnej wielkości stawek

---

## 🏗️ Architektura systemu

### Komponenty wysokopoziomowe

```
┌─────────────────────────────────────────────────────────────────┐
│                        UŻYTKOWNIK                                │
│                    (Przeglądarka / API Client)                   │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       │ HTTP/HTTPS
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (React + Vite)                       │
│  ┌────────────┬────────────┬────────────┬────────────────────┐  │
│  │ Dashboard  │  Reports   │  Analytics │  Betting Board     │  │
│  │ Component  │  Component │ Component  │  Component         │  │
│  └────────────┴────────────┴────────────┴────────────────────┘  │
│                 TypeScript + Tailwind CSS                        │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       │ REST API
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                  BACKEND (FastAPI + Python)                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              API Layer (8 modułów)                        │  │
│  │  Teams │ Games │ Odds │ Value Board │ Picks │ Reports    │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │            Service Layer (10 serwisów)                    │  │
│  │  Analytics │ Betting Math │ Quality Gates │ CLV │ Sync   │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │          Provider Layer (4 providery)                     │  │
│  │  NBA Stats │ Odds API │ Basketball-Ref │ Base Provider   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                APScheduler (harmonogram zadań)                   │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       │ PostgreSQL Client
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                  DATABASE (Supabase PostgreSQL)                  │
│  ┌────────────┬────────────┬────────────┬─────────────────────┐ │
│  │   teams    │   games    │   players  │   odds_snapshots    │ │
│  ├────────────┼────────────┼────────────┼─────────────────────┤ │
│  │   picks    │   reports  │ api_budget │   pick_results      │ │
│  ├────────────┼────────────┼────────────┼─────────────────────┤ │
│  │team_game   │player_game │ api_cache  │   uploads_stub      │ │
│  │   _stats   │   _stats   │            │                     │ │
│  └────────────┴────────────┴────────────┴─────────────────────┘ │
│                     Indexes + Triggers                           │
└─────────────────────────────────────────────────────────────────┘
                       ▲
                       │
              ┌────────┴────────┐
              │                 │
         External APIs:    External APIs:
      NBA Stats API      The Odds API
   Basketball-Reference
```

### Warstwa Provider (Zbieranie danych)

**4 providery** odpowiedzialne za pobieranie danych z zewnętrznych źródeł:

1. **`nba_stats.py`** - NBA Stats API (darmowe)
   - Zespoły, gracze, wyniki meczów, statystyki graczy
   - Cache z TTL (scoreboard: 1h, gracze: 7 dni)
   - Rate limiting: max 2 jednoczesne zapytania

2. **`odds_api.py`** - The Odds API (500 wywołań/miesiąc darmowo)
   - Kursy bukmacherskie w czasie rzeczywistym
   - Budżet: 10 wywołań/dzień (konfigurowalne)
   - Deduplikacja przez content hash
   - Bookmakerzy: DraftKings, BetMGM, FanDuel

3. **`basketball_reference.py`** - Web scraping (uprzejmy)
   - Składy zespołów, rozszerzone statystyki
   - 3 sekundy między zapytaniami
   - Concurrency = 1
   - Graceful fallback przy rate limit

4. **`base.py`** - Interfejs bazowy
   - Abstrakcyjna klasa dla wszystkich providerów
   - Metody: `fetch()`, `normalize()`, `upsert()`, `healthcheck()`, `sync()`

### Warstwa Service (Logika biznesowa)

**10 głównych serwisów** implementujących logikę aplikacji:

1. **`betting_math.py`** - Matematyka zakładowa
   - Konwersja kursów (amerykańskie ↔ dziesiętne)
   - Prawdopodobieństwo implikowane
   - Expected Value (EV)
   - Kelly Criterion (pełny i frakcyjny)
   - Obliczenia CLV
   - Usuwanie vigu
   - Kursy parlay
   - **25 testów jednostkowych - 100% zdanych ✓**

2. **`quality_gates.py`** - System jakości danych
   - 13+ bramek walidacyjnych
   - Sprawdzanie dostępności i świeżości kursów
   - Walidacja wielkości próbek
   - Kontrola jakości rynku
   - Progi EV i edge
   - Zwraca pass/fail z kodami przyczyn

3. **`analytics_service.py`** - Analityka zespołów/graczy
   - Trendy zespołowe (tempo, OffRtg, DefRtg, 3PT%, FT%)
   - Statystyki graczy (PTS, REB, AST, minuty)
   - Analiza Bulls po graczu
   - Wydajność ATS vs kursy zamknięcia
   - Wydajność O/U

4. **`clv_service.py`** - Closing Line Value
   - Przechowywanie snapshotów kursów z deduplikacją
   - Pobranie kursu zamknięcia (ostatni snapshot przed rozpoczęciem)
   - Obliczanie CLV dla typerów
   - Timeline ruchu linii
   - Statystyki podsumowujące CLV

5. **`budget_service.py`** - Kontrola budżetu API
   - Dzienny limit wywołań per provider
   - Auto-reset o północy
   - Zapytania o pozostały budżet
   - Liczniki wywołań
   - Endpoint podsumowania budżetu

6. **`sync_service.py`** - Orkiestracja providerów
   - Synchronizacja startowa: Teams → Players → Games → Odds
   - Zaplanowana synchronizacja (co 12h)
   - Specjalna synchronizacja składu Bulls
   - Sprawdzanie zdrowia providerów
   - Pobieranie z uwzględnieniem budżetu

7. **`report_service.py`** - Generowanie raportów (1063 linie)
   - Trzy codzienne raporty (7:50, 8:00, 11:00 CT)
   - Integracja z bramkami jakości
   - Zapisywanie do bazy danych

8. **`value_service.py`** - Identyfikacja wartości
   - Wyszukiwanie zakładów z dodatnim EV
   - Porównanie multi-bookmaker
   - Filtrowanie przez bramki jakości

9. **`odds_service.py`** - Zarządzanie kursami
   - Pobieranie kursów dla gier
   - Historia ruchów linii
   - Grupowanie po bukmacherze i rynku

10. **`betting_stats_service.py`** - Statystyki zakładów
    - ROI, win rate, yield
    - Śledzenie jednostek wygranych/przegranych
    - Historia wydajności

### Warstwa API (Endpointy HTTP)

**8 modułów routingu** udostępniających funkcjonalności przez REST API:

- `routes_teams.py` - Zarządzanie zespołami
- `routes_games.py` - Harmonogramy i wyniki gier
- `routes_odds.py` - Kursy bukmacherskie i ruchy linii
- `routes_value_board.py` - Zakłady wartościowe (quality-gated)
- `routes_picks.py` - Rekomendacje i rozliczenia
- `routes_performance.py` - Metryki wydajności (ROI/CLV)
- `routes_reports.py` - Codzienne raporty
- `routes_uploads_stub.py` - Metadata zrzutów ekranu

---

## ⚙️ Zasada działania

### Cykl życia aplikacji

```
START APLIKACJI
    │
    ├─► [1] Inicjalizacja
    │   ├─ Połączenie z Supabase
    │   ├─ Konfiguracja z zmiennych środowiskowych
    │   └─ Utworzenie klienta HTTP
    │
    ├─► [2] Synchronizacja startowa
    │   ├─ Pobranie zespołów (NBA Stats + Basketball-Ref)
    │   ├─ Pobranie graczy
    │   ├─ Pobranie dzisiejszych gier
    │   └─ Pobranie kursów (z kontrolą budżetu)
    │
    ├─► [3] Uruchomienie harmonogramu (APScheduler)
    │   ├─ Raport 7:50 AM CT (Analiza poprzedniego dnia)
    │   ├─ Raport 8:00 AM CT (Podsumowanie poranne)
    │   ├─ Raport 11:00 AM CT (Scouting dnia meczowego)
    │   └─ Synchronizacja co 12h (dane na żywo)
    │
    ├─► [4] Serwer API (FastAPI)
    │   ├─ Nasłuchiwanie na porcie 8000
    │   ├─ CORS middleware
    │   ├─ Basic auth dla wrażliwych endpointów
    │   └─ Obsługa wyjątków globalnie
    │
    └─► [5] Pętla główna
        ├─ Obsługa zapytań HTTP
        ├─ Wykonywanie zaplanowanych zadań
        ├─ Monitoring zdrowia providerów
        └─ Logowanie i diagnostyka

ZATRZYMANIE APLIKACJI
    ├─ Graceful shutdown
    ├─ Zakończenie harmonogramu
    └─ Zamknięcie połączeń
```

### Przepływ generowania rekomendacji zakładów

```
1. ZBIERANIE DANYCH
   │
   ├─ NBA Stats API
   │  └─ Statystyki zespołów i graczy (ostatnie 10 gier)
   │
   ├─ The Odds API
   │  └─ Kursy 3 bookmakerów (DraftKings, BetMGM, FanDuel)
   │
   └─ Basketball-Reference
      └─ Szczegółowe składy i kontuzje

2. ANALITYKA
   │
   ├─ Obliczenia trendu (7-dniowe rolling avg)
   │  ├─ Tempo (pace)
   │  ├─ OffRtg, DefRtg
   │  ├─ 3PT%, FT%
   │  └─ Minuty graczy
   │
   ├─ Matchup analysis
   │  ├─ Przewagi pozycyjne
   │  ├─ Tempo gry (fast vs slow)
   │  └─ Inside vs outside scoring
   │
   └─ Bulls player breakdown
      ├─ Forma (ostatnie 5 gier)
      ├─ Zmiany roli
      └─ Zmienność minut

3. MATEMATYKA ZAKŁADOWA
   │
   ├─ Obliczenie prawdopodobieństwa implikowanego
   ├─ Usunięcie vigu
   ├─ Własna estymacja prawdopodobieństwa
   ├─ Obliczenie Expected Value (EV)
   └─ Obliczenie wielkości stawki (Kelly Criterion)

4. BRAMKI JAKOŚCI (13+ sprawdzeń)
   │
   ├─ ✓ Kursy dostępne i świeże (< 12h)?
   ├─ ✓ Linia zamknięcia istnieje?
   ├─ ✓ Wystarczająca próbka zespołowa (≥5 gier)?
   ├─ ✓ Wystarczająca próbka gracza (≥3 gry)?
   ├─ ✓ Statystyki świeże (< 24h)?
   ├─ ✓ Jakość rynku OK (juice check)?
   ├─ ✓ EV powyżej progu (≥+2%)?
   ├─ ✓ Edge wystarczający (≥+3%)?
   ├─ ✓ Ufność wystarczająca (≥0.55)?
   ├─ ✓ Parlay max nogi (≤5)?
   ├─ ✓ Parlay min prawdopodobieństwo (≥0.20)?
   ├─ ✓ Zmienność minut gracza OK?
   └─ ✓ Czas rozpoczęcia znany?

5. GENEROWANIE REKOMENDACJI
   │
   ├─ Jeśli wszystkie bramki przeszły:
   │  ├─ Stwórz rekomendację z obliczonym EV
   │  ├─ Określ wielkość stawki (Kelly)
   │  └─ Dodaj do value board
   │
   └─ Jeśli jakaś bramka nie przeszła:
      ├─ Zwróć "NO BET"
      ├─ Podaj kod przyczyny
      └─ Dostarczaj analizę bez rekomendacji

6. ŚLEDZENIE CLV
   │
   ├─ Zapisz snapshot kursu
   ├─ Po rozpoczęciu gry - znajdź kurs zamknięcia
   ├─ Oblicz CLV = (kurs typera - kurs zamknięcia) / kurs zamknięcia
   └─ Zapisz w pick_results

7. RAPORTOWANIE
   │
   └─ Włącz rekomendacje do codziennych raportów
      ├─ 7:50 AM: Wyniki vs kursy zamknięcia
      ├─ 8:00 AM: Lean kierunkowe
      └─ 11:00 AM: Propozycje parlay z bramkami jakości
```

---

## 🎨 Kluczowe funkcjonalności

### 1. Automatyczny scraping danych z kontrolą budżetu

**Zespoły NBA**
- Źródło: NBA Stats API + Basketball-Reference
- Częstotliwość: Raz dziennie + on-demand
- Cache: 7 dni
- Dane: Nazwa, miasto, skrót, logo

**Gracze NBA**
- Źródło: NBA Stats API
- Częstotliwość: Raz dziennie
- Cache: 7 dni
- Dane: Imię, nazwisko, pozycja, numer, zespół

**Harmonogramy i wyniki gier**
- Źródło: NBA Stats API + The Odds API
- Częstotliwość: Co 12h (6h w dni meczowe)
- Dane: Data rozpoczęcia, drużyna domowa/gości, wynik

**Kursy bukmacherskie**
- Źródło: The Odds API
- Częstotliwość: Co 12h (6h w dni meczowe)
- Budżet: 10 wywołań/dzień (konfigurowalne)
- Bookmakerzy: DraftKings, BetMGM, FanDuel
- Rynki: H2H (moneyline), Spread, Totals (O/U)
- Deduplikacja: Content hash zapobiega duplikatom

### 2. System 9 zespołów fokusowych

**Analiza głęboka dla:**
- Boston Celtics
- Minnesota Timberwolves
- Oklahoma City Thunder
- Orlando Magic
- Cleveland Cavaliers
- Sacramento Kings
- Houston Rockets
- New York Knicks
- **Chicago Bulls** (specjalna analiza per-gracz)

**Metryki śledzone:**
- Offensive Rating (OffRtg)
- Defensive Rating (DefRtg)
- Tempo/Pace
- 3-point % (3PT%)
- Free Throw % (FT%)
- Against The Spread (ATS) performance
- Over/Under (O/U) trends

### 3. Trzy codzienne raporty (strefa czasowa Chicago)

#### 📊 Raport 7:50 AM - Analiza poprzedniego dnia

**Zawartość:**
- **Wyniki vs kursy zamknięcia**: Porównanie końcowych wyników z closing lines (ATS, O/U)
- **Top 3 trendy**: Zespoły konsekwentnie powyżej/poniżej oczekiwań Vegas
- **Bulls gracz-po-graczu**: Indywidualne statystyki (PTS/REB/AST), rola, minuty
- **Ryzyka**: Kluczowe spostrzeżenia na następny dzień tradingu

**Przykład:**
```
=== WYNIKI WCZORAJ vs CLOSING LINE ===
Celtics 112-105 Heat
  - Spread: BOS -7.5 → WON by 7 (PUSH)
  - Total: 217.5 → 217 (UNDER)
  - CLV: +1.5 points (picked BOS -6 early)

=== TOP 3 TRENDY (7 dni) ===
1. Thunder: 6-1 ATS (+15.2 units)
2. Wolves: 5-2 O/U Overs (68.2 avg margin)
3. Bulls: 3-4 ATS but +2.3 CLV avg

=== BULLS PLAYER BREAKDOWN ===
DeRozan: 28.2 PPG, 5.1 APG, 36.4 MPG (starter, hot form)
LaVine: 22.8 PPG, 4.2 RPG, 34.1 MPG (starter, inconsistent)
Vucevic: 16.5 PPG, 10.8 RPG, 32.7 MPG (center, steady)
...
```

#### 📰 Raport 8:00 AM - Podsumowanie poranne

**Zawartość:**
- **Wyniki wczoraj**: 1-liniowe podsumowanie per zespół fokusowy (wynik, ATS, O/U)
- **Trendy 7-dniowe**: Analiza trendu (tempo, OffRtg, DefRtg, 3PT%, FT%)
- **Bulls zawodnicy**: Aktualna forma (ostatnie 5 gier), minuty, zmiany roli
- **Wnioski bukmacherskie**: 2-3 kierunkowe leans (np. "X under look", "Y rebounds uptick")
- **Prośba o kursy**: Akcja wymagana - upload screenshotów DraftKings/BetMGM

**Przykład:**
```
=== WCZORAJ (Focus Teams) ===
✓ Celtics beat Heat, covered -7.5, under 217.5
✗ Bulls lost to Cavs, missed +4.5, over 224.5
✓ Thunder beat Rockets, covered -5, under 230

=== TRENDY 7-DNI ===
Tempo: Thunder ↑ (105.2), Bulls → (98.1), Magic ↓ (95.3)
OffRtg: Celtics ↑ (121.4), Thunder ↑ (118.7)
3PT%: Kings ↑ (39.2%), Knicks ↓ (32.1%)

=== WNIOSKI BUKMACHERSKIE ===
1. Thunder Overs trend - 6/7 last games, pace increasing
2. LaVine rebounds uptick - 5.8 last 3 games vs 3.2 season avg
3. Magic Unders at home - 4/5 covered, elite defense

>>> ACTION: Upload DraftKings/BetMGM screenshots for today's slate
```

#### 🎯 Raport 11:00 AM - Scouting dnia meczowego

**Zawartość:**
- **Kto gra dziś**: Pełna lista z czasami gier + status kontuzji/nieobecności
- **Match-up notes**: Tempo, przewagi pozycyjne, trendy inside/outside
- **Bulls arkusz**:
  - Recap ostatniej gry
  - Zaktualizowana forma graczy (ostatnie 5 gier)
  - Match-upy pozycyjne
  - Początkowy lean (O/U i strona)
- **Propozycje zakładów** (przeszły przez bramki jakości):
  - Parlay ogólny (3-5 nóg, niskie ryzyko)
  - Parlay Bulls (2-5 nóg, propsy graczy + linie gry)
  - Konserwatywne alternatywy
- **Ryzyka**: Późne scratches, ograniczenia minut, B2B, podróż, ruchy linii

**Przykład:**
```
=== KTO GRA DZIŚ (6 PM CT start) ===
Bulls @ Cavaliers 6:00 PM
  - Bulls: DeRozan PROBABLE (ankle), LaVine OUT (knee)
  - Cavs: Mitchell QUESTIONABLE (hamstring)
Celtics vs Heat 6:30 PM
  - Full rosters active
Thunder @ Rockets 7:00 PM
  - Rockets: Sengun OUT (ankle)

=== BULLS GAME SHEET ===
Last game: L 105-110 vs Cavs (missed +4.5, over 224.5)
Current form (L5): 2-3 SU, 1-4 ATS, 3-2 O/U

Position matchups:
  PG: Ayo (32 mpg) vs Garland → Even
  SG: Caruso (28 mpg) vs Mitchell → Cavs edge
  SF: DJJ (24 mpg) vs Okoro → Bulls edge
  PF: Williams (30 mpg) vs Mobley → Cavs BIG edge
  C: Vucevic (33 mpg) vs Allen → Cavs edge

Initial lean: Cavs -6.5 ✓, Under 225.5 ✓

=== PROPOZYCJE ZAKŁADÓW (Quality-Gated) ===

GENERAL PARLAY (3 legs, +262 odds)
✓ Thunder -5 vs Rockets (EV: +4.2%, Kelly: 1.2u)
✓ Celtics Under 230.5 (EV: +3.1%, Kelly: 0.8u)
✓ Bulls Under 224.5 (EV: +2.8%, Kelly: 0.7u)
Combined prob: 28.4%, EV: +10.7%
RECOMMENDATION: 0.5u to win 1.31u

BULLS PARLAY (4 legs, +580 odds)
✓ Bulls +6.5 (EV: +2.1%)
✓ Vucevic Under 25.5 points (EV: +3.8%)
✓ Ayo Under 10.5 points (EV: +2.9%)
✓ Game Under 224.5 (EV: +2.8%)
Combined prob: 14.7%, EV: +15.2%
RECOMMENDATION: 0.3u to win 1.74u

CONSERVATIVE SINGLE
✓ Thunder -5 (EV: +4.2%, Kelly: 1.2u)
RECOMMENDATION: 1.0u to win 0.91u

=== RYZYKA ===
⚠ LaVine OUT - Bulls offense down 20ppg
⚠ Mitchell QUESTIONABLE - If sits, Bulls +6.5 better value
⚠ B2B for Bulls - 3rd game in 4 nights, fatigue factor
⚠ Line moved from -5.5 to -6.5 (sharp action on Cavs)
```

### 4. System bramek jakości (Quality Gates)

**13+ walidacji** zapewniających najwyższą jakość rekomendacji:

| # | Bramka | Opis | Próg |
|---|--------|------|------|
| 1 | **Dostępność kursów** | Kursy istnieją i są świeże | < 12h od teraz |
| 2 | **Linia zamknięcia** | Closing line dostępna do CLV | Istnieje |
| 3 | **Próbka zespołowa** | Wystarczająco gier do trendu | ≥ 5 gier |
| 4 | **Próbka gracza** | Wystarczająco gier gracza | ≥ 3 gry |
| 5 | **Świeżość stats** | Statystyki zaktualizowane | < 24h |
| 6 | **Jakość rynku** | Juice rozsądny (nie za wysoki) | Vig < 10% |
| 7 | **Próg EV** | Expected Value dodatni | ≥ +2.0% |
| 8 | **Próg Edge** | Przewaga wystarczająca | ≥ +3.0% |
| 9 | **Próg ufności** | Prawdopodobieństwo rozsądne | ≥ 0.55 |
| 10 | **Parlay max nogi** | Nie za wiele nóg | ≤ 5 |
| 11 | **Parlay min prob** | Łączne prawdopodobieństwo OK | ≥ 0.20 |
| 12 | **Zmienność minut** | Konsekwentne minuty gracza | StdDev < 8 min |
| 13 | **Czas rozpoczęcia** | Znany czas startu gry | Nie NULL |

**Wyjście gdy bramki zawodzą:**
```json
{
  "bet": "NO BET",
  "reason": "QUALITY_GATE_FAILED",
  "failures": [
    {"gate": "EV_THRESHOLD", "value": 0.8, "required": 2.0},
    {"gate": "SAMPLE_SIZE", "value": 2, "required": 5}
  ],
  "analysis": "Thunder -5 analysis provided below...",
  "recommendation": "Pass on this bet - insufficient edge"
}
```

### 5. Matematyka zakładowa (Betting Math)

**Implementowane funkcje** (100% pokryte testami):

```python
# Konwersja kursów
american_to_decimal(-110) → 1.909
decimal_to_american(2.50) → +150

# Prawdopodobieństwo implikowane
implied_probability_american(-110) → 0.5238 (52.38%)
implied_probability_decimal(2.50) → 0.4 (40%)

# Expected Value
# EV = (prob * profit) - (1-prob * stake)
calculate_ev(prob=0.55, odds=-110) → 0.0145 (1.45% EV)

# Kelly Criterion
# f = (bp - q) / b, gdzie b=odds, p=prob, q=1-p
kelly_criterion(prob=0.55, odds=1.909, fraction=0.25) → 0.0456
# → Bet 4.56% of bankroll

# Fair Odds (usunięcie vigu)
remove_vig(odds1=-110, odds2=-110) → (2.00, 2.00)
# → Fair odds to even money

# Closing Line Value
calculate_clv_spread(
  picked_line=-5, picked_odds=-110,
  closing_line=-6.5, closing_odds=-110
) → +1.5 points CLV (excellent!)

# Parlay Odds
parlay_odds([1.91, 2.00, 1.83]) → 6.99
parlay_implied_probability(6.99) → 0.143 (14.3%)
```

**Przykład praktyczny:**
```
Scenario: Thunder -5 @ -110
Własna estymacja: 58% szans na wygraną
Implied probability: -110 → 52.38%

Edge = 58% - 52.38% = 5.62% ✓ (> 3% próg)
EV = (0.58 * 0.909) - (0.42 * 1) = +0.107 → +10.7% EV ✓

Kelly (quarter) = ((1.909 * 0.58) - 1) / 1.909 * 0.25 = 2.87%
Bankroll: $1000 → Bet: $28.70

Outcome if wins: +$26.08
Outcome if loses: -$28.70
Long-term EV: $28.70 * 10.7% = +$3.07 per bet
```

### 6. Closing Line Value (CLV) Tracking

**CLV** to kluczowa metry ka określająca czy kupujesz "tanio" czy "drogo":

- **Dodatnie CLV** (+): Kupiłeś lepszą linię niż closing → Sharp bet
- **Ujemne CLV** (-): Kupiłeś gorszą linię niż closing → Recreational bet

**Śledzenie:**
1. Zapisz snapshot kursu w momencie typowania
2. Po rozpoczęciu gry - znajdź closing line (ostatni snapshot)
3. Oblicz CLV = (twój kurs - kurs zamknięcia) / kurs zamknięcia * 100%

**Przykład:**
```
Picked: Thunder -5 @ -110 (10:00 AM)
Closing: Thunder -6.5 @ -110 (game time)

CLV = (-5 - (-6.5)) / abs(-5) * 100% = +30% CLV na spreadzie
Interpretation: Znakomita wartość - linia ruszyła się 1.5 punktu w twoją stronę
```

**Historia CLV:**
```sql
SELECT 
  pick_date,
  AVG(clv_percent) as avg_clv,
  COUNT(*) as bets
FROM pick_results
GROUP BY pick_date
ORDER BY pick_date DESC;

-- Example output:
-- 2026-01-20: +3.2% CLV, 8 bets
-- 2026-01-19: +1.8% CLV, 12 bets
-- 2026-01-18: -0.5% CLV, 6 bets (bad day)
```

### 7. Szczegółowa analiza Chicago Bulls

**Per-player breakdown** dostępny w każdym raporcie:

```
=== CHICAGO BULLS ANALYSIS ===

BACKCOURT:
1. Zach LaVine (SG, #8)
   Role: Primary scorer, starter
   Last 5: 24.6 PPG, 4.8 RPG, 4.2 APG (↑ assists)
   Minutes: 35.2 MPG (high usage)
   Form: HOT - 3 straight 25+ games
   Props edge: Overs on points, assists trending up

2. Coby White (PG, #0)
   Role: Starting PG, secondary scorer
   Last 5: 18.2 PPG, 3.4 APG, 1.2 SPG
   Minutes: 31.8 MPG
   Form: STEADY - Consistent 15-20 range
   Props edge: Unders on assists (facilitator role reduced)

FRONTCOURT:
3. DeMar DeRozan (SF, #11)
   Role: Primary playmaker, clutch scorer
   Last 5: 26.4 PPG, 5.8 APG, 4.2 RPG
   Minutes: 36.8 MPG (team high)
   Form: ELITE - Career year, MVP candidate
   Props edge: Overs across the board

4. Patrick Williams (PF, #44)
   Role: 3&D specialist, starter
   Last 5: 11.2 PPG, 4.6 RPG, 0.8 BPG
   Minutes: 28.4 MPG
   Form: IMPROVING - Confidence growing
   Props edge: Unders points (inconsistent scoring)

5. Nikola Vucevic (C, #9)
   Role: Starting center, post presence
   Last 5: 17.8 PPG, 11.2 RPG, 3.2 APG
   Minutes: 32.6 MPG
   Form: STEADY - Double-double machine
   Props edge: Overs on rebounds vs weak frontcourts

BENCH IMPACT:
- Ayo Dosunmu: 12.1 PPG, 28.2 MPG (6th man value)
- Alex Caruso: Defense specialist, 8.4 PPG, 1.8 SPG
- Andre Drummond: Backup C, 6.2 RPG in 16 MPG

TEAM TRENDS (Last 10):
- Pace: 98.7 (18th in NBA) → Slower half-court team
- OffRtg: 114.2 (12th) → Above average offense
- DefRtg: 112.8 (20th) → Below average defense
- ATS: 4-6 (40%) → Not covering spreads well
- O/U: 6-4 Overs (60%) → Games going over
```

### 8. Dashboard interaktywny (Frontend)

**Komponenty React** zbudowane w TypeScript:

1. **Dashboard** - Główny widok przeglądu
   - Dzisiejsze gry z aktualnymi kursami
   - Value board z rekomendacjami
   - Najnowsze raporty
   - Statystyki wydajności (ROI, CLV)

2. **Value Board** - Zakłady wartościowe
   - Filtrowane przez bramki jakości
   - Sortowanie po EV
   - Wizualizacja edge
   - Rekomendacje stake (Kelly)

3. **Reports Section** - Przeglądarka raportów
   - Trzy codzienne raporty
   - Historyczne raporty
   - Export do PDF
   - Search i filtrowanie

4. **Bulls Analysis** - Szczegółowa analiza Bulls
   - Składy i statystyki graczy
   - Trendy zespołowe
   - Match-up analysis
   - Propsy graczy

5. **Live Odds** - Kursy na żywo
   - Porównanie multi-bookmaker
   - Timeline ruchów linii
   - Wizualizacja spread/total
   - Alerty na ruchy wartości

6. **Analytics** - Zaawansowana analityka
   - Wykresy trendów (Recharts)
   - Korelacje statystyk
   - Heatmapy wydajności
   - Predykcje modeli

7. **All Teams** - Przeglądarka wszystkich zespołów
   - Lista 30 zespołów NBA
   - Filtrowanie i sortowanie
   - Quick stats
   - Link do szczegółów

8. **Players Browser** - Baza graczy
   - Wyszukiwanie po imieniu/zespole
   - Statystyki per-gracz
   - Forma (ostatnie N gier)
   - Propsy dostępne

**Technologie Frontend:**
- React 18.3.1
- TypeScript 5.5.3
- Vite 7.3.0 (build tool)
- Tailwind CSS 3.4.1 (styling)
- Lucide React (ikony)
- Recharts 2.10.0 (wykresy)
- Vitest 4.0.16 (testing)

---

## 🛠️ Stack technologiczny

### Backend

| Technologia | Wersja | Zastosowanie |
|-------------|--------|--------------|
| **Python** | 3.11+ | Język główny |
| **FastAPI** | 0.109.0 | Framework webowy (async/await) |
| **Uvicorn** | 0.25.0 | ASGI server |
| **Pydantic** | 2.5.3 | Walidacja danych |
| **Supabase** | 2.7.4 | Klient PostgreSQL |
| **APScheduler** | 3.10.4 | Harmonogram zadań |
| **httpx** | 0.27.0 | Async HTTP client |
| **aiohttp** | 3.9.1 | Dodatkowy async HTTP |
| **BeautifulSoup4** | 4.12.2 | Web scraping |
| **lxml** | 4.9.4 | Parser XML/HTML |
| **nba-api** | 1.4.1 | Oficjalne API NBA Stats |
| **pandas** | 2.1.4 | Analiza danych |
| **numpy** | 1.26.2 | Obliczenia numeryczne |
| **pytz** | 2023.3 | Strefy czasowe |
| **pytest** | 7.4.4 | Testing framework |

### Frontend

| Technologia | Wersja | Zastosowanie |
|-------------|--------|--------------|
| **React** | 18.3.1 | UI Framework |
| **TypeScript** | 5.5.3 | Type safety |
| **Vite** | 7.3.0 | Build tool + dev server |
| **Tailwind CSS** | 3.4.1 | Utility-first CSS |
| **Lucide React** | 0.344.0 | Icon library |
| **Recharts** | 2.10.0 | Wykresy i wizualizacje |
| **Vitest** | 4.0.16 | Unit testing |
| **@testing-library/react** | 14.1.2 | Component testing |

### Database

| Technologia | Zastosowanie |
|-------------|--------------|
| **Supabase (PostgreSQL)** | Główna baza danych |
| **PostgreSQL 15+** | Silnik bazy danych |
| **Row Level Security** | Bezpieczeństwo na poziomie wiersza |
| **Triggers** | Automatyczne updated_at |
| **Indexes** | Optymalizacja zapytań |
| **Migrations** | Kontrola wersji schematu |

### DevOps & Infrastructure

| Technologia | Zastosowanie |
|-------------|--------------|
| **Docker** | Konteneryzacja |
| **Docker Compose** | Orkiestracja kontenerów |
| **Nginx** | Reverse proxy (produkcja) |
| **Caddy** | Alternative reverse proxy |
| **PM2** | Process manager (Node.js) |
| **GitHub Actions** | CI/CD (optional) |

### Zewnętrzne API

| Serwis | Plan | Limity | Koszt |
|--------|------|--------|-------|
| **NBA Stats API** | Free | ~1000 req/dzień | $0 |
| **The Odds API** | Free Tier | 500 req/miesiąc | $0 |
| **Basketball-Reference** | Web scraping | Rate limited | $0 |
| **Supabase** | Free Tier | 500 MB DB, 2 GB bandwidth | $0 |

---

## 📁 Struktura projektu

```
NBA-Prawilne/
│
├── 📂 backend/                         # Backend Python (FastAPI)
│   ├── 📂 api/                         # API Layer (8 modułów routingu)
│   │   ├── __init__.py                 # Router exports
│   │   ├── routes_teams.py             # GET /api/teams
│   │   ├── routes_games.py             # GET /api/games/today
│   │   ├── routes_odds.py              # GET /api/odds/{game_id}
│   │   ├── routes_value_board.py       # GET /api/value-board/today
│   │   ├── routes_picks.py             # GET/POST /api/picks
│   │   ├── routes_performance.py       # GET /api/performance
│   │   ├── routes_reports.py           # GET /api/reports/{type}
│   │   ├── routes_uploads_stub.py      # POST /api/uploads
│   │   └── README.md                   # Dokumentacja API
│   │
│   ├── 📂 providers/                   # Provider Layer (4 providery)
│   │   ├── base.py                     # Interfejs BaseProvider
│   │   ├── nba_stats.py                # NBA Stats API provider
│   │   ├── odds_api.py                 # The Odds API provider
│   │   └── basketball_reference.py     # Web scraping provider
│   │
│   ├── 📂 services/                    # Service Layer (10 serwisów)
│   │   ├── betting_math.py             # Matematyka zakładowa
│   │   ├── quality_gates.py            # System bramek jakości
│   │   ├── analytics_service.py        # Analityka zespołów/graczy
│   │   ├── clv_service.py              # Closing Line Value
│   │   ├── budget_service.py           # Kontrola budżetu API
│   │   ├── sync_service.py             # Orkiestracja providerów
│   │   ├── report_service.py           # Generowanie raportów
│   │   ├── value_service.py            # Identyfikacja wartości
│   │   ├── odds_service.py             # Zarządzanie kursami
│   │   └── betting_stats_service.py    # Statystyki zakładów
│   │
│   ├── 📄 main.py                      # FastAPI app (legacy, stara wersja)
│   ├── 📄 main_new.py                  # FastAPI app (nowa architektura)
│   ├── 📄 settings.py                  # Konfiguracja (Pydantic Settings)
│   ├── 📄 models.py                    # Modele Pydantic
│   ├── 📄 db.py                        # Klient Supabase (singleton)
│   ├── 📄 scrapers.py                  # Scrapery danych (legacy)
│   ├── 📄 reports.py                   # Generator raportów (legacy)
│   ├── 📄 analytics.py                 # Funkcje analityczne
│   ├── 📄 requirements.txt             # Zależności Python
│   ├── 📄 Dockerfile                   # Docker image backend
│   ├── 📄 test_betting_math.py         # Testy jednostkowe (25 testów)
│   └── 📄 README.md                    # Dokumentacja backend
│
├── 📂 src/                             # Frontend React + TypeScript
│   ├── 📂 components/                  # Komponenty React
│   │   ├── Dashboard.tsx               # Główny dashboard
│   │   ├── Header.tsx                  # Header z nawigacją
│   │   ├── Sidebar.tsx                 # Boczne menu
│   │   ├── LoginScreen.tsx             # Ekran logowania
│   │   ├── ReportsSection.tsx          # Przeglądarka raportów
│   │   ├── AllTeams.tsx                # Lista wszystkich zespołów
│   │   ├── BettingRecommendations.tsx  # Rekomendacje zakładów
│   │   ├── LiveOdds.tsx                # Kursy na żywo
│   │   ├── PlayersBrowser.tsx          # Baza graczy
│   │   ├── Analytics.tsx               # Zaawansowana analityka
│   │   ├── BullsAnalysis.tsx           # Analiza Bulls
│   │   └── ValueBoard.tsx              # Zakłady wartościowe
│   │
│   ├── 📂 services/                    # Serwisy API
│   │   ├── api.ts                      # Główny klient API
│   │   └── auth.ts                     # Autentykacja
│   │
│   ├── 📂 types/                       # Typy TypeScript
│   │   └── index.ts                    # Definicje typów
│   │
│   ├── 📂 i18n/                        # Internacjonalizacja
│   │   ├── translations.ts             # Tłumaczenia (PL/EN)
│   │   └── useI18n.ts                  # Hook i18n
│   │
│   ├── 📂 tests/                       # Testy frontend
│   │   └── *.test.tsx                  # Testy komponentów
│   │
│   ├── 📄 App.tsx                      # Główny komponent aplikacji
│   ├── 📄 main.tsx                     # Entry point (Vite)
│   └── 📄 vite-env.d.ts                # Typy Vite
│
├── 📂 supabase/                        # Database schemas & migrations
│   ├── 📂 migrations/                  # Migracje SQL
│   │   ├── 001_create_teams_table.sql
│   │   ├── 002_create_games_table.sql
│   │   ├── 003_create_odds_table.sql
│   │   ├── 011_add_betting_platform_tables.sql  # Nowa architektura
│   │   └── ...
│   └── 📄 README.md                    # Dokumentacja bazy danych
│
├── 📂 deploy/                          # Konfiguracje deployment
│   ├── docker-compose.yml              # Docker Compose (Linux)
│   ├── docker-compose.windows.yml      # Docker Compose (Windows)
│   ├── docker-compose.pi4.yml          # Docker Compose (Raspberry Pi)
│   ├── Dockerfile.frontend.nginx       # Frontend + Nginx
│   ├── Dockerfile.frontend.caddy       # Frontend + Caddy
│   ├── Caddyfile                       # Konfiguracja Caddy
│   ├── nginx.conf                      # Konfiguracja Nginx
│   └── README.md                       # Instrukcje deployment
│
├── 📂 scripts/                         # Skrypty pomocnicze
│   ├── 📂 deploy/                      # Skrypty deployment
│   │   ├── deploy.sh                   # Deploy Linux/macOS
│   │   └── deploy.bat                  # Deploy Windows
│   ├── 📂 setup/                       # Skrypty setup
│   │   ├── setup-ubuntu.sh
│   │   └── setup-pi4.sh
│   └── 📄 README.md                    # Dokumentacja skryptów
│
├── 📂 docs/                            # Dokumentacja szczegółowa
│   ├── API_DOCUMENTATION.md            # Dokumentacja API
│   ├── ARCHITECTURE.md                 # Architektura systemu
│   ├── QUALITY_GATES.md                # System bramek jakości
│   ├── BETTING_MATH.md                 # Matematyka zakładowa
│   └── README.md                       # Indeks dokumentacji
│
├── 📂 logs/                            # Logi aplikacji (gitignored)
├── 📂 dist/                            # Build frontend (gitignored)
├── 📂 node_modules/                    # Zależności Node.js (gitignored)
│
├── 📄 .env                             # Zmienne środowiskowe (gitignored)
├── 📄 .env.example                     # Przykład .env
├── 📄 .gitignore                       # Git ignore rules
├── 📄 docker-compose.yml               # Docker Compose główny
├── 📄 Dockerfile                       # Dockerfile główny
├── 📄 package.json                     # Zależności Node.js
├── 📄 tsconfig.json                    # Konfiguracja TypeScript
├── 📄 vite.config.ts                   # Konfiguracja Vite
├── 📄 tailwind.config.js               # Konfiguracja Tailwind
├── 📄 eslint.config.js                 # Konfiguracja ESLint
├── 📄 vitest.config.ts                 # Konfiguracja Vitest
│
├── 📄 setup.sh / setup.bat             # Automatyczna instalacja
├── 📄 start.sh / start.bat             # Uruchomienie aplikacji
├── 📄 stop.sh / stop.bat               # Zatrzymanie aplikacji
│
├── 📄 README.md                        # Ten plik
├── 📄 INSTALLATION_GUIDE.md            # Szczegółowa instalacja
├── 📄 DEPLOYMENT.md                    # Przewodnik deployment
├── 📄 PROJECT_STATUS.md                # Status projektu
├── 📄 IMPLEMENTATION_SUMMARY.md        # Podsumowanie implementacji
├── 📄 QUICKSTART_WINDOWS.md            # Szybki start Windows
├── 📄 WINDOWS_SETUP.md                 # Setup Windows
└── 📄 RASPBERRY_PI_SETUP.md            # Setup Raspberry Pi
```

### Kluczowe pliki i ich role:

**Backend Core:**
- `main_new.py` - Główna aplikacja FastAPI z nową architekturą providerów
- `settings.py` - Centralna konfiguracja z walidacją Pydantic
- `models.py` - Modele danych (Team, Player, Game, Pick, Report, etc.)
- `db.py` - Singleton klient Supabase

**Frontend Core:**
- `src/App.tsx` - Root component z routingiem i stanem globalnym
- `src/main.tsx` - Entry point Vite
- `src/services/api.ts` - Abstrakcja wywołań API

**Database:**
- `supabase/migrations/*.sql` - Migracje schematu bazy danych
- Najważniejsza: `011_add_betting_platform_tables.sql` (nowa architektura)

**Configuration:**
- `.env` - Zmienne środowiskowe (API keys, database URLs)
- `package.json` - Zależności Node.js i skrypty NPM
- `requirements.txt` - Zależności Python

---

## 🚀 Szybki start

### Opcja 1: Automatyczna instalacja (Zalecana)

**Windows:**
```cmd
# 1. Klonuj repozytorium
git clone https://github.com/Nawigante81/NBA-Prawilne.git
cd NBA-Prawilne

# 2. Uruchom automatyczną instalację
setup.bat

# 3. Skonfiguruj klucze API w .env
notepad .env

# 4. Uruchom aplikację
start.bat
```

**Linux/macOS:**
```bash
# 1. Klonuj repozytorium
git clone https://github.com/Nawigante81/NBA-Prawilne.git
cd NBA-Prawilne

# 2. Uruchom automatyczną instalację
chmod +x setup.sh start.sh stop.sh
./setup.sh

# 3. Skonfiguruj klucze API w .env
nano .env

# 4. Uruchom aplikację
./start.sh
```

### Opcja 2: Docker Deployment

**Wszystkie platformy:**
```bash
# 1. Klonuj repozytorium
git clone https://github.com/Nawigante81/NBA-Prawilne.git
cd NBA-Prawilne

# 2. Skonfiguruj .env
cp .env.example .env
# Edytuj .env z kluczami API

# 3. Uruchom Docker Compose
docker-compose up -d

# 4. Sprawdź logi
docker-compose logs -f

# 5. Zatrzymaj
docker-compose down
```

### Dostęp do aplikacji

Po uruchomieniu:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Health Check**: http://localhost:8000/health

---

## ⚙️ Instalacja i konfiguracja

### Wymagania systemowe

**Minimalne:**
- **System operacyjny**: Windows 10/11, Ubuntu 20.04+, macOS 11+, lub Raspberry Pi 4 (ARM64)
- **RAM**: 2 GB (4 GB zalecane)
- **Procesor**: Dual-core 2.0 GHz+
- **Dysk**: 2 GB wolnego miejsca
- **Internet**: Stabilne połączenie dla API calls

**Software (bez Docker):**
- **Node.js** 18.0+ ([nodejs.org](https://nodejs.org/))
- **Python** 3.11+ ([python.org](https://www.python.org/))
- **Git** ([git-scm.com](https://git-scm.com/))

**Software (z Docker):**
- **Docker** 20.10+ ([docker.com](https://www.docker.com/))
- **Docker Compose** 2.0+ (zazwyczaj w pakiecie z Docker Desktop)

### Krok 1: Klonowanie repozytorium

```bash
git clone https://github.com/Nawigante81/NBA-Prawilne.git
cd NBA-Prawilne
```

### Krok 2: Konfiguracja zmiennych środowiskowych

Utwórz plik `.env` na podstawie przykładu:

```bash
cp .env.example .env
```

Edytuj `.env` i uzupełnij wymagane wartości:

```bash
# =================================================================
# SUPABASE DATABASE
# =================================================================
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# =================================================================
# THE ODDS API
# =================================================================
VITE_ODDS_API_KEY=your-odds-api-key-here
ODDS_API_BUDGET_DAILY=10

# =================================================================
# OPTIONAL - QUALITY GATES THRESHOLDS
# =================================================================
QG_EV_THRESHOLD=2.0
QG_EDGE_THRESHOLD=3.0
QG_CONFIDENCE_THRESHOLD=0.55
QG_MIN_TEAM_GAMES=5
QG_MIN_PLAYER_GAMES=3

# =================================================================
# OPTIONAL - ADMIN API KEY
# =================================================================
ADMIN_API_KEY=your-secret-admin-key-change-this
```

### Krok 3: Rejestracja kont i pozyskanie API keys

#### A. Supabase (Darmowe - wymagane)

1. Przejdź do [supabase.com](https://supabase.com)
2. Utwórz konto i nowy projekt
3. Przejdź do **Settings** → **API**
4. Skopiuj:
   - **Project URL** → `VITE_SUPABASE_URL`
   - **anon public** key → `VITE_SUPABASE_ANON_KEY`
   - **service_role** key → `SUPABASE_SERVICE_ROLE_KEY`

5. Uruchom migracje bazy danych:
   - Przejdź do **SQL Editor** w Supabase Dashboard
   - Wykonaj wszystkie pliki SQL z folderu `supabase/migrations/` w kolejności
   - Lub użyj Supabase CLI: `supabase db push`

#### B. The Odds API (500 wywołań/miesiąc darmowo - wymagane)

1. Przejdź do [the-odds-api.com](https://the-odds-api.com)
2. Utwórz konto (email wystarczy)
3. Po weryfikacji email przejdź do **Dashboard**
4. Skopiuj **API Key** → `VITE_ODDS_API_KEY`
5. Monitor limitów: Dashboard pokazuje pozostałe wywołania

**Uwaga**: Plan darmowy to 500 wywołań/miesiąc. System domyślnie ustawia 10 wywołań/dzień (300/miesiąc) aby pozostawić bufor.

### Krok 4A: Instalacja bez Docker (Native)

#### Windows:

```cmd
# Uruchom automatyczny skrypt instalacji
setup.bat

# Skrypt wykona:
# - npm install (frontend dependencies)
# - python -m pip install -r backend/requirements.txt
# - skopiuje .env.example do .env (jeśli nie istnieje)

# Po zakończeniu:
start.bat
```

#### Linux/macOS:

```bash
# Nadaj uprawnienia wykonywania
chmod +x setup.sh start.sh stop.sh

# Uruchom instalację
./setup.sh

# Skrypt wykona:
# - npm install (frontend dependencies)
# - python3 -m venv backend/venv (opcjonalnie)
# - pip install -r backend/requirements.txt
# - skopiuje .env.example do .env (jeśli nie istnieje)

# Po zakończeniu:
./start.sh
```

### Krok 4B: Instalacja z Docker

```bash
# 1. Zbuduj obrazy
docker-compose build

# 2. Uruchom kontenery
docker-compose up -d

# 3. Sprawdź status
docker-compose ps

# Powinno pokazać:
# backend    running    0.0.0.0:8000->8000/tcp
# frontend   running    0.0.0.0:5173->5173/tcp

# 4. Sprawdź logi
docker-compose logs -f backend
docker-compose logs -f frontend

# 5. Zatrzymanie
docker-compose down

# 6. Zatrzymanie z usunięciem danych
docker-compose down -v
```

### Krok 5: Weryfikacja instalacji

**Sprawdź Backend:**
```bash
# Health check
curl http://localhost:8000/health

# Expected output:
# {"status":"ok","timestamp":"2026-01-22T12:00:00Z","supabase_connected":true}

# API Documentation
# Otwórz przeglądarkę: http://localhost:8000/docs
```

**Sprawdź Frontend:**
```bash
# Otwórz przeglądarkę: http://localhost:5173
# Powinien załadować się dashboard z logowaniem
```

**Sprawdź Database:**
```sql
-- W Supabase SQL Editor:
SELECT COUNT(*) FROM teams;
-- Powinno zwrócić 30 (zespoły NBA)

SELECT COUNT(*) FROM games;
-- Powinno zwrócić dzisiejsze gry

SELECT COUNT(*) FROM odds_snapshots;
-- Powinno zwrócić kursy jeśli są mecze dzisiaj
```

### Troubleshooting instalacji

**Problem: "Python nie znaleziony"**
```bash
# Windows: Zainstaluj Python z python.org
# - Zaznacz "Add Python to PATH"
# - Restart terminala

# Linux/Ubuntu:
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# macOS:
brew install python@3.11
```

**Problem: "Node.js nie znaleziony"**
```bash
# Windows: Zainstaluj z nodejs.org
# - Wybierz LTS version
# - Restart terminala

# Linux/Ubuntu:
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# macOS:
brew install node@18
```

**Problem: "Port zajęty"**
```bash
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/macOS:
lsof -ti:8000 | xargs kill -9
lsof -ti:5173 | xargs kill -9
```

**Problem: "Supabase connection failed"**
- Sprawdź czy klucze API w `.env` są poprawne
- Sprawdź czy projekt Supabase jest aktywny (nie wstrzymany)
- Sprawdź czy tabele zostały utworzone (uruchom migracje)

**Problem: "The Odds API 401 Unauthorized"**
- Sprawdź czy `VITE_ODDS_API_KEY` w `.env` jest poprawny
- Sprawdź czy email został zweryfikowany na the-odds-api.com
- Sprawdź czy nie wyczerpałeś limitu (500 wywołań/miesiąc)

### Struktura migracji bazy danych

Pliki SQL w `supabase/migrations/` (wykonaj w kolejności):

```sql
001_create_teams_table.sql           -- Tabela teams
002_create_games_table.sql           -- Tabela games
003_create_odds_table.sql            -- Tabela odds (legacy)
004_create_players_table.sql         -- Tabela players
005_create_team_game_stats.sql       -- Statystyki zespołowe per gra
006_create_player_game_stats.sql     -- Statystyki graczy per gra
...
011_add_betting_platform_tables.sql  -- Nowa architektura:
                                       - odds_snapshots (CLV tracking)
                                       - picks (rekomendacje)
                                       - pick_results (rozliczenia)
                                       - reports (codzienne raporty)
                                       - api_budget (kontrola budżetu)
                                       - api_cache (cache z TTL)
                                       - uploads_stub (metadata screenshotów)
```

**Aby wykonać migracje:**

**Opcja 1: Ręcznie w Supabase Dashboard**
```
1. Przejdź do supabase.com → twój projekt → SQL Editor
2. Otwórz każdy plik .sql z folderu supabase/migrations/
3. Skopiuj zawartość i wykonaj w kolejności (001 → 002 → ... → 011)
4. Sprawdź czy nie ma błędów w konsoli
```

**Opcja 2: Supabase CLI (zalecane dla zaawansowanych)**
```bash
# Zainstaluj Supabase CLI
npm install -g supabase

# Linkuj projekt
supabase link --project-ref your-project-ref

# Uruchom migracje
supabase db push

# Sprawdź status
supabase db status
```

---

## 🔌 API Endpoints

### 1. Health & Status

```http
GET /health
```
**Response:**
```json
{
  "status": "ok",
  "timestamp": "2026-01-22T12:00:00Z",
  "supabase_connected": true
}
```

```http
GET /api/status
```
**Response:**
```json
{
  "app_name": "NBA Analysis & Betting Platform",
  "version": "2.0.0",
  "providers": {
    "nba_stats": {"status": "healthy", "last_sync": "2026-01-22T11:30:00Z"},
    "odds_api": {"status": "healthy", "budget_remaining": 8},
    "basketball_ref": {"status": "healthy"}
  },
  "scheduler": {
    "running": true,
    "next_report": "2026-01-22T13:50:00-06:00"
  }
}
```

### 2. Teams

```http
GET /api/teams
```
**Description**: Pobranie wszystkich 30 zespołów NBA  
**Response:**
```json
[
  {
    "id": "uuid-here",
    "abbreviation": "CHI",
    "full_name": "Chicago Bulls",
    "name": "Bulls",
    "city": "Chicago",
    "created_at": "2026-01-20T10:00:00Z"
  },
  ...
]
```

### 3. Games

```http
GET /api/games/today
```
**Description**: Pobranie dzisiejszych gier NBA  
**Response:**
```json
[
  {
    "id": "game-id-uuid",
    "sport_key": "basketball_nba",
    "sport_title": "NBA",
    "commence_time": "2026-01-22T19:00:00-06:00",
    "home_team": "Chicago Bulls",
    "away_team": "Cleveland Cavaliers"
  },
  ...
]
```

### 4. Odds

```http
GET /api/odds/{game_id}
```
**Description**: Pobranie kursów dla konkretnej gry  
**Query params**:
- `bookmaker` (optional): Filtruj po bukmacherze (np. "draftkings")
- `market_type` (optional): Filtruj po rynku ("h2h", "spread", "totals")

**Response:**
```json
[
  {
    "id": "uuid",
    "game_id": "game-uuid",
    "bookmaker_key": "draftkings",
    "bookmaker_title": "DraftKings",
    "market_type": "spread",
    "team": "Chicago Bulls",
    "outcome_name": "Chicago Bulls",
    "point": -5.5,
    "price": -110,
    "last_update": "2026-01-22T18:45:00Z"
  },
  ...
]
```

```http
GET /api/line-movement/{game_id}
```
**Description**: Historia ruchów linii dla gry  
**Response:**
```json
{
  "game_id": "game-uuid",
  "movements": [
    {
      "timestamp": "2026-01-22T10:00:00Z",
      "bookmaker": "draftkings",
      "market": "spread",
      "line": -5.0,
      "odds": -110
    },
    {
      "timestamp": "2026-01-22T15:00:00Z",
      "bookmaker": "draftkings",
      "market": "spread",
      "line": -5.5,
      "odds": -110
    },
    ...
  ]
}
```

### 5. Value Board

```http
GET /api/value-board/today
```
**Description**: Zakłady wartościowe na dzisiaj (quality-gated)  
**Query params**:
- `min_ev` (optional): Minimalny EV w % (default: 2.0)
- `min_edge` (optional): Minimalny edge w % (default: 3.0)

**Response:**
```json
[
  {
    "game_id": "uuid",
    "game_info": "Thunder @ Rockets, 7:00 PM CT",
    "bet_type": "spread",
    "team": "Oklahoma City Thunder",
    "line": -5.0,
    "odds": -110,
    "bookmaker": "DraftKings",
    "ev_percent": 4.2,
    "edge_percent": 5.8,
    "confidence": 0.62,
    "kelly_stake": 1.2,
    "recommendation": "BET",
    "quality_gates_passed": true
  },
  {
    "game_info": "Bulls @ Cavaliers, 6:00 PM CT",
    "bet_type": "total",
    "line": "Under 224.5",
    "odds": -110,
    "bookmaker": "BetMGM",
    "ev_percent": 2.8,
    "edge_percent": 3.5,
    "confidence": 0.58,
    "kelly_stake": 0.7,
    "recommendation": "BET",
    "quality_gates_passed": true
  },
  {
    "game_info": "Celtics vs Heat, 6:30 PM CT",
    "bet_type": "h2h",
    "team": "Boston Celtics",
    "odds": -350,
    "bookmaker": "FanDuel",
    "ev_percent": 0.5,
    "recommendation": "NO BET",
    "quality_gates_passed": false,
    "failure_reasons": ["EV_TOO_LOW"]
  }
]
```

### 6. Picks

```http
GET /api/picks/today
```
**Description**: Rekomendacje zakładów na dzisiaj  
**Response:**
```json
[
  {
    "id": "uuid",
    "game_id": "game-uuid",
    "pick_type": "spread",
    "team": "Thunder",
    "line": -5.0,
    "odds": -110,
    "bookmaker": "draftkings",
    "stake_units": 1.2,
    "ev_percent": 4.2,
    "confidence": 0.62,
    "status": "pending",
    "created_at": "2026-01-22T11:00:00Z"
  },
  ...
]
```

```http
POST /api/picks/settle
```
**Description**: Rozliczenie zakładów (po zakończeniu gier)  
**Request Body:**
```json
{
  "pick_id": "uuid",
  "result": "win",  // "win" | "loss" | "push"
  "closing_odds": -110,
  "closing_line": -6.5
}
```
**Response:**
```json
{
  "id": "uuid",
  "result": "win",
  "profit_units": 1.09,
  "clv_percent": 30.0,
  "settled_at": "2026-01-22T21:30:00Z"
}
```

### 7. Performance

```http
GET /api/performance
```
**Description**: Metryki wydajności (ROI, CLV)  
**Query params**:
- `start_date` (optional): Format YYYY-MM-DD
- `end_date` (optional): Format YYYY-MM-DD
- `bet_type` (optional): "spread" | "total" | "h2h"

**Response:**
```json
{
  "period": {
    "start": "2026-01-01",
    "end": "2026-01-22"
  },
  "total_picks": 147,
  "wins": 82,
  "losses": 61,
  "pushes": 4,
  "win_rate": 0.574,
  "roi_percent": 8.2,
  "avg_clv_percent": 3.5,
  "total_units_wagered": 147.3,
  "total_units_profit": 12.1,
  "by_bet_type": {
    "spread": {"picks": 62, "win_rate": 0.581, "roi": 9.1},
    "total": {"picks": 58, "win_rate": 0.569, "roi": 7.8},
    "h2h": {"picks": 27, "win_rate": 0.556, "roi": 6.2}
  }
}
```

### 8. Reports

```http
GET /api/reports/750am
GET /api/reports/800am
GET /api/reports/1100am
```
**Description**: Codzienne raporty (750am, 800am, 1100am)  
**Query params**:
- `date` (optional): Format YYYY-MM-DD (default: today)

**Response:**
```json
{
  "report_type": "750am",
  "report_date": "2026-01-22",
  "generated_at": "2026-01-22T07:50:00-06:00",
  "content": {
    "results_vs_closing": [...],
    "top_trends": [...],
    "bulls_breakdown": [...],
    "risks": [...]
  }
}
```

### 9. Uploads (Screenshot Metadata)

```http
POST /api/uploads
```
**Description**: Upload metadata zrzutu ekranu kursów  
**Request Body (form-data):**
```
bookmaker: "draftkings"
upload_date: "2026-01-22"
notes: "Morning lines before game day"
```
**Response:**
```json
{
  "id": "uuid",
  "bookmaker": "draftkings",
  "upload_date": "2026-01-22",
  "uploaded_at": "2026-01-22T09:15:00Z"
}
```

---

## 📊 Źródła danych

### 1. NBA Stats API (Darmowe, bez rejestracji)

**URL**: `stats.nba.com` (przez bibliotekę `nba-api`)  
**Częstotliwość**: Co 12h (standardowo), co 6h (dni meczowe)  
**Cache**: 1h (scoreboard), 7 dni (gracze/zespoły)  
**Rate limit**: ~1000 wywołań/dzień (niemonitorowane przez NBA, ale przestrzegane)

**Dane pobierane:**
- **Zespoły**: ID, nazwa, miasto, skrót, konferencja, dywizja
- **Gracze**: ID, imię, nazwisko, pozycja, numer, zespół, status
- **Scoreboard**: Dzisiejsze/jutrzejsze gry z czasami rozpoczęcia
- **Team Game Stats**: OffRtg, DefRtg, Pace, FG%, 3PT%, FT%, AST, REB, TO
- **Player Game Stats**: PTS, REB, AST, STL, BLK, MIN, FG%, 3PT%

**Przykład wywołania:**
```python
from nba_api.stats.endpoints import scoreboard

# Pobranie dzisiejszych gier
board = scoreboard.Scoreboard()
games = board.get_dict()
```

### 2. The Odds API (500 wywołań/miesiąc darmowo)

**URL**: `https://api.the-odds-api.com`  
**Częstotliwość**: Co 12h (standardowo), co 6h (dni meczowe)  
**Budżet dzienny**: 10 wywołań/dzień (konfigurowalne w `.env`)  
**Bookmakerzy**: DraftKings, BetMGM, FanDuel (top 3, configurowalne)

**Dane pobierane:**
- **Moneyline (H2H)**: Kursy na wygraną każdego zespołu
- **Spread**: Handicap punktowy + kursy
- **Totals (O/U)**: Over/Under punktów całkowitych + kursy
- **Last update**: Timestamp ostatniej aktualizacji kursu

**Rynki** (market types):
- `h2h` - Head-to-head (moneyline)
- `spreads` - Point spreads
- `totals` - Over/Under total points

**Przykład wywołania:**
```bash
curl "https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?apiKey=YOUR_KEY&regions=us&markets=h2h,spreads,totals&bookmakers=draftkings,betmgm,fanduel"
```

**Response:**
```json
{
  "id": "game-id-uuid",
  "sport_key": "basketball_nba",
  "commence_time": "2026-01-22T19:00:00Z",
  "home_team": "Chicago Bulls",
  "away_team": "Cleveland Cavaliers",
  "bookmakers": [
    {
      "key": "draftkings",
      "title": "DraftKings",
      "last_update": "2026-01-22T18:45:00Z",
      "markets": [
        {
          "key": "h2h",
          "outcomes": [
            {"name": "Chicago Bulls", "price": 180},
            {"name": "Cleveland Cavaliers", "price": -220}
          ]
        },
        {
          "key": "spreads",
          "outcomes": [
            {"name": "Chicago Bulls", "price": -110, "point": 5.5},
            {"name": "Cleveland Cavaliers", "price": -110, "point": -5.5}
          ]
        },
        {
          "key": "totals",
          "outcomes": [
            {"name": "Over", "price": -110, "point": 224.5},
            {"name": "Under", "price": -110, "point": 224.5}
          ]
        }
      ]
    }
  ]
}
```

### 3. Basketball-Reference (Web scraping, uprzejmy)

**URL**: `https://www.basketball-reference.com`  
**Częstotliwość**: Raz dziennie (niski priorytet)  
**Rate limit**: 3 sekundy między zapytaniami, concurrency = 1  
**User agent**: Uprzejmy i identyfikowalny

**Dane pobierane:**
- **Składy zespołów** (rosters): Pełna lista graczy per zespół
- **Szczegółowe statystyki**: Per-game, per-36, advanced metrics
- **Kontuzje** (injury reports): Status graczy (OUT, QUESTIONABLE, DOUBTFUL)
- **Historyczne wyniki**: Box scores, play-by-play (opcjonalnie)

**Przykład scraping:**
```python
import requests
from bs4 import BeautifulSoup
import time

url = "https://www.basketball-reference.com/teams/CHI/2026.html"
response = requests.get(url, headers={"User-Agent": "NBA-Prawilne/2.0"})
soup = BeautifulSoup(response.content, 'lxml')

# Parse table roster
roster_table = soup.find('table', {'id': 'roster'})
players = []
for row in roster_table.find_all('tr')[1:]:  # Skip header
    cols = row.find_all(['th', 'td'])
    player = {
        'number': cols[0].text,
        'name': cols[1].text,
        'position': cols[2].text,
        'height': cols[3].text,
        'weight': cols[4].text
    }
    players.append(player)

time.sleep(3)  # Polite delay
```

### Polityka rate limiting i cachowania

**Wbudowane mechanizmy:**

1. **Budget Service** (`budget_service.py`)
   - Śledzi dzienne limity per provider
   - Auto-reset o północy
   - Blokuje wywołania po przekroczeniu limitu
   - Zapisuje w `api_budget` table

2. **API Cache** (`api_cache` table)
   - Cache z TTL (Time-To-Live)
   - Content hash deduplikacja
   - Automatyczne wygasanie
   - Oszczędność API calls

3. **Exponential Backoff**
   - Przy błędach 429 (rate limit)
   - Przy błędach 5xx (server error)
   - Maksymalnie 3 retry
   - Delay: 1s, 2s, 4s

**Konfiguracja limitów** (w `.env`):
```bash
# The Odds API
ODDS_API_BUDGET_DAILY=10

# NBA Stats API
NBA_STATS_BUDGET_DAILY=1000
NBA_STATS_MAX_CONCURRENT=2

# Basketball-Reference
BBALL_REF_DELAY_SECONDS=3
BBALL_REF_MAX_CONCURRENT=1
```

---

## 🔄 Przepływ danych (Data Flow)

### Startup Flow

```
1. APPLICATION START
   │
   ├─► Initialize Supabase client
   │   └─► Connect to PostgreSQL database
   │
   ├─► Load configuration from .env
   │   ├─► Validate API keys
   │   ├─► Set quality gate thresholds
   │   └─► Set budget limits
   │
   ├─► Initialize HTTP clients
   │   ├─► httpx async client (timeout: 30s)
   │   └─► User agents rotation
   │
   ├─► Initialize Providers
   │   ├─► NBA Stats Provider
   │   ├─► Odds API Provider
   │   └─► Basketball-Reference Provider
   │
   ├─► Run STARTUP SYNC (Sequential)
   │   │
   │   ├─► [1] Sync Teams
   │   │   ├─► Fetch from NBA Stats API
   │   │   ├─► Normalize data
   │   │   └─► Upsert to `teams` table (30 teams)
   │   │
   │   ├─► [2] Sync Players
   │   │   ├─► For each team: Fetch roster
   │   │   ├─► Normalize data
   │   │   └─► Upsert to `players` table (~450 players)
   │   │
   │   ├─► [3] Sync Games
   │   │   ├─► Fetch today + tomorrow from NBA Stats
   │   │   ├─► Normalize data
   │   │   └─► Upsert to `games` table
   │   │
   │   └─► [4] Sync Odds (Budget-aware)
   │       ├─► Check budget remaining
   │       ├─► If budget OK: Fetch from The Odds API
   │       ├─► Normalize data
   │       ├─► Deduplicate by content hash
   │       ├─► Upsert to `odds_snapshots` table
   │       └─► Increment budget counter
   │
   ├─► Initialize Scheduler (APScheduler)
   │   ├─► Add job: 750am Report (CronTrigger)
   │   ├─► Add job: 800am Report (CronTrigger)
   │   ├─► Add job: 1100am Report (CronTrigger)
   │   └─► Add job: 12h Sync (IntervalTrigger)
   │
   └─► Start FastAPI Server
       ├─► CORS middleware
       ├─► Basic auth middleware
       ├─► Mount routers (8 modules)
       └─► Listen on 0.0.0.0:8000

2. APPLICATION RUNNING
   │
   ├─► Handle HTTP requests (API endpoints)
   │
   ├─► Execute scheduled jobs
   │   ├─► 7:50 AM CT: Generate 750am report
   │   ├─► 8:00 AM CT: Generate 800am report
   │   ├─► 11:00 AM CT: Generate 1100am report
   │   └─► Every 12h: Sync all data
   │
   └─► Monitor provider health
       ├─► Health checks every 5 minutes
       └─► Log warnings if unhealthy

3. APPLICATION SHUTDOWN
   │
   ├─► Graceful shutdown scheduler
   ├─► Close HTTP clients
   ├─► Close database connections
   └─► Exit
```

### Report Generation Flow

```
TRIGGER: Scheduler fires at 7:50 AM / 8:00 AM / 11:00 AM CT

1. FETCH DATA
   │
   ├─► Focus teams (9 teams)
   │   └─► Query `teams` WHERE abbreviation IN (...)
   │
   ├─► Recent games (last 7-10 days)
   │   └─► Query `games` WHERE commence_time > NOW() - INTERVAL '10 days'
   │
   ├─► Team game stats (last 10 games per team)
   │   └─► Query `team_game_stats` JOIN games
   │
   ├─► Player game stats (last 5 games per player)
   │   └─► Query `player_game_stats` JOIN players JOIN games
   │
   ├─► Odds snapshots
   │   └─► Query `odds_snapshots` WHERE game_id IN (...)
   │
   └─► Pick results (for CLV)
       └─► Query `pick_results` WHERE pick_date >= NOW() - INTERVAL '7 days'

2. COMPUTE ANALYTICS
   │
   ├─► Team trends (7-day rolling averages)
   │   ├─► Pace, OffRtg, DefRtg
   │   ├─► 3PT%, FT%, eFG%
   │   └─► ATS, O/U performance
   │
   ├─► Player form (last 5 games)
   │   ├─► PTS, REB, AST averages
   │   ├─► Minutes per game
   │   └─► Role classification (starter/bench)
   │
   ├─► Bulls detailed breakdown
   │   ├─► Per-player stats
   │   ├─► Position matchups
   │   └─► Injury status
   │
   └─► Betting opportunities
       ├─► Value bets identification
       ├─► EV calculation
       ├─► Kelly stake sizing
       └─► Quality gates validation

3. GENERATE REPORT CONTENT
   │
   ├─► 750AM Report
   │   ├─► Results vs closing line (yesterday)
   │   ├─► Top 3 trendy teams
   │   ├─► Bulls player breakdown
   │   └─► Risks for today
   │
   ├─► 800AM Report
   │   ├─► Yesterday summary (focus teams)
   │   ├─► 7-day trends
   │   ├─► Bulls current form
   │   ├─► Betting leans (2-3)
   │   └─► Upload reminder
   │
   └─► 1100AM Report
       ├─► Today's slate (games, times, injuries)
       ├─► Matchup notes
       ├─► Bulls game sheet
       ├─► Quality-gated parlays
       │   ├─► General parlay (3-5 legs)
       │   ├─► Bulls parlay (2-5 legs)
       │   └─► Conservative singles
       └─► Game day risks

4. QUALITY GATES (for betting proposals)
   │
   ├─► For each potential bet:
   │   ├─► ✓ Odds available & recent?
   │   ├─► ✓ Closing line exists?
   │   ├─► ✓ Sample size sufficient?
   │   ├─► ✓ Stats fresh?
   │   ├─► ✓ Market quality OK?
   │   ├─► ✓ EV above threshold?
   │   ├─► ✓ Edge sufficient?
   │   ├─► ✓ Confidence adequate?
   │   └─► ✓ (Parlay-specific gates)
   │
   └─► Result:
       ├─► All passed → Include in report with "BET"
       └─► Any failed → Exclude or mark "NO BET" with reason

5. SAVE REPORT
   │
   ├─► Insert into `reports` table
   │   ├─► report_type: "750am" | "800am" | "1100am"
   │   ├─► report_date: TODAY
   │   ├─► content: JSON with all data
   │   └─► generated_at: TIMESTAMP
   │
   └─► Log success/failure

6. SERVE VIA API
   │
   └─► GET /api/reports/{type}?date=YYYY-MM-DD
       └─► Return report from database
```

### Betting Lifecycle Flow

```
1. VALUE IDENTIFICATION
   │
   ├─► Query today's games
   ├─► Query latest odds (last 12h)
   ├─► Calculate implied probability
   ├─► Estimate "true" probability (model/heuristic)
   ├─► Calculate Expected Value (EV)
   └─► Calculate Edge

2. QUALITY GATES
   │
   ├─► Run all 13+ validation checks
   └─► Result: PASS or FAIL with reasons

3. PICK GENERATION (if PASS)
   │
   ├─► Calculate Kelly stake
   ├─► Create pick record
   ├─► Insert into `picks` table
   │   ├─► game_id, pick_type, team, line, odds
   │   ├─► stake_units (Kelly)
   │   ├─► ev_percent, confidence
   │   └─► status: "pending"
   │
   └─► Include in Value Board API response

4. ODDS SNAPSHOT (for CLV)
   │
   ├─► At pick time: Record odds snapshot
   │   └─► Insert into `odds_snapshots`
   │       ├─► game_id, bookmaker, market_type
   │       ├─► line, odds, timestamp
   │       └─► content_hash (dedupe)
   │
   └─► Before game: Record closing line snapshot
       └─► Last snapshot before commence_time

5. GAME COMPLETION
   │
   ├─► Fetch final score
   ├─► Determine pick result: "win" | "loss" | "push"
   ├─► Fetch closing line from last snapshot
   ├─► Calculate profit/loss in units
   └─► Calculate CLV

6. SETTLEMENT
   │
   └─► POST /api/picks/settle
       ├─► Update pick status to "settled"
       └─► Insert into `pick_results`
           ├─► pick_id, result, profit_units
           ├─► closing_odds, closing_line
           ├─► clv_percent
           └─► settled_at: TIMESTAMP

7. PERFORMANCE TRACKING
   │
   └─► GET /api/performance
       ├─► Query all `pick_results`
       ├─► Calculate ROI
       ├─► Calculate average CLV
       ├─► Calculate win rate
       └─► Group by bet type, date, etc.
```

---

## 🚢 Deployment

### Opcja 1: Docker (Zalecane dla produkcji)

**Przygotowanie:**
```bash
# 1. Sklonuj repo
git clone https://github.com/Nawigante81/NBA-Prawilne.git
cd NBA-Prawilne

# 2. Skonfiguruj .env
cp .env.example .env
nano .env  # Uzupełnij API keys

# 3. Zbuduj obrazy
docker-compose build

# 4. Uruchom kontenery
docker-compose up -d

# 5. Sprawdź logi
docker-compose logs -f

# 6. Sprawdź status
docker-compose ps

# 7. Dostęp
# Frontend: http://localhost:5173
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**Docker Compose warianty:**
```bash
# Standard Linux/macOS
docker-compose -f docker-compose.yml up -d

# Windows
docker-compose -f deploy/docker-compose.windows.yml up -d

# Raspberry Pi 4 (ARM64)
docker-compose -f deploy/docker-compose.pi4.yml up -d
```

**Aktualizacja:**
```bash
# 1. Zatrzymaj kontenery
docker-compose down

# 2. Pobierz najnowszy kod
git pull origin main

# 3. Przebuduj obrazy
docker-compose build

# 4. Uruchom ponownie
docker-compose up -d
```

### Opcja 2: PM2 (Node.js process manager)

**Instalacja PM2:**
```bash
npm install -g pm2
```

**Konfiguracja ecosystem file** (`ecosystem.config.js`):
```javascript
module.exports = {
  apps: [
    {
      name: 'nba-backend',
      cwd: './backend',
      script: 'python',
      args: '-m uvicorn main_new:app --host 0.0.0.0 --port 8000',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production'
      }
    },
    {
      name: 'nba-frontend',
      script: 'npm',
      args: 'run preview',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M'
    }
  ]
};
```

**Deployment:**
```bash
# 1. Zbuduj frontend
npm run build

# 2. Uruchom PM2
pm2 start ecosystem.config.js

# 3. Sprawdź status
pm2 status

# 4. Logi
pm2 logs

# 5. Zatrzymaj
pm2 stop all

# 6. Restart
pm2 restart all

# 7. Auto-start przy reboot
pm2 startup
pm2 save
```

### Opcja 3: Systemd Service (Linux)

**Backend service** (`/etc/systemd/system/nba-backend.service`):
```ini
[Unit]
Description=NBA Analysis Backend
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser/NBA-Prawilne/backend
Environment="PATH=/home/youruser/NBA-Prawilne/backend/venv/bin"
ExecStart=/home/youruser/NBA-Prawilne/backend/venv/bin/python -m uvicorn main_new:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Frontend service** (`/etc/systemd/system/nba-frontend.service`):
```ini
[Unit]
Description=NBA Analysis Frontend
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser/NBA-Prawilne
ExecStart=/usr/bin/npm run preview
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Aktywacja:**
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable nba-backend
sudo systemctl enable nba-frontend

# Start services
sudo systemctl start nba-backend
sudo systemctl start nba-frontend

# Check status
sudo systemctl status nba-backend
sudo systemctl status nba-frontend

# Logi
sudo journalctl -u nba-backend -f
sudo journalctl -u nba-frontend -f
```

### Nginx Reverse Proxy (Produkcja z SSL)

**Konfiguracja** (`/etc/nginx/sites-available/nba-prawilne`):
```nginx
server {
    listen 80;
    server_name nba.yourdomain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend health check
    location /health {
        proxy_pass http://localhost:8000/health;
    }

    # API docs
    location /docs {
        proxy_pass http://localhost:8000/docs;
    }
}
```

**Aktywacja:**
```bash
# Link config
sudo ln -s /etc/nginx/sites-available/nba-prawilne /etc/nginx/sites-enabled/

# Test config
sudo nginx -t

# Reload
sudo systemctl reload nginx
```

**SSL z Let's Encrypt:**
```bash
# Zainstaluj certbot
sudo apt install certbot python3-certbot-nginx

# Uzyskaj certyfikat
sudo certbot --nginx -d nba.yourdomain.com

# Auto-renewal (już skonfigurowany)
sudo certbot renew --dry-run
```

### Cloud Deployment (opcje)

**1. Railway.app**
```bash
# Zainstaluj Railway CLI
npm install -g @railway/cli

# Login
railway login

# Init project
railway init

# Deploy
railway up
```

**2. Render.com**
- Połącz GitHub repo
- Configure:
  - Backend: Python 3.11, `uvicorn main_new:app --host 0.0.0.0 --port $PORT`
  - Frontend: Node 18, `npm run build && npm run preview`
- Dodaj zmienne środowiskowe
- Deploy

**3. Fly.io**
```bash
# Zainstaluj Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Launch app
fly launch

# Deploy
fly deploy
```

---

## 🧪 Rozwój i testy

### Lokalne środowisko deweloperskie

**Backend development:**
```bash
cd backend

# Utwórz virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Zainstaluj zależności
pip install -r requirements.txt

# Uruchom z auto-reload
uvicorn main_new:app --reload --host 0.0.0.0 --port 8000

# W drugim terminalu: watch logi
tail -f logs/backend.log
```

**Frontend development:**
```bash
# Zainstaluj zależności
npm install

# Uruchom dev server z HMR
npm run dev

# W drugim terminalu: watch type checking
npm run typecheck -- --watch
```

### Uruchamianie testów

**Backend tests (pytest):**
```bash
cd backend

# Uruchom wszystkie testy
pytest

# Testy z verbose output
pytest -v

# Tylko testy betting_math
pytest test_betting_math.py -v

# Z coverage
pytest --cov=. --cov-report=html

# Otwórz raport coverage
open htmlcov/index.html
```

**Frontend tests (Vitest):**
```bash
# Watch mode (interactive)
npm run test

# CI mode (run once)
npm run test:run

# Z coverage
npm run test:coverage

# UI mode (browser-based)
npm run test:ui
```

### Linting i formatowanie

**Backend (Python):**
```bash
cd backend

# Flake8 (linting)
flake8 --max-line-length=100 --exclude=venv,__pycache__

# Black (formatting)
black --line-length=100 *.py services/ providers/ api/

# isort (import sorting)
isort --profile=black *.py services/ providers/ api/
```

**Frontend (TypeScript/React):**
```bash
# ESLint (linting)
npm run lint

# Fix auto-fixable issues
npm run lint -- --fix

# Type checking
npm run typecheck
```

### Struktura testów

```
backend/
├── test_betting_math.py         # 25 testów matematyki zakładowej
├── test_imports.py              # Test importów modułów
├── test_main.py                 # Testy endpointów API
├── test_consensus.py            # Testy logiki konsensusu
└── test_betting_stats_logic.py  # Testy statystyk

src/
└── tests/
    ├── Dashboard.test.tsx       # Testy komponentu Dashboard
    ├── BullsAnalysis.test.tsx   # Testy Bulls analysis
    └── ...                      # Inne testy komponentów
```

### Debugging

**Backend (Python debugger):**
```python
# W kodzie:
import pdb; pdb.set_trace()

# Lub z ipdb (lepszy):
import ipdb; ipdb.set_trace()

# Uruchom z debuggerem:
python -m pdb -m uvicorn main_new:app
```

**Frontend (Chrome DevTools):**
```javascript
// W kodzie:
debugger;

// Lub:
console.log('Debug:', variable);
```

**VSCode Launch Configuration** (`.vscode/launch.json`):
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["main_new:app", "--reload"],
      "cwd": "${workspaceFolder}/backend",
      "env": {"PYTHONPATH": "${workspaceFolder}/backend"}
    },
    {
      "name": "Node: Vite",
      "type": "node",
      "request": "launch",
      "runtimeExecutable": "npm",
      "runtimeArgs": ["run", "dev"],
      "console": "integratedTerminal"
    }
  ]
}
```

---

## 🔧 Troubleshooting

### Problem: Backend nie startuje

**Symptom**: `ModuleNotFoundError` lub `ImportError`

**Rozwiązanie:**
```bash
cd backend
pip install -r requirements.txt --upgrade

# Jeśli nadal błąd:
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
```

### Problem: Frontend nie kompiluje

**Symptom**: TypeScript errors, `Cannot find module`

**Rozwiązanie:**
```bash
# Usuń node_modules i lock file
rm -rf node_modules package-lock.json

# Reinstaluj
npm install

# Clear cache
npm cache clean --force
npm install
```

### Problem: Brak połączenia z Supabase

**Symptom**: `401 Unauthorized` lub `Connection refused`

**Rozwiązanie:**
1. Sprawdź czy projekt Supabase jest aktywny (nie paused)
2. Sprawdź czy klucze w `.env` są aktualne
3. Sprawdź czy IP nie jest zablokowane (Supabase → Settings → API → Auth)
4. Test connection:
```bash
curl -X GET "https://your-project.supabase.co/rest/v1/teams" \
  -H "apikey: your-anon-key" \
  -H "Authorization: Bearer your-anon-key"
```

### Problem: The Odds API limit wyczerpany

**Symptom**: `429 Too Many Requests` lub budget alert

**Rozwiązanie:**
1. Sprawdź pozostały budżet: GET `/api/status`
2. Zmniejsz częstotliwość sync: Edytuj harmonogram w `main_new.py`
3. Zwiększ limit dzienny w `.env`: `ODDS_API_BUDGET_DAILY=20`
4. Upgraduj plan na the-odds-api.com (płatny)

### Problem: Raporty się nie generują

**Symptom**: `GET /api/reports/750am` zwraca 404 lub puste

**Diagnosis:**
```bash
# Sprawdź czy harmonogram działa
docker-compose logs backend | grep "Scheduler"

# Sprawdź czy jest raport w bazie
# W Supabase SQL Editor:
SELECT * FROM reports WHERE report_type = '750am' ORDER BY generated_at DESC LIMIT 5;
```

**Rozwiązanie:**
1. Sprawdź timezone: System musi być w `America/Chicago` lub `US/Central`
2. Sprawdź czy APScheduler jest aktywny: Logi backend powinny pokazać "Scheduler started"
3. Ręcznie trigger: POST `/api/reports/generate/750am` (jeśli endpoint dostępny)

### Problem: Quality Gates zawsze failują

**Symptom**: Value Board zawsze pusty lub wszystkie "NO BET"

**Diagnosis:**
```bash
# Sprawdź progi w .env
cat .env | grep QG_

# Sprawdź logi quality gates
docker-compose logs backend | grep "Quality Gate"
```

**Rozwiązanie:**
1. Obniż progi w `.env`:
```bash
QG_EV_THRESHOLD=1.0       # Z 2.0
QG_EDGE_THRESHOLD=1.5     # Z 3.0
QG_MIN_TEAM_GAMES=3       # Z 5
```
2. Restart backend
3. Sprawdź ponownie Value Board

### Problem: Docker kontener crashuje

**Symptom**: `docker-compose ps` pokazuje status `Restarting` lub `Exited`

**Diagnosis:**
```bash
# Sprawdź logi
docker-compose logs backend --tail=100

# Sprawdź exit code
docker-compose ps
```

**Rozwiązanie:**
1. Sprawdź .env (brakujące zmienne)
2. Sprawdź ports (8000, 5173 wolne)
3. Zwiększ memory limit w docker-compose.yml:
```yaml
services:
  backend:
    mem_limit: 2g
    mem_reservation: 1g
```

---

## 🗺️ Roadmap

### W trakcie (Q1 2026)
- [x] Implementacja nowej architektury providerów
- [x] System jakości danych (quality gates)
- [x] Śledzenie CLV
- [x] Trzy codzienne raporty
- [ ] Frontend dashboard z Value Board
- [ ] Email notifications dla raportów

### Planowane (Q2 2026)
- [ ] Automatyczne rozliczanie picks po zakończeniu gier
- [ ] Machine learning model dla estymacji prawdopodobieństwa
- [ ] Backtesting framework dla strategii
- [ ] Więcej bookmakerów (Pinnacle, Circa, BetOnline)
- [ ] Player props analysis (PTS, REB, AST O/U)
- [ ] Live betting integration

### Długoterminowe (Q3-Q4 2026)
- [ ] Mobile app (React Native)
- [ ] Telegram bot z alertami
- [ ] Rozszerzenie na inne ligi (NFL, MLB, NHL)
- [ ] Public API dla użytkowników
- [ ] Community marketplace strategii
- [ ] SaaS model (subskrypcje)

### Ulepszenia techniczne
- [ ] Redis cache dla performance
- [ ] PostgreSQL full-text search
- [ ] GraphQL API (alternative to REST)
- [ ] Kubernetes deployment
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Prometheus + Grafana monitoring
- [ ] Sentry error tracking
- [ ] Rate limiting per user

---

## 📚 Dokumentacja dodatkowa

**Szczegółowe przewodniki:**
- [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) - Pełna instrukcja instalacji
- [DEPLOYMENT.md](DEPLOYMENT.md) - Przewodnik deployment produkcyjny
- [QUICKSTART_WINDOWS.md](QUICKSTART_WINDOWS.md) - Szybki start dla Windows
- [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md) - Setup na Raspberry Pi 4
- [WINDOWS_SETUP.md](WINDOWS_SETUP.md) - Szczegółowy setup Windows

**Dokumentacja techniczna:**
- [backend/README.md](backend/README.md) - Dokumentacja backend API
- [backend/api/README.md](backend/api/README.md) - Dokumentacja endpointów
- [docs/README.md](docs/README.md) - Indeks dokumentacji

**Status i podsumowania:**
- [PROJECT_STATUS.md](PROJECT_STATUS.md) - Status projektu
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Podsumowanie implementacji
- [REPOSITORY_ORGANIZATION.md](REPOSITORY_ORGANIZATION.md) - Organizacja repozytorium

---

## 🤝 Wsparcie i kontakt

### Zgłaszanie problemów

Jeśli napotkasz problem:
1. Sprawdź sekcję [Troubleshooting](#-troubleshooting)
2. Sprawdź [Issues](https://github.com/Nawigante81/NBA-Prawilne/issues) czy problem już został zgłoszony
3. Utwórz nowy Issue z:
   - Opisem problemu
   - Krokami do reprodukcji
   - Logami (backend/frontend)
   - Wersją systemu operacyjnego
   - Wersją Python/Node.js

### Wsparcie techniczne

- **Discord**: [Link do serwera] (jeśli istnieje)
- **Email**: [kontakt@email.com]
- **GitHub Discussions**: [Link do discussions]

### Contributing

Chcesz współtworzyć projekt? Świetnie!
1. Fork repozytorium
2. Utwórz branch dla feature (`git checkout -b feature/AmazingFeature`)
3. Commit zmian (`git commit -m 'Add some AmazingFeature'`)
4. Push do brancha (`git push origin feature/AmazingFeature`)
5. Otwórz Pull Request

---

## ⚖️ Licencja

**Proprietary - NBA Analysis System**

Ten projekt jest własnością prywatną i jest dostarczony wyłącznie do celów edukacyjnych i analitycznych.

**Zastrzeżenia prawne:**
- System nie stanowi porady finansowej ani zachęty do hazardu
- Użytkowanie na własną odpowiedzialność
- Obstawiaj odpowiedzialnie i zgodnie z lokalnymi przepisami
- Dane z zewnętrznych API podlegają ich warunkom użytkowania

**Warunki użytkowania zewnętrznych API:**
- NBA Stats API: [stats.nba.com/terms](https://www.nba.com/termsofuse)
- The Odds API: [the-odds-api.com/terms](https://the-odds-api.com/terms)
- Basketball-Reference: Uprzejmy web scraping z rate limiting

---

## 🎓 Credits

**Autor projektu**: Nawigante81  
**Repozytorium**: [https://github.com/Nawigante81/NBA-Prawilne](https://github.com/Nawigante81/NBA-Prawilne)

**Wykorzystane biblioteki open source:**
- [FastAPI](https://fastapi.tiangolo.com/) - Sebastian Ramirez
- [React](https://react.dev/) - Meta Platforms, Inc.
- [Supabase](https://supabase.com/) - Supabase, Inc.
- [nba-api](https://github.com/swar/nba_api) - Swar Patel
- [The Odds API](https://the-odds-api.com/) - The Odds API
- [Basketball-Reference](https://www.basketball-reference.com/) - Sports Reference LLC

**Szczególne podziękowania:**
- Społeczności NBA analytics za inspirację
- Contributorom wszystkich wykorzystanych bibliotek
- Beta testerom systemu

---

## 📊 Statystyki projektu

- **Linie kodu**: ~20,000+ (Python + TypeScript)
- **Pliki źródłowe**: 80+
- **Komponenty React**: 15+
- **Endpointy API**: 25+
- **Testy jednostkowe**: 25+ (backend), rozbudowa w toku (frontend)
- **Tabele bazy danych**: 12+
- **Supportowane platformy**: Windows, Linux, macOS, Raspberry Pi 4
- **Deployment options**: Docker, PM2, Systemd, Cloud (Railway/Render/Fly.io)

---

<div align="center">

**🏀 NBA-Prawilne - Profesjonalna platforma analityczna NBA 🏀**

Zbudowano z ❤️ dla społeczności NBA analytics

[⬆ Powrót do góry](#-nba-analysis--betting-intelligence-platform)

</div>
