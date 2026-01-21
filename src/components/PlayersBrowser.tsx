import React, { useState, useEffect } from 'react';
import { 
  Users, 
  Search, 
  Filter, 
  X, 
  TrendingUp, 
  BarChart3,
  User
} from 'lucide-react';
import { api } from '../services/api';
import { useI18n } from '../i18n/useI18n';

interface Player {
  id: string;
  name: string;
  team_abbreviation?: string;
  position?: string;
  jersey_number?: number;
  is_active?: boolean;
  basketball_reference_id?: string;
  basketball_reference_url?: string;
  teams?: {
    abbreviation: string;
    full_name: string;
  };
  // Optional stats (only when backend provides them)
  stats?: {
    ppg?: number | null;
    rpg?: number | null;
    apg?: number | null;
    fg_percentage?: number | null;
    three_point_percentage?: number | null;
    ft_percentage?: number | null;
    steals?: number | null;
    blocks?: number | null;
    turnovers?: number | null;
    minutes_per_game?: number | null;
    spg?: number | null;
    bpg?: number | null;
    tov?: number | null;
    mpg?: number | null;
    games_played?: number | null;
    season_year?: string | null;
  };
  bio?: {
    height?: string | null;
    weight?: number | null;
    birth_date?: string | null;
    experience?: number | null;
    college?: string | null;
  };
  recent_games?: Array<{
    game_date?: string | null;
    points?: number | null;
    rebounds?: number | null;
    assists?: number | null;
    steals?: number | null;
    blocks?: number | null;
    turnovers?: number | null;
    minutes?: string | null;
  }> | null;
}

const asRecord = (value: unknown): Record<string, unknown> =>
  value && typeof value === 'object' ? (value as Record<string, unknown>) : {};

const asString = (value: unknown, fallback = ''): string =>
  typeof value === 'string' ? value : fallback;

const toPlayer = (value: unknown): Player | null => {
  const record = asRecord(value);
  const id = asString(record.id);
  const name = asString(record.name);
  if (!id || !name) return null;

  const teamInfo = asRecord(record.teams);
  const teamAbbrev = asString(record.team_abbreviation);
  const position = asString(record.position);

  return {
    id,
    name,
    team_abbreviation: teamAbbrev || undefined,
    position: position || undefined,
    jersey_number: typeof record.jersey_number === 'number' ? record.jersey_number : undefined,
    is_active: typeof record.is_active === 'boolean' ? record.is_active : undefined,
    basketball_reference_id: asString(record.basketball_reference_id) || undefined,
    basketball_reference_url: asString(record.basketball_reference_url) || undefined,
    teams: teamInfo.abbreviation
      ? {
          abbreviation: asString(teamInfo.abbreviation),
          full_name: asString(teamInfo.full_name),
        }
      : undefined,
    stats: (record.stats as Player['stats']) || undefined,
    bio: (record.bio as Player['bio']) || undefined,
    recent_games: (record.recent_games as Player['recent_games']) || undefined,
  };
};

const toTeamOption = (value: unknown): { abbreviation: string } | null => {
  const record = asRecord(value);
  const abbreviation = asString(record.abbreviation);
  return abbreviation ? { abbreviation } : null;
};

