import React from 'react';
import { Calendar, MapPin, Clock } from 'lucide-react';

export interface NextGameData {
  game_id: string;
  opponent: string;
  opponent_abbrev: string;
  commence_time: string;
  is_home: boolean;
  venue?: string;
  status?: string;
}

interface NextGameBlockProps {
  data: NextGameData | null;
  teamAbbrev: string;
  loading?: boolean;
}

const NextGameBlock: React.FC<NextGameBlockProps> = ({ data, teamAbbrev, loading }) => {
  if (loading) {
    return (
      <div className="glass-card p-6">
        <h3 className="text-lg font-bold text-white mb-4">Następny mecz</h3>
        <div className="flex items-center justify-center h-24">
          <div className="w-6 h-6 border-4 border-blue-400/30 border-t-blue-400 rounded-full animate-spin"></div>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="glass-card p-6">
        <h3 className="text-lg font-bold text-white mb-4">Następny mecz</h3>
        <p className="text-sm text-gray-400 text-center py-4">
          Brak zaplanowanych meczów
        </p>
      </div>
    );
  }

  const gameDate = new Date(data.commence_time);
  const now = new Date();
  const hoursUntil = Math.floor((gameDate.getTime() - now.getTime()) / (1000 * 60 * 60));
  const daysUntil = Math.floor(hoursUntil / 24);

  const formatTimeUntil = () => {
    if (hoursUntil < 0) return 'W trakcie lub zakończony';
    if (hoursUntil < 1) return 'Za mniej niż godzinę';
    if (hoursUntil < 24) return `Za ${hoursUntil} godz.`;
    return `Za ${daysUntil} dni`;
  };

  return (
    <div className="glass-card p-6">
      <h3 className="text-lg font-bold text-white mb-4">Następny mecz</h3>
      
      <div className="space-y-4">
        {/* Matchup */}
        <div className="flex items-center justify-center gap-4 py-4">
          <div className="text-center">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white font-bold text-xl mb-2">
              {data.is_home ? teamAbbrev : data.opponent_abbrev}
            </div>
            <div className="text-sm text-gray-400">
              {data.is_home ? 'Home' : 'Away'}
            </div>
          </div>
          
          <div className="text-2xl font-bold text-gray-400">vs</div>
          
          <div className="text-center">
            <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-600 rounded-lg flex items-center justify-center text-white font-bold text-xl mb-2">
              {data.is_home ? data.opponent_abbrev : teamAbbrev}
            </div>
            <div className="text-sm text-gray-400">
              {data.is_home ? 'Away' : 'Home'}
            </div>
          </div>
        </div>

        {/* Game Details */}
        <div className="grid grid-cols-1 gap-3">
          <div className="flex items-center gap-3 text-sm">
            <Calendar className="w-4 h-4 text-gray-400" />
            <span className="text-gray-400">Data:</span>
            <span className="text-white font-medium">
              {gameDate.toLocaleDateString('pl-PL', { 
                weekday: 'short', 
                year: 'numeric', 
                month: 'short', 
                day: 'numeric' 
              })}
            </span>
          </div>

          <div className="flex items-center gap-3 text-sm">
            <Clock className="w-4 h-4 text-gray-400" />
            <span className="text-gray-400">Godzina:</span>
            <span className="text-white font-medium">
              {gameDate.toLocaleTimeString('pl-PL', { 
                hour: '2-digit', 
                minute: '2-digit' 
              })}
            </span>
          </div>

          {data.venue && (
            <div className="flex items-center gap-3 text-sm">
              <MapPin className="w-4 h-4 text-gray-400" />
              <span className="text-gray-400">Miejsce:</span>
              <span className="text-white font-medium">{data.venue}</span>
            </div>
          )}
        </div>

        {/* Time Until */}
        <div className="pt-4 border-t border-gray-700/50">
          <div className="text-center">
            <div className="text-xs text-gray-400 mb-1">Czas do meczu</div>
            <div className={`text-lg font-bold ${
              hoursUntil < 24 ? 'text-green-400' : 
              hoursUntil < 72 ? 'text-yellow-400' : 
              'text-blue-400'
            }`}>
              {formatTimeUntil()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NextGameBlock;
