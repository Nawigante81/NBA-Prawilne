/*
  # Create player_game_stats table for historical NBA data
  
  1. New Tables
    - `player_game_stats`
      - Historical box score data from 2010-2024
      - Player-level game statistics
      - ~424,000 rows of historical data
  
  2. Indexes
    - Index on game_id for fast game lookups
    - Index on player_id for fast player queries
    - Index on game_date for time-based queries
    - Index on team_tricode for team-specific queries
    - Composite index on (player_id, game_date) for player performance over time
*/

CREATE TABLE IF NOT EXISTS public.player_game_stats (
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
  comment text,  -- DNP reasons, injuries, etc.
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

-- Create indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_player_game_stats_game_id ON public.player_game_stats(game_id);
CREATE INDEX IF NOT EXISTS idx_player_game_stats_player_id ON public.player_game_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_player_game_stats_game_date ON public.player_game_stats(game_date);
CREATE INDEX IF NOT EXISTS idx_player_game_stats_team_tricode ON public.player_game_stats(team_tricode);
CREATE INDEX IF NOT EXISTS idx_player_game_stats_player_date ON public.player_game_stats(player_id, game_date);
CREATE INDEX IF NOT EXISTS idx_player_game_stats_season_year ON public.player_game_stats(season_year);

-- Enable RLS
ALTER TABLE public.player_game_stats ENABLE ROW LEVEL SECURITY;

-- Create policy for read access (everyone can read historical data)
CREATE POLICY "Enable read access for all users" ON public.player_game_stats
  FOR SELECT USING (true);

-- Create policy for write access (only service role)
CREATE POLICY "Enable insert for service role only" ON public.player_game_stats
  FOR INSERT WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Enable update for service role only" ON public.player_game_stats
  FOR UPDATE USING (auth.role() = 'service_role');

CREATE POLICY "Enable delete for service role only" ON public.player_game_stats
  FOR DELETE USING (auth.role() = 'service_role');

-- Add comment to table
COMMENT ON TABLE public.player_game_stats IS 'Historical NBA player game statistics (box scores) from 2010-2024 season';
