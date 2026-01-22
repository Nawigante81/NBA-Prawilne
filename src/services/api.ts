// API Service Layer for NBA Analytics Frontend
// Handles all communication with the FastAPI backend
import { useMemo } from 'react';
import { clearAuthState, getAuthHeader } from './auth';

const API_BASE =
  (typeof import.meta.env.VITE_API_BASE_URL === 'string' && import.meta.env.VITE_API_BASE_URL.trim() !== ''
    ? import.meta.env.VITE_API_BASE_URL.trim()
    : (
        typeof window !== 'undefined'
          ? `http://${window.location.hostname}:8000`
          : 'http://localhost:8000'
      ));

type UnknownRecord = Record<string, unknown>;

// Generic API request helper with error handling
async function apiRequest<T>(
  endpoint: string, 
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  
  const config: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(),
      ...options.headers,
    },
    ...options,
  };

  try {
    console.log(`🌐 API Request: ${config.method || 'GET'} ${url}`);
    
    const response = await fetch(url, config);

    if (response.status === 401) {
      clearAuthState();
    }

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`❌ API Error: ${response.status} ${response.statusText}`, errorText);
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log(`✅ API Success: ${endpoint}`, data);
    return data;
  } catch (error) {
    console.error(`💥 API Request Failed: ${endpoint}`, error);
    throw error;
  }
}

// Teams API
export const teamsApi = {
  // Get all teams
  getAll: () => apiRequest<{teams: UnknownRecord[]}>('/api/teams'),
  
  // Get comprehensive teams analysis
  getAllAnalysis: (includeBetting: boolean = true) => apiRequest<{
    teams: UnknownRecord[], 
    count: number, 
    conferences: {Eastern: UnknownRecord[], Western: UnknownRecord[]}
  }>(`/api/teams/analysis?include_betting=${includeBetting}`),
  
  // Get team players
  getPlayers: (teamAbbrev: string) => 
    apiRequest<{team: string, players: UnknownRecord[], count: number}>(`/api/teams/${teamAbbrev}/players`),
  
  // Get detailed team analysis
  getAnalysis: (teamAbbrev: string) => apiRequest<UnknownRecord>(`/api/teams/${teamAbbrev}/analysis`),

  // Get detailed betting stats for team
  getBettingStatsDetail: (teamAbbrev: string, window: number = 20) =>
    apiRequest<UnknownRecord>(`/api/team/${teamAbbrev}/betting-stats?window=${window}`),

  // Get next game info for team
  getNextGame: (teamAbbrev: string) =>
    apiRequest<UnknownRecord>(`/api/team/${teamAbbrev}/next-game`),

  // Get key players with minutes trends
  getKeyPlayers: (teamAbbrev: string) =>
    apiRequest<UnknownRecord>(`/api/team/${teamAbbrev}/key-players`),

  // Get value panel data
  getValuePanel: (teamAbbrev: string) =>
    apiRequest<UnknownRecord>(`/api/team/${teamAbbrev}/value`),
  
  // Compare teams
  compare: (team1: string, team2: string, team3?: string) => {
    const params = new URLSearchParams({ team1, team2 });
    if (team3) params.append('team3', team3);
    return apiRequest<UnknownRecord>(`/api/teams/compare?${params}`);
  }
};

// Players API  
export const playersApi = {
  // Get all players with optional filters
  getAll: (filters?: {team?: string, position?: string, active?: boolean, includeStats?: boolean}) => {
    const params = new URLSearchParams();
    if (filters?.team) params.set('team', filters.team);
    if (filters?.position) params.set('position', filters.position);
    if (filters?.active !== undefined) params.set('active', filters.active.toString());
    if (filters?.includeStats !== undefined) params.set('include_stats', filters.includeStats.toString());
    
    const query = params.toString() ? `?${params}` : '';
    return apiRequest<{players: UnknownRecord[], count: number}>(`/api/players${query}`);
  },
  
  // Get player details
  getById: (playerId: string) => 
    apiRequest<{player: UnknownRecord}>(`/api/players/${playerId}`),
  
  // Search players by name
  searchByName: (name: string) => 
    apiRequest<{query: string, players: UnknownRecord[], count: number}>(`/api/players/search/${name}`),
};

// Games API
export const gamesApi = {
  // Get today's games
  getToday: () => apiRequest<{games: UnknownRecord[]}>('/api/games/today'),
  
  // Get game odds
  getOdds: (gameId: string) => apiRequest<{odds: UnknownRecord[]}>(`/api/odds/${gameId}`),

  // Get current game odds for markets
  getOddsCurrent: (gameId: string) => apiRequest<UnknownRecord>(`/api/game/${gameId}/odds/current`),

  // Get odds movement timeline
  getOddsMovement: (gameId: string) => apiRequest<UnknownRecord>(`/api/game/${gameId}/odds/movement`),
};

