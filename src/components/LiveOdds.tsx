import React, { useState, useEffect, useCallback } from 'react';
import { TrendingUp, TrendingDown, RefreshCw, AlertTriangle, Clock, Activity } from 'lucide-react';
import { useI18n } from '../i18n/useI18n';
import { api } from '../services/api';

interface OddsData {
  gameId: string;
  homeTeam: string;
  awayTeam: string;
  startTime: string;
  bookmakers: {
    name: string;
    moneyline: { home: number | null; away: number | null };
    spread: { line: number | null; home: number | null; away: number | null };
    total: { line: number | null; over: number | null; under: number | null };
  }[];
  movements: {
    type: 'spread' | 'total' | 'ml';
    direction: 'up' | 'down';
    from: number;
    to: number;
    time: string;
  }[];
}

interface LiveAlert {
  id: string;
  type: 'movement' | 'value' | 'reverse';
  game: string;
  message: string;
  severity: 'high' | 'medium' | 'low';
  time: string;
}

interface LiveOddsProps {
  selectedGameId?: string;
}

interface ApiGame {
  id?: string;
  home_team?: string;
  away_team?: string;
  commence_time?: string;
}

interface OddsRow {
  bookmaker_title?: string;
  bookmaker_key?: string;
  market_type?: string;
  team?: string;
  price?: number | string | null;
  point?: number | string | null;
  outcome_name?: string;
}

