/*
  # Create team_betting_stats table

  Cached ATS/OU stats per team for fast dashboard access.
*/

CREATE TABLE IF NOT EXISTS public.team_betting_stats (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  team_name text UNIQUE NOT NULL,
  games_count integer,
  ats_record text,
  ats_percentage numeric,
  over_under text,
  ou_percentage numeric,
  avg_total numeric,
  computed_at timestamptz DEFAULT now(),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_team_betting_stats_team_name ON public.team_betting_stats(team_name);
CREATE INDEX IF NOT EXISTS idx_team_betting_stats_computed_at ON public.team_betting_stats(computed_at);

ALTER TABLE public.team_betting_stats ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Enable read access for all users" ON public.team_betting_stats
  FOR SELECT USING (true);

CREATE POLICY "Enable insert for service role only" ON public.team_betting_stats
  FOR INSERT WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Enable update for service role only" ON public.team_betting_stats
  FOR UPDATE USING (auth.role() = 'service_role');

CREATE POLICY "Enable delete for service role only" ON public.team_betting_stats
  FOR DELETE USING (auth.role() = 'service_role');

CREATE OR REPLACE FUNCTION update_team_betting_stats_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_team_betting_stats_updated_at
  BEFORE UPDATE ON public.team_betting_stats
  FOR EACH ROW
  EXECUTE FUNCTION update_team_betting_stats_updated_at();
