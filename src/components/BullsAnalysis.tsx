import React, { useState, useEffect } from 'react';
import { Target, TrendingUp, TrendingDown, Users, Activity, Clock, AlertTriangle } from 'lucide-react';
import { useApi } from '../services/api';
import { useI18n } from '../i18n/useI18n';

interface Player {
  name: string;
  position: string;
  stats?: {
    ppg?: number | null;
    rpg?: number | null;
    apg?: number | null;
    fgPct?: number | null;
    ftPct?: number | null;
  } | null;
  form?: 'excellent' | 'good' | 'average' | 'poor' | null;
  minutes?: number | null;
  role: string;
  trend?: 'up' | 'down' | 'stable' | null;
}

type BullsNextGame = {
  game_id?: string | null;
  home_team?: string | null;
  away_team?: string | null;
  commence_time?: string | null;
  moneyline?: {
    home?: { best_price?: number | null; best_book?: string | null } | null;
    away?: { best_price?: number | null; best_book?: string | null } | null;
  } | null;
  spread?: { home_line?: number | null } | null;
  total?: { line?: number | null } | null;
} | null;

type TeamStats = {
  record?: { wins?: number | null; losses?: number | null } | null;
  ats?: { covers?: number | null; misses?: number | null; pushes?: number | null } | null;
  ou?: { overs?: number | null; unders?: number | null; pushes?: number | null } | null;
  last5?: { wins?: number | null; losses?: number | null } | null;
  trends?: Record<string, { value?: number | null; trend?: string | null; change?: string | null }> | null;
} | null;

type RiskFactor = {
  key: 'back_to_back' | 'home_court' | string;
  value?: boolean | null;
  meta?: Record<string, unknown> | null;
};

