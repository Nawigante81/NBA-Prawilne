-- ==================================================================
-- NBA Betting Analytics - Core Tables
-- ==================================================================

-- Value Bets Tracking
CREATE TABLE IF NOT EXISTS value_bets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  game_id TEXT NOT NULL,
  market_type TEXT NOT NULL, -- 'h2h', 'spread', 'total'
  selection TEXT NOT NULL,
  odds DECIMAL(10,3),
  implied_prob DECIMAL(5,4),
  model_prob DECIMAL(5,4),
  edge DECIMAL(5,4),
  ev DECIMAL(10,2), -- Expected Value
  confidence DECIMAL(5,4),
  recommendation TEXT, -- 'STRONG_PLAY', 'PLAY', 'LEAN', 'NO_PLAY'
  created_at TIMESTAMP DEFAULT NOW(),
  CONSTRAINT unique_value_bet UNIQUE (game_id, market_type, selection, created_at)
);

CREATE INDEX idx_value_bets_game ON value_bets(game_id);
CREATE INDEX idx_value_bets_recommendation ON value_bets(recommendation);
CREATE INDEX idx_value_bets_created ON value_bets(created_at DESC);

-- Bet History
CREATE TABLE IF NOT EXISTS bet_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID,
  game_id TEXT NOT NULL,
  market_type TEXT NOT NULL,
  selection TEXT NOT NULL,
  odds DECIMAL(10,3) NOT NULL,
  stake DECIMAL(10,2) NOT NULL,
  placed_at TIMESTAMP DEFAULT NOW(),
  
  -- Result tracking
  result TEXT, -- 'won', 'lost', 'push', 'pending'
  profit DECIMAL(10,2),
  settled_at TIMESTAMP,
  
  -- CLV tracking
  closing_odds DECIMAL(10,3),
  clv_percentage DECIMAL(5,4),
  
  -- Model tracking
  model_edge DECIMAL(5,4),
  model_confidence DECIMAL(5,4),
  model_ev DECIMAL(10,2)
);

CREATE INDEX idx_bet_history_user ON bet_history(user_id);
CREATE INDEX idx_bet_history_result ON bet_history(result);
CREATE INDEX idx_bet_history_market ON bet_history(market_type);
CREATE INDEX idx_bet_history_placed ON bet_history(placed_at DESC);

