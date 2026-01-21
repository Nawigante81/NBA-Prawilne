import React, { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { useI18n } from '../i18n/useI18n';
import { getAuthHeader } from '../services/auth';

interface FormData {
  player: string;
  games_analyzed: number;
  current_averages: {
    points: number;
    rebounds: number;
    assists: number;
  };
  trend: {
    direction: 'IMPROVING' | 'DECLINING' | 'STABLE';
    percentage: number;
    description: string;
  };
  games: Array<{
    game_num: number;
    date: string;
    opponent: string;
    actual_points: number;
    actual_rebounds: number;
    actual_assists: number;
    rolling_avg_points: number;
    rolling_avg_rebounds: number;
    rolling_avg_assists: number;
    minutes: string;
  }>;
  last_5_games: {
    points: number;
    rebounds: number;
    assists: number;
  };
}

const API_BASE =
  (typeof import.meta.env.VITE_API_BASE_URL === 'string' && import.meta.env.VITE_API_BASE_URL.trim() !== ''
    ? import.meta.env.VITE_API_BASE_URL.trim()
    : (
        typeof window !== 'undefined'
          ? `http://${window.location.hostname}:8000`
          : 'http://localhost:8000'
      ));

export const FormTracker: React.FC = () => {
  const { t } = useI18n();

  const [playerName, setPlayerName] = useState('Zach LaVine');
  const [games, setGames] = useState(15);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<FormData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedStat, setSelectedStat] = useState<'points' | 'rebounds' | 'assists'>('points');

  const fetchFormData = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        player_name: playerName,
        games: games.toString(),
      });

      const response = await fetch(`${API_BASE}/api/analytics/form?${params}`, {
        headers: getAuthHeader(),
      });
      const result = await response.json();

      if (result.error) {
        setError(result.error);
      } else {
        setData(result);
      }
    } catch {
      setError(t('form.error.fetchFailed'));
    } finally {
      setLoading(false);
    }
  };

  const getTrendLabel = (direction: string) => {
    switch (direction) {
      case 'IMPROVING':
        return t('form.trend.improving');
      case 'DECLINING':
        return t('form.trend.declining');
      default:
        return t('form.trend.stable');
    }
  };

  const getStatLabel = (stat: 'points' | 'rebounds' | 'assists') => {
    switch (stat) {
      case 'points':
        return t('form.stat.points');
      case 'rebounds':
        return t('form.stat.rebounds');
      default:
        return t('form.stat.assists');
    }
  };

  const getTrendIcon = (direction: string) => {
    switch (direction) {
      case 'IMPROVING':
        return <TrendingUp className="text-green-600" size={24} />;
      case 'DECLINING':
        return <TrendingDown className="text-red-600" size={24} />;
      default:
        return <Minus className="text-gray-600" size={24} />;
    }
  };

  const getTrendColor = (direction: string) => {
    switch (direction) {
      case 'IMPROVING':
        return 'bg-green-900/30 border-green-500/30 text-green-200';
      case 'DECLINING':
        return 'bg-red-900/30 border-red-500/30 text-red-200';
      default:
        return 'bg-gray-800/60 border-gray-600/30 text-gray-200';
    }
  };

  return (
    <div className="glass-card p-6">
      <div className="flex items-start justify-between gap-4 mb-6">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full bg-emerald-500/20 px-3 py-1 text-xs uppercase tracking-widest text-emerald-200">
            {t('form.badge.momentumMonitor')}
          </div>
          <h2 className="text-2xl font-bold mt-3 text-white">{t('form.title')}</h2>
          <p className="text-sm text-gray-400 mt-2">
            {t('form.subtitle')}
          </p>
        </div>
        <div className="rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-right">
          <div className="text-xs uppercase tracking-widest text-gray-500">{t('form.window.label')}</div>
          <div className="text-sm font-semibold text-white mt-1">{t('form.window.value', { games })}</div>
        </div>
      </div>

      {/* Input Form */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div>
          <label htmlFor="form-player-name" className="block text-xs uppercase tracking-widest text-gray-500 mb-2">
            {t('form.form.playerName.label')}
          </label>
          <input
            id="form-player-name"
            aria-label={t('form.form.playerName.label')}
            title={t('form.form.playerName.label')}
            type="text"
            value={playerName}
            onChange={(e) => setPlayerName(e.target.value)}
            className="w-full px-3 py-2 rounded-md bg-gray-900/60 border border-gray-700 text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder={t('form.form.playerName.placeholder')}
          />
        </div>

        <div>
          <label htmlFor="form-games" className="block text-xs uppercase tracking-widest text-gray-500 mb-2">
            {t('form.form.games.label')}
          </label>
          <input
            id="form-games"
            aria-label={t('form.form.games.label')}
            title={t('form.form.games.label')}
            type="number"
            value={games}
            onChange={(e) => setGames(parseInt(e.target.value))}
            className="w-full px-3 py-2 rounded-md bg-gray-900/60 border border-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <div className="mt-2 flex items-center gap-2 text-xs text-gray-500">
            <span>{t('form.form.games.quickLabel')}</span>
            <button
              type="button"
              onClick={() => setGames(5)}
              className="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-xs text-gray-200 hover:bg-white/10"
            >
              {t('form.form.games.quickLast5')}
            </button>
            <button
              type="button"
              onClick={() => setGames(10)}
              className="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-xs text-gray-200 hover:bg-white/10"
            >
              {t('form.form.games.quickLast10')}
            </button>
          </div>
        </div>

        <div className="flex items-end">
          <button
            onClick={fetchFormData}
            disabled={loading}
            className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? t('form.actions.loading') : t('form.actions.track')}
          </button>
        </div>
      </div>

      {loading && (
        <div className="space-y-4 mb-6">
          <div className="skeleton h-20"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="skeleton h-28"></div>
            <div className="skeleton h-28"></div>
          </div>
          <div className="skeleton h-56"></div>
          <div className="skeleton h-40"></div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 bg-red-900/20 border border-red-500/30 rounded-md">
          <p className="text-red-200 font-medium">{t('common.error')}</p>
          <p className="text-red-200 text-sm">{error}</p>
        </div>
      )}

      {/* Results */}
      {data && !error && (
        <div className="space-y-6">
          {/* Trend Summary */}
          <div className={`p-6 rounded-lg border-2 ${getTrendColor(data.trend.direction)}`}>
            <div className="flex items-center gap-3 mb-2">
              {getTrendIcon(data.trend.direction)}
              <h3 className="text-2xl font-bold">{getTrendLabel(data.trend.direction)}</h3>
            </div>
            <p className="text-sm font-medium">{data.trend.description}</p>
          </div>

          {/* Stats Overview */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold text-white mb-3">
                {t('form.overallAverages.title', { games: data.games_analyzed })}
              </h4>
              <div className="space-y-2">
                <div className="flex justify-between items-center p-3 bg-gray-800/60 rounded">
                  <span className="text-gray-300">{t('form.stat.points')}</span>
                  <span className="font-bold text-lg text-white">{data.current_averages.points}</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-800/60 rounded">
                  <span className="text-gray-300">{t('form.stat.rebounds')}</span>
                  <span className="font-bold text-lg text-white">{data.current_averages.rebounds}</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-800/60 rounded">
                  <span className="text-gray-300">{t('form.stat.assists')}</span>
                  <span className="font-bold text-lg text-white">{data.current_averages.assists}</span>
                </div>
              </div>
            </div>

            <div>
              <h4 className="font-semibold text-white mb-3">{t('form.last5.title')}</h4>
              <div className="space-y-2">
                <div className="flex justify-between items-center p-3 bg-blue-900/30 rounded">
                  <span className="text-blue-200">{t('form.stat.points')}</span>
                  <span className="font-bold text-lg text-blue-100">{data.last_5_games.points}</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-blue-900/30 rounded">
                  <span className="text-blue-200">{t('form.stat.rebounds')}</span>
                  <span className="font-bold text-lg text-blue-100">{data.last_5_games.rebounds}</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-blue-900/30 rounded">
                  <span className="text-blue-200">{t('form.stat.assists')}</span>
                  <span className="font-bold text-lg text-blue-100">{data.last_5_games.assists}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Stat Selector */}
          <div className="flex gap-2">
            <button
              onClick={() => setSelectedStat('points')}
              className={`px-4 py-2 rounded font-medium transition-colors ${
                selectedStat === 'points'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800/60 text-gray-300 hover:bg-gray-700/60'
              }`}
            >
              {t('form.stat.points')}
            </button>
            <button
              onClick={() => setSelectedStat('rebounds')}
              className={`px-4 py-2 rounded font-medium transition-colors ${
                selectedStat === 'rebounds'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800/60 text-gray-300 hover:bg-gray-700/60'
              }`}
            >
              {t('form.stat.rebounds')}
            </button>
            <button
              onClick={() => setSelectedStat('assists')}
              className={`px-4 py-2 rounded font-medium transition-colors ${
                selectedStat === 'assists'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800/60 text-gray-300 hover:bg-gray-700/60'
              }`}
            >
              {t('form.stat.assists')}
            </button>
          </div>

          {/* Chart */}
          <div className="glass-card p-4">
            <h4 className="font-semibold text-white mb-4">
              {t('form.chart.title', { stat: getStatLabel(selectedStat) })}
            </h4>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={data.games}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis
                  dataKey="opponent"
                  tick={{ fontSize: 12, fill: '#9ca3af' }}
                  axisLine={{ stroke: '#4b5563' }}
                  tickLine={{ stroke: '#4b5563' }}
                />
                <YAxis
                  tick={{ fill: '#9ca3af' }}
                  axisLine={{ stroke: '#4b5563' }}
                  tickLine={{ stroke: '#4b5563' }}
                />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="bg-gray-900 border border-gray-700 p-3 rounded shadow-lg">
                          <p className="font-semibold text-white">{t('form.tooltip.vsOpponent', { opponent: data.opponent })}</p>
                          <p className="text-sm text-gray-400">{data.date}</p>
                          <p className="text-sm mt-1 text-gray-200">
                            {t('form.tooltip.actualLabel')}: <span className="font-bold">{data[`actual_${selectedStat}`]}</span>
                          </p>
                          <p className="text-sm text-gray-200">
                            {t('form.tooltip.avgLabel')}: <span className="font-bold">{data[`rolling_avg_${selectedStat}`]}</span>
                          </p>
                          <p className="text-xs text-gray-500 mt-1">{t('form.tooltip.minutes', { minutes: data.minutes })}</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Legend wrapperStyle={{ color: '#e5e7eb' }} />
                <Line 
                  type="monotone" 
                  dataKey={`actual_${selectedStat}`} 
                  stroke="#3b82f6" 
                  strokeWidth={2}
                  name={t('form.legend.actual')}
                  dot={{ r: 4 }}
                />
                <Line 
                  type="monotone" 
                  dataKey={`rolling_avg_${selectedStat}`} 
                  stroke="#f97316" 
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  name={t('form.legend.rollingAvg')}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Recent Games Table */}
          <div>
            <h4 className="font-semibold text-white mb-3">{t('form.table.titleRecent')}</h4>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-800/60">
                  <tr>
                    <th className="text-left p-2 text-gray-300">{t('form.table.header.date')}</th>
                    <th className="text-left p-2 text-gray-300">{t('form.table.header.opponent')}</th>
                    <th className="text-center p-2 text-gray-300">{t('form.table.header.pts')}</th>
                    <th className="text-center p-2 text-gray-300">{t('form.table.header.reb')}</th>
                    <th className="text-center p-2 text-gray-300">{t('form.table.header.ast')}</th>
                    <th className="text-center p-2 text-gray-300">{t('form.table.header.min')}</th>
                  </tr>
                </thead>
                <tbody>
                  {data.games.slice().reverse().slice(0, 10).map((game, idx) => (
                    <tr key={idx} className="border-b border-gray-800 hover:bg-gray-800/40">
                      <td className="p-2 text-gray-200">{game.date}</td>
                      <td className="p-2 text-gray-200">{t('form.table.cell.vs', { opponent: game.opponent })}</td>
                      <td className="text-center p-2 font-semibold text-white">{game.actual_points}</td>
                      <td className="text-center p-2 text-gray-200">{game.actual_rebounds}</td>
                      <td className="text-center p-2 text-gray-200">{game.actual_assists}</td>
                      <td className="text-center p-2 text-gray-500">{game.minutes}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
