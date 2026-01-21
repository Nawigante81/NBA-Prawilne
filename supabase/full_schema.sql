-- Full schema for NBA Analytics (teams, games, odds, players, player_game_stats)
-- Safe to run multiple times (uses IF NOT EXISTS where possible)

-- TEAMS
CREATE TABLE IF NOT EXISTS public.teams (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  abbreviation text UNIQUE NOT NULL,
  full_name text NOT NULL,
  name text NOT NULL,
  city text,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_teams_abbreviation ON public.teams(abbreviation);

-- GAMES
CREATE TABLE IF NOT EXISTS public.games (
  id text PRIMARY KEY,
  sport_key text,
  sport_title text,
  commence_time timestamptz NOT NULL,
  home_team text NOT NULL,
  away_team text NOT NULL,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_games_commence_time ON public.games(commence_time);

-- ODDS
CREATE TABLE IF NOT EXISTS public.odds (
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

CREATE INDEX IF NOT EXISTS idx_odds_game_id ON public.odds(game_id);
CREATE INDEX IF NOT EXISTS idx_odds_bookmaker_key ON public.odds(bookmaker_key);
CREATE INDEX IF NOT EXISTS idx_odds_market_type ON public.odds(market_type);

-- PLAYERS
CREATE TABLE IF NOT EXISTS public.players (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  player_id bigint,
  jersey_number integer,
  team_id uuid REFERENCES public.teams(id) ON DELETE SET NULL,
  team_abbreviation text NOT NULL,
  position text,
  height text,
  weight integer,
  age integer,
  birth_date date,
  experience integer,
  college text,
  basketball_reference_id text UNIQUE,
  basketball_reference_url text,
  is_active boolean DEFAULT true,
  season_year text DEFAULT '2024-25',
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  UNIQUE(name, team_abbreviation, season_year)
);

CREATE INDEX IF NOT EXISTS idx_players_team_id ON public.players(team_id);
CREATE INDEX IF NOT EXISTS idx_players_team_abbreviation ON public.players(team_abbreviation);
CREATE INDEX IF NOT EXISTS idx_players_name ON public.players(name);
CREATE INDEX IF NOT EXISTS idx_players_player_id ON public.players(player_id);
CREATE INDEX IF NOT EXISTS idx_players_basketball_reference_id ON public.players(basketball_reference_id);
CREATE INDEX IF NOT EXISTS idx_players_active ON public.players(is_active);
CREATE INDEX IF NOT EXISTS idx_players_season ON public.players(season_year);

CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_players_updated_at ON public.players;
CREATE TRIGGER update_players_updated_at
  BEFORE UPDATE ON public.players
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();

-- PLAYER GAME STATS (HISTORICAL)
CREATE TABLE IF NOT EXISTS public.player_game_stats (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  season_year text NOT NULL,
  game_date date NOT NULL,
  game_id text NOT NULL,
  matchup text NOT NULL,
  team_id bigint NOT NULL,
  team_city text,
  team_name text,
  team_tricode text NOT NULL,
  team_slug text,
  player_id bigint NOT NULL,
  player_name text NOT NULL,
  position text,
  jersey_num integer,
  comment text,
  minutes text,
  field_goals_made integer DEFAULT 0,
  field_goals_attempted integer DEFAULT 0,
  field_goals_percentage numeric(5,3),
  three_pointers_made integer DEFAULT 0,
  three_pointers_attempted integer DEFAULT 0,
  three_pointers_percentage numeric(5,3),
  free_throws_made integer DEFAULT 0,
  free_throws_attempted integer DEFAULT 0,
  free_throws_percentage numeric(5,3),
  rebounds_offensive integer DEFAULT 0,
  rebounds_defensive integer DEFAULT 0,
  rebounds_total integer DEFAULT 0,
  assists integer DEFAULT 0,
  steals integer DEFAULT 0,
  blocks integer DEFAULT 0,
  turnovers integer DEFAULT 0,
  fouls_personal integer DEFAULT 0,
  points integer DEFAULT 0,
  plus_minus_points integer,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_player_game_stats_game_id ON public.player_game_stats(game_id);
CREATE INDEX IF NOT EXISTS idx_player_game_stats_player_id ON public.player_game_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_player_game_stats_game_date ON public.player_game_stats(game_date);
CREATE INDEX IF NOT EXISTS idx_player_game_stats_team_tricode ON public.player_game_stats(team_tricode);
CREATE INDEX IF NOT EXISTS idx_player_game_stats_player_date ON public.player_game_stats(player_id, game_date);
CREATE INDEX IF NOT EXISTS idx_player_game_stats_season_year ON public.player_game_stats(season_year);

-- Prevent duplicates on historical data imports
CREATE UNIQUE INDEX IF NOT EXISTS uq_player_game_stats_game_player
ON public.player_game_stats (game_id, player_id);

-- RLS and policies for historical stats
ALTER TABLE public.player_game_stats ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Enable read access for all users'
      AND tablename = 'player_game_stats'
  ) THEN
    CREATE POLICY "Enable read access for all users" ON public.player_game_stats
      FOR SELECT USING (true);
  END IF;
END
$$;

-- REPORTS (optional persistence for generated reports)
CREATE TABLE IF NOT EXISTS public.reports (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  report_type text NOT NULL,
  content jsonb NOT NULL,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_reports_report_type ON public.reports(report_type);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON public.reports(created_at);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Enable insert for service role only'
      AND tablename = 'player_game_stats'
  ) THEN
    CREATE POLICY "Enable insert for service role only" ON public.player_game_stats
      FOR INSERT WITH CHECK (auth.role() = 'service_role');
  END IF;
END
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Enable update for service role only'
      AND tablename = 'player_game_stats'
  ) THEN
    CREATE POLICY "Enable update for service role only" ON public.player_game_stats
      FOR UPDATE USING (auth.role() = 'service_role');
  END IF;
END
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Enable delete for service role only'
      AND tablename = 'player_game_stats'
  ) THEN
    CREATE POLICY "Enable delete for service role only" ON public.player_game_stats
      FOR DELETE USING (auth.role() = 'service_role');
  END IF;
END
$$;
