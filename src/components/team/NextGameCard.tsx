import React from 'react';
import { CalendarDays, MapPin } from 'lucide-react';
import type { NextGameInfo } from '../../types';

interface NextGameCardProps {
  nextGame: NextGameInfo | null;
  isLoading?: boolean;
}

const formatKickoff = (value?: string | null) => {
  if (!value) return 'TBD';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('pl-PL', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

const NextGameCard: React.FC<NextGameCardProps> = ({ nextGame, isLoading }) => {
  if (isLoading) {
    return (
      <div className="glass-card p-4 animate-pulse">
        <div className="h-4 w-24 bg-gray-700/60 rounded mb-3"></div>
        <div className="h-6 w-40 bg-gray-700/60 rounded"></div>
      </div>
    );
  }

  if (!nextGame) {
    return (
      <div className="glass-card p-4 text-sm text-gray-400">
        Brak nadchodzącego meczu.
      </div>
    );
  }

  return (
    <div className="glass-card p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="text-xs uppercase tracking-widest text-gray-400">Następny mecz</div>
        <div className="text-xs text-gray-500">{nextGame.is_home ? 'Home' : 'Away'}</div>
      </div>
      <div className="text-lg font-semibold text-white">
        {nextGame.home_team} vs {nextGame.away_team}
      </div>
      <div className="flex items-center gap-3 text-sm text-gray-300">
        <span className="inline-flex items-center gap-2">
          <CalendarDays className="w-4 h-4 text-blue-400" />
          {formatKickoff(nextGame.commence_time)}
        </span>
        <span className="inline-flex items-center gap-2">
          <MapPin className="w-4 h-4 text-green-400" />
          {nextGame.opponent}
        </span>
      </div>
    </div>
  );
};

export default NextGameCard;
