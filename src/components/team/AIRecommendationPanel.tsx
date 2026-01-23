import React from 'react';
import { Activity, Sparkles, AlertTriangle } from 'lucide-react';
import type { AIRecommendationResponse, AIRecommendationRow } from '../../types';

interface AIRecommendationPanelProps {
  data: AIRecommendationResponse | null;
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

const marketLabel = (market: AIRecommendationRow['market']) => {
  if (market === 'h2h' || market === 'moneyline') return 'ML';
  if (market === 'totals' || market === 'total') return 'TOTAL';
  return 'SPREAD';
};

const RecommendationRow: React.FC<{ row: AIRecommendationRow; highlight?: boolean }> = ({ row, highlight }) => {
  const lineText = row.line !== null && row.line !== undefined ? ` ${row.line}` : '';
  return (
    <div className={`rounded-xl border ${highlight ? 'border-emerald-500/60 bg-emerald-500/10' : 'border-gray-700/60 bg-gray-900/40'} p-3 space-y-2`}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-semibold text-white">{row.selection}{lineText}</div>
          <div className="text-[11px] text-gray-400">{marketLabel(row.market)}</div>
        </div>
        <div className={`text-xs px-2 py-1 rounded-full ${row.decision === 'BET' ? 'bg-emerald-500/20 text-emerald-200' : 'bg-gray-700/50 text-gray-300'}`}>
          {row.decision === 'BET' ? 'AI BET' : 'AI PASS'}
        </div>
      </div>
      <div className="grid grid-cols-2 gap-2 text-xs text-gray-300">
        <div>Odds: <span className="text-white">{row.price ?? '—'}</span></div>
        <div>EV: <span className="text-white">{formatSigned(row.ev)}</span></div>
        <div>Model: <span className="text-white">{formatPct(row.model_prob)}</span></div>
        <div>Edge: <span className="text-white">{formatSignedPct(row.edge)}</span></div>
        <div>Confidence: <span className="text-white">{formatPct(row.confidence)}</span></div>
        <div>Implied: <span className="text-white">{formatPct(row.implied_prob)}</span></div>
      </div>
      {row.why_bullets && row.why_bullets.length > 0 && (
        <div className="text-xs text-gray-400 space-y-1">
          {row.why_bullets.map((bullet) => (
            <div key={bullet}>• {bullet}</div>
          ))}
        </div>
      )}
      {row.reasons && row.reasons.length > 0 && (
        <div className="flex flex-wrap gap-2 text-[11px] text-gray-400">
          {row.reasons.map((reason) => (
            <span key={reason} className="rounded-full bg-gray-800 px-2 py-1 text-gray-300">
              {reason}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

const AIRecommendationPanel: React.FC<AIRecommendationPanelProps> = ({ data, isLoading }) => {
  if (isLoading) {
    return (
      <div className="glass-card p-4 animate-pulse">
        <div className="h-4 w-36 bg-gray-700/60 rounded mb-3"></div>
        <div className="h-24 bg-gray-700/40 rounded"></div>
      </div>
    );
  }

  if (!data || !data.next_game) {
    return (
      <div className="glass-card p-4 text-sm text-gray-400">
        Brak danych AI dla nadchodzącego meczu.
      </div>
    );
  }

  const topPick = data.top_pick ?? null;
  const isSamePick = (a: AIRecommendationRow, b: AIRecommendationRow | null) =>
    Boolean(
      b
      && a.market === b.market
      && a.selection === b.selection
      && a.line === b.line
      && a.price === b.price
    );
  const others = data.recommendations.filter((row) => !isSamePick(row, topPick)).slice(0, 2);

  return (
    <div className="glass-card p-4 space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm uppercase tracking-widest text-gray-400">AI Recommendation</div>
          <div className="text-xs text-gray-500">{data.next_game.home_team} vs {data.next_game.away_team}</div>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <Activity className="w-4 h-4 text-purple-400" />
          {data.model_version}
        </div>
      </div>

      {topPick ? (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-xs text-emerald-200">
            <Sparkles className="w-4 h-4" />
            Najlepszy typ AI
          </div>
          <RecommendationRow row={topPick} highlight />
        </div>
      ) : (
        <div className="text-sm text-gray-400">Brak rekomendacji spełniających warunki.</div>
      )}

      {others.length > 0 && (
        <div className="space-y-2">
          <div className="text-xs uppercase tracking-widest text-gray-500">Pozostałe sygnały</div>
          <div className="grid grid-cols-1 gap-3">
            {others.map((row, idx) => (
              <RecommendationRow key={`${row.market}-${idx}`} row={row} />
            ))}
          </div>
        </div>
      )}

      {data.risk_flags.length > 0 && (
        <div className="rounded-xl border border-yellow-500/40 bg-yellow-500/10 p-3 text-xs text-yellow-200">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4" />
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

export default AIRecommendationPanel;
