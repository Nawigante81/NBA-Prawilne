/*
  # Create odds_snapshots and team_game_results tables
*/

CREATE TABLE IF NOT EXISTS public.odds_snapshots (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  game_id text NOT NULL,
  bookmaker_key text,
  bookmaker_title text,
  market_type text NOT NULL,
  outcome_name text,
  team text,
  point numeric,
  price numeric,
  ts timestamptz NOT NULL,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_odds_snapshots_game_id ON public.odds_snapshots(game_id);
CREATE INDEX IF NOT EXISTS idx_odds_snapshots_market_type ON public.odds_snapshots(market_type);
CREATE INDEX IF NOT EXISTS idx_odds_snapshots_ts ON public.odds_snapshots(ts);

ALTER TABLE public.odds_snapshots ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Enable read access for all users" ON public.odds_snapshots
  FOR SELECT USING (true);

CREATE POLICY "Enable insert for service role only" ON public.odds_snapshots
  FOR INSERT WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Enable update for service role only" ON public.odds_snapshots
  FOR UPDATE USING (auth.role() = 'service_role');

CREATE POLICY "Enable delete for service role only" ON public.odds_snapshots
  FOR DELETE USING (auth.role() = 'service_role');

CREATE TABLE IF NOT EXISTS public.team_game_results (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  game_id text NOT NULL,
  team_abbrev text NOT NULL,
  points_for integer,
  points_against integer,
  closing_spread numeric,
  closing_total numeric,
  ats_result text,
  ou_result text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  UNIQUE(game_id, team_abbrev)
);

CREATE INDEX IF NOT EXISTS idx_team_game_results_game_id ON public.team_game_results(game_id);
CREATE INDEX IF NOT EXISTS idx_team_game_results_team_abbrev ON public.team_game_results(team_abbrev);

ALTER TABLE public.team_game_results ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Enable read access for all users" ON public.team_game_results
  FOR SELECT USING (true);

CREATE POLICY "Enable insert for service role only" ON public.team_game_results
  FOR INSERT WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Enable update for service role only" ON public.team_game_results
  FOR UPDATE USING (auth.role() = 'service_role');

CREATE POLICY "Enable delete for service role only" ON public.team_game_results
  FOR DELETE USING (auth.role() = 'service_role');

CREATE OR REPLACE FUNCTION update_team_game_results_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_team_game_results_updated_at
  BEFORE UPDATE ON public.team_game_results
  FOR EACH ROW
  EXECUTE FUNCTION update_team_game_results_updated_at();
