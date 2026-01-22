/*
  # Add betting-specific fields to game_results table
  
  Adds ATS/OU result tracking fields.
*/

-- Add closing line fields if they don't exist
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'game_results' 
    AND column_name = 'closing_spread_home'
  ) THEN
    ALTER TABLE public.game_results 
      ADD COLUMN closing_spread_home numeric,
      ADD COLUMN closing_spread_away numeric,
      ADD COLUMN closing_total numeric,
      ADD COLUMN ats_result_home text, -- 'W', 'L', 'P' (push)
      ADD COLUMN ats_result_away text, -- 'W', 'L', 'P' (push)
      ADD COLUMN ou_result text; -- 'O' (over), 'U' (under), 'P' (push)
  END IF;
END $$;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_game_results_ats_home ON public.game_results(ats_result_home) WHERE ats_result_home IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_game_results_ats_away ON public.game_results(ats_result_away) WHERE ats_result_away IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_game_results_ou ON public.game_results(ou_result) WHERE ou_result IS NOT NULL;