const PlayersBrowser: React.FC = () => {
  const { t } = useI18n();
  const [players, setPlayers] = useState<Player[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTeam, setSelectedTeam] = useState<string>('All');
  const [selectedPosition, setSelectedPosition] = useState<string>('All');
  const [selectedPlayer, setSelectedPlayer] = useState<Player | null>(null);
  const [selectedPlayerDetails, setSelectedPlayerDetails] = useState<Player | null>(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [comparisonPlayers, setComparisonPlayers] = useState<Player[]>([]);
  const [showComparison, setShowComparison] = useState(false);
  const [teams, setTeams] = useState<{abbreviation: string}[]>([]);

  const positions = ['All', 'PG', 'SG', 'SF', 'PF', 'C'];

  const getStatLabel = (stat: string) => {
    const map: Record<string, string> = {
      ppg: t('players.stats.ppg'),
      rpg: t('players.stats.rpg'),
      apg: t('players.stats.apg'),
      fg_percentage: t('players.stats.fgPct'),
      three_point_percentage: t('players.stats.tpPct'),
      ft_percentage: t('players.stats.ftPct'),
      steals: t('players.stats.steals'),
      blocks: t('players.stats.blocks'),
      turnovers: t('players.stats.turnovers'),
      minutes_per_game: t('players.stats.mpg'),
    };

    return map[stat] || stat;
  };

  const buildSparkPath = (values: number[], width: number, height: number) => {
    if (values.length === 0) return '';
    const min = Math.min(...values);
    const max = Math.max(...values);
    const span = max - min || 1;
    const step = values.length > 1 ? width / (values.length - 1) : 0;
    const points = values.map((v, i) => {
      const x = i * step;
      const y = height - ((v - min) / span) * height;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    });
    return `M ${points.join(' L ')}`;
  };

  const Sparkline = ({ values, tone }: { values: number[]; tone: 'up' | 'down' | 'flat' }) => {
    if (!values.length) {
      return <div className="text-xs text-gray-500">{t('common.noData')}</div>;
    }
    const width = 120;
    const height = 32;
    const path = buildSparkPath(values, width, height);
    const stroke = tone === 'up' ? '#34d399' : tone === 'down' ? '#f87171' : '#60a5fa';
    return (
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className="mx-auto">
        <path d={path} fill="none" stroke={stroke} strokeWidth="2" />
      </svg>
    );
  };

  const trendDelta = (values: number[]) => {
    if (values.length < 6) return null;
    const last5 = values.slice(-5);
    const prev5 = values.slice(-10, -5);
    if (prev5.length === 0) return null;
    const avg = (arr: number[]) => arr.reduce((a, b) => a + b, 0) / arr.length;
    const prev = avg(prev5);
    const curr = avg(last5);
    if (prev === 0) return null;
    return ((curr - prev) / prev) * 100;
  };

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Fetch players
        const playersResponse = await api.players.getAll({
          active: true,
          includeStats: true,
          ...(selectedTeam !== 'All' && { team: selectedTeam }),
          ...(selectedPosition !== 'All' && { position: selectedPosition })
        });

        // Stats are not available from the current backend; do not fabricate.
        const parsedPlayers = (playersResponse.players || [])
          .map(toPlayer)
          .filter((player): player is Player => Boolean(player));
        setPlayers(parsedPlayers);

        // Fetch teams for filter
        const teamsResponse = await api.teams.getAll();
        const parsedTeams = (teamsResponse.teams || [])
          .map(toTeamOption)
          .filter((team): team is { abbreviation: string } => Boolean(team));
        setTeams([{abbreviation: 'All'}, ...parsedTeams]);
      } catch (error) {
        console.error('Error fetching players:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [selectedTeam, selectedPosition]);

  // Get player image URL (Basketball-Reference headshots)
  const getPlayerImage = (player: Player) => {
    let brId = player.basketball_reference_id;
    if (!brId && player.basketball_reference_url) {
      const match = player.basketball_reference_url.match(/\/players\/[a-z]\/([a-z0-9]+)\.html/i);
      if (match) {
        brId = match[1];
      }
    }

    if (brId) {
      return `https://www.basketball-reference.com/req/202106291/images/players/${brId}.jpg`;
    }

    return `https://ui-avatars.com/api/?name=${encodeURIComponent(player.name)}&size=200&background=1f2937&color=fff`;
  };

  const filteredPlayers = players.filter(player => {
    const matchesSearch = player.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      player.team_abbreviation?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      player.position?.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesSearch;
  });

  const addToComparison = (player: Player) => {
    if (comparisonPlayers.length >= 4) {
      alert(t('players.comparison.maxPlayersAlert', { max: 4 }));
      return;
    }
    if (!comparisonPlayers.find(p => p.id === player.id)) {
      setComparisonPlayers([...comparisonPlayers, player]);
    }
  };

  const removeFromComparison = (playerId: string) => {
    setComparisonPlayers(comparisonPlayers.filter(p => p.id !== playerId));
  };

  const toggleComparison = () => {
    if (showComparison && comparisonPlayers.length === 0) return;
    setShowComparison(!showComparison);
  };
  const openPlayerDetails = async (player: Player) => {
    setSelectedPlayer(player);
    setSelectedPlayerDetails(null);
    setDetailsLoading(true);
    try {
      const response = await api.players.getById(player.id);
      if (response?.player) {
        const parsed = toPlayer(response.player);
        if (parsed) {
          setSelectedPlayerDetails(parsed);
        }
      }
    } catch (error) {
      console.error('Failed to load player details:', error);
    } finally {
      setDetailsLoading(false);
    }
  };



  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-400/30 border-t-blue-400 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-400">{t('players.loading')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2 flex items-center space-x-2">
            <Users className="w-8 h-8 text-blue-400" />
            <span>{t('players.title')}</span>
          </h1>
          <p className="text-gray-400">{t('players.subtitle')}</p>
        </div>
        {comparisonPlayers.length > 0 && (
          <button
            onClick={toggleComparison}
            className="flex items-center space-x-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors"
          >
            <BarChart3 className="w-5 h-5" />
            <span>{t('players.actions.compare', { count: comparisonPlayers.length })}</span>
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="glass-card p-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder={t('players.search.placeholder')}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-700/50 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-blue-400 focus:outline-none"
            />
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Filter className="w-4 h-4 text-gray-400" />
              <select
                aria-label={t('players.filter.teamLabel')}
                title={t('players.filter.teamLabel')}
                value={selectedTeam}
                onChange={(e) => setSelectedTeam(e.target.value)}
                className="bg-gray-700/50 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:border-blue-400 focus:outline-none"
              >
                {teams.map(team => (
                  <option key={team.abbreviation} value={team.abbreviation}>
                    {team.abbreviation === 'All' ? t('players.filter.allTeams') : team.abbreviation}
                  </option>
                ))}
              </select>
            </div>

            <select
              aria-label={t('players.filter.positionLabel')}
              title={t('players.filter.positionLabel')}
              value={selectedPosition}
              onChange={(e) => setSelectedPosition(e.target.value)}
              className="bg-gray-700/50 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:border-blue-400 focus:outline-none"
            >
              {positions.map(pos => (
                <option key={pos} value={pos}>{pos === 'All' ? t('players.filter.allPositions') : pos}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Comparison View */}
      {showComparison && comparisonPlayers.length > 0 && (
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-white flex items-center space-x-2">
              <BarChart3 className="w-6 h-6 text-purple-400" />
              <span>{t('players.comparison.title')}</span>
            </h2>
            <button
              onClick={() => setComparisonPlayers([])}
              className="text-sm text-gray-400 hover:text-white"
            >
              {t('common.clearAll')}
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-700/50">
                  <th className="text-left py-3 px-4 text-gray-400">{t('players.comparison.table.stat')}</th>
                  {comparisonPlayers.map(player => (
                    <th key={player.id} className="text-center py-3 px-4 text-white">
                      <div className="flex flex-col items-center">
                        <img 
                          src={getPlayerImage(player)} 
                          alt={player.name}
                          className="w-16 h-16 rounded-full mb-2 object-cover"
                          onError={(e) => {
                            (e.target as HTMLImageElement).src = `https://ui-avatars.com/api/?name=${encodeURIComponent(player.name)}&size=64&background=1f2937&color=fff`;
                          }}
                        />
                        <div className="font-semibold">{player.name}</div>
                        <div className="text-xs text-gray-400">{player.team_abbreviation} - {player.position}</div>
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {comparisonPlayers[0]?.stats ? (
                  Object.entries(comparisonPlayers[0].stats).map(([stat]) => {
                    const values = comparisonPlayers
                      .map(p => p.stats?.[stat as keyof typeof p.stats])
                      .filter((v): v is number => typeof v === 'number' && Number.isFinite(v));
                    const maxValue = values.length ? Math.max(...values) : null;
                    const isPercentage = stat.includes('percentage');

                    return (
                      <tr key={stat} className="border-b border-gray-800/50">
                        <td className="py-3 px-4 text-gray-300 font-medium">{getStatLabel(stat)}</td>
                        {comparisonPlayers.map((player) => {
                          const playerValue = player.stats?.[stat as keyof typeof player.stats];
                          const hasValue = typeof playerValue === 'number' && Number.isFinite(playerValue);
                          const isMax = hasValue && maxValue !== null && playerValue === maxValue && values.filter(v => v === maxValue).length === 1;
                          return (
                            <td key={player.id} className="py-3 px-4 text-center">
                              <div className={`flex items-center justify-center space-x-2 ${
                                isMax ? 'text-green-400 font-bold' : 'text-white'
                              }`}>
                                <span>
                                  {!hasValue
                                    ? t('common.noData')
                                    : isPercentage
                                      ? `${(playerValue * 100).toFixed(1)}%`
                                      : playerValue.toFixed(1)
                                  }
                                </span>
                                {isMax && <TrendingUp className="w-4 h-4" />}
                              </div>
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })
                ) : (
                  <tr className="border-b border-gray-800/50">
                    <td
                      className="py-6 px-4 text-center text-gray-400"
                      colSpan={comparisonPlayers.length + 1}
                    >
                      {t('common.noData')}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Players Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {filteredPlayers.map(player => {
          const isInComparison = comparisonPlayers.some(p => p.id === player.id);
          return (
            <div 
              key={player.id} 
              className="glass-card p-6 hover:neon-border transition-all duration-300 cursor-pointer group"
              onClick={() => openPlayerDetails(player)}
            >
              <div className="flex flex-col items-center mb-4">
                <img 
                  src={getPlayerImage(player)} 
                  alt={player.name}
                  className="w-32 h-32 rounded-full mb-3 object-cover border-4 border-gray-700 group-hover:border-blue-500 transition-colors"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = `https://ui-avatars.com/api/?name=${encodeURIComponent(player.name)}&size=128&background=1f2937&color=fff`;
                  }}
                />
                <h3 className="text-lg font-bold text-white text-center group-hover:text-blue-400 transition-colors">
                  {player.name}
                </h3>
                <div className="text-sm text-gray-400 mt-1">
                  #{player.jersey_number ?? t('common.unknownShort')} - {player.position || t('common.na')} - {player.team_abbreviation || t('common.na')}
                </div>
              </div>

              {player.stats && (
                <div className="grid grid-cols-3 gap-2 text-center mb-4">
                  <div>
                    <div className="text-lg font-bold text-white">{typeof player.stats.ppg === 'number' ? player.stats.ppg.toFixed(1) : t('common.noData')}</div>
                    <div className="text-xs text-gray-400">{t('players.statShort.ppg')}</div>
                  </div>
                  <div>
                    <div className="text-lg font-bold text-white">{typeof player.stats.rpg === 'number' ? player.stats.rpg.toFixed(1) : t('common.noData')}</div>
                    <div className="text-xs text-gray-400">{t('players.statShort.rpg')}</div>
                  </div>
                  <div>
                    <div className="text-lg font-bold text-white">{typeof player.stats.apg === 'number' ? player.stats.apg.toFixed(1) : t('common.noData')}</div>
                    <div className="text-xs text-gray-400">{t('players.statShort.apg')}</div>
                  </div>
                </div>
              )}

              <div className="flex items-center justify-between">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    if (isInComparison) {
                      removeFromComparison(player.id);
                    } else {
                      addToComparison(player);
                    }
                  }}
                  className={`px-3 py-1 rounded text-sm transition-colors ${
                    isInComparison
                      ? 'bg-purple-600 hover:bg-purple-700 text-white'
                      : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                  }`}
                >
                  {isInComparison ? t('players.actions.removeFromComparison') : t('players.actions.addToComparison')}
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    openPlayerDetails(player);
                  }}
                  className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm text-white"
                >
                  {t('common.details')}
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {filteredPlayers.length === 0 && (
        <div className="glass-card p-12 text-center">
          <User className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">{t('players.empty.title')}</h3>
          <p className="text-gray-400">{t('players.empty.subtitle')}</p>
        </div>
      )}

      {/* Player Details Modal */}
      {selectedPlayer && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/70" onClick={() => setSelectedPlayer(null)}></div>
          <div className="relative w-full max-w-4xl max-h-[90vh] bg-gray-900 border border-gray-700/50 rounded-lg overflow-auto">
            {(() => {
              const detail = selectedPlayerDetails || selectedPlayer;
              const stats = detail.stats;
              const bio = detail.bio;
              const seasonLabel = stats?.season_year ? ` - ${stats.season_year}` : '';
              const recentGames = detail.recent_games || [];
              const pointsSeries = recentGames
                .map(g => g.points)
                .filter((v): v is number => typeof v === 'number');
              const reboundsSeries = recentGames
                .map(g => g.rebounds)
                .filter((v): v is number => typeof v === 'number');
              const assistsSeries = recentGames
                .map(g => g.assists)
                .filter((v): v is number => typeof v === 'number');
              const stealsSeries = recentGames
                .map(g => g.steals)
                .filter((v): v is number => typeof v === 'number');
              const blocksSeries = recentGames
                .map(g => g.blocks)
                .filter((v): v is number => typeof v === 'number');
              const turnoversSeries = recentGames
                .map(g => g.turnovers)
                .filter((v): v is number => typeof v === 'number');
              return (
                <>
                  <div className="p-6 border-b border-gray-700/50 flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <img
                        src={getPlayerImage(detail)}
                        alt={detail.name}
                        className="w-20 h-20 rounded-full object-cover"
                        onError={(e) => {
                          (e.target as HTMLImageElement).src = `https://ui-avatars.com/api/?name=${encodeURIComponent(detail.name)}&size=80&background=1f2937&color=fff`;
                        }}
                      />
                      <div>
                        <h2 className="text-2xl font-bold text-white">{detail.name}</h2>
                        <div className="text-gray-400">
                          #{detail.jersey_number ?? t('common.unknownShort')} - {detail.position || t('common.na')} - {detail.team_abbreviation || t('common.na')}{seasonLabel}
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => setSelectedPlayer(null)}
                      aria-label={t('common.close')}
                      title={t('common.close')}
                      className="p-2 hover:bg-white/10 rounded transition-colors"
                    >
                      <X className="w-6 h-6 text-gray-400" />
                    </button>
                  </div>

                  <div className="p-6">
                    {detailsLoading && (
                      <div className="glass-card p-6 text-center text-gray-400 mb-6">
                        {t('players.details.loading')}
                      </div>
                    )}

                    {!detailsLoading && stats ? (
                      <div className="space-y-6 mb-6">
                        <div>
                          <div className="text-xs uppercase tracking-widest text-gray-500 mb-3">{t('players.details.seasonStats')}</div>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div className="glass-card p-4 text-center">
                              <div className="text-sm text-gray-400 mb-1">PPG</div>
                              <div className="text-2xl font-bold text-white">{typeof stats.ppg === 'number' ? stats.ppg.toFixed(1) : t('common.noData')}</div>
                            </div>
                            <div className="glass-card p-4 text-center">
                              <div className="text-sm text-gray-400 mb-1">RPG</div>
                              <div className="text-2xl font-bold text-white">{typeof stats.rpg === 'number' ? stats.rpg.toFixed(1) : t('common.noData')}</div>
                            </div>
                            <div className="glass-card p-4 text-center">
                              <div className="text-sm text-gray-400 mb-1">APG</div>
                              <div className="text-2xl font-bold text-white">{typeof stats.apg === 'number' ? stats.apg.toFixed(1) : t('common.noData')}</div>
                            </div>
                            <div className="glass-card p-4 text-center">
                              <div className="text-sm text-gray-400 mb-1">{t('players.details.gamesPlayed')}</div>
                              <div className="text-2xl font-bold text-white">{typeof stats.games_played === 'number' ? stats.games_played : t('common.noData')}</div>
                            </div>
                          </div>
                        </div>

                        <div>
                          <div className="text-xs uppercase tracking-widest text-gray-500 mb-3" title={t('players.tooltip.gameMetrics')}>{t('players.details.gameMetrics')}</div>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div className="glass-card p-4 text-center">
                              <div className="text-sm text-gray-400 mb-1">{t('players.stats.fgPct')}</div>
                              <div className="text-2xl font-bold text-white">{typeof stats.fg_percentage === 'number' ? `${(stats.fg_percentage * 100).toFixed(1)}%` : t('common.noData')}</div>
                            </div>
                            <div className="glass-card p-4 text-center">
                              <div className="text-sm text-gray-400 mb-1">{t('players.stats.tpPct')}</div>
                              <div className="text-2xl font-bold text-white">{typeof stats.three_point_percentage === 'number' ? `${(stats.three_point_percentage * 100).toFixed(1)}%` : t('common.noData')}</div>
                            </div>
                            <div className="glass-card p-4 text-center">
                              <div className="text-sm text-gray-400 mb-1">{t('players.stats.ftPct')}</div>
                              <div className="text-2xl font-bold text-white">{typeof stats.ft_percentage === 'number' ? `${(stats.ft_percentage * 100).toFixed(1)}%` : t('common.noData')}</div>
                            </div>
                            <div className="glass-card p-4 text-center">
                              <div className="text-sm text-gray-400 mb-1">{t('players.stats.mpg')}</div>
                              <div className="text-2xl font-bold text-white">{typeof stats.mpg === 'number' ? stats.mpg.toFixed(1) : t('common.noData')}</div>
                            </div>
                            <div className="glass-card p-4 text-center">
                              <div className="text-sm text-gray-400 mb-1">{t('players.stats.steals')}</div>
                              <div className="text-2xl font-bold text-white">{typeof stats.spg === 'number' ? stats.spg.toFixed(1) : t('common.noData')}</div>
                            </div>
                            <div className="glass-card p-4 text-center">
                              <div className="text-sm text-gray-400 mb-1">{t('players.stats.blocks')}</div>
                              <div className="text-2xl font-bold text-white">{typeof stats.bpg === 'number' ? stats.bpg.toFixed(1) : t('common.noData')}</div>
                            </div>
                            <div className="glass-card p-4 text-center">
                              <div className="text-sm text-gray-400 mb-1">{t('players.stats.turnovers')}</div>
                              <div className="text-2xl font-bold text-white">{typeof stats.tov === 'number' ? stats.tov.toFixed(1) : t('common.noData')}</div>
                            </div>
                          </div>
                        </div>
                      </div>
                    ) : !detailsLoading && (
                      <div className="glass-card p-6 text-center text-gray-400 mb-6">
                        {t('common.noData')}
                      </div>
                    )}

                    <div className="glass-card p-4 mb-6">
                      <div className="text-xs uppercase tracking-widest text-gray-500 mb-3" title={t('players.tooltip.recentTrends')}>{t('players.details.recentTrends')}</div>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="text-center">
                          <div className="text-sm text-gray-400 mb-2">PTS</div>
                          <Sparkline values={pointsSeries} tone={trendDelta(pointsSeries) === null ? 'flat' : trendDelta(pointsSeries)! >= 0 ? 'up' : 'down'} />
                          <div className="text-sm text-gray-300 mt-2">
                            {pointsSeries.length ? pointsSeries[pointsSeries.length - 1].toFixed(1) : t('common.noData')}
                          </div>
                        </div>
                        <div className="text-center">
                          <div className="text-sm text-gray-400 mb-2">REB</div>
                          <Sparkline values={reboundsSeries} tone={trendDelta(reboundsSeries) === null ? 'flat' : trendDelta(reboundsSeries)! >= 0 ? 'up' : 'down'} />
                          <div className="text-sm text-gray-300 mt-2">
                            {reboundsSeries.length ? reboundsSeries[reboundsSeries.length - 1].toFixed(1) : t('common.noData')}
                          </div>
                        </div>
                        <div className="text-center">
                          <div className="text-sm text-gray-400 mb-2">AST</div>
                          <Sparkline values={assistsSeries} tone={trendDelta(assistsSeries) === null ? 'flat' : trendDelta(assistsSeries)! >= 0 ? 'up' : 'down'} />
                          <div className="text-sm text-gray-300 mt-2">
                            {assistsSeries.length ? assistsSeries[assistsSeries.length - 1].toFixed(1) : t('common.noData')}
                          </div>
                        </div>
                        <div className="text-center">
                          <div className="text-sm text-gray-400 mb-2">STL</div>
                          <Sparkline values={stealsSeries} tone={trendDelta(stealsSeries) === null ? 'flat' : trendDelta(stealsSeries)! >= 0 ? 'up' : 'down'} />
                          <div className="text-sm text-gray-300 mt-2">
                            {stealsSeries.length ? stealsSeries[stealsSeries.length - 1].toFixed(1) : t('common.noData')}
                          </div>
                        </div>
                        <div className="text-center">
                          <div className="text-sm text-gray-400 mb-2">BLK</div>
                          <Sparkline values={blocksSeries} tone={trendDelta(blocksSeries) === null ? 'flat' : trendDelta(blocksSeries)! >= 0 ? 'up' : 'down'} />
                          <div className="text-sm text-gray-300 mt-2">
                            {blocksSeries.length ? blocksSeries[blocksSeries.length - 1].toFixed(1) : t('common.noData')}
                          </div>
                        </div>
                        <div className="text-center">
                          <div className="text-sm text-gray-400 mb-2">TOV</div>
                          <Sparkline values={turnoversSeries} tone={trendDelta(turnoversSeries) === null ? 'flat' : trendDelta(turnoversSeries)! >= 0 ? 'up' : 'down'} />
                          <div className="text-sm text-gray-300 mt-2">
                            {turnoversSeries.length ? turnoversSeries[turnoversSeries.length - 1].toFixed(1) : t('common.noData')}
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="glass-card p-4 mb-6">
                      <div className="text-xs uppercase tracking-widest text-gray-500 mb-3" title={t('players.tooltip.trendSummary')}>{t('players.details.trendSummary')}</div>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                        {[
                          { label: 'PTS', values: pointsSeries },
                          { label: 'REB', values: reboundsSeries },
                          { label: 'AST', values: assistsSeries },
                          { label: 'STL', values: stealsSeries },
                          { label: 'BLK', values: blocksSeries },
                          { label: 'TOV', values: turnoversSeries },
                        ].map((item) => {
                          const delta = trendDelta(item.values);
                          const display = delta === null ? t('common.noData') : `${delta > 0 ? '+' : ''}${delta.toFixed(1)}%`;
                          const tone = delta === null ? 'text-gray-400' : delta >= 0 ? 'text-green-400' : 'text-red-400';
                          const badge = delta === null ? null : delta >= 5 ? 'hot' : delta <= -5 ? 'cold' : 'steady';
                          const badgeTone = badge === 'hot'
                            ? 'bg-green-600/20 text-green-300'
                            : badge === 'cold'
                              ? 'bg-red-600/20 text-red-300'
                              : 'bg-gray-600/20 text-gray-300';
                          return (
                            <div key={item.label} className="flex items-center justify-between rounded-lg bg-gray-800/40 px-3 py-2">
                              <span className="text-sm text-gray-300">{item.label}</span>
                              <div className="flex items-center space-x-2">
                                {badge && (
                                  <span className={`px-2 py-0.5 rounded-full text-[10px] uppercase tracking-widest ${badgeTone}`}>
                                    {badge}
                                  </span>
                                )}
                                <span className={`text-sm font-semibold ${tone}`}>{display}</span>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    <div className="glass-card p-4 mb-6">
                      <div className="text-xs uppercase tracking-widest text-gray-500 mb-3" title={t('players.tooltip.bio')}>{t('players.details.bio')}</div>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                        <div className="text-gray-300">
                          <span className="text-gray-500">{t('players.details.height')}: </span>
                          {bio?.height || t('common.noData')}
                        </div>
                        <div className="text-gray-300">
                          <span className="text-gray-500">{t('players.details.weight')}: </span>
                          {typeof bio?.weight === 'number' ? `${bio.weight} lb` : t('common.noData')}
                        </div>
                        <div className="text-gray-300">
                          <span className="text-gray-500">{t('players.details.birthDate')}: </span>
                          {bio?.birth_date || t('common.noData')}
                        </div>
                        <div className="text-gray-300">
                          <span className="text-gray-500">{t('players.details.experience')}: </span>
                          {typeof bio?.experience === 'number' ? bio.experience : t('common.noData')}
                        </div>
                        <div className="text-gray-300">
                          <span className="text-gray-500">{t('players.details.college')}: </span>
                          {bio?.college || t('common.noData')}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-4">
                      <button
                        onClick={() => {
                          addToComparison(detail);
                          setSelectedPlayer(null);
                        }}
                        className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded text-white"
                        disabled={comparisonPlayers.some(p => p.id === detail.id) || comparisonPlayers.length >= 4}
                      >
                        {t('players.actions.addToComparison')}
                      </button>
                      <button
                        onClick={() => setSelectedPlayer(null)}
                        className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-white"
                      >
                        {t('common.close')}
                      </button>
                    </div>
                  </div>
                </>
              );
            })()}
          </div>
        </div>
      )}
    </div>
  );
};

export default PlayersBrowser;

