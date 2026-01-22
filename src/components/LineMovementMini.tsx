import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export interface LineSnapshot {
  timestamp: string;
  value: number;
  bookmaker: string;
}

export interface LineMovementData {
  market_type: 'spread' | 'total';
  opening: LineSnapshot;
  current: LineSnapshot;
  closing?: LineSnapshot;
  history: LineSnapshot[];
  movement: {
    value_change: number;
    percentage_change?: number;
    direction: 'UP' | 'DOWN' | 'STABLE';
  };
}

interface LineMovementMiniProps {
  data: LineMovementData[];
  loading?: boolean;
}

const LineMovementMini: React.FC<LineMovementMiniProps> = ({ data, loading }) => {
  if (loading) {
    return (
      <div className="glass-card p-6">
        <h3 className="text-lg font-bold text-white mb-4">Ruch linii (Line Movement)</h3>
        <div className="flex items-center justify-center h-24">
          <div className="w-6 h-6 border-4 border-blue-400/30 border-t-blue-400 rounded-full animate-spin"></div>
        </div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="glass-card p-6">
        <h3 className="text-lg font-bold text-white mb-4">Ruch linii (Line Movement)</h3>
        <p className="text-sm text-gray-400 text-center py-4">Brak danych o ruchu linii</p>
      </div>
    );
  }

  const renderSparkline = (history: LineSnapshot[], current: number) => {
    if (!history || history.length < 2) return null;

    const values = history.map(h => h.value);
    const min = Math.min(...values, current);
    const max = Math.max(...values, current);
    const range = max - min || 1;

    const points = history.map((snapshot, idx) => {
      const x = (idx / (history.length - 1)) * 100;
      const y = 100 - ((snapshot.value - min) / range) * 100;
      return `${x},${y}`;
    }).join(' ');

    return (
      <div className="relative h-12 w-full">
        <svg
          className="w-full h-full"
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
        >
          <polyline
            points={points}
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            className="text-blue-400"
          />
        </svg>
      </div>
    );
  };

  const renderMovementIcon = (direction: string) => {
    if (direction === 'UP') return <TrendingUp className="w-4 h-4 text-green-400" />;
    if (direction === 'DOWN') return <TrendingDown className="w-4 h-4 text-red-400" />;
    return <Minus className="w-4 h-4 text-gray-400" />;
  };

  const formatValue = (value: number) => {
    return value > 0 ? `+${value}` : `${value}`;
  };

  return (
    <div className="glass-card p-6">
      <h3 className="text-lg font-bold text-white mb-4">Ruch linii (Line Movement)</h3>
      
      <div className="space-y-4">
        {data.map((line, idx) => (
          <div key={idx} className="border border-gray-700/50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-white uppercase">
                  {line.market_type === 'spread' ? 'Spread' : 'Total'}
                </span>
                {renderMovementIcon(line.movement.direction)}
              </div>
              <div className={`text-sm font-medium ${
                line.movement.direction === 'UP' ? 'text-green-400' :
                line.movement.direction === 'DOWN' ? 'text-red-400' :
                'text-gray-400'
              }`}>
                {line.movement.value_change > 0 ? '+' : ''}{line.movement.value_change.toFixed(1)}
              </div>
            </div>

            {renderSparkline(line.history, line.current.value)}

            <div className="grid grid-cols-3 gap-2 mt-3 text-xs">
              <div className="text-center">
                <div className="text-gray-400">Open</div>
                <div className="text-white font-semibold">
                  {formatValue(line.opening.value)}
                </div>
              </div>
              <div className="text-center">
                <div className="text-gray-400">Current</div>
                <div className="text-blue-400 font-semibold">
                  {formatValue(line.current.value)}
                </div>
              </div>
              {line.closing && (
                <div className="text-center">
                  <div className="text-gray-400">Close</div>
                  <div className="text-white font-semibold">
                    {formatValue(line.closing.value)}
                  </div>
                </div>
              )}
            </div>

            <div className="mt-2 text-xs text-gray-400 text-center">
              {line.current.bookmaker} • {line.history.length} snapshots
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default LineMovementMini;
