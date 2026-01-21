# 🚀 Advanced Analytics Features

## Przegląd

Projekt został rozszerzony o 4 zaawansowane funkcje analityczne wykorzystujące dane historyczne NBA (2010-2024):

1. **Prop Bet Predictor** - Predykcja zakładów na statystyki graczy
2. **Matchup Analyzer** - Analiza matchupów drużyn i graczy
3. **Form Tracker** - Śledzenie formy graczy z trendami
4. **Injury Impact Analyzer** - Analiza wpływu kontuzji na wyniki

---

## 1. 🎯 Prop Bet Predictor

### Funkcjonalność
Analizuje zakłady na statystyki graczy (prop bets) na podstawie danych historycznych i wskazuje czy dane jest wartość w zakładzie OVER/UNDER.

### Parametry
- `player_name` - Imię i nazwisko gracza
- `stat_type` - Typ statystyki: `points`, `rebounds_total`, `assists`, `three_pointers_made`, `steals`, `blocks`
- `line` - Linia zakładu (np. 24.5)
- `games` - Liczba meczy do analizy (domyślnie 20)
- `opponent` - Opcjonalnie: kod przeciwnika (np. "LAL")

### API Endpoint
```
GET /api/analytics/prop-bet?player_name=Zach LaVine&stat_type=points&line=24.5&games=20&opponent=LAL
```

### Przykładowa odpowiedź
```json
{
  "player": "Zach LaVine",
  "stat_type": "points",
  "line": 24.5,
  "prediction": 26.3,
  "hit_rate": 75.0,
  "value": "OVER",
  "confidence": 75.0,
  "trend": 8.5,
  "sample_size": 20,
  "recommendation": "LEAN OVER. Avg 26.3 vs 24.5. 75.0% hit rate.",
  "recent_games": [28, 31, 22, 25, 29, 24, 27, 30, 23, 26],
  "vs_opponent": {
    "games": 5,
    "avg": 28.4,
    "high": 35,
    "low": 22,
    "over_rate": 80.0
  }
}
```

### Interpretacja
- **Value**: `OVER`, `UNDER`, lub `NO VALUE`
- **Confidence**: 0-100% (>75% = STRONG, 60-75% = LEAN)
- **Hit Rate**: % meczy gdzie gracz przeszedł linię
- **Trend**: Czy forma idzie w górę (+) czy w dół (-)

### Strategia użycia
1. **STRONG OVER/UNDER (confidence >75%)**: Rozważ zakład
2. **LEAN (confidence 60-75%)**: Mniejsza stawka lub skip
3. **NO VALUE**: Skip - za blisko 50/50

---

## 2. 🏀 Matchup Analyzer

### Funkcjonalność
Analizuje historyczne matchupy między drużynami lub graczami vs konkretnym przeciwnikiem.

### A) Team Matchup Analysis

#### Endpoint
```
GET /api/analytics/matchup/team?team=CHI&opponent=LAL&seasons_back=3
```

#### Przykładowa odpowiedź
```json
{
  "team": "CHI",
  "opponent": "LAL",
  "total_games": 12,
  "home_games": 6,
  "away_games": 6,
  "averages": {
    "points": 108.5,
    "rebounds": 45.2,
    "assists": 24.3
  },
  "home_away_split": {
    "home_ppg": 112.3,
    "away_ppg": 104.7,
    "home_advantage": 7.6
  },
  "recent_games": [...]
}
```

### B) Player Matchup Analysis

#### Endpoint
```
GET /api/analytics/matchup/player?player_name=Zach LaVine&opponent=LAL&seasons_back=3
```

#### Przykładowa odpowiedź
```json
{
  "player": "Zach LaVine",
  "opponent": "LAL",
  "games_played": 8,
  "averages": {
    "points": 28.4,
    "rebounds": 4.8,
    "assists": 5.2
  },
  "highs": {
    "points": 38,
    "rebounds": 8,
    "assists": 9
  },
  "recent_games": [...]
}
```

### Zastosowania
- Identyfikacja korzystnych matchupów dla graczy
- Home/away advantage analysis
- Przygotowanie do konkretnego meczu

---

## 3. 📈 Form Tracker

### Funkcjonalność
Śledzi formę gracza z rolling averages (średnie kroczące) i trendami. Wizualizuje dane na wykresie.

### Endpoint
```
GET /api/analytics/form?player_name=Zach LaVine&games=15
```

### Przykładowa odpowiedź
```json
{
  "player": "Zach LaVine",
  "games_analyzed": 15,
  "current_averages": {
    "points": 25.3,
    "rebounds": 4.8,
    "assists": 4.2
  },
  "trend": {
    "direction": "IMPROVING",
    "percentage": 12.5,
    "description": "Points up 12.5% over last 15 games"
  },
  "games": [
    {
      "game_num": 1,
      "date": "2024-03-15",
      "opponent": "LAL",
      "actual_points": 28,
      "rolling_avg_points": 25.4,
      "minutes": "35:22"
    }
    // ... więcej meczy
  ],
  "last_5_games": {
    "points": 27.8,
    "rebounds": 5.2,
    "assists": 4.6
  }
}
```

### Features
- **Rolling Average**: 5-game rolling average pokazuje trend
- **Trend Direction**: IMPROVING, DECLINING, STABLE
- **Visual Chart**: Wykres liniowy z Recharts
- **Comparison**: Last 5 games vs overall average

