# 📊 Import danych historycznych NBA (2010-2024)

## Przegląd

Projekt zawiera **424,478 wierszy** danych historycznych NBA box score z sezonów 2010-2024. Dane te obejmują statystyki graczy z każdego meczu sezonu regularnego.

## 📦 Dane w projekcie

**Lokalizacja:** `nba historia/`

**Pliki:**
- `regular_season_box_scores_2010_2024_part_1.csv` (141,493 wierszy)
- `regular_season_box_scores_2010_2024_part_2.csv` (141,493 wierszy)
- `regular_season_box_scores_2010_2024_part_3.csv` (141,492 wierszy)

**Łącznie:** 424,478 wierszy danych

## 📋 Struktura danych

### Kolumny w CSV:

**Identyfikatory gry:**
- `season_year` - Sezon (np. "2023-24")
- `game_date` - Data meczu
- `gameId` - Unikalny ID meczu
- `matchup` - Matchup (np. "CHI @ LAL")

**Informacje o drużynie:**
- `teamId` - ID drużyny
- `teamCity` - Miasto (np. "Chicago")
- `teamName` - Nazwa (np. "Bulls")
- `teamTricode` - Kod 3-literowy (np. "CHI")
- `teamSlug` - Slug (np. "bulls")

**Informacje o graczu:**
- `personId` - ID gracza
- `personName` - Imię i nazwisko
- `position` - Pozycja
- `jerseyNum` - Numer koszulki

**Udział w grze:**
- `comment` - Komentarz (DNP, kontuzje, etc.)
- `minutes` - Minuty gry (format MM:SS)

**Statystyki rzutowe:**
- `fieldGoalsMade/Attempted/Percentage` - Rzuty z gry
- `threePointersMade/Attempted/Percentage` - Rzuty za 3
- `freeThrowsMade/Attempted/Percentage` - Rzuty wolne

**Zbiórki:**
- `reboundsOffensive` - Zbiórki ofensywne
- `reboundsDefensive` - Zbiórki defensywne
- `reboundsTotal` - Zbiórki łącznie

**Inne statystyki:**
- `assists` - Asysty
- `steals` - Przechwyty
- `blocks` - Bloki
- `turnovers` - Straty
- `foulsPersonal` - Faule osobiste
- `points` - Punkty
- `plusMinusPoints` - Plus/minus

---

## 🚀 Instrukcja importu (3 kroki)

### Krok 1: Utwórz tabelę w Supabase

1. **Otwórz plik:** `supabase/migrations/20251231141500_005_create_player_game_stats_table.sql`
2. **Zaloguj się do Supabase:** https://supabase.com/dashboard
3. **Wybierz swój projekt**
4. **Kliknij "SQL Editor"** w lewym menu
5. **Kliknij "New Query"**
6. **Skopiuj i wklej** całą zawartość pliku SQL
7. **Kliknij "Run"** (lub Ctrl+Enter)
8. ✅ Tabela `player_game_stats` została utworzona!

### Krok 2: Skonfiguruj klucze API

Upewnij się, że masz skonfigurowane klucze w pliku `.env`:

```env
VITE_SUPABASE_URL=https://twoj-projekt.supabase.co
VITE_SUPABASE_ANON_KEY=twoj-anon-key
SUPABASE_SERVICE_KEY=twoj-service-key  # Opcjonalnie, dla szybszego importu
```

### Krok 3: Uruchom import

```powershell
# Z katalogu głównego projektu
cd backend
python import_historical_data.py
```

**Import trwa około 5-10 minut** (zależy od szybkości połączenia).

---

## 📊 Schemat tabeli w bazie danych