const BullsAnalysis: React.FC = () => {
  const [players, setPlayers] = useState<Player[]>([]);
  const [nextGame, setNextGame] = useState<BullsNextGame>(null);
  const [teamStats, setTeamStats] = useState<TeamStats>(null);
  const [riskFactors, setRiskFactors] = useState<RiskFactor[]>([]);
  const [loading, setLoading] = useState(true);
  
  const apiHook = useApi();
  const { t } = useI18n();

  const asString = (value: unknown, fallback: string) =>
    typeof value === 'string' ? value : fallback;

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      
      try {
        // Fetch real Bulls data from API
        const [bullsPlayersData, bullsAnalysisData] = await Promise.all([
          apiHook.getBullsPlayers(),
          apiHook.getBullsAnalysis().catch(() => null) // Optional - fallback if analysis not available
        ]);

        const analysisData =
          bullsAnalysisData && typeof bullsAnalysisData === 'object'
            ? (bullsAnalysisData as Record<string, unknown>)
            : null;
        const analysisPlayers = Array.isArray(analysisData?.players)
          ? (analysisData?.players as Record<string, unknown>[])
          : null;
        
        // Transform Bulls players data to match Player interface
        const transformedPlayers = analysisPlayers
          ? analysisPlayers.map((p: Record<string, unknown>) => ({
              name: asString(p?.name, t('bulls.fallback.unknownName')),
              position: asString(p?.position, t('common.na')),
              role: asString(p?.role, asString(p?.position, t('bulls.fallback.playerRole'))),
              stats: (p?.stats as Player['stats']) ?? null,
              form: (p?.form as Player['form']) ?? null,
              minutes: typeof p?.minutes === 'number' ? p.minutes : null,
              trend: (p?.trend as Player['trend']) ?? null
            }))
          : (bullsPlayersData || []).slice(0, 12).map((player: Record<string, unknown>) => ({
              name: asString(player?.name, t('bulls.fallback.unknownName')),
              position: asString(player?.position, t('common.na')),
              role: asString(player?.position, t('bulls.fallback.playerRole')),
              stats: null,
              form: null,
              minutes: null,
              trend: null
            }));
        
        setPlayers(transformedPlayers);
        setNextGame((analysisData?.next_game as BullsNextGame) ?? null);
        setTeamStats((analysisData?.team_stats as TeamStats) ?? null);
        setRiskFactors(Array.isArray(analysisData?.risk_factors) ? (analysisData?.risk_factors as RiskFactor[]) : []);
        
      } catch (error) {
        console.error('Error fetching Bulls data:', error);
        setPlayers([]);
        setNextGame(null);
        setTeamStats(null);
        setRiskFactors([]);
      }
      finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [apiHook, t]);

  const getFormLabel = (form: Player['form']) => (form ? t(`bulls.form.${form}`) : t('common.noData'));

  const getTrendLabel = (trendKey: string) => {
    const labelMap: Record<string, string> = {
      pace: 'bulls.trends.pace',
      offRtg: 'bulls.trends.offRtg',
      defRtg: 'bulls.trends.defRtg',
      threePointPct: 'bulls.trends.threePointPct',
      freeThrowPct: 'bulls.trends.freeThrowPct'
    };
    const translationKey = labelMap[trendKey];
    return translationKey ? t(translationKey) : trendKey;
  };

  const getFormColor = (form: string) => {
    switch (form) {
      case 'excellent': return 'text-green-400 bg-green-600/20';
      case 'good': return 'text-blue-400 bg-blue-600/20';
      case 'average': return 'text-yellow-400 bg-yellow-600/20';
      case 'poor': return 'text-red-400 bg-red-600/20';
      default: return 'text-gray-400 bg-gray-600/20';
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return <TrendingUp className="w-4 h-4 text-green-400" />;
      case 'down': return <TrendingDown className="w-4 h-4 text-red-400" />;
      case 'stable': return <Activity className="w-4 h-4 text-yellow-400" />;
      default: return null;
    }
  };



  const formatWl = (record?: { wins?: number | null; losses?: number | null } | null) => {
    const wins = record?.wins;
    const losses = record?.losses;
    if (typeof wins !== 'number' || typeof losses !== 'number') return t('common.noData');
    return `${wins}-${losses}`;
  };

  const formatWlp = (record?: { wins?: number | null; losses?: number | null; pushes?: number | null } | null) => {
    const wins = record?.wins;
    const losses = record?.losses;
    const pushes = record?.pushes;
    if (typeof wins !== 'number' || typeof losses !== 'number') return t('common.noData');
    if (typeof pushes === 'number') return `${wins}-${losses}-${pushes}`;
    return `${wins}-${losses}`;
  };

  const formatNumber = (value: number) => value.toFixed(2).replace(/\.?0+$/, '');

  const formatStat = (value: number | null | undefined) =>
    (typeof value === 'number' ? formatNumber(value) : t('common.noData'));

  const formatPercent = (value: number | null | undefined) =>
    (typeof value === 'number' ? `${formatNumber(value * 100)}%` : t('common.noData'));

  const formatTrendValue = (value: number | null | undefined, key: string) => {
    if (typeof value !== 'number') return t('common.noData');
    if (key === 'threePointPct' || key === 'freeThrowPct') return `${(value * 100).toFixed(1)}%`;
    return value.toFixed(1);
  };

  const isBullsHome = (homeTeam?: string | null) => (homeTeam || '').trim().toLowerCase() === 'chicago bulls';

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-red-400/30 border-t-red-400 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-400">{t('bulls.loading')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Team Overview */}
      <div className="glass-card">
        <div className="p-6 border-b border-gray-700/50">
          <h2 className="text-2xl font-bold text-white flex items-center space-x-3">
            <div className="w-10 h-10 bulls-gradient rounded-lg flex items-center justify-center">
              <span className="text-white font-bold">🐂</span>
            </div>
            <span>{t('bulls.header.title')}</span>
            <div className="ml-auto flex items-center space-x-2">
              <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
              <span className="text-sm text-gray-400">{t('bulls.header.liveData')}</span>
            </div>
          </h2>
        </div>

        <div className="p-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-white">{formatWl(teamStats?.record)}</div>
              <div className="text-sm text-gray-400">{t('bulls.overview.overallRecord')}</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-400">
                {formatWlp(teamStats?.ats ? { wins: teamStats.ats.covers ?? null, losses: teamStats.ats.misses ?? null, pushes: teamStats.ats.pushes ?? null } : null)}
              </div>
              <div className="text-sm text-gray-400">{t('bulls.overview.atsRecord')}</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-400">
                {formatWlp(teamStats?.ou ? { wins: teamStats.ou.overs ?? null, losses: teamStats.ou.unders ?? null, pushes: teamStats.ou.pushes ?? null } : null)}
              </div>
              <div className="text-sm text-gray-400">{t('bulls.overview.ouRecord')}</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-400">{formatWl(teamStats?.last5)}</div>
              <div className="text-sm text-gray-400">{t('bulls.overview.last5Games')}</div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Player Analysis */}
        <div className="xl:col-span-2">
          <div className="glass-card">
            <div className="p-6 border-b border-gray-700/50">
              <h3 className="text-xl font-bold text-white flex items-center space-x-2">
                <Users className="w-5 h-5 text-blue-400" />
                <span>{t('bulls.sections.playerAnalysis')}</span>
              </h3>
            </div>
            <div className="p-6 space-y-4">
              {players.length === 0 ? (
                <div className="text-center text-gray-400 py-8">{t('common.noData')}</div>
              ) : (
                players.map((player, index) => (
                  <div key={index} className="glass-card p-4 hover:bg-white/5 transition-colors">
                    <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-4">
                      <div className="flex items-center space-x-3">
                        <div className="w-12 h-12 bg-red-600/20 rounded-lg flex items-center justify-center">
                          <span className="text-red-400 font-bold text-sm">{player.position || t('common.na')}</span>
                        </div>
                        <div>
                          <div className="font-semibold text-white">{player.name}</div>
                          <div className="text-sm text-gray-400">{player.role}</div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        {player.form ? (
                          <span className={`px-2 py-1 rounded text-xs ${getFormColor(player.form)}`}>
                            {getFormLabel(player.form)}
                          </span>
                        ) : (
                          <span className="px-2 py-1 rounded text-xs text-gray-400 bg-gray-600/20">
                            {t('common.noData')}
                          </span>
                        )}
                        {player.trend ? getTrendIcon(player.trend) : null}
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-6 gap-3 text-center">
                      <div>
                        <div className="text-lg font-bold text-white">{formatStat(player.stats?.ppg)}</div>
                        <div className="text-xs text-gray-400">PTS</div>
                      </div>
                      <div>
                        <div className="text-lg font-bold text-white">{formatStat(player.stats?.rpg)}</div>
                        <div className="text-xs text-gray-400">REB</div>
                      </div>
                      <div>
                        <div className="text-lg font-bold text-white">{formatStat(player.stats?.apg)}</div>
                        <div className="text-xs text-gray-400">AST</div>
                      </div>
                      <div>
                        <div className="text-lg font-bold text-white">{formatPercent(player.stats?.fgPct)}</div>
                        <div className="text-xs text-gray-400">FG%</div>
                      </div>
                      <div>
                        <div className="text-lg font-bold text-white">{formatPercent(player.stats?.ftPct)}</div>
                        <div className="text-xs text-gray-400">FT%</div>
                      </div>
                      <div>
                        <div className="text-lg font-bold text-white">{formatStat(player.minutes)}</div>
                        <div className="text-xs text-gray-400">MIN</div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Next Game Analysis */}
        <div>
          <div className="glass-card">
            <div className="p-6 border-b border-gray-700/50">
              <h3 className="text-xl font-bold text-white flex items-center space-x-2">
                <Target className="w-5 h-5 text-green-400" />
                <span>{t('bulls.sections.nextGame')}</span>
              </h3>
            </div>
            <div className="p-6 space-y-4">
              {nextGame ? (
                <>
                  <div className="text-center mb-6">
                    {(() => {
                      const homeTeam = nextGame?.home_team || '';
                      const awayTeam = nextGame?.away_team || '';
                      const bullsHome = isBullsHome(homeTeam);
                      const opponent = (bullsHome ? awayTeam : homeTeam) || t('common.noData');
                      const locationLabel = bullsHome ? t('bulls.nextGame.location.home') : t('bulls.nextGame.location.away');
                      const dateLabel = nextGame?.commence_time
                        ? new Date(nextGame.commence_time).toLocaleString(undefined, { month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' })
                        : t('common.noData');

                      const homeLine = nextGame?.spread?.home_line;
                      const bullsSpread = typeof homeLine === 'number' ? (bullsHome ? homeLine : -homeLine) : null;
                      const spreadLabel = typeof bullsSpread === 'number' ? `${bullsSpread > 0 ? '+' : ''}${bullsSpread}` : t('common.noData');
                      const totalLine = nextGame?.total?.line;
                      const totalLabel = typeof totalLine === 'number' ? totalLine : t('common.noData');

                      return (
                        <>
                          <div className="text-lg font-bold text-white mb-1">{t('bulls.nextGame.vsOpponent', { opponent })}</div>
                          <div className="text-gray-400 mb-2">
                            {t('bulls.nextGame.dateLocation', { date: dateLabel, location: locationLabel })}
                          </div>
                          <div className="flex justify-center space-x-4 text-sm">
                            <span className="text-blue-400">{t('bulls.nextGame.spread', { value: spreadLabel })}</span>
                            <span className="text-purple-400">{t('bulls.nextGame.total', { value: totalLabel })}</span>
                          </div>
                        </>
                      );
                    })()}
                  </div>

                  <div className="glass-card p-4 border border-green-600/20">
                    <div className="text-center mb-3">
                      <div className="text-sm text-gray-400 mb-1">{t('bulls.nextGame.prediction')}</div>
                      <div className="text-lg font-bold text-gray-300">{t('common.noData')}</div>
                    </div>
                  </div>

                  <div>
                    <div className="text-sm font-semibold text-gray-300 mb-3">{t('bulls.nextGame.positionalMatchups')}</div>
                    <div className="text-center text-gray-400 py-4">{t('common.noData')}</div>
                  </div>
                </>
              ) : (
                <div className="text-center text-gray-400 py-6">{t('common.noData')}</div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Team Trends */}
      <div className="glass-card">
        <div className="p-6 border-b border-gray-700/50">
          <h3 className="text-xl font-bold text-white flex items-center space-x-2">
            <Activity className="w-5 h-5 text-purple-400" />
            <span>{t('bulls.trends.title', { games: 7 })}</span>
          </h3>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
            {teamStats?.trends ? (
              Object.entries(teamStats.trends).map(([key, data]) => {
                const trendData = data as { value?: number | null; trend?: string | null; change?: string | null };
                return (
                  <div key={key} className="text-center">
                    <div className="flex items-center justify-center space-x-2 mb-2">
                      <span className="text-lg font-bold text-white">{formatTrendValue(trendData.value, key)}</span>
                      {trendData.trend ? getTrendIcon(trendData.trend) : null}
                    </div>
                    <div className="text-sm text-gray-400 mb-1">{getTrendLabel(key)}</div>
                    <div className="text-xs text-gray-400">{trendData.change || t('common.noData')}</div>
                  </div>
                );
              })
            ) : (
              <div className="col-span-full text-center text-gray-400 py-4">{t('common.noData')}</div>
            )}
          </div>
        </div>
      </div>

      {/* Risk Factors */}
      <div className="glass-card border-yellow-400/20">
        <div className="p-6 border-b border-gray-700/50">
          <h3 className="text-xl font-bold text-white flex items-center space-x-2">
            <AlertTriangle className="w-5 h-5 text-yellow-400" />
            <span>{t('bulls.risk.title')}</span>
          </h3>
        </div>
        <div className="p-6">
          {riskFactors.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {riskFactors.map((rf, idx) => {
                const isB2B = rf.key === 'back_to_back';
                const isHome = rf.key === 'home_court';
                const titleKey = isB2B ? 'bulls.risk.backToBack.title' : isHome ? 'bulls.risk.homeCourt.title' : 'bulls.risk.title';
                const descKey = isB2B ? 'bulls.risk.backToBack.desc' : isHome ? 'bulls.risk.homeCourt.desc' : null;
                const icon = isB2B ? (
                  <AlertTriangle className="w-5 h-5 text-yellow-400 flex-shrink-0" />
                ) : (
                  <Clock className="w-5 h-5 text-blue-400 flex-shrink-0" />
                );

                const desc = descKey
                  ? t(descKey, {
                      ...(isB2B ? { isBackToBack: rf.value ? t('common.yes') : t('common.no') } : {}),
                      ...(isHome ? { record: asString(rf?.meta?.home_record, t('common.noData')) } : {})
                    })
                  : t('common.noData');

                return (
                  <div
                    key={`${rf.key}-${idx}`}
                    className={`flex items-center space-x-3 p-3 rounded-lg border ${
                      isB2B
                        ? 'bg-yellow-600/10 border-yellow-600/20'
                        : 'bg-blue-600/10 border-blue-600/20'
                    }`}
                  >
                    {icon}
                    <div>
                      <div className="text-white font-medium">{t(titleKey)}</div>
                      <div className="text-sm text-gray-400">{desc}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center text-gray-400 py-2">{t('common.noData')}</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default BullsAnalysis;
