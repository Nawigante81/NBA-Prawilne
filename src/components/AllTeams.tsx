import React, { useState, useEffect } from 'react';
import { 
  Users, 
  TrendingUp, 
  TrendingDown, 
  Filter,
  Search,
  BarChart3,
  Target,
  Activity as Globe,
  Activity as ArrowUpDown,
  Eye,
  Zap
} from 'lucide-react';
import { useApi } from '../services/api';
import { useI18n } from '../i18n/useI18n';
import ValuePanel from './ValuePanel';
import LineMovementMini from './LineMovementMini';
import KeyPlayersCard from './KeyPlayersCard';
import BettingStatsCard from './BettingStatsCard';
import NextGameBlock from './NextGameBlock';

interface Team {
  id: string;
  abbreviation: string;
  full_name: string;
  name: string;
  city: string;
  conference: string;
  division: string;
  season_stats?: {
    wins: number;
    losses: number;
    win_percentage: number;
    points_per_game: number;
    points_allowed: number;
    offensive_rating: number;
    defensive_rating: number;
    net_rating: number;
  } | null;
  recent_form?: {
    last_10: string;
    last_5: string;
    home_record: string;
    away_record: string;
    vs_conference: string;
  } | null;
  betting_stats?: {
    ats_record: string;
    ats_percentage: number;
    over_under: string;
    ou_percentage: number;
    avg_total: number;
  } | null;
  strength_rating?: number | null;
  key_players?: string[] | null;
}

interface AllTeamsProps {
  onTeamSelect?: (team: Team) => void;
  preselectTeamAbbrev?: string;
}

const asRecord = (value: unknown): Record<string, unknown> =>
  value && typeof value === 'object' ? (value as Record<string, unknown>) : {};

const asString = (value: unknown, fallback = ''): string =>
  typeof value === 'string' ? value : fallback;

const toTeam = (value: unknown): Team | null => {
  const record = asRecord(value);
  const id = asString(record.id);
  const abbreviation = asString(record.abbreviation);
  const fullName = asString(record.full_name, asString(record.name));
  const name = asString(record.name, fullName);
  const city = asString(record.city);
  const conference = asString(record.conference);
  const division = asString(record.division);

  if (!id || !abbreviation || !fullName || !name || !city || !conference || !division) {
    return null;
  }

  const rawKeyPlayers = Array.isArray(record.key_players) ? record.key_players : null;
  const keyPlayers = rawKeyPlayers ? rawKeyPlayers.map((p) => String(p)) : null;

  return {
    id,
    abbreviation,
    full_name: fullName,
    name,
    city,
    conference,
    division,
    season_stats: (record.season_stats as Team['season_stats']) ?? null,
    recent_form: (record.recent_form as Team['recent_form']) ?? null,
    betting_stats: (record.betting_stats as Team['betting_stats']) ?? null,
    strength_rating: typeof record.strength_rating === 'number' ? record.strength_rating : null,
    key_players: keyPlayers,
  };
};

