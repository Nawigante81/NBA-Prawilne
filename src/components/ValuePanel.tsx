import React from 'react';
import { TrendingUp, TrendingDown, AlertTriangle, Clock, Target } from 'lucide-react';

export interface MarketOdds {
  market_type: 'spread' | 'total' | 'h2h';
  line_value?: number;
  odds: number;
  bookmaker: string;
  implied_prob: number;
  model_prob: number;
  edge: number; // in percentage points
  ev: number; // expected value in currency
  ev_percentage: number;
  recommendation: 'VALUE' | 'PASS';
  stake_recommendations: {
    kelly_full: number;
    kelly_half: number;
    recommended: number;
    risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  };
  risk_flags?: string[];
}

export interface ValuePanelData {
  game_id: string;
  home_team: string;
  away_team: string;
  commence_time: string;
  markets: {
    spread?: MarketOdds;
    total?: MarketOdds;
    h2h?: MarketOdds;
  };
  last_updated: string;
}

interface ValuePanelProps {
  data: ValuePanelData | null;
  loading?: boolean;
  onRefresh?: () => void;
}

const ValuePanel: React.FC<ValuePanelProps> = ({ data, loading, onRefresh }) => {
  if (loading) {
    return (
      <div className="glass-card p-6">
        <div className="flex items-center justify-center h-32">
          <div className="w-8 h-8 border-4 border-blue-400/30 border-t-blue-400 rounded-full animate-spin"></div>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="glass-card p-6">
        <div className="text-center">
          <Target className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-white mb-2">Brak aktywnych meczów</h3>
          <p className="text-sm text-gray-400 mb-4">
            Nie znaleziono nadchodzących meczów dla tego zespołu
          </p>
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white text-sm transition-colors"
            >
              Odśwież
            </button>
          )}
        </div>
      </div>
    );
  }

  const renderMarketCard = (market: MarketOdds | undefined, label: string) => {
    if (!market) return null;

    const isValue = market.recommendation === 'VALUE';
    const edgeColor = market.edge >= 3 ? 'text-green-400' : market.edge >= 0 ? 'text-yellow-400' : 'text-red-400';

    return (
      <div className="glass-card p-4 hover:bg-white/5 transition-all">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h4 className="text-sm font-medium text-gray-400">{label}</h4>
            {market.line_value !== undefined && (
              <div className="text-lg font-bold text-white">
                {market.line_value > 0 ? '+' : ''}{market.line_value}
              </div>
            )}
            <div className="text-sm text-gray-300">
              Odds: {market.odds.toFixed(2)} ({market.bookmaker})
            </div>
          </div>
          <div className={`px-3 py-1 rounded-full text-xs font-bold ${
            isValue ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'
          }`}>
            {market.recommendation}
          </div>
        </div>

        <div className="space-y-2 mb-3">
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Implied Prob:</span>
            <span className="text-white">{(market.implied_prob * 100).toFixed(1)}%</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Model Prob:</span>
            <span className="text-white">{(market.model_prob * 100).toFixed(1)}%</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Edge:</span>
            <span className={`font-semibold ${edgeColor}`}>
              {market.edge > 0 ? '+' : ''}{market.edge.toFixed(1)}%
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">EV:</span>
            <span className={`font-semibold ${market.ev >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {market.ev >= 0 ? '+' : ''}{market.ev.toFixed(2)} ({market.ev_percentage > 0 ? '+' : ''}{market.ev_percentage.toFixed(1)}%)
            </span>
          </div>
        </div>

        {isValue && (
          <div className="border-t border-gray-700/50 pt-3">
            <div className="text-xs text-gray-400 mb-2">Recommended Stake:</div>
            <div className="flex items-center justify-between">
              <div className="text-sm text-white">
                <span className="font-bold">${market.stake_recommendations.recommended.toFixed(2)}</span>
                <span className="text-gray-400 ml-1">(½ Kelly)</span>
              </div>
              <div className={`px-2 py-1 rounded text-xs ${
                market.stake_recommendations.risk_level === 'LOW' ? 'bg-green-500/20 text-green-400' :
                market.stake_recommendations.risk_level === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-400' :
                'bg-red-500/20 text-red-400'
              }`}>
                {market.stake_recommendations.risk_level}
              </div>
            </div>
          </div>
        )}

        {market.risk_flags && market.risk_flags.length > 0 && (
          <div className="mt-3 pt-3 border-t border-gray-700/50">
            {market.risk_flags.map((flag, idx) => (
              <div key={idx} className="flex items-center gap-2 text-xs text-yellow-400 mb-1">
                <AlertTriangle className="w-3 h-3" />
                <span>{flag}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-bold text-white">Panel wartości (Value Panel)</h3>
          <p className="text-sm text-gray-400">
            {data.away_team} @ {data.home_team}
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <Clock className="w-4 h-4" />
          <span>{new Date(data.last_updated).toLocaleTimeString()}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {renderMarketCard(data.markets.spread, 'Spread')}
        {renderMarketCard(data.markets.total, 'Total')}
        {renderMarketCard(data.markets.h2h, 'Moneyline')}
      </div>

      {onRefresh && (
        <div className="text-center">
          <button
            onClick={onRefresh}
            className="px-4 py-2 bg-gray-700/50 hover:bg-gray-600/50 rounded-lg text-sm text-gray-300 hover:text-white transition-colors"
          >
            Odśwież dane
          </button>
        </div>
      )}
    </div>
  );
};

export default ValuePanel;
