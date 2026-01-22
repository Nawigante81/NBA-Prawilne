import React from 'react';
import { TrendingUp, TrendingDown, Minus, AlertCircle } from 'lucide-react';

export interface PlayerStatus {
  player_name: string;
  team: string;
  status: 'OUT' | 'DOUBTFUL' | 'QUESTIONABLE' | 'PROBABLE' | 'ACTIVE' | 'UNKNOWN';
  minutes_last_5_avg: number | null;
  minutes_trend: {
    change: number | null;
    direction: 'UP' | 'DOWN' | 'STABLE' | null;
  };
  position?: string;
  injury_note?: string;
}

interface KeyPlayersCardProps {
  players: PlayerStatus[];
  loading?: boolean;
}

const KeyPlayersCard: React.FC<KeyPlayersCardProps> = ({ players, loading }) => {
  if (loading) {
    return (
      <div className="glass-card p-6">
        <h3 className="text-lg font-bold text-white mb-4">Kluczowi gracze</h3>
        <div className="flex items-center justify-center h-24">
          <div className="w-6 h-6 border-4 border-blue-400/30 border-t-blue-400 rounded-full animate-spin"></div>
        </div>
      </div>
    );
  }

  if (!players || players.length === 0) {
    return (
      <div className="glass-card p-6">
        <h3 className="text-lg font-bold text-white mb-4">Kluczowi gracze</h3>
        <p className="text-sm text-gray-400 text-center py-4">Brak danych o graczach</p>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'OUT': return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'DOUBTFUL': return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
      case 'QUESTIONABLE': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'PROBABLE': return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'ACTIVE': return 'bg-green-500/20 text-green-400 border-green-500/30';
      default: return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  const renderTrendIcon = (direction: string | null) => {
    if (direction === 'UP') return <TrendingUp className="w-3 h-3 text-green-400" />;
    if (direction === 'DOWN') return <TrendingDown className="w-3 h-3 text-red-400" />;
    if (direction === 'STABLE') return <Minus className="w-3 h-3 text-gray-400" />;
    return null;
  };

  return (
    <div className="glass-card p-6">
      <h3 className="text-lg font-bold text-white mb-4">Kluczowi gracze</h3>
      
      <div className="space-y-3">
        {players.map((player, idx) => (
          <div
            key={idx}
            className="border border-gray-700/50 rounded-lg p-4 hover:bg-white/5 transition-all"
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h4 className="font-semibold text-white">{player.player_name}</h4>
                  {player.status !== 'ACTIVE' && player.status !== 'UNKNOWN' && (
                    <AlertCircle className="w-4 h-4 text-yellow-400" />
                  )}
                </div>
                {player.position && (
                  <div className="text-xs text-gray-400">{player.position}</div>
                )}
              </div>
              <div className={`px-2 py-1 rounded border text-xs font-semibold ${getStatusColor(player.status)}`}>
                {player.status}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <div className="text-gray-400 text-xs mb-1">Minutes (Last 5 avg)</div>
                {player.minutes_last_5_avg !== null ? (
                  <div className="flex items-center gap-2">
                    <span className="text-white font-medium">
                      {player.minutes_last_5_avg.toFixed(1)} min
                    </span>
                    {player.minutes_trend.direction && renderTrendIcon(player.minutes_trend.direction)}
                  </div>
                ) : (
                  <span className="text-gray-500">N/A</span>
                )}
              </div>

              {player.minutes_trend.change !== null && (
                <div>
                  <div className="text-gray-400 text-xs mb-1">Trend</div>
                  <div className={`text-sm font-medium ${
                    player.minutes_trend.direction === 'UP' ? 'text-green-400' :
                    player.minutes_trend.direction === 'DOWN' ? 'text-red-400' :
                    'text-gray-400'
                  }`}>
                    {player.minutes_trend.change > 0 ? '+' : ''}
                    {player.minutes_trend.change.toFixed(1)} min
                  </div>
                </div>
              )}
            </div>

            {player.injury_note && (
              <div className="mt-3 pt-3 border-t border-gray-700/50">
                <div className="text-xs text-yellow-400 flex items-start gap-2">
                  <AlertCircle className="w-3 h-3 mt-0.5 flex-shrink-0" />
                  <span>{player.injury_note}</span>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default KeyPlayersCard;
