import React from 'react';
import { RefreshCw } from 'lucide-react';

export interface BettingStatsData {
  ats_season: {
    wins: number;
    losses: number;
    pushes: number;
    percentage: number;
    avg_margin: number; // average margin vs spread
  };
  ats_last_20: {
    wins: number;
    losses: number;
    pushes: number;
    percentage: number;
    avg_margin: number;
  };
  ou_season: {
    overs: number;
    unders: number;
    pushes: number;
    percentage: number; // percentage of overs
    avg_margin: number; // average margin vs total
  };
  ou_last_20: {
    overs: number;
    unders: number;
    pushes: number;
    percentage: number;
    avg_margin: number;
  };
  avg_total_points: {
    season: number;
    last_20: number;
  };
  splits?: {
    home_ats?: string;
    away_ats?: string;
    home_ou?: string;
    away_ou?: string;
  };
}

interface BettingStatsCardProps {
  data: BettingStatsData | null;
  loading?: boolean;
  onRefresh?: () => void;
  teamName?: string;
}

const BettingStatsCard: React.FC<BettingStatsCardProps> = ({ 
  data, 
  loading, 
  onRefresh,
  teamName 
}) => {
  if (loading) {
    return (
      <div className="glass-card p-6">
        <h3 className="text-lg font-bold text-white mb-4">Statystyki zakładów</h3>
        <div className="flex items-center justify-center h-32">
          <div className="w-8 h-8 border-4 border-blue-400/30 border-t-blue-400 rounded-full animate-spin"></div>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="glass-card p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-white">Statystyki zakładów</h3>
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="p-2 hover:bg-white/10 rounded-lg transition-colors"
              title="Odśwież dane"
            >
              <RefreshCw className="w-4 h-4 text-gray-400" />
            </button>
          )}
        </div>
        <div className="text-center py-8">
          <p className="text-gray-400 mb-4">Brak danych - uruchom synchronizację</p>
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white transition-colors"
            >
              Odśwież
            </button>
          )}
        </div>
      </div>
    );
  }

  const formatRecord = (w: number, l: number, p: number) => {
    return `${w}-${l}${p > 0 ? `-${p}` : ''}`;
  };

  const formatPercentage = (pct: number) => {
    return `${(pct * 100).toFixed(1)}%`;
  };

  const formatMargin = (margin: number) => {
    return margin > 0 ? `+${margin.toFixed(1)}` : `${margin.toFixed(1)}`;
  };

  const getPercentageColor = (pct: number) => {
    if (pct >= 0.55) return 'text-green-400';
    if (pct >= 0.48) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <div className="glass-card p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-white">Statystyki zakładów</h3>
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="p-2 hover:bg-white/10 rounded-lg transition-colors"
            title="Odśwież dane"
          >
            <RefreshCw className="w-4 h-4 text-gray-400 hover:text-white" />
          </button>
        )}
      </div>

      <div className="space-y-6">
        {/* ATS Stats */}
        <div>
          <div className="text-sm font-semibold text-gray-300 mb-3">Against The Spread (ATS)</div>
          <div className="grid grid-cols-2 gap-4">
            <div className="border border-gray-700/50 rounded-lg p-3">
              <div className="text-xs text-gray-400 mb-1">Season</div>
              <div className="text-lg font-bold text-white mb-1">
                {formatRecord(data.ats_season.wins, data.ats_season.losses, data.ats_season.pushes)}
              </div>
              <div className={`text-sm font-semibold ${getPercentageColor(data.ats_season.percentage)}`}>
                {formatPercentage(data.ats_season.percentage)}
              </div>
              <div className="text-xs text-gray-400 mt-1">
                Avg: {formatMargin(data.ats_season.avg_margin)} pts
              </div>
            </div>

            <div className="border border-gray-700/50 rounded-lg p-3">
              <div className="text-xs text-gray-400 mb-1">Last 20</div>
              <div className="text-lg font-bold text-white mb-1">
                {formatRecord(data.ats_last_20.wins, data.ats_last_20.losses, data.ats_last_20.pushes)}
              </div>
              <div className={`text-sm font-semibold ${getPercentageColor(data.ats_last_20.percentage)}`}>
                {formatPercentage(data.ats_last_20.percentage)}
              </div>
              <div className="text-xs text-gray-400 mt-1">
                Avg: {formatMargin(data.ats_last_20.avg_margin)} pts
              </div>
            </div>
          </div>
        </div>

        {/* O/U Stats */}
        <div>
          <div className="text-sm font-semibold text-gray-300 mb-3">Over/Under (O/U)</div>
          <div className="grid grid-cols-2 gap-4">
            <div className="border border-gray-700/50 rounded-lg p-3">
              <div className="text-xs text-gray-400 mb-1">Season</div>
              <div className="text-lg font-bold text-white mb-1">
                {data.ou_season.overs}O-{data.ou_season.unders}U
                {data.ou_season.pushes > 0 && `-${data.ou_season.pushes}P`}
              </div>
              <div className={`text-sm font-semibold ${getPercentageColor(data.ou_season.percentage)}`}>
                {formatPercentage(data.ou_season.percentage)} Over
              </div>
              <div className="text-xs text-gray-400 mt-1">
                Avg: {formatMargin(data.ou_season.avg_margin)} pts
              </div>
            </div>

            <div className="border border-gray-700/50 rounded-lg p-3">
              <div className="text-xs text-gray-400 mb-1">Last 20</div>
              <div className="text-lg font-bold text-white mb-1">
                {data.ou_last_20.overs}O-{data.ou_last_20.unders}U
                {data.ou_last_20.pushes > 0 && `-${data.ou_last_20.pushes}P`}
              </div>
              <div className={`text-sm font-semibold ${getPercentageColor(data.ou_last_20.percentage)}`}>
                {formatPercentage(data.ou_last_20.percentage)} Over
              </div>
              <div className="text-xs text-gray-400 mt-1">
                Avg: {formatMargin(data.ou_last_20.avg_margin)} pts
              </div>
            </div>
          </div>
        </div>

        {/* Average Total Points */}
        <div>
          <div className="text-sm font-semibold text-gray-300 mb-3">Average Total Points</div>
          <div className="grid grid-cols-2 gap-4">
            <div className="border border-gray-700/50 rounded-lg p-3">
              <div className="text-xs text-gray-400 mb-1">Season</div>
              <div className="text-xl font-bold text-blue-400">
                {data.avg_total_points.season.toFixed(1)}
              </div>
            </div>
            <div className="border border-gray-700/50 rounded-lg p-3">
              <div className="text-xs text-gray-400 mb-1">Last 20</div>
              <div className="text-xl font-bold text-blue-400">
                {data.avg_total_points.last_20.toFixed(1)}
              </div>
            </div>
          </div>
        </div>

        {/* Home/Away Splits (if available) */}
        {data.splits && (
          <div>
            <div className="text-sm font-semibold text-gray-300 mb-3">Home/Away Splits</div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              {data.splits.home_ats && (
                <div>
                  <span className="text-gray-400">Home ATS:</span>
                  <span className="text-white ml-2 font-medium">{data.splits.home_ats}</span>
                </div>
              )}
              {data.splits.away_ats && (
                <div>
                  <span className="text-gray-400">Away ATS:</span>
                  <span className="text-white ml-2 font-medium">{data.splits.away_ats}</span>
                </div>
              )}
              {data.splits.home_ou && (
                <div>
                  <span className="text-gray-400">Home O/U:</span>
                  <span className="text-white ml-2 font-medium">{data.splits.home_ou}</span>
                </div>
              )}
              {data.splits.away_ou && (
                <div>
                  <span className="text-gray-400">Away O/U:</span>
                  <span className="text-white ml-2 font-medium">{data.splits.away_ou}</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default BettingStatsCard;
