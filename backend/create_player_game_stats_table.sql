-- Create player_game_stats table for NBA historical data
-- This table stores player statistics for each game

CREATE TABLE IF NOT EXISTS player_game_stats (
    id BIGSERIAL PRIMARY KEY,
    season_year TEXT NOT NULL,
    game_date DATE NOT NULL,
    game_id TEXT NOT NULL,
    matchup TEXT,
    team_id BIGINT,
    team_city TEXT,
    team_name TEXT,
    team_tricode TEXT,
    team_slug TEXT,
    player_id BIGINT NOT NULL,
    player_name TEXT NOT NULL,
    position TEXT,
    comment TEXT,
    jersey_num INTEGER,
    minutes TEXT,
    field_goals_made INTEGER DEFAULT 0,
    field_goals_attempted INTEGER DEFAULT 0,
    field_goals_percentage NUMERIC,
    three_pointers_made INTEGER DEFAULT 0,
    three_pointers_attempted INTEGER DEFAULT 0,
    three_pointers_percentage NUMERIC,
    free_throws_made INTEGER DEFAULT 0,
    free_throws_attempted INTEGER DEFAULT 0,
    free_throws_percentage NUMERIC,
    rebounds_offensive INTEGER DEFAULT 0,
    rebounds_defensive INTEGER DEFAULT 0,
    rebounds_total INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    steals INTEGER DEFAULT 0,
    blocks INTEGER DEFAULT 0,
    turnovers INTEGER DEFAULT 0,
    fouls_personal INTEGER DEFAULT 0,
    points INTEGER DEFAULT 0,
    plus_minus_points INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_player_game_stats_player_id ON player_game_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_player_game_stats_game_id ON player_game_stats(game_id);
CREATE INDEX IF NOT EXISTS idx_player_game_stats_game_date ON player_game_stats(game_date);
CREATE INDEX IF NOT EXISTS idx_player_game_stats_season_year ON player_game_stats(season_year);
CREATE INDEX IF NOT EXISTS idx_player_game_stats_team_tricode ON player_game_stats(team_tricode);
CREATE INDEX IF NOT EXISTS idx_player_game_stats_player_name ON player_game_stats(player_name);

-- Create composite index for common queries
CREATE INDEX IF NOT EXISTS idx_player_game_stats_player_season ON player_game_stats(player_id, season_year);
CREATE INDEX IF NOT EXISTS idx_player_game_stats_team_season ON player_game_stats(team_tricode, season_year);

-- Add comment to table
COMMENT ON TABLE player_game_stats IS 'NBA player game statistics from 2010-2024';
