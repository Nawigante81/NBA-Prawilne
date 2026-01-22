/**
 * Betting Analytics Types
 * Enhanced types for betting decision support
 */

// ============================================================================
// Value Betting Types
// ============================================================================

export interface ValueMetrics {
  ev: number;                    // Expected Value in currency ($2.50)
  evPercentage: number;          // EV as percentage (5.2%)
  impliedProb: number;           // From bookmaker odds (52.4%)
  fairProb: number;              // From model (58.1%)
  edge: number;                  // fairProb - impliedProb (5.7%)
  edgePoints?: number;           // For spreads (2.3 pts)
  recommendation: 'STRONG_PLAY' | 'PLAY' | 'LEAN' | 'NO_PLAY';
  confidence: number;            // 0-100
}

export interface ValueBet {
  id: string;
  game_id: string;
  market_type: 'h2h' | 'spread' | 'total';
  selection: string;
  odds: number;
  bookmaker: string;
  metrics: ValueMetrics;
  game_info: {
    home_team: string;
    away_team: string;
    commence_time: string;
  };
  context?: GameContext;
}

// ============================================================================
// Game Context Types
// ============================================================================

export interface GameContext {
  game_id: string;
  home_team: string;
  away_team: string;
  game_date: string;
  
  // Rest & Fatigue
  rest: {
    home_rest_days: number;
    away_rest_days: number;
    home_b2b: boolean;
    away_b2b: boolean;
    home_3in4: boolean;
    away_3in4: boolean;
    advantage: 'HOME' | 'AWAY' | 'NEUTRAL';
  };
  
  // Travel
  travel?: {
    away_travel_miles: number;
    away_timezone_change: number;
  };
  
  // Injuries
  injuries: InjuryImpact[];
}

export interface InjuryImpact {
  player_name: string;
  team: string;
  status: 'OUT' | 'DOUBTFUL' | 'QUESTIONABLE' | 'PROBABLE';
  impact_points: number;
  projected_replacement?: string;
}

// ============================================================================
// Bet Tracking Types
// ============================================================================

export interface BetPlacement {
  game_id: string;
  market_type: 'h2h' | 'spread' | 'total';
  selection: string;
  odds: number;
  stake: number;
  bookmaker?: string;
  model_edge?: number;
  model_confidence?: number;
  model_ev?: number;
}

export interface BetHistory {
  id: string;
  user_id: string;
  game_id: string;
  market_type: 'h2h' | 'spread' | 'total';
  selection: string;
  odds: number;
  stake: number;
  placed_at: string;
  
  // Result
  result?: 'won' | 'lost' | 'push' | 'pending';
  profit?: number;
  settled_at?: string;
  
  // CLV
  closing_odds?: number;
  clv_percentage?: number;
  
  // Model metrics
  model_edge?: number;
  model_confidence?: number;
  model_ev?: number;
}

// ============================================================================
// Performance Types
// ============================================================================

export interface PerformanceMetrics {
  total_bets: number;
  wins: number;
  losses: number;
  pushes: number;
  win_rate: number;           // %
  total_wagered: number;
  total_profit: number;
  roi: number;                // %
  yield: number;              // %
  avg_clv: number;            // %
  avg_odds: number;
  
  // By market
  by_market: {
    [key in 'h2h' | 'spread' | 'total']: MarketPerformance;
  };
  
  // Recent form
  last_10: RecentForm;
  last_30: RecentForm;
}

export interface MarketPerformance {
  bets: number;
  wins: number;
  win_rate: number;
  total_wagered: number;
  total_profit: number;
  roi: number;
}

export interface RecentForm {
  bets: number;
  wins: number;
  profit: number;
  roi: number;
}

// ============================================================================
// Bankroll Types
// ============================================================================

export interface BankrollSettings {
  user_id: string;
  total_bankroll: number;
  current_balance: number;
  daily_limit_pct: number;      // % of bankroll
  max_bet_pct: number;          // % of bankroll
  updated_at: string;
}

export interface ActiveExposure {
  total_exposure: number;        // Total $ at risk
  num_pending_bets: number;
  bets: Array<{
    game_id: string;
    stake: number;
    status: 'pending' | 'won' | 'lost' | 'push';
  }>;
}

export interface StakeRecommendation {
  kelly_stake: number;           // Full Kelly
  quarter_kelly: number;         // 0.25 Kelly (recommended)
  half_kelly: number;            // 0.5 Kelly
  flat_stake: number;            // Flat 1-2% of bankroll
  recommended: number;           // Final recommendation
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  warnings: string[];
}

// ============================================================================
// Line Movement Types
// ============================================================================

export interface LineSnapshot {
  timestamp: string;
  bookmaker: string;
  market_type: 'h2h' | 'spread' | 'total';
  line_value?: number;           // For spreads/totals
  odds: number;
}

export interface LineMovement {
  game_id: string;
  market_type: 'h2h' | 'spread' | 'total';
  opening: LineSnapshot;
  current: LineSnapshot;
  movement: {
    value: number;
    percentage: number;
    direction: 'UP' | 'DOWN' | 'STABLE';
  };
  history: LineSnapshot[];
}

// ============================================================================
// Alerts Types
// ============================================================================

export interface Alert {
  id: string;
  alert_type: 'injury' | 'line_move' | 'value' | 'result';
  game_id?: string;
  title: string;
  message: string;
  severity: 'info' | 'warning' | 'critical';
  is_read: boolean;
  created_at: string;
}

export interface AlertRule {
  alert_type: 'injury' | 'line_move' | 'value';
  conditions: {
    min_edge?: number;
    min_confidence?: number;
    line_move_threshold?: number;  // % or points
    teams?: string[];
    markets?: ('h2h' | 'spread' | 'total')[];
  };
}

// ============================================================================
// Filter Types
// ============================================================================

export interface FilterState {
  minEdge: number;               // 0-20%
  minConfidence: number;         // 0-100%
  markets: ('h2h' | 'spread' | 'total')[];
  bookmakers: string[];
  injuryFlag: boolean;           // Games with key injuries
  restAdvantage: boolean;        // Teams with rest edge
  liveOnly: boolean;
  valueBetsOnly: boolean;        // Edge > 0
  teams: string[];
}

// ============================================================================
// API Response Types
// ============================================================================

export interface ValueBetsResponse {
  generated_at: string;
  count: number;
  bets: ValueBet[];
}

export interface PerformanceResponse {
  user_id: string;
  metrics: PerformanceMetrics;
}

export interface LineMovementResponse {
  game_id: string;
  movements: {
    [key in 'h2h' | 'spread' | 'total']?: LineMovement;
  };
}

// ============================================================================
// Props Types
// ============================================================================

export interface PlayerProp {
  player_name: string;
  team: string;
  stat_type: 'points' | 'rebounds' | 'assists' | 'threes' | 'steals' | 'blocks';
  line: number;
  over_odds: number;
  under_odds: number;
  prediction: number;
  recommendation: 'OVER' | 'UNDER' | 'NO_VALUE';
  confidence: number;
  hit_rate: number;            // Historical % over line
  recent_games: number[];
  projected_minutes?: number;
}

export interface PropsBoard {
  generated_at: string;
  props: PlayerProp[];
}

// ============================================================================
// Utility Types
// ============================================================================

export type SortDirection = 'asc' | 'desc';
export type SortField = 'edge' | 'ev' | 'confidence' | 'odds' | 'commence_time';

export interface SortConfig {
  field: SortField;
  direction: SortDirection;
}

export interface PaginationConfig {
  page: number;
  perPage: number;
  total: number;
}
