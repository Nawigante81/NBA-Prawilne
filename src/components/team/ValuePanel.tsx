import React from 'react';
import { BadgeCheck, ShieldAlert } from 'lucide-react';
import type { TeamValueResponse, TeamValueRow } from '../../types';

interface ValuePanelProps {
  data: TeamValueResponse | null;
  isLoading?: boolean;
}

const formatPct = (value?: number | null) => {
  if (value === null || value === undefined) return '—';
  return `${(value * 100).toFixed(1)}%`;
};

const formatSignedPct = (value?: number | null) => {
  if (value === null || value === undefined) return '—';
  const sign = value > 0 ? '+' : '';
  return `${sign}${(value * 100).toFixed(1)}%`;
};

const formatSigned = (value?: number | null) => {
  if (value === null || value === undefined) return '—';
  const sign = value > 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}`;
};

const ValueRow: React.FC<{ row: TeamValueRow; minEv: number }> = ({ row, minEv }) => {
  const isValue = (row.ev ?? 0) >= minEv;
  return (
    <div className="rounded-xl border border-gray-700/60 bg-gray-900/40 p-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-semibold text-white">
            {row.label}
            {row.line !== null && row.line !== undefined ? ` ${row.line}` : ''}
          </div>
          <div className="text-xs text-gray-400">{row.market.toUpperCase()}</div>
        </div>
        <div className={`text-xs px-2 py-1 rounded-full ${isValue ? 'bg-green-500/20 text-green-300' : 'bg-gray-700/50 text-gray-300'}`}>
          {isValue ? 'VALUE' : 'PASS'}
        </div>
      </div>
      <div className="grid grid-cols-2 gap-2 text-xs mt-3 text-gray-300">
        <div>Odds: <span className="text-white">{row.price ?? '—'}</span></div>
        <div>Implied: <span className="text-white">{formatPct(row.implied_prob)}</span></div>
        <div>Model: <span className="text-white">{formatPct(row.model_prob)}</span></div>
        <div>Edge: <span className="text-white">{formatSignedPct(row.edge)}</span></div>
        <div>EV: <span className="text-white">{formatSigned(row.ev)}</span></div>
        <div>Stake: <span className="text-white">{formatPct(row.stake_fraction)}</span></div>
      </div>
    </div>
  );
};

const ValuePanel: React.FC<ValuePanelProps> = ({ data, isLoading }) => {
  if (isLoading) {
    return (
      <div className="glass-card p-4 animate-pulse">
        <div className="h-4 w-28 bg-gray-700/60 rounded mb-3"></div>
        <div className="h-20 bg-gray-700/40 rounded"></div>
      </div>
    );
  }

  if (!data || !data.next_game) {
    return (
      <div className="glass-card p-4 text-sm text-gray-400">
        Brak danych o rynku dla nadchodzącego meczu.
      </div>
    );
  }

  const minEv = data.thresholds?.min_ev ?? 0.02;

  return (
    <div className="glass-card p-4 space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-sm uppercase tracking-widest text-gray-400">Value Panel</div>
          <div className="text-xs text-gray-500">{data.next_game.home_team} vs {data.next_game.away_team}</div>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <BadgeCheck className="w-4 h-4 text-green-400" />
          EV ≥ {(minEv * 100).toFixed(0)}%
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3">
        {data.value.length === 0 ? (
          <div className="text-sm text-gray-400">Brak linii do oceny.</div>
        ) : (
          data.value.map((row, idx) => (
            <ValueRow key={`${row.market}-${idx}`} row={row} minEv={minEv} />
          ))
        )}
      </div>

      {data.risk_flags.length > 0 && (
        <div className="rounded-xl border border-yellow-500/40 bg-yellow-500/10 p-3 text-xs text-yellow-200">
          <div className="flex items-center gap-2 mb-2">
            <ShieldAlert className="w-4 h-4" />
            Ryzyka
          </div>
          <div className="flex flex-wrap gap-2">
            {data.risk_flags.map((flag) => (
              <span key={flag} className="px-2 py-1 rounded-full bg-yellow-500/20">{flag}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ValuePanel;
