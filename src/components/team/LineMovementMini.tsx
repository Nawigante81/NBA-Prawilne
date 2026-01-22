import React from 'react';
import type { OddsMovementResponse, OddsMovementPoint } from '../../types';

interface LineMovementMiniProps {
  data: OddsMovementResponse | null;
  isHome?: boolean | null;
  isLoading?: boolean;
}

const formatLine = (value?: number | null) => {
  if (value === null || value === undefined) return '—';
  const sign = value > 0 ? '+' : '';
  return `${sign}${value.toFixed(1)}`;
};

const buildPath = (points: OddsMovementPoint[], width: number, height: number) => {
  if (points.length < 2) return '';
  const values = points.map((p) => p.point);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  return points
    .map((p, idx) => {
      const x = (idx / (points.length - 1)) * width;
      const y = height - ((p.point - min) / range) * height;
      return `${idx === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(' ');
};

const Sparkline: React.FC<{ points: OddsMovementPoint[] }> = ({ points }) => {
  const width = 120;
  const height = 36;
  const path = buildPath(points, width, height);
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className="text-blue-400">
      <path
        d={path}
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
};

const LineRow: React.FC<{ label: string; points: OddsMovementPoint[] }> = ({ label, points }) => {
  const open = points[0]?.point;
  const current = points[points.length - 1]?.point;
  const delta = open !== undefined && current !== undefined ? current - open : null;

  return (
    <div className="flex items-center justify-between gap-3">
      <div>
        <div className="text-xs text-gray-400">{label}</div>
        <div className="text-sm text-white">
          {formatLine(open)} → {formatLine(current)}
          <span className={`ml-2 text-xs ${delta !== null && delta >= 0 ? 'text-green-300' : 'text-red-300'}`}>
            {delta === null ? '—' : `${delta >= 0 ? '+' : ''}${delta.toFixed(1)}`}
          </span>
        </div>
      </div>
      {points.length >= 2 ? <Sparkline points={points} /> : <div className="text-xs text-gray-500">Brak ruchu</div>}
    </div>
  );
};

const LineMovementMini: React.FC<LineMovementMiniProps> = ({ data, isHome, isLoading }) => {
  if (isLoading) {
    return (
      <div className="glass-card p-4 animate-pulse">
        <div className="h-4 w-24 bg-gray-700/60 rounded mb-3"></div>
        <div className="h-16 bg-gray-700/40 rounded"></div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="glass-card p-4 text-sm text-gray-400">
        Brak danych o ruchu linii.
      </div>
    );
  }

  const spreadSeries = isHome === true
    ? data.series.spread_home
    : isHome === false
      ? data.series.spread_away
      : (data.series.spread_home.length ? data.series.spread_home : data.series.spread_away);
  const totalSeries = data.series.total;

  return (
    <div className="glass-card p-4 space-y-4">
      <div className="text-sm uppercase tracking-widest text-gray-400">Ruch linii</div>
      <LineRow label="Spread" points={spreadSeries} />
      <LineRow label="Total" points={totalSeries} />
    </div>
  );
};

export default LineMovementMini;
