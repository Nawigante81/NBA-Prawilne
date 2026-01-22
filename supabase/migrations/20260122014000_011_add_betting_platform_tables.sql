-- Migration: Add tables for production-grade betting platform
-- Date: 2026-01-22
-- Description: Adds api_budget, api_cache, odds_snapshots (enhanced), picks, pick_results, reports, uploads_stub

-- API Budget tracking table
CREATE TABLE IF NOT EXISTS public.api_budget (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  provider text NOT NULL,
  date date NOT NULL,
  calls_made integer NOT NULL DEFAULT 0,
  calls_limit integer NOT NULL,
  last_call_at timestamptz,
  created_at timestamptz DEFAULT now(),
  UNIQUE(provider, date)
);

CREATE INDEX IF NOT EXISTS idx_api_budget_provider_date ON public.api_budget(provider, date);

-- API Cache table
CREATE TABLE IF NOT EXISTS public.api_cache (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  provider text NOT NULL,
  endpoint text NOT NULL,
  params_hash text NOT NULL,
  response_data jsonb NOT NULL,
  ttl_seconds integer NOT NULL,
  cached_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL,
  created_at timestamptz DEFAULT now(),
  UNIQUE(provider, endpoint, params_hash)
);

CREATE INDEX IF NOT EXISTS idx_api_cache_expires ON public.api_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_api_cache_provider_endpoint ON public.api_cache(provider, endpoint);

-- Enhanced odds_snapshots table (for CLV tracking)
CREATE TABLE IF NOT EXISTS public.odds_snapshots (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  game_id text NOT NULL REFERENCES public.games(id) ON DELETE CASCADE,
  bookmaker_key text NOT NULL,
  bookmaker_title text,
  market_type text NOT NULL,
  outcome_name text,
  team text,
  point numeric,
  price numeric,
  snapshot_time timestamptz NOT NULL,
  content_hash text,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_odds_snapshots_game_id ON public.odds_snapshots(game_id);
CREATE INDEX IF NOT EXISTS idx_odds_snapshots_market_type ON public.odds_snapshots(market_type);
CREATE INDEX IF NOT EXISTS idx_odds_snapshots_snapshot_time ON public.odds_snapshots(snapshot_time);
CREATE INDEX IF NOT EXISTS idx_odds_snapshots_content_hash ON public.odds_snapshots(content_hash);

-- Picks table
CREATE TABLE IF NOT EXISTS public.picks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  game_id text NOT NULL REFERENCES public.games(id) ON DELETE CASCADE,
  market_type text NOT NULL,
  selection text NOT NULL,
  bookmaker text NOT NULL,
  odds numeric NOT NULL,
  odds_format text NOT NULL DEFAULT 'american',
  point numeric,
  stake_units numeric NOT NULL,
  stake_usd numeric NOT NULL,
  edge numeric NOT NULL,
  ev numeric NOT NULL,
  confidence numeric NOT NULL,
  kelly_fraction numeric NOT NULL,
  notes text,
  pick_time timestamptz NOT NULL,
  game_commence_time timestamptz NOT NULL,
  status text NOT NULL DEFAULT 'pending',
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_picks_game_id ON public.picks(game_id);
CREATE INDEX IF NOT EXISTS idx_picks_status ON public.picks(status);
CREATE INDEX IF NOT EXISTS idx_picks_pick_time ON public.picks(pick_time);

-- Pick results table
CREATE TABLE IF NOT EXISTS public.pick_results (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  pick_id uuid NOT NULL REFERENCES public.picks(id) ON DELETE CASCADE,
  status text NOT NULL,
  closing_odds numeric,
  closing_point numeric,
  clv numeric,
  profit_loss numeric NOT NULL,
  settled_at timestamptz NOT NULL,
  created_at timestamptz DEFAULT now(),
  UNIQUE(pick_id)
);

CREATE INDEX IF NOT EXISTS idx_pick_results_pick_id ON public.pick_results(pick_id);
CREATE INDEX IF NOT EXISTS idx_pick_results_settled_at ON public.pick_results(settled_at);

-- Reports table
CREATE TABLE IF NOT EXISTS public.reports (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  report_type text NOT NULL,
  report_date date NOT NULL,
  content jsonb NOT NULL,
  generated_at timestamptz NOT NULL,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_reports_type_date ON public.reports(report_type, report_date);
CREATE INDEX IF NOT EXISTS idx_reports_generated_at ON public.reports(generated_at);

-- Uploads stub table (for screenshot metadata)
CREATE TABLE IF NOT EXISTS public.uploads_stub (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  filename text NOT NULL,
  upload_date timestamptz NOT NULL,
  bookmaker text,
  notes text,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_uploads_stub_upload_date ON public.uploads_stub(upload_date);

-- Add team_game_stats table if not exists (for analytics)
CREATE TABLE IF NOT EXISTS public.team_game_stats (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  game_id text NOT NULL,
  team_abbreviation text NOT NULL,
  game_date date NOT NULL,
  is_home boolean NOT NULL,
  points integer,
  opponent_points integer,
  field_goals_made integer,
  field_goals_attempted integer,
  three_point_made integer,
  three_point_attempted integer,
  free_throws_made integer,
  free_throws_attempted integer,
  offensive_rebounds integer,
  defensive_rebounds integer,
  total_rebounds integer,
  assists integer,
  steals integer,
  blocks integer,
  turnovers integer,
  personal_fouls integer,
  offensive_rating numeric,
  defensive_rating numeric,
  pace numeric,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_team_game_stats_game_id ON public.team_game_stats(game_id);
CREATE INDEX IF NOT EXISTS idx_team_game_stats_team_date ON public.team_game_stats(team_abbreviation, game_date);

-- Trigger for updating updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to games table
DROP TRIGGER IF EXISTS update_games_updated_at ON public.games;
CREATE TRIGGER update_games_updated_at
  BEFORE UPDATE ON public.games
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to odds table
DROP TRIGGER IF EXISTS update_odds_updated_at ON public.odds;
CREATE TRIGGER update_odds_updated_at
  BEFORE UPDATE ON public.odds
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();
