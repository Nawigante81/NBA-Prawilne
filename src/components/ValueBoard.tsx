import React, { useState, useEffect } from 'react';
import { Target, Filter, TrendingUp, Clock, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { ValueMetrics, ConfidenceMeter } from './ValueMetrics';
import { useI18n } from '../i18n/useI18n';
import { api } from '../services/api';
import {
  calculateEV,
  calculateEdge,
  decimalToImpliedProbability,
  formatAmericanOdds,
  formatCurrency,
  formatPercentage,
  getRecommendation,
} from '../utils/bettingCalculations';

interface GameData {
  game_id: string;
  home_team: string;
  away_team: string;
  commence_time: string;
}

interface ValueOpportunity {
  game_id: string;
  market_type: 'h2h' | 'spread' | 'total';
  selection: string;
  odds: number;
  bookmaker: string;
  model_prob: number;
  edge: number;
  game: GameData;
}

interface FilterState {
  minEdge: number;
  minConfidence: number;
  markets: string[];
  showValueOnly: boolean;
  sortBy: 'edge' | 'ev' | 'time';
  sortDirection: 'asc' | 'desc';
}

/**
 * ValueBoard Component
 * Main dashboard for today's value betting opportunities
 */
const ValueBoard: React.FC = () => {
  const { t, locale } = useI18n();
  const [opportunities, setOpportunities] = useState<ValueOpportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [bankroll] = useState(1000);
  
  const [filters, setFilters] = useState<FilterState>({
    minEdge: 0,
    minConfidence: 60,
    markets: ['h2h', 'spread', 'total'],
    showValueOnly: true,
    sortBy: 'edge',
    sortDirection: 'desc'
  });
  
  useEffect(() => {
    fetchOpportunities();
  }, []);
  
  const fetchOpportunities = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // In production, this would fetch from /api/value/today
      // For now, we'll adapt the existing betting recommendations
      const resp = await api.betting.getRecommendations() as any;
      
      if (resp?.picks && Array.isArray(resp.picks)) {
        const transformed: ValueOpportunity[] = resp.picks.map((pick: any) => ({
          game_id: pick.game_id || '',
          market_type: 'h2h' as const,
          selection: pick.team || '',
          odds: pick.best_price || 2.0,
          bookmaker: pick.best_book || 'Unknown',
          model_prob: pick.consensus_prob || 0.5,
          edge: pick.edge || 0,
          game: {
            game_id: pick.game_id || '',
            home_team: pick.team || '',
            away_team: pick.opponent || '',
            commence_time: pick.commence_time || new Date().toISOString()
          }
        }));
        
        setOpportunities(transformed);
      }
    } catch (err) {
      setError(t('common.error'));
      console.error('Failed to fetch opportunities:', err);
    } finally {
      setLoading(false);
    }
  };
  
  // Apply filters
  const filteredOpportunities = opportunities.filter(opp => {
    if (filters.showValueOnly && opp.edge <= 0) return false;
    if (opp.edge < filters.minEdge / 100) return false;
    if (!filters.markets.includes(opp.market_type)) return false;
    
    // Approximate confidence (in production, would come from backend)
    const confidence = Math.min(0.95, Math.max(0.50, opp.model_prob + opp.edge * 2));
    if (confidence * 100 < filters.minConfidence) return false;
    
    return true;
  });
  
  // Sort opportunities
  const sortedOpportunities = [...filteredOpportunities].sort((a, b) => {
    let comparison = 0;
    
    switch (filters.sortBy) {
      case 'edge':
        comparison = b.edge - a.edge;
        break;
      case 'ev': {
        const evA = calculateEV(a.odds, a.model_prob, 100);
        const evB = calculateEV(b.odds, b.model_prob, 100);
        comparison = evB - evA;
        break;
      }
      case 'time': {
        const timeA = new Date(a.game.commence_time).getTime();
        const timeB = new Date(b.game.commence_time).getTime();
        comparison = timeA - timeB;
        break;
      }
    }
    
    return filters.sortDirection === 'desc' ? comparison : -comparison;
  });
  
  const valueCount = opportunities.filter(o => o.edge > 0).length;
  const totalEV = sortedOpportunities.reduce((sum, opp) => {
    return sum + calculateEV(opp.odds, opp.model_prob, 100);
  }, 0);
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-green-400/30 border-t-green-400 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-400">{t('betting.loading')}</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-white flex items-center gap-3">
            <Target className="w-8 h-8 text-green-400" />
            <span>Today's Value Board</span>
          </h2>
          <p className="text-gray-400 mt-1">
            Real-time value betting opportunities with EV calculations
          </p>
        </div>
        
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="glass-card px-4 py-2 flex items-center gap-2 hover:bg-white/10 transition-colors"
        >
          <Filter className="w-4 h-4" />
          <span>Filters</span>
          {showFilters ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>
      
      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass-card p-4">
          <div className="text-sm text-gray-400 mb-1">Total Games</div>
          <div className="text-2xl font-bold text-white">{opportunities.length}</div>
        </div>
        
        <div className="glass-card p-4">
          <div className="text-sm text-gray-400 mb-1">Value Opportunities</div>
          <div className="text-2xl font-bold text-green-400">{valueCount}</div>
        </div>
        
        <div className="glass-card p-4">
          <div className="text-sm text-gray-400 mb-1">Total EV</div>
          <div className={`text-2xl font-bold ${totalEV > 0 ? 'text-green-400' : 'text-gray-400'}`}>
            {formatCurrency(totalEV, true)}
          </div>
        </div>
        
        <div className="glass-card p-4">
          <div className="text-sm text-gray-400 mb-1">Showing</div>
          <div className="text-2xl font-bold text-blue-400">{sortedOpportunities.length}</div>
        </div>
      </div>
      
      {/* Filters Panel */}
      {showFilters && (
        <div className="glass-card p-6 space-y-4">
          <h3 className="text-lg font-semibold text-white mb-4">Filter Options</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Min Edge */}
            <div>
              <label className="block text-sm text-gray-400 mb-2">
                Min Edge: {filters.minEdge}%
              </label>
              <input
                type="range"
                min="0"
                max="20"
                step="0.5"
                value={filters.minEdge}
                onChange={(e) => setFilters({ ...filters, minEdge: Number(e.target.value) })}
                className="w-full"
              />
            </div>
            
            {/* Min Confidence */}
            <div>
              <label className="block text-sm text-gray-400 mb-2">
                Min Confidence: {filters.minConfidence}%
              </label>
              <input
                type="range"
                min="50"
                max="95"
                step="5"
                value={filters.minConfidence}
                onChange={(e) => setFilters({ ...filters, minConfidence: Number(e.target.value) })}
                className="w-full"
              />
            </div>
            
            {/* Sort By */}
            <div>
              <label className="block text-sm text-gray-400 mb-2">Sort By</label>
              <select
                value={filters.sortBy}
                onChange={(e) => setFilters({ ...filters, sortBy: e.target.value as any })}
                className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white"
              >
                <option value="edge">Edge (Highest)</option>
                <option value="ev">Expected Value</option>
                <option value="time">Game Time</option>
              </select>
            </div>
          </div>
          
          {/* Market Types */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">Markets</label>
            <div className="flex gap-2">
              {['h2h', 'spread', 'total'].map((market) => (
                <button
                  key={market}
                  onClick={() => {
                    const newMarkets = filters.markets.includes(market)
                      ? filters.markets.filter(m => m !== market)
                      : [...filters.markets, market];
                    setFilters({ ...filters, markets: newMarkets });
                  }}
                  className={`px-4 py-2 rounded-lg text-sm transition-colors ${
                    filters.markets.includes(market)
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  {market.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
          
          {/* Value Only Toggle */}
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="valueOnly"
              checked={filters.showValueOnly}
              onChange={(e) => setFilters({ ...filters, showValueOnly: e.target.checked })}
              className="w-4 h-4"
            />
            <label htmlFor="valueOnly" className="text-sm text-gray-300">
              Show only value bets (positive edge)
            </label>
          </div>
        </div>
      )}
      
      {/* Error State */}
      {error && (
        <div className="glass-card p-4 border border-red-500/30 flex items-center gap-3 text-red-300">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
        </div>
      )}
      
      {/* Opportunities List */}
      <div className="space-y-4">
        {sortedOpportunities.length === 0 ? (
          <div className="glass-card p-8 text-center text-gray-400">
            <TrendingUp className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>No value opportunities found with current filters</p>
            <button
              onClick={() => setFilters({
                ...filters,
                minEdge: 0,
                minConfidence: 50,
                showValueOnly: false
              })}
              className="mt-4 text-blue-400 hover:text-blue-300 underline"
            >
              Reset Filters
            </button>
          </div>
        ) : (
          sortedOpportunities.map((opp, index) => {
            const impliedProb = decimalToImpliedProbability(opp.odds);
            const ev = calculateEV(opp.odds, opp.model_prob, 100);
            const confidence = Math.min(0.95, Math.max(0.50, opp.model_prob + opp.edge * 2));
            const recommendation = getRecommendation(opp.edge, confidence);
            const gameTime = new Date(opp.game.commence_time);
            
            return (
              <div key={`${opp.game_id}-${index}`} className="glass-card p-6 hover:bg-white/5 transition-colors">
                {/* Game Header */}
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-xl font-bold text-white mb-1">
                      {opp.selection}
                      <span className="text-gray-400 mx-2">vs</span>
                      {opp.game.away_team}
                    </h3>
                    <div className="flex items-center gap-3 text-sm text-gray-400">
                      <span className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {gameTime.toLocaleTimeString(locale, { 
                          hour: '2-digit', 
                          minute: '2-digit',
                          timeZone: 'America/Chicago' 
                        })}
                      </span>
                      <span>•</span>
                      <span>{opp.market_type.toUpperCase()}</span>
                      <span>•</span>
                      <span>{opp.bookmaker}</span>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <div className="text-2xl font-bold text-white mb-1">
                      {formatAmericanOdds(opp.odds)}
                    </div>
                    <div className="text-sm text-gray-400">
                      Decimal: {opp.odds.toFixed(2)}
                    </div>
                  </div>
                </div>
                
                {/* Value Metrics */}
                <ValueMetrics
                  odds={opp.odds}
                  modelProb={opp.model_prob}
                  edge={opp.edge}
                  stake={100}
                  compact={false}
                />
                
                {/* Action Buttons */}
                <div className="mt-4 flex gap-3">
                  {recommendation !== 'NO_PLAY' && (
                    <>
                      <button className="flex-1 bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors">
                        Place Bet
                      </button>
                      <button className="px-6 py-3 glass-card hover:bg-white/10 text-white font-semibold rounded-lg transition-colors">
                        Track
                      </button>
                    </>
                  )}
                  {recommendation === 'NO_PLAY' && (
                    <button className="flex-1 bg-gray-700 text-gray-400 font-semibold py-3 px-6 rounded-lg cursor-not-allowed">
                      Skip - No Value
                    </button>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

export default ValueBoard;