const LiveOdds: React.FC<LiveOddsProps> = ({ selectedGameId }) => {
  const { t, locale } = useI18n();
  const [oddsData, setOddsData] = useState<OddsData[]>([]);
  const [alerts, setAlerts] = useState<LiveAlert[]>([]);
  const [selectedGame, setSelectedGame] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [loading, setLoading] = useState(true);
  const [showSelectedOnly, setShowSelectedOnly] = useState(false);

  const decimalToAmerican = (decimal: number): number | null => {
    if (!Number.isFinite(decimal) || decimal <= 1) return null;
    if (decimal >= 2) return Math.round((decimal - 1) * 100);
    return -Math.round(100 / (decimal - 1));
  };

  const loadOdds = useCallback(async () => {
    setLoading(true);
    try {
      const gamesResp = await api.games.getToday();
      const games = gamesResp.games || [];

      const built: OddsData[] = await Promise.all(
        games
          .filter((g: ApiGame) => typeof g?.id === 'string' && g.id.trim() !== '')
          .map(async (g: ApiGame) => {
            const gameId = String(g.id);
            const homeTeam = String(g.home_team || '');
            const awayTeam = String(g.away_team || '');
            const startTime = g.commence_time
              ? new Date(g.commence_time).toLocaleTimeString(locale, { timeZone: 'America/Chicago' })
              : t('common.tbd');

            const oddsResp = await api.games.getOdds(gameId);
            const rows = (oddsResp.odds as OddsRow[]) || [];

            const byBook: Record<string, OddsRow[]> = {};
            for (const row of rows) {
              const book = String(row.bookmaker_title || row.bookmaker_key || '');
              if (!book) continue;
              byBook[book] = byBook[book] || [];
              byBook[book].push(row);
            }

            const bookmakers = Object.entries(byBook).map(([name, bookRows]) => {
              const h2h = bookRows.filter((r) => r.market_type === 'h2h');
              const spreads = bookRows.filter(
                (r) => r.market_type === 'spread' || r.market_type === 'spreads'
              );
              const totals = bookRows.filter((r) => r.market_type === 'totals');

              const findTeamRow = (arr: OddsRow[], team: string) =>
                arr.find((r) => String(r.team || '').trim().toLowerCase() === team.trim().toLowerCase());

              const homeMl = findTeamRow(h2h, homeTeam);
              const awayMl = findTeamRow(h2h, awayTeam);

              const homeSpread = findTeamRow(spreads, homeTeam);
              const awaySpread = findTeamRow(spreads, awayTeam);

              const overRow = totals.find((r) => String(r.outcome_name || '').toLowerCase() === 'over');
              const underRow = totals.find((r) => String(r.outcome_name || '').toLowerCase() === 'under');

              const spreadLine = homeSpread?.point ?? awaySpread?.point ?? null;
              const totalLine = overRow?.point ?? underRow?.point ?? null;

              const homeMlAmerican = decimalToAmerican(Number(homeMl?.price));
              const awayMlAmerican = decimalToAmerican(Number(awayMl?.price));

              const homeSpreadAmerican = decimalToAmerican(Number(homeSpread?.price));
              const awaySpreadAmerican = decimalToAmerican(Number(awaySpread?.price));

              const overAmerican = decimalToAmerican(Number(overRow?.price));
              const underAmerican = decimalToAmerican(Number(underRow?.price));

              return {
                name,
                moneyline: { home: homeMlAmerican, away: awayMlAmerican },
                spread: {
                  line: spreadLine === null || spreadLine === undefined ? null : Number(spreadLine),
                  home: homeSpreadAmerican,
                  away: awaySpreadAmerican,
                },
                total: {
                  line: totalLine === null || totalLine === undefined ? null : Number(totalLine),
                  over: overAmerican,
                  under: underAmerican,
                },
              };
            });

            return {
              gameId,
              homeTeam,
              awayTeam,
              startTime,
              bookmakers,
              movements: [],
            };
          })
      );

      setOddsData(built);
      setAlerts([]);
    } catch (e) {
      console.error('Failed to load odds:', e);
      setOddsData([]);
      setAlerts([]);
    } finally {
      setLoading(false);
      if (selectedGameId) setSelectedGame(selectedGameId);
    }
  }, [selectedGameId, t, locale]);

  useEffect(() => {
    loadOdds();
  }, [loadOdds]);

  useEffect(() => {
    if (!loading && selectedGameId) {
      setSelectedGame(selectedGameId);
    }
  }, [selectedGameId, loading]);

  const formatOdds = (odds: number) => {
    return odds > 0 ? `+${odds}` : `${odds}`;
  };

  const formatOddsOrNoData = (odds: number | null | undefined, emptyLabel?: string) => {
    if (typeof odds !== 'number' || !Number.isFinite(odds)) return emptyLabel || t('common.noData');
    return formatOdds(odds);
  };

  const hasSpreadData = (bookmakers: OddsData['bookmakers']) =>
    bookmakers.some(
      (book) =>
        typeof book?.spread?.line === 'number' ||
        Number.isFinite(book?.spread?.home) ||
        Number.isFinite(book?.spread?.away)
    );

  const getFirstSpreadLine = (bookmakers: OddsData['bookmakers']) => {
    const found = bookmakers.find((book) => typeof book?.spread?.line === 'number');
    return typeof found?.spread?.line === 'number' ? found.spread.line : null;
  };

  const getBestOdds = (bookmakers: OddsData['bookmakers'], market: 'moneyline' | 'spread' | 'total', side: 'home' | 'away' | 'over' | 'under') => {
    let bestBook: string | null = null;
    let bestValue: number | null = null;

    bookmakers.forEach(book => {
      let value: number | null | undefined;
      if (market === 'moneyline') {
        value = side === 'home' ? book.moneyline.home : book.moneyline.away;
      } else if (market === 'spread') {
        value = side === 'home' ? book.spread.home : book.spread.away;
      } else if (market === 'total') {
        value = side === 'over' ? book.total.over : book.total.under;
      }

      if (typeof value !== 'number' || !Number.isFinite(value)) return;

      if (bestValue === null || value > bestValue) {
        bestValue = value;
        bestBook = book.name;
      }
    });

    return { value: bestValue, book: bestBook };
  };

  const getAlertColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'border-red-400/30 bg-red-600/10 text-red-400';
      case 'medium': return 'border-yellow-400/30 bg-yellow-600/10 text-yellow-400';
      case 'low': return 'border-blue-400/30 bg-blue-600/10 text-blue-400';
      default: return 'border-gray-400/30 bg-gray-600/10 text-gray-400';
    }
  };

  const getMovementIcon = (direction: string) => {
    return direction === 'up' ? 
      <TrendingUp className="w-4 h-4 text-green-400" /> : 
      <TrendingDown className="w-4 h-4 text-red-400" />;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-400/30 border-t-blue-400 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-400">{t('odds.loading')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Controls */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white flex items-center space-x-2">
          <Activity className="w-6 h-6 text-blue-400" />
          <span>{t('odds.title')}</span>
        </h2>
        <div className="flex items-center space-x-4">
          {selectedGame && (
            <div className="glass-card px-3 py-2 flex items-center space-x-2">
              <span className="text-sm text-gray-300">{t('odds.selectedGame')}:</span>
              <span className="text-sm text-blue-400">{selectedGame}</span>
              <button
                onClick={() => { setSelectedGame(null); setShowSelectedOnly(false); }}
                className="text-xs text-gray-400 hover:text-white"
              >
                {t('common.clear')}
              </button>
            </div>
          )}
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={showSelectedOnly}
              onChange={(e) => setShowSelectedOnly(e.target.checked)}
              disabled={!selectedGame}
              aria-label={t('odds.onlySelected')}
              title={t('odds.onlySelected')}
              className="rounded"
            />
            <span className={`text-sm ${selectedGame ? 'text-gray-300' : 'text-gray-500'}`}>{t('odds.onlySelected')}</span>
          </div>
          <button
            onClick={async () => {
              await loadOdds();
              setLastUpdate(new Date());
            }}
            aria-label={t('odds.refresh')}
            title={t('odds.refresh')}
            className="glass-card p-2 hover:bg-white/10 transition-colors"
          >
            <RefreshCw className="w-5 h-5 text-gray-400 hover:text-white" />
          </button>
          <div className="glass-card px-3 py-2">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-sm text-gray-300">
                {t('odds.lastUpdate')}: {lastUpdate.toLocaleTimeString(locale, { timeZone: 'America/Chicago' })}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
        {/* Live Alerts */}
        <div className="xl:col-span-1">
          <div className="glass-card">
            <div className="p-6 border-b border-gray-700/50">
              <h3 className="text-xl font-bold text-white flex items-center space-x-2" title={t('odds.tooltip.liveAlerts')}>
                <AlertTriangle className="w-5 h-5 text-yellow-400" />
                <span>{t('odds.liveAlerts')}</span>
              </h3>
            </div>
            <div className="p-6 space-y-3">
              {alerts.map((alert) => (
                <div key={alert.id} className={`p-3 rounded-lg border ${getAlertColor(alert.severity)}`}>
                  <div className="flex items-start justify-between mb-2">
                    <div className="text-sm font-medium">{alert.game}</div>
                    <div className="text-xs opacity-70">{alert.time}</div>
                  </div>
                  <div className="text-sm opacity-90">{alert.message}</div>
                  <div className="flex items-center justify-between mt-2">
                    <span className={`text-xs px-2 py-1 rounded ${
                      alert.type === 'movement' ? 'bg-blue-600/20 text-blue-400' :
                      alert.type === 'value' ? 'bg-green-600/20 text-green-400' :
                      'bg-red-600/20 text-red-400'
                    }`}>
                      {t(`odds.alertType.${alert.type}`)}
                    </span>
                    <span className="text-xs opacity-60 capitalize">{t(`odds.severity.${alert.severity}`)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Odds Comparison */}
        <div className="xl:col-span-3">
          <div className="glass-card">
            <div className="p-6 border-b border-gray-700/50">
              <h3 className="text-xl font-bold text-white flex items-center justify-between" title={t('odds.tooltip.comparison')}>
                <div className="flex items-center space-x-2">
                  <TrendingUp className="w-5 h-5 text-green-400" />
                  <span>{t('odds.comparisonTitle')}</span>
                </div>
                <span className="text-sm text-gray-400">{oddsData.length} {t('odds.gamesSuffix')}</span>
              </h3>
            </div>
            <div className="p-6 space-y-6">
              {(showSelectedOnly && selectedGame ? oddsData.filter(g => g.gameId === selectedGame) : oddsData).map((game) => (
                <div 
                  key={game.gameId} 
                  className={`glass-card p-4 cursor-pointer transition-all duration-300 ${
                    selectedGame === game.gameId ? 'neon-border' : 'hover:bg-white/5'
                  }`}
                  onClick={() => setSelectedGame(selectedGame === game.gameId ? null : game.gameId)}
                >
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <div className="text-lg font-semibold text-white">
                        {game.homeTeam} vs {game.awayTeam}
                      </div>
                      <div className="flex items-center space-x-4 text-sm text-gray-400">
                        <div className="flex items-center space-x-1">
                          <Clock className="w-4 h-4" />
                          <span>{game.startTime}</span>
                        </div>
                        {game.movements.length > 0 && (
                          <div className="flex items-center space-x-1">
                            <Activity className="w-4 h-4 text-yellow-400" />
                            <span>{game.movements.length} movements</span>
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="px-2 py-1 bg-blue-600/20 text-blue-400 text-xs rounded">
                        {t('odds.featured')}
                      </span>
                    </div>
                  </div>

                  {/* Quick Best Odds */}
                  <div
                    className={`grid gap-4 mb-4 ${
                      hasSpreadData(game.bookmakers) ? 'grid-cols-3' : 'grid-cols-2'
                    }`}
                  >
                    {hasSpreadData(game.bookmakers) && (
                      <div className="text-center p-3 bg-gray-800/30 rounded-lg">
                        <div className="text-xs text-gray-400 mb-1">{t('odds.label.spread')}</div>
                        <div className="text-white font-semibold">
                          {(() => {
                            const line = getFirstSpreadLine(game.bookmakers);
                            if (typeof line !== 'number') return t('common.noData');
                            return `${line > 0 ? '+' : ''}${line}`;
                          })()}
                        </div>
                        <div className="text-xs text-green-400">
                          {t('odds.best')}: {formatOddsOrNoData(getBestOdds(game.bookmakers, 'spread', 'home').value, t('common.noData'))}
                        </div>
                      </div>
                    )}
                    <div className="text-center p-3 bg-gray-800/30 rounded-lg">
                      <div className="text-xs text-gray-400 mb-1">{t('odds.label.total')}</div>
                      <div className="text-white font-semibold">
                        {typeof game.bookmakers[0]?.total.line === 'number' ? game.bookmakers[0].total.line : t('common.noData')}
                      </div>
                      <div className="text-xs text-green-400">
                        O: {formatOddsOrNoData(getBestOdds(game.bookmakers, 'total', 'over').value)}
                      </div>
                    </div>
                    <div className="text-center p-3 bg-gray-800/30 rounded-lg">
                      <div className="text-xs text-gray-400 mb-1">{t('odds.label.moneyline')}</div>
                      <div className="text-white font-semibold">
                        {formatOddsOrNoData(game.bookmakers[0]?.moneyline.home ?? null)}
                      </div>
                      <div className="text-xs text-green-400">
                        {t('odds.best')}: {formatOddsOrNoData(getBestOdds(game.bookmakers, 'moneyline', 'home').value)}
                      </div>
                    </div>
                  </div>

                  {/* Recent Movements */}
                  {game.movements.length > 0 && (
                    <div className="border-t border-gray-700/50 pt-3">
                      <div className="text-sm font-medium text-gray-300 mb-2">{t('odds.recentMovements')}</div>
                      <div className="flex space-x-4">
                        {game.movements.slice(0, 3).map((movement, index) => (
                          <div key={index} className="flex items-center space-x-2 text-sm">
                            {getMovementIcon(movement.direction)}
                            <span className="text-gray-400">
                              {movement.type}: {movement.from} → {movement.to}
                            </span>
                            <span className="text-xs text-gray-500">({movement.time})</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Detailed Bookmaker Comparison (when selected) */}
                  {selectedGame === game.gameId && (
                    <div className="border-t border-gray-700/50 pt-4 mt-4">
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b border-gray-700/50">
                              <th className="text-left py-2 text-gray-400">{t('odds.table.sportsbook')}</th>
                              {hasSpreadData(game.bookmakers) && (
                                <th className="text-center py-2 text-gray-400">{t('odds.label.spread')}</th>
                              )}
                              <th className="text-center py-2 text-gray-400">{t('odds.label.total')}</th>
                              <th className="text-center py-2 text-gray-400">{t('odds.label.moneyline')}</th>
                            </tr>
                          </thead>
                          <tbody>
                            {game.bookmakers.map((book, index) => (
                              <tr key={index} className="border-b border-gray-800/50">
                                <td className="py-2 font-medium text-white">{book.name}</td>
                                {hasSpreadData(game.bookmakers) && (
                                  <td className="text-center py-2">
                                    <div className="text-white">
                                      {typeof book.spread.line === 'number'
                                        ? `${book.spread.line > 0 ? '+' : ''}${book.spread.line}`
                                        : t('common.noData')}
                                    </div>
                                    <div className="text-xs text-gray-400">
                                      {formatOddsOrNoData(book.spread.home, t('common.noData'))} / {formatOddsOrNoData(book.spread.away, t('common.noData'))}
                                    </div>
                                  </td>
                                )}
                                <td className="text-center py-2">
                                  <div className="text-white">{book.total.line}</div>
                                  <div className="text-xs text-gray-400">
                                    {formatOddsOrNoData(book.total.over)} / {formatOddsOrNoData(book.total.under)}
                                  </div>
                                </td>
                                <td className="text-center py-2">
                                  <div className="text-xs text-gray-400">
                                    {formatOddsOrNoData(book.moneyline.home)} / {formatOddsOrNoData(book.moneyline.away)}
                                  </div>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiveOdds;