### Zastosowania
- Identyfikacja graczy "na fali"
- Spot declining form (unikaj zakładów)
- Timing zakładów (kupuj wysoko, sprzedawaj nisko)

---

## 4. 🚑 Injury Impact Analyzer

### Funkcjonalność
Analizuje jak wypadnięcie kluczowego gracza wpływa na team performance i innych graczy (beneficjenci).

### Endpoint
```
GET /api/analytics/injury-impact?team=CHI&missing_player=Zach LaVine&seasons_back=2
```

### Przykładowa odpowiedź
```json
{
  "missing_player": "Zach LaVine",
  "team": "CHI",
  "with_player": {
    "avg_team_points": 112.5,
    "games": 45
  },
  "without_player": {
    "avg_team_points": 105.3,
    "games": 12
  },
  "team_impact": {
    "points_difference": -7.2,
    "description": "Team scores 7.2 less points without Zach LaVine"
  },
  "beneficiaries": [
    {
      "player": "DeMar DeRozan",
      "avg_with_player": 24.2,
      "avg_without_player": 28.7,
      "increase": 4.5,
      "percent_increase": 18.6
    },
    {
      "player": "Coby White",
      "avg_with_player": 12.3,
      "avg_without_player": 16.8,
      "increase": 4.5,
      "percent_increase": 36.6
    }
  ],
  "sample_size": {
    "games_with": 45,
    "games_without": 12
  }
}
```

### Zastosowania
- **Prop Bets**: Gdy gracz wypadnie, obstawiaj beneficjentów OVER
- **Team Totals**: Adjust expectations dla team scoring
- **Usage Rate**: Kto przejmuje shots/usage?

### Przykład strategii
Gdy Zach LaVine OUT:
- ✅ DeMar DeRozan Points OVER (historycznie +4.5 ppg)
- ✅ Coby White Points OVER (historycznie +4.5 ppg, +36%)
- ❌ Bulls Team Total może być niższy

---

## 🎨 Frontend Components

### PropBetAnalyzer.tsx
- Formularz input (player, stat, line, opponent)
- Kolorowe wyniki (zielony OVER, czerwony UNDER)
- Recent games visualization
- Confidence meter

### FormTracker.tsx
- **Wykres liniowy** (Recharts) showing trends
- **Rolling averages** (5-game)
- Tabela ostatnich meczy
- Stat selector (Points/Rebounds/Assists)

### Integracja w aplikacji
Dodaj do głównego dashboard:

```tsx
import { PropBetAnalyzer } from './components/PropBetAnalyzer';
import { FormTracker } from './components/FormTracker';

// W App.tsx lub Dashboard.tsx
<div className="space-y-6">
  <PropBetAnalyzer />
  <FormTracker />
  {/* Inne komponenty */}
</div>
```

---

## 🔧 Instalacja i Setup

### 1. Zainstaluj zależności
```bash
npm install recharts
```

### 2. Zaimportuj dane historyczne
```bash
cd backend
python import_historical_data.py
```

### 3. Uruchom backend
```bash
cd backend
uvicorn main:app --reload
```

### 4. Uruchom frontend
```bash
npm run dev
```

---

## 📊 Wymagania

### Backend
- ✅ Python 3.8+
- ✅ FastAPI
- ✅ Supabase z danymi historycznymi (424k wierszy)
- ✅ Moduł `analytics.py`

### Frontend
- ✅ React 18+
- ✅ TypeScript
- ✅ Recharts 2.10+
- ✅ Lucide React (icons)
- ✅ Tailwind CSS

---

## 🎯 Use Cases

### Dla Bulls fan (Chicago Bulls focus)
1. **Przed meczem Bulls vs LAL:**
   - Sprawdź matchup: `CHI vs LAL` historycznie
   - Sprawdź formę: `Zach LaVine` form tracker
   - Prop bet: `DeMar DeRozan points` vs linia 24.5

2. **Gdy Lonzo Ball OUT:**
   - Injury Impact: `CHI without Lonzo Ball`
   - Zobacz beneficjentów (np. Coby White usage)
   - Obstawiaj OVER na beneficjentów

### Dla ogólnych zakładów NBA
1. **Value hunting:**
   - Prop Bet Predictor na wielu graczy
   - Szukaj STRONG OVER/UNDER (confidence >75%)
   
2. **Matchup edges:**
   - Player vs weak defense (np. Trae Young vs Portland)
   - Team in favorable matchup

3. **Trend following:**
   - Form Tracker: gracze IMPROVING = OVER
   - Form Tracker: gracze DECLINING = UNDER

---

## 🚀 Przyszłe rozszerzenia

Możliwe dodatkowe funkcje:
- **ML Predictions**: Machine learning model na 424k danych
- **Optimal Parlay Builder**: Automatyczne budowanie parlay
- **Line Movement Tracker**: Śledzenie zmian kursów
- **Bet Performance Tracking**: ROI calculator
- **Email Notifications**: Alerty o value betach
- **Discord Bot**: Automatyczne posty z rekomendacjami

---

## 📚 Dokumentacja API

Pełna dokumentacja API dostępna pod:
```
http://localhost:8000/docs
```

Swagger UI z interaktywną dokumentacją wszystkich endpointów.

---

## ⚠️ Disclaimer

System służy celom edukacyjnym i analitycznym. Nie stanowi porady finansowej. Obstawiaj odpowiedzialnie i tylko jeśli jest to legalne w Twojej jurysdykcji.

---

**Gotowe! 🎉** Masz teraz profesjonalny system analityczny NBA z danymi historycznymi!
