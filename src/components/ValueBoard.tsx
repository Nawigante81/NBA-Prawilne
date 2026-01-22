import React, { useState, useEffect, useCallback } from 'react';
import { Target, Filter, TrendingUp, Clock, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { ValueMetrics } from './ValueMetrics';
import { useI18n } from '../i18n/useI18n';
import { api } from '../services/api';
import {
  calculateEV,
  americanToDecimal,
  formatAmericanOdds,
  formatCurrency,
  getRecommendation,
} from '../utils/bettingCalculations';

interface GameData {
  id: string;
  home_team: string;
  away_team: string;
  commence_time: string;
}

interface ValueOpportunity {
  game_id: string;
  market_type: 'h2h' | 'spreads' | 'totals' | 'spread' | 'total';
  selection: string;
  point?: number | null;
  price?: number | null;
  model_prob: number;
  edge_prob: number;
  ev?: number | null;
  kelly_fraction?: number | null;
  why_bullets?: string[];
  decision?: 'BET' | 'NO_BET';
  reasons?: string[];
  commence_time?: string | null;
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
  
  const [filters, setFilters] = useState<FilterState>({
    minEdge: 0,
    minConfidence: 60,
    markets: ['h2h', 'spread', 'total'],
    showValueOnly: true,
    sortBy: 'edge',
    sortDirection: 'desc'
  });
  
  const fetchOpportunities = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const [valueResp, gamesResp] = await Promise.all([
        api.valueBoard.getToday(),
        api.games.getToday(),
      ]);

      const games = (gamesResp as { games?: GameData[] })?.games || [];
      const byGameId = new Map<string, GameData>();
      games.forEach((game) => {
        if (game.id) {
          byGameId.set(game.id, game);
        }
      });

      const items = (valueResp as { items?: ValueOpportunity[] })?.items || [];
      const transformed = items.map((item) => ({
        ...item,
        commence_time: item.commence_time || byGameId.get(item.game_id)?.commence_time || null,
      }));
      setOpportunities(transformed);
    } catch (err) {
      setError(t('common.error'));
      console.error('Failed to fetch opportunities:', err);
    } finally {
      setLoading(false);
    }
  }, [t]);
  
  useEffect(() => {
    fetchOpportunities();
  }, [fetchOpportunities]);
  
  // Apply filters
  const filteredOpportunities = opportunities.filter(opp => {
    if (filters.showValueOnly && opp.decision === 'NO_BET') return false;
    if (opp.edge_prob < filters.minEdge / 100) return false;
    const marketKey = opp.market_type === 'spreads' ? 'spread' : opp.market_type === 'totals' ? 'total' : opp.market_type;
    if (!filters.markets.includes(marketKey)) return false;
    
    const confidence = Math.min(0.95, Math.max(0.50, opp.model_prob + opp.edge_prob * 2));
    if (confidence * 100 < filters.minConfidence) return false;
    
    return true;
  });
  
  // Sort opportunities
  const sortedOpportunities = [...filteredOpportunities].sort((a, b) => {
    let comparison = 0;
    
    switch (filters.sortBy) {
      case 'edge':
        comparison = b.edge_prob - a.edge_prob;
        break;
      case 'ev': {
        const oddsA = a.price ? americanToDecimal(a.price) : 1;
        const oddsB = b.price ? americanToDecimal(b.price) : 1;
        const evA = calculateEV(oddsA, a.model_prob, 100);
        const evB = calculateEV(oddsB, b.model_prob, 100);
        comparison = evB - evA;
        break;
      }
      case 'time': {
        const timeA = new Date(a.commence_time || 0).getTime();
        const timeB = new Date(b.commence_time || 0).getTime();
        comparison = timeA - timeB;
        break;
      }
    }
    
    return filters.sortDirection === 'desc' ? comparison : -comparison;
  });
  
  const valueCount = opportunities.filter(o => o.decision === 'BET').length;
  const totalEV = sortedOpportunities.reduce((sum, opp) => {
    const odds = opp.price ? americanToDecimal(opp.price) : 1;
    return sum + calculateEV(odds, opp.model_prob, 100);
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
                onChange={(e) => setFilters({ ...filters, sortBy: e.target.value as FilterState['sortBy'] })}
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
            const confidence = Math.min(0.95, Math.max(0.50, opp.model_prob + opp.edge_prob * 2));
            const recommendation = getRecommendation(opp.edge_prob, confidence);
            const gameTime = new Date(opp.commence_time || Date.now());
            const decimalOdds = opp.price ? americanToDecimal(opp.price) : 1;
            const reasons = opp.reasons || [];
            
            return (
              <div key={`${opp.game_id}-${index}`} className="glass-card p-6 hover:bg-white/5 transition-colors">
                {/* Game Header */}
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-xl font-bold text-white mb-1">
                      {opp.selection}
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
                      <span>{opp.decision === 'BET' ? 'VALUE' : 'NO BET'}</span>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <div className="text-2xl font-bold text-white mb-1">
                      {opp.price !== null && opp.price !== undefined ? `${opp.price > 0 ? '+' : ''}${opp.price}` : '—'}
                    </div>
                    <div className="text-sm text-gray-400">
                      Decimal: {decimalOdds.toFixed(2)}
                    </div>
                  </div>
                </div>
                
                {/* Value Metrics */}
                <ValueMetrics
                  odds={decimalOdds}
                  modelProb={opp.model_prob}
                  edge={opp.edge_prob}
                  stake={100}
                  compact={false}
                />

                {opp.why_bullets && opp.why_bullets.length > 0 && (
                  <div className="mt-4 text-sm text-gray-400 space-y-1">
                    {opp.why_bullets.map((bullet) => (
                      <div key={bullet}>• {bullet}</div>
                    ))}
                  </div>
                )}

                {reasons.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2 text-xs text-gray-400">
                    {reasons.map((reason) => (
                      <span key={reason} className="rounded-full bg-gray-800 px-2 py-1 text-gray-300">
                        {reason}
                      </span>
                    ))}
                  </div>
                )}
                
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
