-- ============================================
-- KOMPLETNA KONFIGURACJA BAZY DANYCH NBA
-- Wszystkie tabele: teams, games, odds, player_game_stats
-- Skopiuj i wklej cały kod do SQL Editor w Supabase
-- ============================================

-- 1. USUŃ STARE TABELE (jeśli istnieją)
DROP TABLE IF EXISTS public.player_game_stats CASCADE;
DROP TABLE IF EXISTS public.odds CASCADE;
DROP TABLE IF EXISTS public.games CASCADE;
DROP TABLE IF EXISTS public.teams CASCADE;

-- ============================================
-- 2. UTWÓRZ TABELE
-- ============================================

-- Tabela: teams (drużyny NBA)
CREATE TABLE public.teams (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  abbreviation text UNIQUE NOT NULL,
  full_name text NOT NULL,
  name text NOT NULL,
  city text,
  created_at timestamptz DEFAULT now()
);

-- Tabela: games (mecze NBA)
CREATE TABLE public.games (
  id text PRIMARY KEY,
  sport_key text,
  sport_title text,
  commence_time timestamptz NOT NULL,
  home_team text NOT NULL,
  away_team text NOT NULL,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Tabela: odds (kursy bukmacherskie)
CREATE TABLE public.odds (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  game_id text NOT NULL REFERENCES public.games(id) ON DELETE CASCADE,
  bookmaker_key text NOT NULL,
  bookmaker_title text,
  last_update timestamptz,
  market_type text NOT NULL,
  team text,
  outcome_name text,
  point numeric,
  price numeric,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Tabela: player_game_stats (historyczne statystyki graczy 2010-2024)
CREATE TABLE public.player_game_stats (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Game identifiers
  season_year text NOT NULL,
  game_date date NOT NULL,
  game_id text NOT NULL,
  matchup text NOT NULL,
  
  -- Team information
  team_id bigint NOT NULL,
  team_city text,
  team_name text,
  team_tricode text NOT NULL,
  team_slug text,
  
  -- Player information
  player_id bigint NOT NULL,
  player_name text NOT NULL,
  position text,
  jersey_num integer,
  
  -- Game participation
  comment text,
  minutes text,
  
  -- Shooting statistics
  field_goals_made integer DEFAULT 0,
  field_goals_attempted integer DEFAULT 0,
  field_goals_percentage numeric(5,3),
  three_pointers_made integer DEFAULT 0,
  three_pointers_attempted integer DEFAULT 0,
  three_pointers_percentage numeric(5,3),
  free_throws_made integer DEFAULT 0,
  free_throws_attempted integer DEFAULT 0,
  free_throws_percentage numeric(5,3),
  
  -- Rebounds
  rebounds_offensive integer DEFAULT 0,
  rebounds_defensive integer DEFAULT 0,
  rebounds_total integer DEFAULT 0,
  
  -- Other stats
  assists integer DEFAULT 0,
  steals integer DEFAULT 0,
  blocks integer DEFAULT 0,
  turnovers integer DEFAULT 0,
  fouls_personal integer DEFAULT 0,
  
  -- Scoring
  points integer DEFAULT 0,
  plus_minus_points integer,
  
  -- Metadata
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- ============================================
-- 3. UTWÓRZ INDEKSY
-- ============================================

-- Indeksy dla teams
CREATE INDEX idx_teams_abbreviation ON public.teams(abbreviation);

-- Indeksy dla games
CREATE INDEX idx_games_commence_time ON public.games(commence_time);

-- Indeksy dla odds
CREATE INDEX idx_odds_game_id ON public.odds(game_id);
CREATE INDEX idx_odds_bookmaker_key ON public.odds(bookmaker_key);
CREATE INDEX idx_odds_market_type ON public.odds(market_type);

-- Indeksy dla player_game_stats
CREATE INDEX idx_player_game_stats_game_id ON public.player_game_stats(game_id);
CREATE INDEX idx_player_game_stats_player_id ON public.player_game_stats(player_id);
CREATE INDEX idx_player_game_stats_game_date ON public.player_game_stats(game_date);
CREATE INDEX idx_player_game_stats_team_tricode ON public.player_game_stats(team_tricode);
CREATE INDEX idx_player_game_stats_player_date ON public.player_game_stats(player_id, game_date);
CREATE INDEX idx_player_game_stats_season_year ON public.player_game_stats(season_year);

-- ============================================
-- 4. WŁĄCZ RLS I USTAW POLITYKI (pełny dostęp)
-- ============================================

-- Włącz RLS dla wszystkich tabel
ALTER TABLE public.teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.games ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.odds ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.player_game_stats ENABLE ROW LEVEL SECURITY;

-- Polityki pełnego dostępu (uproszczone dla development)
CREATE POLICY "Allow all" ON public.teams FOR ALL USING (true);
CREATE POLICY "Allow all" ON public.games FOR ALL USING (true);
CREATE POLICY "Allow all" ON public.odds FOR ALL USING (true);
CREATE POLICY "Allow all" ON public.player_game_stats FOR ALL USING (true);

-- ============================================
-- 5. DODAJ 30 DRUŻYN NBA
-- ============================================

INSERT INTO public.teams (abbreviation, full_name, name, city) VALUES
  ('BOS', 'Boston Celtics', 'Celtics', 'Boston'),
  ('BKN', 'Brooklyn Nets', 'Nets', 'Brooklyn'),
  ('NYK', 'New York Knicks', 'Knicks', 'New York'),
  ('PHI', 'Philadelphia 76ers', '76ers', 'Philadelphia'),
  ('TOR', 'Toronto Raptors', 'Raptors', 'Toronto'),
  ('CHI', 'Chicago Bulls', 'Bulls', 'Chicago'),
  ('CLE', 'Cleveland Cavaliers', 'Cavaliers', 'Cleveland'),
  ('DET', 'Detroit Pistons', 'Pistons', 'Detroit'),
  ('IND', 'Indiana Pacers', 'Pacers', 'Indiana'),
  ('MIL', 'Milwaukee Bucks', 'Bucks', 'Milwaukee'),
  ('ATL', 'Atlanta Hawks', 'Hawks', 'Atlanta'),
  ('CHA', 'Charlotte Hornets', 'Hornets', 'Charlotte'),
  ('MIA', 'Miami Heat', 'Heat', 'Miami'),
  ('ORL', 'Orlando Magic', 'Magic', 'Orlando'),
  ('WAS', 'Washington Wizards', 'Wizards', 'Washington'),
  ('DEN', 'Denver Nuggets', 'Nuggets', 'Denver'),
  ('MIN', 'Minnesota Timberwolves', 'Timberwolves', 'Minnesota'),
  ('OKC', 'Oklahoma City Thunder', 'Thunder', 'Oklahoma City'),
  ('POR', 'Portland Trail Blazers', 'Trail Blazers', 'Portland'),
  ('UTA', 'Utah Jazz', 'Jazz', 'Utah'),
  ('GSW', 'Golden State Warriors', 'Warriors', 'Golden State'),
  ('LAC', 'Los Angeles Clippers', 'Clippers', 'Los Angeles'),
  ('LAL', 'Los Angeles Lakers', 'Lakers', 'Los Angeles'),
  ('PHX', 'Phoenix Suns', 'Suns', 'Phoenix'),
  ('SAC', 'Sacramento Kings', 'Kings', 'Sacramento'),
  ('DAL', 'Dallas Mavericks', 'Mavericks', 'Dallas'),
  ('HOU', 'Houston Rockets', 'Rockets', 'Houston'),
  ('MEM', 'Memphis Grizzlies', 'Grizzlies', 'Memphis'),
  ('NOP', 'New Orleans Pelicans', 'Pelicans', 'New Orleans'),
  ('SAS', 'San Antonio Spurs', 'Spurs', 'San Antonio');

-- ============================================
-- 6. DODAJ KOMENTARZE DO TABEL
-- ============================================

COMMENT ON TABLE public.teams IS 'NBA teams data - 30 teams with abbreviations and full names';
COMMENT ON TABLE public.games IS 'NBA games schedule and results - populated by API scraper';
COMMENT ON TABLE public.odds IS 'Betting odds from multiple bookmakers - populated by The Odds API';
COMMENT ON TABLE public.player_game_stats IS 'Historical NBA player game statistics (box scores) from 2010-2024 season - ~424k rows';

-- ============================================
-- 7. SPRAWDŹ INSTALACJĘ
-- ============================================

SELECT 
  'teams' as table_name, 
  COUNT(*) as row_count,
  'Drużyny NBA' as description
FROM public.teams
UNION ALL
SELECT 
  'games' as table_name, 
  COUNT(*) as row_count,
  'Mecze NBA (pusta - wypełni się przez API)' as description
FROM public.games
UNION ALL
SELECT 
  'odds' as table_name, 
  COUNT(*) as row_count,
  'Kursy bukmacherskie (pusta - wypełni się przez API)' as description
FROM public.odds
UNION ALL
SELECT 
  'player_game_stats' as table_name, 
  COUNT(*) as row_count,
  'Statystyki historyczne (pusta - import przez Python script)' as description
FROM public.player_game_stats
ORDER BY table_name;

-- ============================================
-- ✅ GOTOWE!
-- ============================================

/*
NASTĘPNE KROKI:

1. ✅ Uruchomiłeś ten SQL - tabele są gotowe
2. ⏳ Uzupełnij klucze API w pliku .env
3. ⏳ Uruchom backend - tabele games i odds wypełnią się automatycznie
4. ⏳ Uruchom: python backend/import_historical_data.py - zaimportuje dane historyczne

WERYFIKACJA:
- SELECT * FROM teams; → Powinno być 30 drużyn
- SELECT * FROM games; → Pusta (wypełni się przez scraper)
- SELECT * FROM odds; → Pusta (wypełni się przez scraper)
- SELECT * FROM player_game_stats; → Pusta (wypełni się przez import script)

Dokumentacja:
- HISTORICAL_DATA_IMPORT.md - Instrukcje importu danych historycznych
- SUPABASE_SETUP.md - Szczegółowa dokumentacja bazy danych
*/
