// Type definitions for NBA Analysis Application
import { ComponentType } from 'react';

export interface GameData {
  id: string;
  home_team: string;
  away_team: string;
  game_date: string;
  status: 'scheduled' | 'live' | 'finished';
  home_score?: number;
  away_score?: number;
}

export interface OddsData {
  id: string;
  game_id: string;
  sportsbook: string;
  home_odds: number;
  away_odds: number;
  total_over: number;
  total_under: number;
  total_points: number;
  timestamp: string;
}

export interface BettingRecommendation {
  selection: string;
  odds: number;
  stake: number;
  confidence: number;
  reasoning: string;
  sportsbook: string;
  kelly_percentage: number;
}

export interface BullsAnalysis {
  last_game_recap: {
    opponent: string;
    result: string;
    key_performances: string[];
    team_stats: string;
    concerns: string;
  };
  current_form_analysis: {
    record_l10: string;
    ats_l10: string;
    home_record: string;
    vs_west: string;
    clutch_record: string;
  };
  player_projections: {
    [playerName: string]: {
      pts: number;
      reb: number;
      ast: number;
      betting_props: string;
    };
  };
}

export type ReportData = {
  timestamp: string;
  report_type: string;
} & Record<string, unknown>;

export interface PerformanceMetrics {
  roi: number;
  total_bets: number;
  win_rate: number;
  total_profit: number;
  total_wagered: number;
  avg_bet_size: number;
}

export interface ArbitrageOpportunity {
  game: string;
  profit_margin: number;
  home_bet: {
    sportsbook: string;
    odds: number;
    allocation: number;
  };
  away_bet: {
    sportsbook: string;
    odds: number;
    allocation: number;
  };
}

export interface KellyCalculation {
  kelly_fraction: number;
  percentage: number;
  recommended_stake: string;
}

export interface TeamBettingWindowStats {
  ats: {
    w: number;
    l: number;
    p: number;
    avg_spread_diff: number | null;
    win_pct: number | null;
  };
  ou: {
    o: number;
    u: number;
    p: number;
    avg_total_diff: number | null;
    over_pct: number | null;
  };
  avg_total_points: number | null;
  games_count: number;
}

export interface TeamBettingStatsResponse {
  team: string;
  team_name: string;
  window: number;
  last_window: TeamBettingWindowStats | null;
  season: TeamBettingWindowStats | null;
  has_data: boolean;
  missing_reason?: string | null;
  computed_at: string;
}

export interface NextGameInfo {
  game_id: string;
  commence_time: string;
  home_team: string;
  away_team: string;
  is_home: boolean;
  opponent: string;
}

export interface OddsSelection {
  outcome: string;
  point?: number | null;
  price?: number | null;
  decimal_price?: number | null;
  implied_prob?: number | null;
  bookmaker_key?: string | null;
  bookmaker_title?: string | null;
  last_update?: string | null;
}

export interface OddsCurrentResponse {
  game_id: string;
  markets: {
    h2h: OddsSelection[];
    spread: OddsSelection[];
    totals: OddsSelection[];
  };
  latest_update?: string | null;
  snapshot_age_hours?: number | null;
}

export interface OddsMovementPoint {
  ts: string;
  point: number;
}

export interface OddsMovementResponse {
  game_id: string;
  home_team?: string | null;
  away_team?: string | null;
  commence_time?: string | null;
  series: {
    spread_home: OddsMovementPoint[];
    spread_away: OddsMovementPoint[];
    total: OddsMovementPoint[];
  };
}

export interface KeyPlayerInfo {
  name: string;
  status: 'OUT' | 'Q' | 'PROBABLE' | 'ACTIVE' | 'UNKNOWN' | 'DNP_FLAG' | 'Probable' | 'Active' | 'Unknown';
  minutes_last5_avg: number | null;
  minutes_prev5_avg: number | null;
  minutes_trend: 'up' | 'down' | 'stable' | null;
  minutes_trend_delta: number | null;
  minutes_volatility: number | null;
  trend_note?: string | null;
}

export interface TeamValueRow {
  market: 'spreads' | 'totals' | 'h2h' | 'spread' | 'total' | 'moneyline';
  label: string;
  line: number | null;
  price: number | null;
  decimal_price: number | null;
  implied_prob: number | null;
  model_prob: number | null;
  edge: number | null;
  ev: number | null;
  stake_fraction: number;
  why_bullets?: string[];
  reasons?: string[];
  decision?: 'BET' | 'NO_BET';
}

export interface TeamValueResponse {
  team: string;
  next_game: NextGameInfo | null;
  value: TeamValueRow[];
  risk_flags: string[];
  snapshot_age_hours?: number | null;
  thresholds: {
    min_ev: number;
    min_edge: number;
    max_stake_fraction: number;
  };
}

export interface AIRecommendationRow {
  market: 'spreads' | 'totals' | 'h2h' | 'spread' | 'total' | 'moneyline';
  selection: string;
  line: number | null;
  price: number | null;
  implied_prob: number | null;
  model_prob: number | null;
  edge: number | null;
  ev: number | null;
  confidence: number;
  decision: 'BET' | 'NO_BET';
  reasons?: string[];
  why_bullets?: string[];
}

export interface AIRecommendationResponse {
  team: string;
  model_version: string;
  generated_at: string;
  next_game: NextGameInfo | null;
  top_pick?: AIRecommendationRow | null;
  recommendations: AIRecommendationRow[];
  risk_flags: string[];
}

export interface AIInsightResponse {
  provider: 'openai' | 'gemini' | 'none';
  available: boolean;
  model: string | null;
  summary: string | null;
  bullets: string[];
  warnings: string[];
  generated_at: string;
}

// Component Props
export interface NavItem {
  id: string;
  label: string;
  icon: ComponentType;
}

export interface LoadingState {
  isLoading: boolean;
  error?: string;
}

// API Response Types
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

// Section Types
export type SectionType = 
  | 'dashboard' 
  | 'reports' 
  | 'bulls-analysis' 
  | 'betting-recommendations' 
  | 'live-odds';

// Configuration
export interface AppConfig {
  API_BASE_URL: string;
  REFRESH_INTERVAL: number;
  TIMEZONE: string;
}
