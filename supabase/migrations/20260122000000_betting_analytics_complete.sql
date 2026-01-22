-- ==================================================================
-- NBA Betting Analytics - Complete Backend Schema
-- ==================================================================
-- Created: 2026-01-22
-- Description: Complete database schema for NBA betting analytics platform
--              with consensus lines, ATS/O-U tracking, and budget management

-- ==================================================================
-- 1. TEAMS TABLE (Enhanced)
-- ==================================================================
-- Update teams table to include conference and division
ALTER TABLE IF EXISTS public.teams 
  ADD COLUMN IF NOT EXISTS conference text,
  ADD COLUMN IF NOT EXISTS division text;

-- ==================================================================
-- 2. PLAYERS TABLE (Enhanced)
-- ==================================================================
CREATE TABLE IF NOT EXISTS public.players (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  nba_player_id int UNIQUE,
  team_abbrev text,
  name text NOT NULL,
  position text,
  is_active boolean DEFAULT true,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_players_team ON public.players(team_abbrev);
CREATE INDEX IF NOT EXISTS idx_players_nba_id ON public.players(nba_player_id);

-- ==================================================================
-- 3. GAMES TABLE (Enhanced)
-- ==================================================================
-- Add missing fields to games table
ALTER TABLE IF EXISTS public.games
  ADD COLUMN IF NOT EXISTS nba_game_id text UNIQUE,
  ADD COLUMN IF NOT EXISTS status text DEFAULT 'scheduled';

-- ==================================================================
-- 4. TEAM GAME RESULTS TABLE
-- ==================================================================
CREATE TABLE IF NOT EXISTS public.team_game_results (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  game_id text NOT NULL REFERENCES public.games(id) ON DELETE CASCADE,
  team_abbrev text NOT NULL,
  points_for int NOT NULL,
  points_against int NOT NULL,
  is_home boolean NOT NULL,
  created_at timestamptz DEFAULT now(),
  UNIQUE(game_id, team_abbrev)
);

CREATE INDEX IF NOT EXISTS idx_team_game_results_game ON public.team_game_results(game_id);
CREATE INDEX IF NOT EXISTS idx_team_game_results_team ON public.team_game_results(team_abbrev);

-- ==================================================================
-- 5. TEAM GAME STATS TABLE (For Trends)
-- ==================================================================
CREATE TABLE IF NOT EXISTS public.team_game_stats (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  game_id text NOT NULL REFERENCES public.games(id) ON DELETE CASCADE,
  team_abbrev text NOT NULL,
  pace numeric,
  off_rtg numeric,
  def_rtg numeric,
  three_pt_pct numeric,
  ft_pct numeric,
  created_at timestamptz DEFAULT now(),
  UNIQUE(game_id, team_abbrev)
);

CREATE INDEX IF NOT EXISTS idx_team_game_stats_game ON public.team_game_stats(game_id);
CREATE INDEX IF NOT EXISTS idx_team_game_stats_team ON public.team_game_stats(team_abbrev);

-- ==================================================================
-- 6. PLAYER GAME STATS TABLE (Enhanced)
-- ==================================================================
CREATE TABLE IF NOT EXISTS public.player_game_stats (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  game_id text NOT NULL REFERENCES public.games(id) ON DELETE CASCADE,
  player_id uuid NOT NULL REFERENCES public.players(id) ON DELETE CASCADE,
  team_abbrev text NOT NULL,
  minutes numeric,
  pts int,
  reb int,
  ast int,
  usage numeric,
  created_at timestamptz DEFAULT now(),
  UNIQUE(game_id, player_id)
);

CREATE INDEX IF NOT EXISTS idx_player_game_stats_game ON public.player_game_stats(game_id);
CREATE INDEX IF NOT EXISTS idx_player_game_stats_player ON public.player_game_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_player_game_stats_team ON public.player_game_stats(team_abbrev);

-- ==================================================================
-- 7. ODDS SNAPSHOTS TABLE (Critical for deduplication)
-- ==================================================================
CREATE TABLE IF NOT EXISTS public.odds_snapshots (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  game_id text NOT NULL REFERENCES public.games(id) ON DELETE CASCADE,
  bookmaker_key text NOT NULL,
  market_type text NOT NULL, -- 'h2h', 'spread', 'totals'
  outcome_name text,
  team text,
  point numeric,
  price numeric NOT NULL,
  ts timestamptz NOT NULL,
  content_hash text NOT NULL,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_odds_snapshots_game_ts ON public.odds_snapshots(game_id, ts DESC);
CREATE INDEX IF NOT EXISTS idx_odds_snapshots_market ON public.odds_snapshots(market_type);
CREATE INDEX IF NOT EXISTS idx_odds_snapshots_bookmaker ON public.odds_snapshots(bookmaker_key);
CREATE INDEX IF NOT EXISTS idx_odds_snapshots_hash ON public.odds_snapshots(content_hash);

-- Unique constraint to prevent duplicate snapshots
CREATE UNIQUE INDEX IF NOT EXISTS idx_odds_snapshots_unique 
  ON public.odds_snapshots(game_id, bookmaker_key, market_type, COALESCE(outcome_name, ''), COALESCE(team, ''), COALESCE(point, 0), price, ts);

-- ==================================================================
-- 8. PICKS TABLE
-- ==================================================================
CREATE TABLE IF NOT EXISTS public.picks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at timestamptz DEFAULT now(),
  game_id text REFERENCES public.games(id) ON DELETE SET NULL,
  team_abbrev text,
  market text NOT NULL, -- 'spread', 'totals', 'h2h'
  selection text NOT NULL,
  line numeric,
  price numeric NOT NULL,
  implied_prob numeric NOT NULL,
  model_prob numeric NOT NULL,
  edge_prob numeric NOT NULL,
  ev numeric NOT NULL,
  kelly_fraction numeric NOT NULL,
  stake_units numeric NOT NULL,
  reason_codes text[] DEFAULT '{}',
  status text DEFAULT 'open' -- 'open', 'settled', 'void'
);

CREATE INDEX IF NOT EXISTS idx_picks_game ON public.picks(game_id);
CREATE INDEX IF NOT EXISTS idx_picks_status ON public.picks(status);
CREATE INDEX IF NOT EXISTS idx_picks_created ON public.picks(created_at DESC);

-- ==================================================================
-- 9. PICK RESULTS TABLE
-- ==================================================================
CREATE TABLE IF NOT EXISTS public.pick_results (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  pick_id uuid NOT NULL REFERENCES public.picks(id) ON DELETE CASCADE,
  settled_at timestamptz NOT NULL,
  result text NOT NULL, -- 'win', 'loss', 'push', 'void'
  pnl_units numeric NOT NULL,
  created_at timestamptz DEFAULT now(),
  UNIQUE(pick_id)
);

CREATE INDEX IF NOT EXISTS idx_pick_results_pick ON public.pick_results(pick_id);

-- ==================================================================
-- 10. API BUDGET TABLE (Critical for rate limiting)
-- ==================================================================
CREATE TABLE IF NOT EXISTS public.api_budget (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  provider text NOT NULL,
  day date NOT NULL,
  calls int DEFAULT 0,
  created_at timestamptz DEFAULT now(),
  UNIQUE(provider, day)
);

CREATE INDEX IF NOT EXISTS idx_api_budget_provider_day ON public.api_budget(provider, day);

-- ==================================================================
-- 11. API CACHE TABLE
-- ==================================================================
CREATE TABLE IF NOT EXISTS public.api_cache (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  provider text NOT NULL,
  cache_key text NOT NULL,
  payload jsonb NOT NULL,
  created_at timestamptz DEFAULT now(),
  ttl_seconds int NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_api_cache_provider_key ON public.api_cache(provider, cache_key);
CREATE INDEX IF NOT EXISTS idx_api_cache_created ON public.api_cache(created_at);

-- Unique constraint to prevent duplicate cache entries
CREATE UNIQUE INDEX IF NOT EXISTS idx_api_cache_unique 
  ON public.api_cache(provider, cache_key);

-- ==================================================================
-- 12. CLOSING LINES TABLE (For Consensus Closing Lines)
-- ==================================================================
CREATE TABLE IF NOT EXISTS public.closing_lines (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  game_id text NOT NULL REFERENCES public.games(id) ON DELETE CASCADE,
  market_type text NOT NULL, -- 'spread', 'totals', 'h2h'
  team text, -- nullable; for spread/h2h only
  point numeric, -- nullable; for spread/totals
  price numeric NOT NULL,
  ts_cutoff timestamptz NOT NULL, -- commence_time
  method text DEFAULT 'consensus_median_mad',
  sample_count int NOT NULL,
  used_bookmakers text[] DEFAULT '{}',
  created_at timestamptz DEFAULT now(),
  UNIQUE(game_id, market_type, COALESCE(team, ''))
);

CREATE INDEX IF NOT EXISTS idx_closing_lines_game ON public.closing_lines(game_id);
CREATE INDEX IF NOT EXISTS idx_closing_lines_market ON public.closing_lines(market_type);

-- ==================================================================
-- 13. REPORTS TABLE (Optional)
-- ==================================================================
CREATE TABLE IF NOT EXISTS public.reports (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  report_type text NOT NULL,
  report_date date NOT NULL,
  content jsonb NOT NULL,
  created_at timestamptz DEFAULT now(),
  UNIQUE(report_type, report_date)
);

CREATE INDEX IF NOT EXISTS idx_reports_type_date ON public.reports(report_type, report_date DESC);

-- ==================================================================
-- Helper Functions
-- ==================================================================

-- Function to calculate implied probability from American odds
CREATE OR REPLACE FUNCTION implied_prob_from_american(odds numeric) 
RETURNS numeric AS $$
BEGIN
  IF odds > 0 THEN
    RETURN 100.0 / (odds + 100.0);
  ELSE
    RETURN ABS(odds) / (ABS(odds) + 100.0);
  END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to calculate implied probability from decimal odds
CREATE OR REPLACE FUNCTION implied_prob_from_decimal(odds numeric) 
RETURNS numeric AS $$
BEGIN
  RETURN 1.0 / odds;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ==================================================================
-- Row Level Security
-- ==================================================================

-- Enable RLS on sensitive tables
ALTER TABLE public.picks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pick_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.api_budget ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.api_cache ENABLE ROW LEVEL SECURITY;

-- Public read access to game data (read-only for all authenticated users)
CREATE POLICY "Public read access to odds_snapshots" ON public.odds_snapshots 
    FOR SELECT 
    USING (true);

CREATE POLICY "Public read access to closing_lines" ON public.closing_lines 
    FOR SELECT 
    USING (true);

CREATE POLICY "Public read access to team_game_results" ON public.team_game_results 
    FOR SELECT 
    USING (true);

CREATE POLICY "Public read access to team_game_stats" ON public.team_game_stats 
    FOR SELECT 
    USING (true);

CREATE POLICY "Public read access to player_game_stats" ON public.player_game_stats 
    FOR SELECT 
    USING (true);

-- Restrict sensitive tables to service_role only
-- Note: In Supabase, check role with: auth.role() = 'service_role'
-- For production, these should use auth.uid() checks or service role checks

-- api_budget - service role only
CREATE POLICY "Service role full access to api_budget" ON public.api_budget
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- api_cache - service role only
CREATE POLICY "Service role full access to api_cache" ON public.api_cache
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- picks - service role only (or add user-specific policies later)
CREATE POLICY "Service role full access to picks" ON public.picks
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- pick_results - service role only
CREATE POLICY "Service role full access to pick_results" ON public.pick_results
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ==================================================================
-- END OF MIGRATION
-- ==================================================================
