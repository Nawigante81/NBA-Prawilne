/*
  # Add closing_lines table for consensus closing lines
*/

CREATE TABLE IF NOT EXISTS public.closing_lines (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  game_id text NOT NULL REFERENCES public.games(id) ON DELETE CASCADE,
  market_type text NOT NULL,
  team text,
  point numeric,
  price numeric,
  ts_cutoff timestamptz NOT NULL,
  method text NOT NULL DEFAULT 'consensus_median_mad',
  sample_count integer NOT NULL DEFAULT 0,
  used_bookmakers text[] DEFAULT '{}',
  created_at timestamptz DEFAULT now(),
  UNIQUE(game_id, market_type, team)
);

CREATE INDEX IF NOT EXISTS idx_closing_lines_game_id ON public.closing_lines(game_id);
CREATE INDEX IF NOT EXISTS idx_closing_lines_market_type ON public.closing_lines(market_type);
CREATE INDEX IF NOT EXISTS idx_closing_lines_ts_cutoff ON public.closing_lines(ts_cutoff);

ALTER TABLE public.closing_lines ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'closing_lines'
      AND policyname = 'Enable read access for all users'
  ) THEN
    CREATE POLICY "Enable read access for all users" ON public.closing_lines
      FOR SELECT USING (true);
  END IF;
END;
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'closing_lines'
      AND policyname = 'Enable insert for service role only'
  ) THEN
    CREATE POLICY "Enable insert for service role only" ON public.closing_lines
      FOR INSERT WITH CHECK (auth.role() = 'service_role');
  END IF;
END;
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'closing_lines'
      AND policyname = 'Enable update for service role only'
  ) THEN
    CREATE POLICY "Enable update for service role only" ON public.closing_lines
      FOR UPDATE USING (auth.role() = 'service_role');
  END IF;
END;
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'closing_lines'
      AND policyname = 'Enable delete for service role only'
  ) THEN
    CREATE POLICY "Enable delete for service role only" ON public.closing_lines
      FOR DELETE USING (auth.role() = 'service_role');
  END IF;
END;
$$;

-- Dedupe index for odds snapshots if not present
CREATE UNIQUE INDEX IF NOT EXISTS uq_odds_snapshots_dedupe
ON public.odds_snapshots (game_id, bookmaker_key, market_type, outcome_name, point, price, ts);