-- Line Movements Tracking
CREATE TABLE IF NOT EXISTS line_movements (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  game_id TEXT NOT NULL,
  bookmaker TEXT NOT NULL,
  market_type TEXT NOT NULL,
  line_value DECIMAL(10,3), -- for spreads/totals
  odds DECIMAL(10,3),
  timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_line_movements_game ON line_movements(game_id, timestamp DESC);
CREATE INDEX idx_line_movements_market ON line_movements(market_type);

-- Bankroll Management
CREATE TABLE IF NOT EXISTS user_bankroll (
  user_id UUID PRIMARY KEY,
  total_bankroll DECIMAL(10,2) NOT NULL,
  current_balance DECIMAL(10,2) NOT NULL,
  daily_limit_pct DECIMAL(5,2) DEFAULT 10.00,
  max_bet_pct DECIMAL(5,2) DEFAULT 5.00,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Active Exposure (bets not yet settled)
CREATE TABLE IF NOT EXISTS active_exposure (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_bankroll(user_id) ON DELETE CASCADE,
  game_id TEXT NOT NULL,
  stake DECIMAL(10,2) NOT NULL,
  status TEXT DEFAULT 'pending', -- pending, won, lost, push
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_active_exposure_user ON active_exposure(user_id);
CREATE INDEX idx_active_exposure_status ON active_exposure(status);

-- User Alerts
CREATE TABLE IF NOT EXISTS user_alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID,
  alert_type TEXT NOT NULL, -- 'injury', 'line_move', 'value', 'result'
  game_id TEXT,
  title TEXT NOT NULL,
  message TEXT NOT NULL,
  severity TEXT DEFAULT 'info', -- 'info', 'warning', 'critical'
  is_read BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_user_alerts_user ON user_alerts(user_id, is_read);
CREATE INDEX idx_user_alerts_created ON user_alerts(created_at DESC);

-- Game Context (Rest, Travel, Fatigue)
CREATE TABLE IF NOT EXISTS game_context (
  game_id TEXT PRIMARY KEY,
  home_team TEXT NOT NULL,
  away_team TEXT NOT NULL,
  game_date DATE NOT NULL,
  
  -- Rest & Fatigue
  home_rest_days INTEGER,
  away_rest_days INTEGER,
  home_b2b BOOLEAN DEFAULT FALSE,
  away_b2b BOOLEAN DEFAULT FALSE,
  home_3in4 BOOLEAN DEFAULT FALSE,
  away_3in4 BOOLEAN DEFAULT FALSE,
  
  -- Travel
  away_travel_miles INTEGER,
  away_timezone_change INTEGER,
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_game_context_date ON game_context(game_date DESC);
CREATE INDEX idx_game_context_teams ON game_context(home_team, away_team);

-- Injury Impact
CREATE TABLE IF NOT EXISTS injury_impact (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  game_id TEXT NOT NULL,
  player_name TEXT NOT NULL,
  team TEXT NOT NULL,
  status TEXT NOT NULL, -- 'OUT', 'DOUBTFUL', 'QUESTIONABLE', 'PROBABLE'
  impact_points DECIMAL(5,2), -- Estimated spread impact
  projected_replacement TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_injury_impact_game ON injury_impact(game_id);
CREATE INDEX idx_injury_impact_status ON injury_impact(status);

-- ==================================================================
-- Views for Performance Analytics
-- ==================================================================

-- Overall Performance View
CREATE OR REPLACE VIEW v_performance_summary AS
SELECT 
  user_id,
  COUNT(*) as total_bets,
  SUM(CASE WHEN result = 'won' THEN 1 ELSE 0 END) as wins,
  SUM(CASE WHEN result = 'lost' THEN 1 ELSE 0 END) as losses,
  SUM(CASE WHEN result = 'push' THEN 1 ELSE 0 END) as pushes,
  ROUND(SUM(CASE WHEN result = 'won' THEN 1 ELSE 0 END)::DECIMAL / 
        NULLIF(COUNT(CASE WHEN result IN ('won', 'lost') THEN 1 END), 0) * 100, 2) as win_rate,
  SUM(stake) as total_wagered,
  SUM(COALESCE(profit, 0)) as total_profit,
  ROUND(SUM(COALESCE(profit, 0))::DECIMAL / NULLIF(SUM(stake), 0) * 100, 2) as roi,
  AVG(COALESCE(clv_percentage, 0)) as avg_clv
FROM bet_history
WHERE result IS NOT NULL
GROUP BY user_id;

-- Performance by Market Type
CREATE OR REPLACE VIEW v_performance_by_market AS
SELECT 
  user_id,
  market_type,
  COUNT(*) as bets,
  SUM(CASE WHEN result = 'won' THEN 1 ELSE 0 END) as wins,
  ROUND(SUM(CASE WHEN result = 'won' THEN 1 ELSE 0 END)::DECIMAL / 
        NULLIF(COUNT(CASE WHEN result IN ('won', 'lost') THEN 1 END), 0) * 100, 2) as win_rate,
  SUM(stake) as total_wagered,
  SUM(COALESCE(profit, 0)) as total_profit,
  ROUND(SUM(COALESCE(profit, 0))::DECIMAL / NULLIF(SUM(stake), 0) * 100, 2) as roi
FROM bet_history
WHERE result IS NOT NULL
GROUP BY user_id, market_type;

-- Recent Form (Last 10, 30 bets)
CREATE OR REPLACE VIEW v_recent_form AS
WITH numbered_bets AS (
  SELECT 
    *,
    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY placed_at DESC) as bet_num
  FROM bet_history
  WHERE result IS NOT NULL
)
SELECT 
  user_id,
  'last_10' as period,
  COUNT(*) as bets,
  SUM(CASE WHEN result = 'won' THEN 1 ELSE 0 END) as wins,
  SUM(COALESCE(profit, 0)) as profit,
  ROUND(SUM(COALESCE(profit, 0))::DECIMAL / NULLIF(SUM(stake), 0) * 100, 2) as roi
FROM numbered_bets
WHERE bet_num <= 10
GROUP BY user_id

UNION ALL

SELECT 
  user_id,
  'last_30' as period,
  COUNT(*) as bets,
  SUM(CASE WHEN result = 'won' THEN 1 ELSE 0 END) as wins,
  SUM(COALESCE(profit, 0)) as profit,
  ROUND(SUM(COALESCE(profit, 0))::DECIMAL / NULLIF(SUM(stake), 0) * 100, 2) as roi
FROM numbered_bets
WHERE bet_num <= 30
GROUP BY user_id;

-- ==================================================================
-- Helper Functions
-- ==================================================================

-- Calculate Expected Value
CREATE OR REPLACE FUNCTION calculate_ev(
  odds DECIMAL,
  win_probability DECIMAL,
  stake DECIMAL DEFAULT 100
) RETURNS DECIMAL AS $$
DECLARE
  decimal_odds DECIMAL;
  win_amount DECIMAL;
  lose_amount DECIMAL;
BEGIN
  decimal_odds := odds;
  win_amount := (decimal_odds - 1) * stake;
  lose_amount := stake;
  
  RETURN (win_probability * win_amount) - ((1 - win_probability) * lose_amount);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Calculate Implied Probability from Decimal Odds
CREATE OR REPLACE FUNCTION implied_probability(odds DECIMAL) RETURNS DECIMAL AS $$
BEGIN
  RETURN 1.0 / odds;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ==================================================================
-- Sample Data for Testing (Optional)
-- ==================================================================

-- Insert sample bankroll (if needed for testing)
-- INSERT INTO user_bankroll (user_id, total_bankroll, current_balance)
-- VALUES 
--   (gen_random_uuid(), 1000.00, 1000.00)
-- ON CONFLICT (user_id) DO NOTHING;

-- ==================================================================
-- Permissions (Adjust based on your RLS policies)
-- ==================================================================

-- Enable Row Level Security
ALTER TABLE value_bets ENABLE ROW LEVEL SECURITY;
ALTER TABLE bet_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE line_movements ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_bankroll ENABLE ROW LEVEL SECURITY;
ALTER TABLE active_exposure ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE game_context ENABLE ROW LEVEL SECURITY;
ALTER TABLE injury_impact ENABLE ROW LEVEL SECURITY;

-- Create basic policies (adjust as needed)
-- Allow authenticated users to read all game/odds data
CREATE POLICY "Allow read access to value_bets" ON value_bets FOR SELECT USING (true);
CREATE POLICY "Allow read access to game_context" ON game_context FOR SELECT USING (true);
CREATE POLICY "Allow read access to injury_impact" ON injury_impact FOR SELECT USING (true);
CREATE POLICY "Allow read access to line_movements" ON line_movements FOR SELECT USING (true);

-- Users can only access their own betting data
CREATE POLICY "Users can view own bet history" ON bet_history FOR SELECT USING (user_id = auth.uid());
CREATE POLICY "Users can insert own bets" ON bet_history FOR INSERT WITH CHECK (user_id = auth.uid());
CREATE POLICY "Users can update own bets" ON bet_history FOR UPDATE USING (user_id = auth.uid());

CREATE POLICY "Users can view own bankroll" ON user_bankroll FOR SELECT USING (user_id = auth.uid());
CREATE POLICY "Users can update own bankroll" ON user_bankroll FOR UPDATE USING (user_id = auth.uid());
CREATE POLICY "Users can insert own bankroll" ON user_bankroll FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can view own exposure" ON active_exposure FOR SELECT USING (user_id = auth.uid());
CREATE POLICY "Users can insert own exposure" ON active_exposure FOR INSERT WITH CHECK (user_id = auth.uid());
CREATE POLICY "Users can update own exposure" ON active_exposure FOR UPDATE USING (user_id = auth.uid());

CREATE POLICY "Users can view own alerts" ON user_alerts FOR SELECT USING (user_id = auth.uid());
CREATE POLICY "Users can update own alerts" ON user_alerts FOR UPDATE USING (user_id = auth.uid());

-- ==================================================================
-- END
-- ==================================================================
