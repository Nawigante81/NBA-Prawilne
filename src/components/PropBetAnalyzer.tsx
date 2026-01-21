import React, { useState } from 'react';
import { TrendingUp, TrendingDown, Minus, AlertCircle } from 'lucide-react';
import { useI18n } from '../i18n/useI18n';
import { getAuthHeader } from '../services/auth';

interface PropBetResult {
  player: string;
  stat_type: string;
  line: number;
  prediction: number;
  median: number;
  hit_rate: number;
  value: 'OVER' | 'UNDER' | 'NO VALUE';
  confidence: number;
  trend: number;
  sample_size: number;
  recent_games: number[];
  recommendation: string;
  vs_opponent?: {
    games: number;
    avg: number;
    high: number;
    low: number;
    over_rate: number;
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

export const PropBetAnalyzer: React.FC = () => {
  const { t } = useI18n();

  const [playerName, setPlayerName] = useState('Zach LaVine');
  const [statType, setStatType] = useState('points');
  const [line, setLine] = useState(24.5);
  const [opponent, setOpponent] = useState('');
  const [games, setGames] = useState(20);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PropBetResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const analyzeProp = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams({
        player_name: playerName,
        stat_type: statType,
        line: line.toString(),
        games: games.toString(),
      });
      
      if (opponent) {
        params.append('opponent', opponent);
      }
      
      const response = await fetch(`${API_BASE}/api/analytics/prop-bet?${params}`, {
        headers: getAuthHeader(),
      });
      const data = await response.json();
      
      if (data.error) {
        setError(data.error);
      } else {
        setResult(data);
      }
    } catch {
      setError(t('prop.error.analyzeFailed'));
    } finally {
      setLoading(false);
    }
  };

  const getValueLabel = (value: PropBetResult['value']) => {
    switch (value) {
      case 'OVER':
        return t('prop.value.over');
      case 'UNDER':
        return t('prop.value.under');
      default:
        return t('prop.value.noValue');
    }
  };

  const getValueColor = (value: string) => {
    switch (value) {
      case 'OVER':
        return 'text-green-300 bg-green-900/30 border-green-500/30';
      case 'UNDER':
        return 'text-red-300 bg-red-900/30 border-red-500/30';
      default:
        return 'text-gray-300 bg-gray-800/50 border-gray-600/30';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 75) return 'text-green-300';
    if (confidence >= 60) return 'text-yellow-300';
    return 'text-gray-300';
  };

