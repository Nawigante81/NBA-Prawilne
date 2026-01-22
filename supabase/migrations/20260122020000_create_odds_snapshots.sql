/*
  # Create odds_snapshots table for line movement tracking
  
  Stores historical odds snapshots to track line movements over time.
*/

CREATE TABLE IF NOT EXISTS public.odds_snapshots (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  game_id text NOT NULL,
  bookmaker_key text NOT NULL,
  bookmaker_title text,
  market_type text NOT NULL, -- 'h2h', 'spread', 'totals'
  outcome_name text,
  team text,
  point numeric, -- spread/total line value
  price numeric NOT NULL, -- decimal odds
  ts timestamptz DEFAULT now(),
  created_at timestamptz DEFAULT now()
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_odds_snapshots_game_id ON public.odds_snapshots(game_id);
CREATE INDEX IF NOT EXISTS idx_odds_snapshots_game_market ON public.odds_snapshots(game_id, market_type);
CREATE INDEX IF NOT EXISTS idx_odds_snapshots_ts ON public.odds_snapshots(ts DESC);
CREATE INDEX IF NOT EXISTS idx_odds_snapshots_bookmaker ON public.odds_snapshots(bookmaker_key);

-- RLS policies
ALTER TABLE public.odds_snapshots ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to read odds snapshots (public data for betting analysis)
CREATE POLICY "Enable read access for authenticated users" ON public.odds_snapshots
  FOR SELECT USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');

CREATE POLICY "Enable insert for service role only" ON public.odds_snapshots
  FOR INSERT WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Enable update for service role only" ON public.odds_snapshots
  FOR UPDATE USING (auth.role() = 'service_role');

CREATE POLICY "Enable delete for service role only" ON public.odds_snapshots
  FOR DELETE USING (auth.role() = 'service_role');
