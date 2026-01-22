import React from 'react';
import { ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react';
import type { KeyPlayerInfo } from '../../types';

interface KeyPlayersPanelProps {
  players: KeyPlayerInfo[] | null;
  isLoading?: boolean;
}

const statusStyles: Record<string, string> = {
  OUT: 'bg-red-500/20 text-red-300',
  Q: 'bg-yellow-500/20 text-yellow-300',
  PROBABLE: 'bg-green-500/20 text-green-300',
  ACTIVE: 'bg-blue-500/20 text-blue-300',
  UNKNOWN: 'bg-gray-600/30 text-gray-300',
  DNP_FLAG: 'bg-orange-500/20 text-orange-300',
  Probable: 'bg-green-500/20 text-green-300',
  Active: 'bg-blue-500/20 text-blue-300',
  Unknown: 'bg-gray-600/30 text-gray-300',
};

const normalizeStatus = (status?: string) => {
  const value = (status || 'UNKNOWN').toUpperCase();
  if (value === 'DNP_FLAG') return 'DNP_FLAG';
  if (value === 'ACTIVE') return 'ACTIVE';
  if (value === 'PROBABLE') return 'PROBABLE';
  if (value === 'OUT') return 'OUT';
  if (value === 'Q') return 'Q';
  return 'UNKNOWN';
};

const trendIcon = (trend?: KeyPlayerInfo['minutes_trend']) => {
  if (trend === 'up') return <ArrowUpRight className="w-4 h-4 text-green-300" />;
  if (trend === 'down') return <ArrowDownRight className="w-4 h-4 text-red-300" />;
  return <Minus className="w-4 h-4 text-gray-400" />;
};

const KeyPlayersPanel: React.FC<KeyPlayersPanelProps> = ({ players, isLoading }) => {
  if (isLoading) {
    return (
      <div className="glass-card p-4 animate-pulse">
        <div className="h-4 w-28 bg-gray-700/60 rounded mb-3"></div>
        <div className="h-20 bg-gray-700/40 rounded"></div>
      </div>
    );
  }

  if (!players || players.length === 0) {
    return (
      <div className="glass-card p-4 text-sm text-gray-400">
        Brak danych o kluczowych graczach.
      </div>
    );
  }

  return (
    <div className="glass-card p-4 space-y-3">
      <div className="text-sm uppercase tracking-widest text-gray-400">Kluczowi gracze</div>
      <div className="space-y-3">
        {players.map((player) => (
          <div key={player.name} className="rounded-xl border border-gray-700/60 bg-gray-900/40 p-3">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-semibold text-white">{player.name}</div>
                <div className="text-xs text-gray-500">
                  avg {player.minutes_last5_avg?.toFixed(1) ?? '—'} min (L5)
                </div>
              </div>
              <span className={`text-xs px-2 py-1 rounded-full ${statusStyles[normalizeStatus(player.status)] || statusStyles.Unknown}`}>
                {normalizeStatus(player.status)}
              </span>
            </div>
            <div className="mt-3 flex items-center justify-between text-xs text-gray-400">
              <span className="inline-flex items-center gap-2">
                {trendIcon(player.minutes_trend)}
                trend: {player.trend_note ? `${player.trend_note} min last 5` : '—'}
              </span>
              <span className="text-gray-500">vol: {player.minutes_volatility?.toFixed(1) ?? '—'}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default KeyPlayersPanel;
