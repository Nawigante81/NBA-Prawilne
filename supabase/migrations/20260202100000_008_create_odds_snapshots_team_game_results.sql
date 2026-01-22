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

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'odds_snapshots'
      AND policyname = 'Enable read access for all users'
  ) THEN
    CREATE POLICY "Enable read access for all users" ON public.odds_snapshots
      FOR SELECT USING (true);
  END IF;
END;
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'odds_snapshots'
      AND policyname = 'Enable insert for service role only'
  ) THEN
    CREATE POLICY "Enable insert for service role only" ON public.odds_snapshots
      FOR INSERT WITH CHECK (auth.role() = 'service_role');
  END IF;
END;
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'odds_snapshots'
      AND policyname = 'Enable update for service role only'
  ) THEN
    CREATE POLICY "Enable update for service role only" ON public.odds_snapshots
      FOR UPDATE USING (auth.role() = 'service_role');
  END IF;
END;
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'odds_snapshots'
      AND policyname = 'Enable delete for service role only'
  ) THEN
    CREATE POLICY "Enable delete for service role only" ON public.odds_snapshots
      FOR DELETE USING (auth.role() = 'service_role');
  END IF;
END;
$$;

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

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'team_game_results'
      AND policyname = 'Enable read access for all users'
  ) THEN
    CREATE POLICY "Enable read access for all users" ON public.team_game_results
      FOR SELECT USING (true);
  END IF;
END;
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'team_game_results'
      AND policyname = 'Enable insert for service role only'
  ) THEN
    CREATE POLICY "Enable insert for service role only" ON public.team_game_results
      FOR INSERT WITH CHECK (auth.role() = 'service_role');
  END IF;
END;
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'team_game_results'
      AND policyname = 'Enable update for service role only'
  ) THEN
    CREATE POLICY "Enable update for service role only" ON public.team_game_results
      FOR UPDATE USING (auth.role() = 'service_role');
  END IF;
END;
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'team_game_results'
      AND policyname = 'Enable delete for service role only'
  ) THEN
    CREATE POLICY "Enable delete for service role only" ON public.team_game_results
      FOR DELETE USING (auth.role() = 'service_role');
  END IF;
END;
$$;

CREATE OR REPLACE FUNCTION update_team_game_results_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_trigger
    WHERE tgname = 'update_team_game_results_updated_at'
  ) THEN
    CREATE TRIGGER update_team_game_results_updated_at
      BEFORE UPDATE ON public.team_game_results
      FOR EACH ROW
      EXECUTE FUNCTION update_team_game_results_updated_at();
  END IF;
END;
$$;