const AllTeams: React.FC<AllTeamsProps> = ({ onTeamSelect, preselectTeamAbbrev }) => {
  const { t } = useI18n();
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedConference, setSelectedConference] = useState<string>('All');
  const [selectedDivision, setSelectedDivision] = useState<string>('All');
  const [sortBy, setSortBy] = useState<string>('win_percentage');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [showTopFive, setShowTopFive] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');
  const [selectedTeam, setSelectedTeam] = useState<Team | null>(null);
  
  const apiHook = useApi();

  const numOrNull = (value: unknown): number | null => {
    if (typeof value !== 'number') return null;
    return Number.isFinite(value) ? value : null;
  };

  const formatPercentOrNoData = (value: number | null, digits: number = 1) => {
    if (value === null) return t('common.noData');
    return `${(value * 100).toFixed(digits)}%`;
  };

  const formatNumberOrNoData = (value: number | null, digits: number = 1) => {
    if (value === null) return t('common.noData');
    return value.toFixed(digits);
  };

  useEffect(() => {
    const fetchTeams = async () => {
      try {
        setLoading(true);
        const response = await apiHook.getTeamsAnalysis();
        const parsed = (response.teams || [])
          .map(toTeam)
          .filter((team): team is Team => Boolean(team));
        setTeams(parsed);
      } catch (error) {
        console.error('Error fetching teams:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTeams();
  }, [apiHook]);

  // Preselect team when requested and teams are loaded
  useEffect(() => {
    if (!loading && preselectTeamAbbrev) {
      const t = teams.find(t => t.abbreviation.toUpperCase() === preselectTeamAbbrev.toUpperCase());
      if (t) {
        setSelectedTeam(t);
      }
    }
  }, [loading, preselectTeamAbbrev, teams]);

  // Filter and sort teams
  const filteredTeams = teams
    .filter(team => {
      const matchesSearch = team.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          team.abbreviation.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          team.city.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesConference = selectedConference === 'All' || team.conference === selectedConference;
      const matchesDivision = selectedDivision === 'All' || team.division === selectedDivision;

      return matchesSearch && matchesConference && matchesDivision;
    });

  const sortedTeams = [...filteredTeams].sort((a, b) => {
    let aValue: string | number | null = null;
    let bValue: string | number | null = null;

    switch (sortBy) {
      case 'win_percentage':
        aValue = numOrNull(a.season_stats?.win_percentage ?? null);
        bValue = numOrNull(b.season_stats?.win_percentage ?? null);
        break;
      case 'net_rating':
        aValue = numOrNull(a.season_stats?.net_rating ?? null);
        bValue = numOrNull(b.season_stats?.net_rating ?? null);
        break;
      case 'points_per_game':
        aValue = numOrNull(a.season_stats?.points_per_game ?? null);
        bValue = numOrNull(b.season_stats?.points_per_game ?? null);
        break;
      case 'strength_rating':
        aValue = numOrNull(a.strength_rating ?? null);
        bValue = numOrNull(b.strength_rating ?? null);
        break;
      case 'ats_percentage':
        aValue = numOrNull(a.betting_stats?.ats_percentage ?? null);
        bValue = numOrNull(b.betting_stats?.ats_percentage ?? null);
        break;
      default:
        aValue = a.full_name;
        bValue = b.full_name;
    }

    if (typeof aValue === 'string') {
      const aStr = aValue;
      const bStr = typeof bValue === 'string' ? bValue : '';
      return sortOrder === 'asc' ? aStr.localeCompare(bStr) : bStr.localeCompare(aStr);
    }

    const aNum = typeof aValue === 'number' ? aValue : -Infinity;
    const bNum = typeof bValue === 'number' ? bValue : -Infinity;
    return sortOrder === 'asc' ? aNum - bNum : bNum - aNum;
  });

  const displayedTeams = showTopFive ? sortedTeams.slice(0, 5) : sortedTeams;

  const conferences = ['All', 'Eastern', 'Western'];
  const divisions = ['All', 'Atlantic', 'Central', 'Southeast', 'Northwest', 'Pacific', 'Southwest'];

  const TeamCard = ({ team }: { team: Team }) => (
    <div 
      className="glass-card p-6 hover:neon-border transition-all duration-300 cursor-pointer group"
      onClick={() => { setSelectedTeam(team); onTeamSelect?.(team); }}
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white font-bold text-lg">
            {team.abbreviation}
          </div>
          <div>
            <h3 className="text-lg font-bold text-white group-hover:text-blue-400 transition-colors">
              {team.full_name}
            </h3>
            <p className="text-sm text-gray-400">{team.conference} • {team.division}</p>
          </div>
        </div>
        <Eye className="w-5 h-5 text-gray-400 group-hover:text-blue-400 transition-colors" />
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="text-center">
          <div className="text-2xl font-bold text-white">
            {team.season_stats ? `${team.season_stats.wins}-${team.season_stats.losses}` : t('common.noData')}
          </div>
          <div className="text-xs text-gray-400">{t('teams.table.record')}</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-white">
            {formatPercentOrNoData(numOrNull(team.season_stats?.win_percentage ?? null), 1)}
          </div>
          <div className="text-xs text-gray-400">{t('teams.table.winPct')}</div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 mb-4">
        <div className="text-center">
          <div className="text-lg font-semibold text-green-400">
            {formatNumberOrNoData(numOrNull(team.season_stats?.offensive_rating ?? null), 1)}
          </div>
          <div className="text-xs text-gray-400">{t('teams.table.offRtg')}</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-semibold text-red-400">
            {formatNumberOrNoData(numOrNull(team.season_stats?.defensive_rating ?? null), 1)}
          </div>
          <div className="text-xs text-gray-400">{t('teams.table.defRtg')}</div>
        </div>
      </div>

      <div className="flex items-center justify-between mb-3">
        <span className="text-sm text-gray-400">{t('teams.card.formLast10')}</span>
        <span className="text-sm font-medium text-white">{team.recent_form?.last_10 ?? t('common.noData')}</span>
      </div>

      <div className="flex items-center justify-between mb-3">
        <span className="text-sm text-gray-400">{t('teams.card.atsRecord')}</span>
        <span className="text-sm font-medium text-white">{team.betting_stats?.ats_record ?? t('common.noData')}</span>
      </div>

      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-400">{t('teams.card.strength')}</span>
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${
            typeof team.strength_rating === 'number'
              ? (team.strength_rating >= 85 ? 'bg-green-400' : team.strength_rating >= 75 ? 'bg-yellow-400' : 'bg-red-400')
              : 'bg-gray-500'
          }`}></div>
          <span className="text-sm font-medium text-white">
            {typeof team.strength_rating === 'number' ? team.strength_rating : t('common.noData')}
          </span>
        </div>
      </div>
    </div>
  );

  const TeamRow = ({ team }: { team: Team }) => {
    const netRating = numOrNull(team.season_stats?.net_rating ?? null);
    const formattedNetRating = netRating === null
      ? t('common.noData')
      : `${netRating > 0 ? '+' : ''}${netRating.toFixed(1)}`;

    return (
    <tr 
      className="border-b border-gray-700/50 hover:bg-white/5 cursor-pointer transition-colors"
      onClick={() => { setSelectedTeam(team); onTeamSelect?.(team); }}
    >
      <td className="px-6 py-4">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded flex items-center justify-center text-white font-bold text-sm">
            {team.abbreviation}
          </div>
          <div>
            <div className="font-semibold text-white">{team.full_name}</div>
            <div className="text-sm text-gray-400">{team.conference}</div>
          </div>
        </div>
      </td>
      <td className="px-6 py-4 text-white font-medium">
        {team.season_stats ? `${team.season_stats.wins}-${team.season_stats.losses}` : t('common.noData')}
      </td>
      <td className="px-6 py-4 text-white">
        {formatPercentOrNoData(numOrNull(team.season_stats?.win_percentage ?? null), 1)}
      </td>
      <td className="px-6 py-4 text-green-400">
        {formatNumberOrNoData(numOrNull(team.season_stats?.offensive_rating ?? null), 1)}
      </td>
      <td className="px-6 py-4 text-red-400">
        {formatNumberOrNoData(numOrNull(team.season_stats?.defensive_rating ?? null), 1)}
      </td>
      <td className="px-6 py-4">
        <div className={`flex items-center space-x-1 ${
          (netRating ?? 0) >= 0 ? 'text-green-400' : 'text-red-400'
        }`}>
          {typeof netRating === 'number'
            ? (netRating >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />)
            : null}
          <span>
            {formattedNetRating}
          </span>
        </div>
      </td>
      <td className="px-6 py-4 text-white">
        {team.recent_form?.last_10 ?? t('common.noData')}
      </td>
      <td className="px-6 py-4 text-white">
        {team.betting_stats?.ats_record ?? t('common.noData')}
      </td>
      <td className="px-6 py-4">
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${
            typeof team.strength_rating === 'number'
              ? (team.strength_rating >= 85 ? 'bg-green-400' : team.strength_rating >= 75 ? 'bg-yellow-400' : 'bg-red-400')
              : 'bg-gray-500'
          }`}></div>
          <span className="text-white">{typeof team.strength_rating === 'number' ? team.strength_rating : t('common.noData')}</span>
        </div>
      </td>
    </tr>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-400/30 border-t-blue-400 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-400">{t('teams.loading')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2" title={t('teams.tooltip.title')}>{t('teams.title')}</h1>
          <p className="text-gray-400">{t('teams.subtitle')}</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setViewMode(viewMode === 'grid' ? 'table' : 'grid')}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
          >
            <BarChart3 className="w-4 h-4" />
            <span>{viewMode === 'grid' ? t('teams.actions.tableView') : t('teams.actions.gridView')}</span>
          </button>
        </div>
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass-card p-4 text-center" title={t('teams.tooltip.totalTeams')}>
          <Users className="w-8 h-8 text-blue-400 mx-auto mb-2" />
          <div className="text-2xl font-bold text-white">{teams.length}</div>
          <div className="text-sm text-gray-400">{t('teams.stats.totalTeams')}</div>
        </div>
        <div className="glass-card p-4 text-center" title={t('teams.tooltip.filtered')}>
          <Globe className="w-8 h-8 text-green-400 mx-auto mb-2" />
          <div className="text-2xl font-bold text-white">
            {teams.filter(t => t.conference === 'Eastern').length}
          </div>
          <div className="text-sm text-gray-400">{t('teams.conference.eastern')}</div>
        </div>
        <div className="glass-card p-4 text-center">
          <Globe className="w-8 h-8 text-purple-400 mx-auto mb-2" />
          <div className="text-2xl font-bold text-white">
            {teams.filter(t => t.conference === 'Western').length}
          </div>
          <div className="text-sm text-gray-400">{t('teams.conference.western')}</div>
        </div>
        <div className="glass-card p-4 text-center">
          <Target className="w-8 h-8 text-yellow-400 mx-auto mb-2" />
          <div className="text-2xl font-bold text-white">
            {displayedTeams.length}
          </div>
          <div className="text-sm text-gray-400">{t('teams.stats.filtered')}</div>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="glass-card p-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          {/* Search */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder={t('teams.search.placeholder')}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-700/50 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-blue-400 focus:outline-none"
            />
          </div>

          {/* Filters */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center space-x-2">
              <Filter className="w-4 h-4 text-gray-400" />
              <select
                value={selectedConference}
                onChange={(e) => setSelectedConference(e.target.value)}
                aria-label={t('teams.filter.conferenceLabel')}
                title={t('teams.filter.conferenceLabel')}
                className="bg-gray-700/50 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:border-blue-400 focus:outline-none"
              >
                {conferences.map(conf => (
                  <option key={conf} value={conf}>
                    {conf === 'All' ? conf : `${conf} ${t('teams.filter.conferenceSuffix')}`}
                  </option>
                ))}
              </select>
            </div>

            <select
              value={selectedDivision}
              onChange={(e) => setSelectedDivision(e.target.value)}
              aria-label={t('teams.filter.divisionLabel')}
              title={t('teams.filter.divisionLabel')}
              className="bg-gray-700/50 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:border-blue-400 focus:outline-none"
            >
              {divisions.map(div => (
                <option key={div} value={div}>{div} {div !== 'All' ? t('teams.filter.divisionSuffix') : ''}</option>
              ))}
            </select>

            <div className="flex items-center space-x-2">
              <ArrowUpDown className="w-4 h-4 text-gray-400" />
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                aria-label={t('teams.sort.label')}
                title={t('teams.sort.label')}
                className="bg-gray-700/50 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:border-blue-400 focus:outline-none"
              >
                <option value="win_percentage">{t('teams.sort.winPct')}</option>
                <option value="net_rating">{t('teams.sort.netRating')}</option>
                <option value="points_per_game">{t('teams.sort.pointsPerGame')}</option>
                <option value="strength_rating">{t('teams.sort.strength')}</option>
                <option value="ats_percentage">{t('teams.sort.atsPct')}</option>
              </select>
              <button
                onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                className="p-2 bg-gray-700/50 hover:bg-gray-600/50 rounded-lg transition-colors"
              >
                {sortOrder === 'asc' ? <TrendingUp className="w-4 h-4 text-gray-400" /> : <TrendingDown className="w-4 h-4 text-gray-400" />}
              </button>
            </div>
            <button
              type="button"
              onClick={() => setShowTopFive((prev) => !prev)}
              className={`rounded-lg border px-3 py-2 text-sm transition-colors ${
                showTopFive
                  ? 'border-blue-500/60 bg-blue-500/10 text-blue-200'
                  : 'border-gray-600 bg-gray-700/40 text-gray-300 hover:bg-gray-600/40'
              }`}
              title={t('teams.filter.topFiveHelper')}
            >
              {t('teams.filter.topFive')}
            </button>
          </div>
        </div>
      </div>

      {/* Teams Display */}
      {viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {displayedTeams.map(team => (
            <TeamCard key={team.id} team={team} />
          ))}
        </div>
      ) : (
        <div className="glass-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-800/50">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-medium text-gray-300">{t('teams.table.team')}</th>
                  <th className="px-6 py-4 text-left text-sm font-medium text-gray-300">{t('teams.table.record')}</th>
                  <th className="px-6 py-4 text-left text-sm font-medium text-gray-300">{t('teams.table.winPct')}</th>
                  <th className="px-6 py-4 text-left text-sm font-medium text-gray-300">{t('teams.table.offRtg')}</th>
                  <th className="px-6 py-4 text-left text-sm font-medium text-gray-300">{t('teams.table.defRtg')}</th>
                  <th className="px-6 py-4 text-left text-sm font-medium text-gray-300">{t('teams.table.netRtg')}</th>
                  <th className="px-6 py-4 text-left text-sm font-medium text-gray-300">L10</th>
                  <th className="px-6 py-4 text-left text-sm font-medium text-gray-300">ATS</th>
                  <th className="px-6 py-4 text-left text-sm font-medium text-gray-300">{t('teams.table.strength')}</th>
                </tr>
              </thead>
              <tbody>
                {displayedTeams.map(team => (
                  <TeamRow key={team.id} team={team} />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {displayedTeams.length === 0 && (
        <div className="glass-card p-12 text-center">
          <Zap className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">{t('teams.empty.title')}</h3>
          <p className="text-gray-400">{t('teams.empty.subtitle')}</p>
        </div>
      )}

      {/* Team Details Panel */}
      {selectedTeam && (
        <div className="fixed inset-0 z-50 flex justify-end">
          <div className="absolute inset-0 bg-black/50" onClick={() => setSelectedTeam(null)}></div>
          <div className="relative w-full max-w-2xl h-full bg-gray-900 border-l border-gray-700/50 overflow-auto">
            <div className="p-6 border-b border-gray-700/50 flex items-center justify-between sticky top-0 bg-gray-900 z-10">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded flex items-center justify-center text-white font-bold">
                  {selectedTeam.abbreviation}
                </div>
                <div>
                  <div className="text-xl font-bold text-white">{selectedTeam.full_name}</div>
                  <div className="text-sm text-gray-400">{selectedTeam.conference} • {selectedTeam.division}</div>
                </div>
              </div>
              <button className="px-3 py-1 glass-card hover:bg-white/10 rounded text-sm" onClick={() => setSelectedTeam(null)}>{t('common.close')}</button>
            </div>
            <TeamDetailContent team={selectedTeam} />
          </div>
        </div>
      )}
    </div>
  );
};

// Separate component for team details to keep code organized
const TeamDetailContent: React.FC<{ team: Team }> = ({ team }) => {
  const { t } = useI18n();
  const [bettingStats, setBettingStats] = React.useState<any>(null);
  const [nextGame, setNextGame] = React.useState<any>(null);
  const [valuePanelData, setValuePanelData] = React.useState<any>(null);
  const [lineMovement, setLineMovement] = React.useState<any[]>([]);
  const [keyPlayers, setKeyPlayers] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);
  const apiHook = useApi();

  const numOrNull = (value: unknown): number | null => {
    if (typeof value !== 'number') return null;
    return Number.isFinite(value) ? value : null;
  };

  const formatPercentOrNoData = (value: number | null, digits: number = 1) => {
    if (value === null) return t('common.noData');
    return `${(value * 100).toFixed(digits)}%`;
  };

  const formatNumberOrNoData = (value: number | null, digits: number = 1) => {
    if (value === null) return t('common.noData');
    return value.toFixed(digits);
  };

  React.useEffect(() => {
    const fetchTeamData = async () => {
      setLoading(true);
      try {
        // Fetch all data in parallel
        const [bettingResponse, nextGameResponse, keyPlayersResponse] = await Promise.all([
          fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/team/${team.abbreviation}/betting-stats/detailed`)
            .then(r => r.ok ? r.json() : null),
          fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/team/${team.abbreviation}/next-game`)
            .then(r => r.ok ? r.json() : null),
          fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/team/${team.abbreviation}/key-players`)
            .then(r => r.ok ? r.json() : null),
        ]);

        setBettingStats(bettingResponse);
        setNextGame(nextGameResponse?.next_game);
        setKeyPlayers(keyPlayersResponse?.players || []);

        // If we have a next game, fetch value panel and line movement
        if (nextGameResponse?.next_game?.game_id) {
          const gameId = nextGameResponse.next_game.game_id;
          
          const [valueResponse, movementResponse] = await Promise.all([
            fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/team/${team.abbreviation}/value`)
              .then(r => r.ok ? r.json() : null),
            fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/game/${gameId}/odds/movement`)
              .then(r => r.ok ? r.json() : null),
          ]);

          setValuePanelData(valueResponse);
          setLineMovement(movementResponse?.movements || []);
        }
      } catch (error) {
        console.error('Error fetching team data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTeamData();
  }, [team.abbreviation]);

  const handleRefresh = () => {
    setLoading(true);
    // Trigger re-fetch
    setBettingStats(null);
    setNextGame(null);
    setValuePanelData(null);
    setLineMovement([]);
    setKeyPlayers([]);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Team KPI Cards */}
      <div className="grid grid-cols-2 gap-4">
        <div className="glass-card p-4 text-center">
          <div className="text-2xl font-bold text-white">
            {team.season_stats ? `${team.season_stats.wins}-${team.season_stats.losses}` : t('common.noData')}
          </div>
          <div className="text-sm text-gray-400">{t('teams.label.record')}</div>
        </div>
        <div className="glass-card p-4 text-center">
          <div className="text-2xl font-bold text-white">
            {formatPercentOrNoData(numOrNull(team.season_stats?.win_percentage ?? null), 1)}
          </div>
          <div className="text-sm text-gray-400">{t('teams.label.winPct')}</div>
        </div>
        <div className="glass-card p-4 text-center">
          <div className="text-xl font-semibold text-green-400">{formatNumberOrNoData(numOrNull(team.season_stats?.offensive_rating ?? null), 1)}</div>
          <div className="text-sm text-gray-400">{t('teams.label.offRtg')}</div>
        </div>
        <div className="glass-card p-4 text-center">
          <div className="text-xl font-semibold text-red-400">{formatNumberOrNoData(numOrNull(team.season_stats?.defensive_rating ?? null), 1)}</div>
          <div className="text-sm text-gray-400">{t('teams.label.defRtg')}</div>
        </div>
      </div>

      {/* Next Game Block - Import component when ready */}
      {nextGame && (
        <NextGameBlock 
          data={{
            game_id: nextGame.game_id,
            opponent: nextGame.opponent,
            opponent_abbrev: nextGame.opponent_abbrev,
            commence_time: nextGame.commence_time,
            is_home: nextGame.is_home,
            venue: nextGame.venue,
            status: nextGame.status,
          }}
          teamAbbrev={team.abbreviation}
          loading={loading}
        />
      )}

      {/* Betting Stats Card */}
      <BettingStatsCard
        data={bettingStats ? {
          ats_season: bettingStats.ats_season || {
            wins: 0, losses: 0, pushes: 0, percentage: 0, avg_margin: 0
          },
          ats_last_20: bettingStats.ats_last_20 || {
            wins: 0, losses: 0, pushes: 0, percentage: 0, avg_margin: 0
          },
          ou_season: bettingStats.ou_season || {
            overs: 0, unders: 0, pushes: 0, percentage: 0, avg_margin: 0
          },
          ou_last_20: bettingStats.ou_last_20 || {
            overs: 0, unders: 0, pushes: 0, percentage: 0, avg_margin: 0
          },
          avg_total_points: bettingStats.avg_total_points || {
            season: 0, last_20: 0
          }
        } : null}
        loading={loading}
        onRefresh={handleRefresh}
        teamName={team.full_name}
      />

      {/* Value Panel */}
      {valuePanelData && (
        <ValuePanel
          data={valuePanelData}
          loading={loading}
          onRefresh={handleRefresh}
        />
      )}

      {/* Line Movement */}
      {lineMovement.length > 0 && (
        <LineMovementMini
          data={lineMovement}
          loading={loading}
        />
      )}

      {/* Key Players */}
      <KeyPlayersCard
        players={keyPlayers}
        loading={loading}
      />

      <div className="text-right">
        <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-white" onClick={() => {}}>
          {t('common.done')}
        </button>
      </div>
    </div>
  );
};

export default AllTeams;