  return (
    <div className="glass-card p-6">
      <div className="flex items-start justify-between gap-4 mb-6">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full bg-blue-500/20 px-3 py-1 text-xs uppercase tracking-widest text-blue-200">
            {t('prop.badge.signalDesk')}
          </div>
          <h2 className="text-2xl font-bold mt-3 text-white">{t('prop.title')}</h2>
          <p className="text-sm text-gray-400 mt-2">
            {t('prop.subtitle')}
          </p>
        </div>
        <div className="rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-right">
          <div className="text-xs uppercase tracking-widest text-gray-500">{t('prop.mode.label')}</div>
          <div className="text-sm font-semibold text-white mt-1">{t('prop.mode.value')}</div>
        </div>
      </div>

      {/* Input Form */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        <div>
          <label htmlFor="prop-player-name" className="block text-xs uppercase tracking-widest text-gray-500 mb-2">
            {t('prop.form.playerName.label')}
          </label>
          <input
            id="prop-player-name"
            aria-label={t('prop.form.playerName.label')}
            title={t('prop.form.playerName.label')}
            type="text"
            value={playerName}
            onChange={(e) => setPlayerName(e.target.value)}
            className="w-full px-3 py-2 rounded-md bg-gray-900/60 border border-gray-700 text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder={t('prop.form.playerName.placeholder')}
          />
        </div>

        <div>
          <label htmlFor="prop-stat-type" className="block text-xs uppercase tracking-widest text-gray-500 mb-2">
            {t('prop.form.statType.label')}
          </label>
          <select
            id="prop-stat-type"
            aria-label={t('prop.form.statType.label')}
            title={t('prop.form.statType.label')}
            value={statType}
            onChange={(e) => setStatType(e.target.value)}
            className="w-full px-3 py-2 rounded-md bg-gray-900/60 border border-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="points">{t('prop.stat.points')}</option>
            <option value="rebounds_total">{t('prop.stat.rebounds')}</option>
            <option value="assists">{t('prop.stat.assists')}</option>
            <option value="three_pointers_made">{t('prop.stat.threePointersMade')}</option>
            <option value="steals">{t('prop.stat.steals')}</option>
            <option value="blocks">{t('prop.stat.blocks')}</option>
          </select>
        </div>

        <div>
          <label htmlFor="prop-line" className="block text-xs uppercase tracking-widest text-gray-500 mb-2">
            {t('prop.form.line.label')}
          </label>
          <input
            id="prop-line"
            aria-label={t('prop.form.line.label')}
            title={t('prop.form.line.label')}
            type="number"
            step="0.5"
            value={line}
            onChange={(e) => setLine(parseFloat(e.target.value))}
            className="w-full px-3 py-2 rounded-md bg-gray-900/60 border border-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label htmlFor="prop-opponent" className="block text-xs uppercase tracking-widest text-gray-500 mb-2">
            {t('prop.form.opponent.label')}
          </label>
          <input
            id="prop-opponent"
            aria-label={t('prop.form.opponent.label')}
            title={t('prop.form.opponent.label')}
            type="text"
            value={opponent}
            onChange={(e) => setOpponent(e.target.value)}
            className="w-full px-3 py-2 rounded-md bg-gray-900/60 border border-gray-700 text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder={t('prop.form.opponent.placeholder')}
          />
        </div>

        <div>
          <label htmlFor="prop-games" className="block text-xs uppercase tracking-widest text-gray-500 mb-2">
            {t('prop.form.games.label')}
          </label>
          <input
            id="prop-games"
            aria-label={t('prop.form.games.label')}
            title={t('prop.form.games.label')}
            type="number"
            value={games}
            onChange={(e) => setGames(parseInt(e.target.value))}
            className="w-full px-3 py-2 rounded-md bg-gray-900/60 border border-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="flex items-end">
          <button
            onClick={analyzeProp}
            disabled={loading}
            className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? t('prop.actions.analyzing') : t('prop.actions.analyze')}
          </button>
        </div>
      </div>

      {loading && (
        <div className="space-y-4 mb-6">
          <div className="skeleton h-24"></div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="skeleton h-16"></div>
            <div className="skeleton h-16"></div>
            <div className="skeleton h-16"></div>
            <div className="skeleton h-16"></div>
          </div>
          <div className="skeleton h-20"></div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 bg-red-900/20 border border-red-500/30 rounded-md flex items-start gap-2">
          <AlertCircle className="text-red-300 flex-shrink-0 mt-0.5" size={20} />
          <div>
            <p className="text-red-200 font-medium">{t('common.error')}</p>
            <p className="text-red-200 text-sm">{error}</p>
          </div>
        </div>
      )}

      {/* Results */}
      {result && !error && (
        <div className="space-y-6">
          {/* Main Recommendation */}
          <div className={`p-6 rounded-lg border ${getValueColor(result.value)}`}>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-2xl font-bold">{getValueLabel(result.value)}</h3>
              <span className={`text-3xl font-bold ${getConfidenceColor(result.confidence)}`}>
                {result.confidence}%
              </span>
            </div>
            <p className="text-sm font-medium mb-3">{result.recommendation}</p>
                <div className="flex items-center gap-2 text-sm">
                  {result.trend > 0 ? (
                    <>
                      <TrendingUp size={16} className="text-green-300" />
                      <span>{t('prop.trend.up', { value: result.trend.toFixed(1) })}</span>
                    </>
                  ) : result.trend < 0 ? (
                    <>
                      <TrendingDown size={16} className="text-red-300" />
                      <span>{t('prop.trend.down', { value: Math.abs(result.trend).toFixed(1) })}</span>
                    </>
                  ) : (
                    <>
                      <Minus size={16} className="text-gray-300" />
                      <span>{t('prop.trend.stable')}</span>
                    </>
                  )}
                </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="glass-card p-4">
              <p className="text-sm text-gray-400">{t('prop.stats.predictionAvg')}</p>
              <p className="text-2xl font-bold text-white">{result.prediction}</p>
            </div>
            <div className="glass-card p-4">
              <p className="text-sm text-gray-400">{t('prop.stats.hitRate')}</p>
              <p className="text-2xl font-bold text-white">{result.hit_rate}%</p>
            </div>
            <div className="glass-card p-4">
              <p className="text-sm text-gray-400">{t('prop.stats.median')}</p>
              <p className="text-2xl font-bold text-white">{result.median}</p>
            </div>
            <div className="glass-card p-4">
              <p className="text-sm text-gray-400">{t('prop.stats.sampleSize')}</p>
              <p className="text-2xl font-bold text-white">{result.sample_size}</p>
            </div>
          </div>

          {/* Recent Games */}
          <div>
            <h4 className="font-semibold text-white mb-3">{t('prop.recentGames.title')}</h4>
            <div className="flex gap-2 flex-wrap">
              {result.recent_games.map((value, idx) => (
                <div
                  key={idx}
                  className={`px-3 py-2 rounded font-semibold text-sm ${
                    value > result.line
                      ? 'bg-green-900/40 text-green-200'
                      : 'bg-red-900/40 text-red-200'
                  }`}
                >
                  {value}
                </div>
              ))}
            </div>
          </div>

          {/* Vs Opponent Stats */}
          {result.vs_opponent && (
            <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4">
              <h4 className="font-semibold text-blue-200 mb-3">
                {t('prop.vsOpponent.title', { opponent: opponent.toUpperCase(), games: result.vs_opponent.games })}
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm text-blue-300">{t('prop.vsOpponent.avg')}</p>
                  <p className="text-xl font-bold text-blue-100">{result.vs_opponent.avg.toFixed(1)}</p>
                </div>
                <div>
                  <p className="text-sm text-blue-300">{t('prop.vsOpponent.high')}</p>
                  <p className="text-xl font-bold text-blue-100">{result.vs_opponent.high}</p>
                </div>
                <div>
                  <p className="text-sm text-blue-300">{t('prop.vsOpponent.low')}</p>
                  <p className="text-xl font-bold text-blue-100">{result.vs_opponent.low}</p>
                </div>
                <div>
                  <p className="text-sm text-blue-300">{t('prop.vsOpponent.overRate')}</p>
                  <p className="text-xl font-bold text-blue-100">{result.vs_opponent.over_rate.toFixed(1)}%</p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
