import React from 'react';
import type { TeamBettingStatsResponse, TeamBettingWindowStats } from '../../types';

interface BettingStatsPanelProps {
  data: TeamBettingStatsResponse | null;
  isLoading?: boolean;
  onRefresh?: () => void;
}

const formatRecord = (w?: number, l?: number, p?: number) => {
  if (w === undefined || l === undefined || p === undefined) return '—';
  return `${w}-${l}-${p}`;
};

const formatPct = (value?: number | null) => {
  if (value === null || value === undefined) return '—';
  return `${(value * 100).toFixed(1)}%`;
};

const formatDiff = (value?: number | null) => {
  if (value === null || value === undefined) return '—';
  const sign = value > 0 ? '+' : '';
  return `${sign}${value.toFixed(1)}`;
};

const Section: React.FC<{ title: string; stats: TeamBettingWindowStats | null }> = ({ title, stats }) => (
  <div className="rounded-xl border border-gray-700/60 bg-gray-900/40 p-3 space-y-3">
    <div className="text-xs uppercase tracking-widest text-gray-400">{title}</div>
    <div className="grid grid-cols-2 gap-3 text-sm">
      <div>
        <div className="text-gray-400">ATS</div>
        <div className="text-white font-semibold">
          {formatRecord(stats?.ats.w, stats?.ats.l, stats?.ats.p)}
          <span className="text-xs text-gray-400 ml-2">{formatPct(stats?.ats.win_pct)}</span>
        </div>
        <div className="text-xs text-gray-500">avg diff: {formatDiff(stats?.ats.avg_spread_diff)}</div>
      </div>
      <div>
        <div className="text-gray-400">O/U</div>
        <div className="text-white font-semibold">
          {formatRecord(stats?.ou.o, stats?.ou.u, stats?.ou.p)}
          <span className="text-xs text-gray-400 ml-2">{formatPct(stats?.ou.over_pct)}</span>
        </div>
        <div className="text-xs text-gray-500">avg diff: {formatDiff(stats?.ou.avg_total_diff)}</div>
      </div>
    </div>
    <div className="flex items-center justify-between text-xs text-gray-400">
      <span>Średnia suma punktów</span>
      <span className="text-white">{stats?.avg_total_points?.toFixed(1) ?? '—'}</span>
    </div>
  </div>
);

const BettingStatsPanel: React.FC<BettingStatsPanelProps> = ({ data, isLoading, onRefresh }) => {
  if (isLoading) {
    return (
      <div className="glass-card p-4 animate-pulse">
        <div className="h-4 w-32 bg-gray-700/60 rounded mb-3"></div>
        <div className="h-20 bg-gray-700/40 rounded"></div>
      </div>
    );
  }

  if (!data || !data.has_data) {
    return (
      <div className="glass-card p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div className="text-sm uppercase tracking-widest text-gray-400">Statystyki zakładów</div>
          {onRefresh && (
            <button
              type="button"
              onClick={onRefresh}
              className="text-xs text-blue-300 hover:text-blue-200"
            >
              Odśwież
            </button>
          )}
        </div>
        <div className="text-sm text-gray-400">
          {data?.missing_reason || 'Brak danych - uruchom synchronizację'}
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div className="text-sm uppercase tracking-widest text-gray-400">Statystyki zakładów</div>
        {onRefresh && (
          <button
            type="button"
            onClick={onRefresh}
            className="text-xs text-blue-300 hover:text-blue-200"
          >
            Odśwież
          </button>
        )}
      </div>
      <Section title={`Ostatnie ${data.window}`} stats={data.last_window} />
      <Section title="Sezon" stats={data.season} />
    </div>
  );
};

export default BettingStatsPanel;