```sql
CREATE TABLE player_game_stats (
  id uuid PRIMARY KEY,
  
  -- Game identifiers
  season_year text NOT NULL,
  game_date date NOT NULL,
  game_id text NOT NULL,
  matchup text NOT NULL,
  
  -- Team information
  team_id bigint NOT NULL,
  team_city text,
  team_name text,
  team_tricode text NOT NULL,  -- "CHI", "LAL", etc.
  team_slug text,
  
  -- Player information
  player_id bigint NOT NULL,
  player_name text NOT NULL,
  position text,
  jersey_num integer,
  
  -- Game participation
  comment text,
  minutes text,
  
  -- Statistics (all integer or numeric types)
  field_goals_made integer,
  field_goals_attempted integer,
  field_goals_percentage numeric(5,3),
  three_pointers_made integer,
  three_pointers_attempted integer,
  three_pointers_percentage numeric(5,3),
  free_throws_made integer,
  free_throws_attempted integer,
  free_throws_percentage numeric(5,3),
  rebounds_offensive integer,
  rebounds_defensive integer,
  rebounds_total integer,
  assists integer,
  steals integer,
  blocks integer,
  turnovers integer,
  fouls_personal integer,
  points integer,
  plus_minus_points integer,
  
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);
```

### Indeksy (dla szybkich zapytań):
- `game_id` - Wyszukiwanie po meczu
- `player_id` - Wyszukiwanie po graczu
- `game_date` - Zapytania czasowe
- `team_tricode` - Wyszukiwanie po drużynie
- `(player_id, game_date)` - Performance gracza w czasie
- `season_year` - Wyszukiwanie po sezonie

---

## 🔍 Przykładowe zapytania SQL

### 1. Najlepsze występy LeBrona Jamesa (ostatnie 10 meczy)

```sql
SELECT 
  game_date, 
  matchup, 
  points, 
  rebounds_total, 
  assists,
  minutes
FROM player_game_stats
WHERE player_name = 'LeBron James'
ORDER BY game_date DESC
LIMIT 10;
```

### 2. Statystyki Chicago Bulls w sezonie 2023-24

```sql
SELECT 
  player_name,
  COUNT(*) as games_played,
  AVG(points) as avg_points,
  AVG(rebounds_total) as avg_rebounds,
  AVG(assists) as avg_assists
FROM player_game_stats
WHERE team_tricode = 'CHI' 
  AND season_year = '2023-24'
GROUP BY player_name
HAVING COUNT(*) > 10
ORDER BY avg_points DESC;
```

### 3. Top 10 scorerów w historii (2010-2024)

```sql
SELECT 
  player_name,
  COUNT(*) as games,
  SUM(points) as total_points,
  AVG(points) as ppg
FROM player_game_stats
GROUP BY player_name
HAVING COUNT(*) > 100
ORDER BY total_points DESC
LIMIT 10;
```

### 4. Triple-double games

```sql
SELECT 
  game_date,
  player_name,
  team_tricode,
  matchup,
  points,
  rebounds_total,
  assists
FROM player_game_stats
WHERE points >= 10 
  AND rebounds_total >= 10 
  AND assists >= 10
ORDER BY game_date DESC
LIMIT 50;
```

### 5. Średnie statystyki gracza w ostatnich 5 meczach

```sql
SELECT 
  player_name,
  game_date,
  points,
  rebounds_total,
  assists,
  AVG(points) OVER (
    PARTITION BY player_name 
    ORDER BY game_date 
    ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
  ) as last_5_ppg
FROM player_game_stats
WHERE player_name = 'Zach LaVine'
  AND season_year = '2023-24'
ORDER BY game_date DESC;
```

---

## 🔗 Integracja z aplikacją

### Backend (Python/FastAPI)

Dodaj endpoint do `backend/main.py`:

```python
@app.get("/api/player-stats/{player_name}")
async def get_player_stats(player_name: str, limit: int = 10):
    """Get recent player statistics"""
    try:
        response = app.state.supabase.table('player_game_stats') \
            .select('*') \
            .eq('player_name', player_name) \
            .order('game_date', desc=True) \
            .limit(limit) \
            .execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Frontend (React/TypeScript)

```typescript
// src/types/index.ts
export interface PlayerGameStats {
  id: string;
  game_date: string;
  player_name: string;
  team_tricode: string;
  matchup: string;
  points: number;
  rebounds_total: number;
  assists: number;
  minutes: string;
  field_goals_percentage: number;
  three_pointers_made: number;
  // ... inne pola
}