// Focus Teams API
export const focusTeamsApi = {
  // Get today's focus teams based on best edge
  getToday: (limit: number = 5) => apiRequest<{teams: UnknownRecord[]}>(`/api/focus-teams/today?limit=${limit}`),
};

// Reports API
export const reportsApi = {
  // Get 7:50 AM report (previous day analysis)
  get750Report: () => apiRequest<UnknownRecord>('/api/reports/750am'),
  
  // Get 8:00 AM report (morning summary)
  get800Report: () => apiRequest<UnknownRecord>('/api/reports/800am'),
  
  // Get 11:00 AM report (game-day scouting)
  get1100Report: () => apiRequest<UnknownRecord>('/api/reports/1100am'),

  // Get saved reports
  getSaved: (limit: number = 10) =>
    apiRequest<{reports: UnknownRecord[], count: number}>(`/api/reports?limit=${limit}`),
};

// Bulls Analysis API
export const bullsApi = {
  // Get Bulls-focused analysis
  getAnalysis: () => apiRequest<UnknownRecord>('/api/bulls-analysis'),
};

// Betting API
export const bettingApi = {
  // Get betting recommendations
  getRecommendations: () => apiRequest<UnknownRecord>('/api/betting-recommendations'),
  
  // Get arbitrage opportunities
  getArbitrageOpportunities: () => apiRequest<{opportunities: UnknownRecord[], count: number}>('/api/arbitrage-opportunities'),
  
  // Calculate Kelly criterion
  calculateKelly: (estimatedProb: number, decimalOdds: number) => 
    apiRequest<{kelly_fraction: number, percentage: number, recommended_stake: string}>(
      `/api/kelly-calculator?estimated_prob=${estimatedProb}&decimal_odds=${decimalOdds}`
    ),
  
  // Get performance metrics
  getPerformanceMetrics: () => apiRequest<UnknownRecord>('/api/performance-metrics'),
  
  // Generate betting slip
  generateBettingSlip: (bets: UnknownRecord[], totalStake: number = 100) => 
    apiRequest<UnknownRecord>('/api/betting-slip', {
      method: 'POST',
      body: JSON.stringify({bets, total_stake: totalStake}),
    }),
};

// System API
export const systemApi = {
  // Health check
  getHealth: () => apiRequest<{status: string, timestamp: string}>('/health'),
  
  // Get application status
  getStatus: () => apiRequest<UnknownRecord>('/api/status'),
  
  // Trigger roster scraping
  triggerRosterScrape: (season: string = '2025') => 
    apiRequest<{message: string, timestamp: string, status: string}>('/api/scrape/rosters', {
      method: 'POST',
      body: JSON.stringify({season}),
    }),
};

// Export combined API object
export const api = {
  teams: teamsApi,
  players: playersApi,
  games: gamesApi,
  focusTeams: focusTeamsApi,
  reports: reportsApi,
  bulls: bullsApi,
  betting: bettingApi,
  system: systemApi,
};

// React Hook for API calls with loading state
export function useApi() {
  return useMemo(() => ({
    // Quick access to common endpoints
    async getTeams() {
      try {
        const response = await api.teams.getAll();
        return response.teams || [];
      } catch (error) {
        console.error('Failed to fetch teams:', error);
        return [];
      }
    },
    
    async getTodayGames() {
      try {
        const response = await api.games.getToday();
        return response.games || [];
      } catch (error) {
        console.error('Failed to fetch today games:', error);
        return [];
      }
    },

    async getFocusTeamsToday(limit: number = 5) {
      try {
        const response = await api.focusTeams.getToday(limit);
        return response.teams || [];
      } catch (error) {
        console.error('Failed to fetch focus teams:', error);
        return [];
      }
    },
    
    async getBullsPlayers() {
      try {
        const response = await api.teams.getPlayers('CHI');
        return response.players || [];
      } catch (error) {
        console.error('Failed to fetch Bulls players:', error);
        return [];
      }
    },
    
    async getBullsAnalysis() {
      try {
        return await api.bulls.getAnalysis();
      } catch (error) {
        console.error('Failed to fetch Bulls analysis:', error);
        return null;
      }
    },
    
    async getBettingRecommendations() {
      try {
        return await api.betting.getRecommendations();
      } catch (error) {
        console.error('Failed to fetch betting recommendations:', error);
        return null;
      }
    },
    
    async getTeamsAnalysis(includeBetting: boolean = true) {
      try {
        return await api.teams.getAllAnalysis(includeBetting);
      } catch (error) {
        console.error('Failed to fetch teams analysis:', error);
        return { teams: [], count: 0, conferences: { Eastern: [], Western: [] } };
      }
    },
    
    async getPlayers(filters?: {team?: string, position?: string, active?: boolean}) {
      try {
        const response = await api.players.getAll(filters);
        return response.players || [];
      } catch (error) {
        console.error('Failed to fetch players:', error);
        return [];
      }
    },
  }), []);
}

export default api;
