/*
  # Create game_results table

  Stores final NBA scores for ATS/OU calculations.
*/

CREATE TABLE IF NOT EXISTS public.game_results (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  game_id text, -- NBA stats game id (may differ from odds game id)
  game_date date NOT NULL,
  home_team text NOT NULL,
  away_team text NOT NULL,
  home_score integer,
  away_score integer,
  status text,
  finalized_at timestamptz,
  source text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  UNIQUE(game_date, home_team, away_team)
);

CREATE INDEX IF NOT EXISTS idx_game_results_game_date ON public.game_results(game_date);
CREATE INDEX IF NOT EXISTS idx_game_results_home_team ON public.game_results(home_team);
CREATE INDEX IF NOT EXISTS idx_game_results_away_team ON public.game_results(away_team);

ALTER TABLE public.game_results ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'game_results'
      AND policyname = 'Enable read access for all users'
  ) THEN
    CREATE POLICY "Enable read access for all users" ON public.game_results
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
      AND tablename = 'game_results'
      AND policyname = 'Enable insert for service role only'
  ) THEN
    CREATE POLICY "Enable insert for service role only" ON public.game_results
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
      AND tablename = 'game_results'
      AND policyname = 'Enable update for service role only'
  ) THEN
    CREATE POLICY "Enable update for service role only" ON public.game_results
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
      AND tablename = 'game_results'
      AND policyname = 'Enable delete for service role only'
  ) THEN
    CREATE POLICY "Enable delete for service role only" ON public.game_results
      FOR DELETE USING (auth.role() = 'service_role');
  END IF;
END;
$$;

CREATE OR REPLACE FUNCTION update_game_results_updated_at()
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
    WHERE tgname = 'update_game_results_updated_at'
  ) THEN
    CREATE TRIGGER update_game_results_updated_at
      BEFORE UPDATE ON public.game_results
      FOR EACH ROW
      EXECUTE FUNCTION update_game_results_updated_at();
  END IF;
END;
$$;