// Komponent do wyświetlania statystyk
const PlayerStats: React.FC<{ playerName: string }> = ({ playerName }) => {
  const [stats, setStats] = useState<PlayerGameStats[]>([]);
  
  useEffect(() => {
    fetch(`http://localhost:8000/api/player-stats/${playerName}`)
      .then(res => res.json())
      .then(data => setStats(data));
  }, [playerName]);
  
  return (
    <div>
      {stats.map(stat => (
        <div key={stat.id}>
          <p>{stat.game_date}: {stat.points} PTS, {stat.rebounds_total} REB, {stat.assists} AST</p>
        </div>
      ))}
    </div>
  );
};
```

---

## 📈 Zastosowania w aplikacji

### 1. Analiza formy graczy
- Średnie z ostatnich 5/10/15 meczy
- Trendy (wzrost/spadek produktywności)
- Porównanie z sezonową średnią

### 2. Head-to-head matchups
- Jak gracz radzi sobie przeciwko konkretnej drużynie
- Historyczne występy na konkretnej arenie

### 3. Predykcje prop bets
- Historyczne PTS/REB/AST vs. aktualnych linii
- Identyfikacja value betów na podstawie formy

### 4. Bulls deep dive
- Analiza każdego gracza Bulls w czasie
- Rotacje i minuty w różnych sezonach
- Performance w home vs. away games

### 5. Advanced analytics
- True Shooting % trends
- Usage rate analysis
- Pace adjustments

---

## ⚠️ Uwagi techniczne

### Rozmiar danych:
- **424,478 wierszy** zajmuje ~150-200 MB w bazie PostgreSQL
- Import może potrwać **5-10 minut**
- Supabase Free Tier: limit 500 MB (wystarczający)

### Performance:
- Wszystkie indeksy są automatycznie tworzone
- Zapytania są zoptymalizowane
- Dla bardzo dużych zapytań użyj paginacji

### Rate limiting:
- Import używa batchy po 1000 wierszy
- Między batches jest delay 0.1s
- Zapobiega przekroczeniu limitów Supabase API

---

## 🐛 Troubleshooting

### Problem: "Tabela nie istnieje"
**Rozwiązanie:** Uruchom migrację SQL (Krok 1)

### Problem: "Rate limit exceeded"
**Rozwiązanie:** 
- Zmniejsz `batch_size` w skrypcie (np. do 500)
- Zwiększ delay między batches

### Problem: "Permission denied"
**Rozwiązanie:** 
- Użyj `SUPABASE_SERVICE_KEY` zamiast `ANON_KEY`
- Sprawdź polityki RLS w Supabase

### Problem: "Import bardzo wolny"
**Rozwiązanie:**
- Użyj `SUPABASE_SERVICE_KEY` (szybsze uprawnienia)
- Sprawdź połączenie internetowe
- Dla lokalnego developmentu rozważ Supabase CLI

---

## ✅ Weryfikacja po imporcie

```sql
-- Sprawdź liczbę wierszy
SELECT COUNT(*) FROM player_game_stats;
-- Oczekiwane: 424,478

-- Sprawdź zakres dat
SELECT MIN(game_date), MAX(game_date) FROM player_game_stats;
-- Oczekiwane: 2010-10-26 do 2024-04-14

-- Sprawdź unikalne sezony
SELECT DISTINCT season_year FROM player_game_stats ORDER BY season_year;
-- Oczekiwane: 14 sezonów (2010-11 do 2023-24)

-- Sprawdź top graczy
SELECT player_name, COUNT(*) as games 
FROM player_game_stats 
GROUP BY player_name 
ORDER BY games DESC 
LIMIT 10;
```

---

**Gotowe! 🎉** Masz teraz pełną historię NBA w swojej bazie danych!
