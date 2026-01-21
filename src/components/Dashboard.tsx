import React, { useState, useEffect, useCallback } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Target, 
  DollarSign, 
  Clock,
  Users,
  Activity,
  AlertTriangle,
  Trophy,
  Zap,
  BarChart3
} from 'lucide-react';
import { useApi } from '../services/api';
import { api } from '../services/api';
import AllTeams from './AllTeams';
import { useI18n } from '../i18n/useI18n';

type DashboardProps = {
  onViewOdds?: (gameId: string) => void;
};

interface ApiGame {
  id?: string;
  home_team?: string;
  away_team?: string;
  commence_time?: string;
}

interface ApiTeam {
  id: string;
  name?: string;
  abbreviation: string;
  full_name?: string;
  city?: string;
}

interface OddsRow {
  market_type?: string;
  team?: string;
  price?: number | string | null;
  point?: number | string | null;
  outcome_name?: string;
}

interface GameData {
  id: string;
  homeTeam: string;
  awayTeam: string;
  time: string;
  commenceTime: string | null;
  spread: number | null;
  total: number | null;
  homeOdds: number | null;
  awayOdds: number | null;
}

interface FocusTeamCandidate {
  team: string;
  opponent: string;
  game_id: string;
  commence_time?: string;
  best_price: number;
  best_book: string;
  consensus_prob: number;
  edge: number;
}

interface TeamSeasonStats {
  win_percentage?: number;
  offensive_rating?: number;
  defensive_rating?: number;
  net_rating?: number;
  wins?: number;
  losses?: number;
}

interface TeamRecentForm {
  last_5?: string;
}

interface TeamAnalysisEntry {
  id?: string;
  name?: string;
  full_name?: string;
  abbreviation?: string;
  season_stats?: TeamSeasonStats;
  recent_form?: TeamRecentForm;
  key_players?: string[];
}

interface FocusTeamRow {
  team?: string;
  opponent?: string;
  game_id?: string;
  commence_time?: string;
  best_price?: number | null;
  best_book?: string | null;
  consensus_prob?: number | null;
  edge?: number | null;
}

const asRecord = (value: unknown): Record<string, unknown> =>
  value && typeof value === 'object' ? (value as Record<string, unknown>) : {};

const asString = (value: unknown, fallback = ''): string =>
  typeof value === 'string' ? value : fallback;

const toApiTeam = (value: unknown): ApiTeam | null => {
  const record = asRecord(value);
  const id = asString(record.id);
  const abbreviation = asString(record.abbreviation);
  if (!id || !abbreviation) return null;
  return {
    id,
    abbreviation,
    name: asString(record.name),
    full_name: asString(record.full_name),
    city: asString(record.city),
  };
};

const Dashboard: React.FC<DashboardProps> = ({ onViewOdds }) => {
  const { t, locale } = useI18n();
  const [todayGames, setTodayGames] = useState<GameData[]>([]);
  const [focusTeams, setFocusTeams] = useState<FocusTeamCandidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeSection, setActiveSection] = useState<'dashboard' | 'all-teams' | 'scheduled' | 'tracked' | 'season' | 'value'>('dashboard');
  const [teamsRaw, setTeamsRaw] = useState<ApiTeam[]>([]);
  const [teamsAnalysis, setTeamsAnalysis] = useState<TeamAnalysisEntry[]>([]);
  const [preselectTeamAbbrev, setPreselectTeamAbbrev] = useState<string | undefined>(undefined);
  const [filterTeam, setFilterTeam] = useState<string>('All');
  const [searchTerm, setSearchTerm] = useState('');
  const [sortKey, setSortKey] = useState<string>('time');
  const [sortOrder] = useState<'asc' | 'desc'>('desc');

  const apiHook = useApi();

  const chicagoTodayLabel = (() => {
    try {
      return new Intl.DateTimeFormat('en-US', {
        timeZone: 'America/Chicago',
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      }).format(new Date());
    } catch {
      return new Date().toISOString().slice(0, 10);
    }
  })();

  const decimalToAmerican = (decimal: number): number | null => {
    if (!Number.isFinite(decimal) || decimal <= 1) return null;
    if (decimal >= 2) return Math.round((decimal - 1) * 100);
    return -Math.round(100 / (decimal - 1));
  };

  const formatAmericanOrNoData = (american: number | null) => {
    if (american === null || !Number.isFinite(american)) return t('common.noData');
    return american > 0 ? `+${american}` : `${american}`;
  };

  const formatLineOrNoData = (value: number | null, emptyLabel?: string) => {
    if (value === null || !Number.isFinite(value)) return emptyLabel || t('common.noData');
    return value > 0 ? `+${value}` : `${value}`;
  };

  const formatPercentOrNoData = (value: number | null, digits = 1) => {
    if (value === null || !Number.isFinite(value)) return t('common.noData');
    return `${(value * 100).toFixed(digits)}%`;
  };

  const formatNumberOrNoData = (
    value: number | null,
    digits: number = 1,
    withSign: boolean = false,
    emptyLabel?: string
  ) => {
    if (value === null || !Number.isFinite(value)) return emptyLabel ?? t('common.noData');
    const fixed = value.toFixed(digits);
    return withSign ? `${value > 0 ? '+' : ''}${fixed}` : fixed;
  };

  const normalize = (value: string) => value.trim().toLowerCase();
  const methodologyLink = '/docs/METHODOLOGY.md';

  const findTeamAnalysis = (teamName: string) => {
    const needle = normalize(teamName || '');
    if (!needle) return null;
    return teamsAnalysis.find((t) =>
      normalize(t?.full_name || '') === needle ||
      normalize(t?.name || '') === needle ||
      normalize(t?.abbreviation || '') === needle
    ) || teamsAnalysis.find((t) =>
      normalize(t?.full_name || '').includes(needle) ||
      normalize(t?.name || '').includes(needle)
    ) || null;
  };

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [gamesData, teamsData, focusTeamsData, teamsAnalysisData] = await Promise.all([
        apiHook.getTodayGames(),
        apiHook.getTeams(),
        apiHook.getFocusTeamsToday(5),
        apiHook.getTeamsAnalysis(),
      ]);

      setTeamsRaw(
        (teamsData || [])
          .map(toApiTeam)
          .filter((team): team is ApiTeam => Boolean(team))
      );
      setTeamsAnalysis((teamsAnalysisData?.teams as TeamAnalysisEntry[]) || []);

      const gamesWithIds = (gamesData || []).filter(
        (g: ApiGame) => typeof g?.id === 'string' && String(g.id).trim() !== ''
      );

      const enrichedGames: GameData[] = await Promise.all(
        gamesWithIds.map(async (game: ApiGame) => {
          const gameId = String(game.id);
          const homeTeam = String(game.home_team || t('common.tbd'));
          const awayTeam = String(game.away_team || t('common.tbd'));
          const time = game.commence_time
            ? new Date(game.commence_time).toLocaleTimeString(locale, { timeZone: 'America/Chicago' })
            : t('common.tbd');

          let spread: number | null = null;
          let total: number | null = null;
          let homeOdds: number | null = null;
          let awayOdds: number | null = null;

          try {
            const oddsResp = await api.games.getOdds(gameId);
            const rows = oddsResp?.odds || [];

            const findTeamRow = (arr: OddsRow[], team: string) =>
              arr.find((r) => String(r.team || '').trim().toLowerCase() === team.trim().toLowerCase());

            const h2h = rows.filter((r: OddsRow) => r.market_type === 'h2h');
            const spreads = rows.filter(
              (r: OddsRow) => r.market_type === 'spread' || r.market_type === 'spreads'
            );
            const totals = rows.filter((r: OddsRow) => r.market_type === 'totals');

            const homeMlRows = h2h.filter(
              (r: OddsRow) =>
                String(r.team || '').trim().toLowerCase() === homeTeam.trim().toLowerCase() &&
                Number.isFinite(Number(r.price))
            );
            const awayMlRows = h2h.filter(
              (r: OddsRow) =>
                String(r.team || '').trim().toLowerCase() === awayTeam.trim().toLowerCase() &&
                Number.isFinite(Number(r.price))
            );

            const bestHomeDec = homeMlRows.reduce<number | null>((best, r) => {
              const price = Number(r.price);
              if (!Number.isFinite(price)) return best;
              return best === null || price > best ? price : best;
            }, null);
            const bestAwayDec = awayMlRows.reduce<number | null>((best, r) => {
              const price = Number(r.price);
              if (!Number.isFinite(price)) return best;
              return best === null || price > best ? price : best;
            }, null);

            homeOdds = bestHomeDec === null ? null : decimalToAmerican(bestHomeDec);
            awayOdds = bestAwayDec === null ? null : decimalToAmerican(bestAwayDec);

            const homeSpread = findTeamRow(spreads, homeTeam);
            spread = homeSpread?.point === null || homeSpread?.point === undefined ? null : Number(homeSpread.point);

            const overRow = totals.find((r: OddsRow) => String(r.outcome_name || '').toLowerCase() === 'over');
            total = overRow?.point === null || overRow?.point === undefined ? null : Number(overRow.point);
          } catch {
            // odds missing -> keep nulls
          }

          return {
            id: gameId,
            homeTeam,
            awayTeam,
            time,
            commenceTime: game.commence_time || null,
            spread,
            total,
            homeOdds,
            awayOdds,
          };
        })
      );

      setTodayGames(enrichedGames);

      const normalizedFocusTeams = (focusTeamsData as FocusTeamRow[] | undefined || [])
        .filter((x) => x && typeof x.team === 'string' && typeof x.opponent === 'string')
        .map((x) => {
          const bestPrice = x.best_price === null || x.best_price === undefined ? null : Number(x.best_price);
          const edge = x.edge === null || x.edge === undefined ? null : Number(x.edge);
          const consensusProb = x.consensus_prob === null || x.consensus_prob === undefined ? null : Number(x.consensus_prob);

          return {
            team: x.team,
            opponent: x.opponent,
            game_id: String(x.game_id || ''),
            commence_time: x.commence_time,
            best_price: bestPrice,
            best_book: x.best_book ? String(x.best_book) : '',
            consensus_prob: consensusProb,
            edge,
          };
        })
        .filter(
          (x) =>
            x.game_id &&
            Number.isFinite(x.best_price) &&
            Number.isFinite(x.edge) &&
            Number.isFinite(x.consensus_prob)
        )
        .map((x) => ({
          ...x,
          best_price: Number(x.best_price),
          edge: Number(x.edge),
          consensus_prob: Number(x.consensus_prob),
        }));

      setFocusTeams(normalizedFocusTeams as FocusTeamCandidate[]);
    } catch (e) {
      console.error('Error fetching dashboard data:', e);
      setTodayGames([]);
      setTeamsRaw([]);
      setTeamsAnalysis([]);
      setFocusTeams([]);
      setError(t('dashboard.error.loadFailed'));
    } finally {
      setLoading(false);
    }
  }, [apiHook, locale, t]);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  const StatCard = ({ value, subtitle, icon: Icon, trend, color, onClick, tooltip }: {
    value: string | number;
    subtitle: string;
    icon: React.ElementType;
    trend?: 'up' | 'down' | 'neutral';
    color: string;
    onClick?: () => void;
    tooltip?: string;
  }) => (
    <button
      type="button"
      onClick={onClick}
      title={tooltip}
      className="glass-card p-6 hover:bg-white/10 transition-all duration-300 text-left"
    >
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        {trend && (
          <div className={`flex items-center space-x-1 ${
            trend === 'up' ? 'text-green-400' : trend === 'down' ? 'text-red-400' : 'text-yellow-400'
          }`}>
            {trend === 'up' ? <TrendingUp className="w-4 h-4" /> : 
             trend === 'down' ? <TrendingDown className="w-4 h-4" /> : 
             <Activity className="w-4 h-4" />}
          </div>
        )}
      </div>
      <div className="text-2xl font-bold text-white mb-1">{value}</div>
      <div className="text-sm text-gray-400">{subtitle}</div>
    </button>
  );

  const MetricBadge = ({ label, tooltip, tone }: { label: string; tooltip: string; tone: string }) => (
    <span
      title={tooltip}
      className={`rounded-full border px-2 py-0.5 text-[10px] uppercase tracking-widest ${tone}`}
    >
      {label}
    </span>
  );

  const downloadCsv = (filename: string, headers: string[], rows: Array<Array<string | number>>) => {
    const safeRows = rows.map(r => r.map(v => `"${String(v ?? '').replace(/"/g, '""')}"`));
    const csv = [headers.map(h => `"${h.replace(/"/g, '""')}"`).join(','), ...safeRows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const downloadPdf = async (title: string, headers: string[], rows: Array<Array<string | number>>, filename: string) => {
    const { jsPDF } = await import('jspdf');
    const doc = new jsPDF({ unit: 'pt', format: 'a4' });
    const marginX = 40;
    const marginY = 48;
    const pageWidth = doc.internal.pageSize.getWidth();
    const usableWidth = pageWidth - marginX * 2;
    let y = marginY;
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(16);
    doc.text(title, marginX, y);
    y += 20;
    doc.setFontSize(10);
    doc.setFont('helvetica', 'bold');
    doc.text(headers.join(' | '), marginX, y);
    y += 14;
    doc.setFont('helvetica', 'normal');
    rows.forEach((row) => {
      const line = row.map(v => String(v ?? '')).join(' | ');
      const lines = doc.splitTextToSize(line, usableWidth);
      lines.forEach((l: string) => {
        if (y > doc.internal.pageSize.getHeight() - marginY) {
          doc.addPage();
          y = marginY;
        }
        doc.text(l, marginX, y);
        y += 12;
      });
    });
    doc.save(filename);
  };

  const openTeamAnalysis = (teamName: string) => {
    // Try to match by full_name or name contains
    const match = teamsRaw.find(t => 
      (t.full_name && t.full_name.toLowerCase() === teamName.toLowerCase()) ||
      (t.name && t.name.toLowerCase() === teamName.toLowerCase())
    ) || teamsRaw.find(t => (t.full_name || '').toLowerCase().includes(teamName.toLowerCase()) || (t.name || '').toLowerCase().includes(teamName.toLowerCase()));
    if (match) {
      setPreselectTeamAbbrev(match.abbreviation);
      setActiveSection('all-teams');
    } else {
      setActiveSection('all-teams');
    }
  };

  const GameCard = ({ game }: { game: GameData }) => (
    <div className="glass-card p-4 hover:neon-border transition-all duration-300">
      <div className="flex items-center justify-between mb-3">
        <div className="text-sm text-gray-400">{game.time}</div>
      </div>
      
      <div className="space-y-2 mb-4">
        <div className="flex items-center justify-between">
          <button onClick={() => openTeamAnalysis(game.homeTeam)} className="font-semibold text-left text-white hover:underline">
            {game.homeTeam}
          </button>
          <span className="text-gray-300">{formatAmericanOrNoData(game.homeOdds)}</span>
        </div>
        <div className="flex items-center justify-between">
          <button onClick={() => openTeamAnalysis(game.awayTeam)} className="text-gray-300 hover:underline text-left">
            {game.awayTeam}
          </button>
          <span className="text-gray-300">{formatAmericanOrNoData(game.awayOdds)}</span>
        </div>
      </div>

      <div className="flex justify-between items-center text-sm border-t border-gray-700/50 pt-3">
        {typeof game.spread === 'number' && Number.isFinite(game.spread) && (
          <div className="text-center">
            <div className="text-gray-400">{t('dashboard.label.spread')}</div>
            <div className="text-white font-semibold">
              {formatLineOrNoData(game.spread)}
            </div>
          </div>
        )}
        <div className="text-center">
          <div className="text-gray-400">{t('dashboard.label.total')}</div>
          <div className="text-white font-semibold">
            {game.total === null || !Number.isFinite(game.total) ? t('common.noData') : game.total}
          </div>
        </div>
        <div className="flex items-center space-x-2">
        {onViewOdds && (
          <button
            onClick={() => onViewOdds(game.id)}
            className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-white ml-2"
          >
            {t('dashboard.actions.viewOdds')}
          </button>
        )}
        <button
          onClick={() => openTeamAnalysis(game.homeTeam)}
          className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-white"
        >
          {t('dashboard.actions.teamAnalysis')}
        </button>
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-400/30 border-t-blue-400 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-400">{t('dashboard.loading')}</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-card p-8 text-center">
        <div className="text-red-400 font-semibold mb-2">{error}</div>
        <button
          onClick={() => {
            loadDashboard();
          }}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-white"
        >
          {t('common.retry')}
        </button>
      </div>
    );
  }

  const scheduledFiltered = todayGames.filter(
    g => filterTeam === 'All' || g.homeTeam === filterTeam || g.awayTeam === filterTeam
  );
  const seasonTeamsCount = teamsAnalysis.filter(t => t?.season_stats?.win_percentage !== null && t?.season_stats?.win_percentage !== undefined).length;
  const scheduledSearched = scheduledFiltered.filter(g => {
    const hay = `${g.homeTeam} ${g.awayTeam}`.toLowerCase();
    return hay.includes(searchTerm.toLowerCase());
  });
  const trackedSearched = focusTeams.filter(t => {
    const hay = `${t.team} ${t.opponent}`.toLowerCase();
    return hay.includes(searchTerm.toLowerCase());
  });
  const seasonSearched = teamsAnalysis.filter(t => {
    const hay = `${t.full_name || t.name || ''}`.toLowerCase();
    return hay.includes(searchTerm.toLowerCase());
  });
  const valueSearched = focusTeams.filter(t => t.edge > 0).filter(t => {
    const hay = `${t.team} ${t.opponent}`.toLowerCase();
    return hay.includes(searchTerm.toLowerCase());
  });

  const spotlightGame = todayGames[0] || null;
  const spotlightHome = spotlightGame ? findTeamAnalysis(spotlightGame.homeTeam) : null;
  const spotlightAway = spotlightGame ? findTeamAnalysis(spotlightGame.awayTeam) : null;

  const formatLast5 = (team: TeamAnalysisEntry | null) => team?.recent_form?.last_5 ?? t('common.noData');
  const formatKeyPlayers = (team: TeamAnalysisEntry | null) => {
    const players = Array.isArray(team?.key_players) ? team.key_players : [];
    return players.length ? players.slice(0, 3).join(', ') : t('common.noData');
  };
  const teamLabel = (team: TeamAnalysisEntry | null, fallback: string) => team?.abbreviation || fallback;

  const sortList = <T,>(list: T[], getter: (item: T) => number | string | null) => {
    const sorted = [...list].sort((a, b) => {
      const av = getter(a);
      const bv = getter(b);
      if (typeof av === 'string' && typeof bv === 'string') {
        return sortOrder === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av);
      }
      const an = typeof av === 'number' ? av : -Infinity;
      const bn = typeof bv === 'number' ? bv : -Infinity;
      return sortOrder === 'asc' ? an - bn : bn - an;
    });
    return sorted;
  };

  return (
    <div className="space-y-6">
      {/* Navigation Tabs */}
      <div className="flex space-x-1 bg-gray-800/50 rounded-lg p-1">
        <button
          onClick={() => setActiveSection('dashboard')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            activeSection === 'dashboard'
              ? 'bg-blue-600 text-white'
              : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
          }`}
        >
          {t('dashboard.tabs.dashboard')}
        </button>
        <button
          onClick={() => setActiveSection('all-teams')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            activeSection === 'all-teams'
              ? 'bg-blue-600 text-white'
              : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
          }`}
        >
          {t('dashboard.tabs.allTeams')}
        </button>
      </div>

      {/* Content based on active section */}
      {activeSection === 'all-teams' ? (
        <AllTeams preselectTeamAbbrev={preselectTeamAbbrev} />
      ) : activeSection === 'scheduled' ? (
        <div className="glass-card">
          <div className="p-6 border-b border-gray-700/50 flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-white" title={t('dashboard.tooltip.scheduledGames')}>{t('dashboard.section.scheduledGames')}</h2>
              <p className="text-sm text-gray-400">{t('dashboard.section.scheduledSubtitle')}</p>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setActiveSection('dashboard')}
                className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-white text-sm"
              >
                {t('common.back')}
              </button>
              <div className="text-sm text-gray-400">
                {t('dashboard.filter.date')}: {chicagoTodayLabel}
              </div>
              <input
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder={t('dashboard.filter.search')}
                className="bg-gray-700/50 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:border-blue-400 focus:outline-none"
              />
              <span className="text-sm text-gray-400">{t('dashboard.filter.team')}</span>
              <select
                value={filterTeam}
                onChange={(e) => setFilterTeam(e.target.value)}
                className="bg-gray-700/50 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:border-blue-400 focus:outline-none"
              >
                <option value="All">{t('players.filter.allTeams')}</option>
                {teamsRaw.map(team => (
                  <option key={team.abbreviation} value={team.full_name || team.name || team.abbreviation}>
                    {team.full_name || team.name || team.abbreviation}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="p-6 space-y-4">
            {sortList(scheduledSearched, (g) => g.commenceTime || '').map(game => (
              <GameCard key={game.id} game={game} />
            ))}
            {scheduledSearched.length === 0 && (
              <div className="text-sm text-gray-400">{t('common.noData')}</div>
            )}
            {scheduledSearched.length > 0 && (
              <div className="flex items-center space-x-3 pt-2">
                <button
                  onClick={() => downloadCsv('scheduled-games.csv', ['Time', 'Home', 'Away', 'Spread', 'Total'], scheduledSearched.map(g => [g.time, g.homeTeam, g.awayTeam, g.spread ?? '', g.total ?? '']))}
                  className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-white text-sm"
                >
                  {t('dashboard.actions.exportCsv')}
                </button>
                <button
                  onClick={() => downloadPdf(t('dashboard.section.scheduledGames'), ['Time', 'Home', 'Away', 'Spread', 'Total'], scheduledSearched.map(g => [g.time, g.homeTeam, g.awayTeam, g.spread ?? '', g.total ?? '']), 'scheduled-games.pdf')}
                  className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-white text-sm"
                >
                  {t('dashboard.actions.exportPdf')}
                </button>
              </div>
            )}
          </div>
        </div>
      ) : activeSection === 'tracked' ? (
        <div className="glass-card">
          <div className="p-6 border-b border-gray-700/50 flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-white" title={t('dashboard.tooltip.trackedTeams')}>{t('dashboard.section.trackedTeams')}</h2>
              <p className="text-sm text-gray-400">{t('dashboard.section.trackedSubtitle')}</p>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setActiveSection('dashboard')}
                className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-white text-sm"
              >
                {t('common.back')}
              </button>
              <input
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder={t('dashboard.filter.search')}
                className="bg-gray-700/50 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:border-blue-400 focus:outline-none"
              />
              <select
                value={sortKey}
                onChange={(e) => setSortKey(e.target.value)}
                className="bg-gray-700/50 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:border-blue-400 focus:outline-none"
              >
                <option value="edge">{t('dashboard.sort.edge')}</option>
                <option value="team">{t('dashboard.sort.team')}</option>
              </select>
            </div>
          </div>
          <div className="p-6 space-y-4">
            {trackedSearched.length === 0 && (
              <div className="text-sm text-gray-400">{t('common.noData')}</div>
            )}
            {sortList(trackedSearched, (t) => (sortKey === 'team' ? t.team : t.edge)).map(team => (
              <div key={`${team.game_id}:${team.team}`} className="flex items-center justify-between p-4 bg-gray-800/30 rounded-lg">
                <div>
                  <div className="text-white font-semibold">{team.team}</div>
                  <div className="text-xs text-gray-400">{t('betting.pick.vs')} {team.opponent}</div>
                </div>
                <div className="text-sm text-gray-300">{((team.edge || 0) * 100).toFixed(1)}% {t('dashboard.label.edge')}</div>
              </div>
            ))}
            {trackedSearched.length > 0 && (
              <div className="flex items-center space-x-3 pt-2">
                <button
                  onClick={() => downloadCsv('tracked-teams.csv', ['Team', 'Opponent', 'Edge'], trackedSearched.map(t => [t.team, t.opponent, ((t.edge || 0) * 100).toFixed(1) + '%']))}
                  className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-white text-sm"
                >
                  {t('dashboard.actions.exportCsv')}
                </button>
                <button
                  onClick={() => downloadPdf(t('dashboard.section.trackedTeams'), ['Team', 'Opponent', 'Edge'], trackedSearched.map(t => [t.team, t.opponent, ((t.edge || 0) * 100).toFixed(1) + '%']), 'tracked-teams.pdf')}
                  className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-white text-sm"
                >
                  {t('dashboard.actions.exportPdf')}
                </button>
              </div>
            )}
          </div>
        </div>
      ) : activeSection === 'season' ? (
        <div className="glass-card">
          <div className="p-6 border-b border-gray-700/50 flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-white" title={t('dashboard.tooltip.seasonOverview')}>{t('dashboard.section.seasonOverview')}</h2>
              <p className="text-sm text-gray-400">{t('dashboard.section.seasonSubtitle')}</p>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setActiveSection('dashboard')}
                className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-white text-sm"
              >
                {t('common.back')}
              </button>
              <input
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder={t('dashboard.filter.search')}
                className="bg-gray-700/50 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:border-blue-400 focus:outline-none"
              />
              <select
                value={sortKey}
                onChange={(e) => setSortKey(e.target.value)}
                className="bg-gray-700/50 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:border-blue-400 focus:outline-none"
              >
                <option value="winPct">{t('dashboard.sort.winPct')}</option>
                <option value="net">{t('dashboard.sort.netRtg')}</option>
                <option value="off">{t('dashboard.sort.offRtg')}</option>
                <option value="def">{t('dashboard.sort.defRtg')}</option>
              </select>
            </div>
          </div>
          <div className="p-6 space-y-4">
            {seasonSearched.length === 0 && (
              <div className="text-sm text-gray-400">{t('common.noData')}</div>
            )}
            {sortList(
              seasonSearched.filter(t => t?.season_stats?.win_percentage !== null && t?.season_stats?.win_percentage !== undefined),
              (t) => {
                const stats = t.season_stats || {};
                if (sortKey === 'net') return stats.net_rating || 0;
                if (sortKey === 'off') return stats.offensive_rating || 0;
                if (sortKey === 'def') return stats.defensive_rating || 0;
                return stats.win_percentage || 0;
              }
            ).slice(0, 12).map((team: TeamAnalysisEntry) => (
                <div key={team.id} className="flex items-center justify-between p-4 bg-gray-800/30 rounded-lg">
                  <div>
                    <div className="text-white font-semibold">{team.full_name || team.name}</div>
                    <div className="text-xs text-gray-400">
                      {team.season_stats?.wins}-{team.season_stats?.losses} · Net {formatNumberOrNoData(typeof team.season_stats?.net_rating === 'number' ? team.season_stats.net_rating : null, 1, true)}
                    </div>
                  </div>
                  <div className="text-sm text-gray-300">
                    {((team.season_stats?.win_percentage || 0) * 100).toFixed(1)}% · Off {formatNumberOrNoData(typeof team.season_stats?.offensive_rating === 'number' ? team.season_stats.offensive_rating : null, 1)} · Def {formatNumberOrNoData(typeof team.season_stats?.defensive_rating === 'number' ? team.season_stats.defensive_rating : null, 1)}
                  </div>
                </div>
              ))}
            {seasonSearched.length > 0 && (
              <div className="flex items-center space-x-3 pt-2">
                <button
                  onClick={() => downloadCsv(
                    'season-overview.csv',
                    ['Team', 'W-L', 'Win%', 'OffRtg', 'DefRtg', 'NetRtg'],
                    seasonSearched.map(t => [
                      String(t.full_name || t.name || ''),
                      `${t.season_stats?.wins}-${t.season_stats?.losses}`,
                      ((t.season_stats?.win_percentage || 0) * 100).toFixed(1),
                      formatNumberOrNoData(typeof t.season_stats?.offensive_rating === 'number' ? t.season_stats.offensive_rating : null, 1, false, ''),
                      formatNumberOrNoData(typeof t.season_stats?.defensive_rating === 'number' ? t.season_stats.defensive_rating : null, 1, false, ''),
                      formatNumberOrNoData(typeof t.season_stats?.net_rating === 'number' ? t.season_stats.net_rating : null, 1, true, '')
                    ])
                  )}
                  className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-white text-sm"
                >
                  {t('dashboard.actions.exportCsv')}
                </button>
                <button
                  onClick={() => downloadPdf(
                    t('dashboard.section.seasonOverview'),
                    ['Team', 'W-L', 'Win%', 'OffRtg', 'DefRtg', 'NetRtg'],
                    seasonSearched.map(t => [
                      String(t.full_name || t.name || ''),
                      `${t.season_stats?.wins}-${t.season_stats?.losses}`,
                      ((t.season_stats?.win_percentage || 0) * 100).toFixed(1),
                      formatNumberOrNoData(typeof t.season_stats?.offensive_rating === 'number' ? t.season_stats.offensive_rating : null, 1, false, ''),
                      formatNumberOrNoData(typeof t.season_stats?.defensive_rating === 'number' ? t.season_stats.defensive_rating : null, 1, false, ''),
                      formatNumberOrNoData(typeof t.season_stats?.net_rating === 'number' ? t.season_stats.net_rating : null, 1, true, '')
                    ]),
                    'season-overview.pdf'
                  )}
                  className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-white text-sm"
                >
                  {t('dashboard.actions.exportPdf')}
                </button>
              </div>
            )}
          </div>
        </div>
      ) : activeSection === 'value' ? (
        <div className="glass-card">
          <div className="p-6 border-b border-gray-700/50 flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-white" title={t('dashboard.tooltip.valuePicks')}>{t('dashboard.section.valuePicks')}</h2>
              <p className="text-sm text-gray-400">{t('dashboard.section.valueSubtitle')}</p>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setActiveSection('dashboard')}
                className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-white text-sm"
              >
                {t('common.back')}
              </button>
              <input
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder={t('dashboard.filter.search')}
                className="bg-gray-700/50 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:border-blue-400 focus:outline-none"
              />
              <select
                value={sortKey}
                onChange={(e) => setSortKey(e.target.value)}
                className="bg-gray-700/50 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:border-blue-400 focus:outline-none"
              >
                <option value="edge">{t('dashboard.sort.edge')}</option>
                <option value="team">{t('dashboard.sort.team')}</option>
              </select>
            </div>
          </div>
          <div className="p-6 space-y-4">
              {sortList(valueSearched, (t) => (sortKey === 'team' ? t.team : t.edge)).map(team => (
                <div key={`${team.game_id}:${team.team}`} className="flex items-center justify-between p-4 bg-gray-800/30 rounded-lg">
                  <div>
                    <div className="text-white font-semibold">{team.team}</div>
                    <div className="text-xs text-gray-400">{t('betting.pick.vs')} {team.opponent}</div>
                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      <MetricBadge
                        label={t('badges.value')}
                        tooltip={t('badges.valueTooltip')}
                        tone={team.edge && team.edge > 0
                          ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-200'
                          : 'border-gray-600/40 bg-gray-700/40 text-gray-300'
                        }
                      />
                      <MetricBadge
                        label={`${t('badges.edge')} ${formatPercentOrNoData(team.edge ?? null)}`}
                        tooltip={t('badges.edgeTooltip')}
                        tone="border-blue-500/40 bg-blue-500/10 text-blue-200"
                      />
                      <MetricBadge
                        label={`${t('badges.confidence')} ${formatPercentOrNoData(team.consensus_prob ?? null)}`}
                        tooltip={t('badges.confidenceTooltip')}
                        tone="border-purple-500/40 bg-purple-500/10 text-purple-200"
                      />
                      <a
                        href={methodologyLink}
                        target="_blank"
                        rel="noreferrer"
                        className="text-[10px] uppercase tracking-widest text-blue-300 hover:text-blue-200"
                        title={t('badges.methodologyTooltip')}
                      >
                        {t('badges.methodologyLink')}
                      </a>
                    </div>
                  </div>
                  <div className="text-sm text-green-400">+{((team.edge || 0) * 100).toFixed(1)}%</div>
                </div>
              ))}
            {valueSearched.length === 0 && (
              <div className="text-sm text-gray-400">{t('common.noData')}</div>
            )}
            {valueSearched.length > 0 && (
              <div className="flex items-center space-x-3 pt-2">
                <button
                  onClick={() => downloadCsv('value-opportunities.csv', ['Team', 'Opponent', 'Edge'], valueSearched.map(t => [t.team, t.opponent, ((t.edge || 0) * 100).toFixed(1) + '%']))}
                  className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-white text-sm"
                >
                  {t('dashboard.actions.exportCsv')}
                </button>
                <button
                  onClick={() => downloadPdf(t('dashboard.section.valuePicks'), ['Team', 'Opponent', 'Edge'], valueSearched.map(t => [t.team, t.opponent, ((t.edge || 0) * 100).toFixed(1) + '%']), 'value-opportunities.pdf')}
                  className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-white text-sm"
                >
                  {t('dashboard.actions.exportPdf')}
                </button>
              </div>
            )}
          </div>
        </div>
      ) : (
        <>
          {/* Stats Overview */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          value={todayGames.length}
          subtitle={t('dashboard.stats.gamesScheduled')}
          icon={Trophy}
          color="bg-blue-600"
          onClick={() => setActiveSection('scheduled')}
          tooltip={t('dashboard.tooltip.stats.gamesScheduled')}
        />
        <StatCard
          value={teamsRaw.length}
          subtitle={t('dashboard.stats.teamsTracked')}
          icon={Users}
          color="bg-green-600"
          onClick={() => setActiveSection('tracked')}
          tooltip={t('dashboard.tooltip.stats.teamsTracked')}
        />
        <StatCard
          value={seasonTeamsCount > 0 ? seasonTeamsCount : t('common.noData')}
          subtitle={t('dashboard.stats.thisSeason')}
          icon={Target}
          trend="neutral"
          color="bg-red-600"
          onClick={() => setActiveSection('season')}
          tooltip={t('dashboard.tooltip.stats.thisSeason')}
        />
        <StatCard
          value={focusTeams.filter(t => t.edge > 0).length}
          subtitle={t('dashboard.stats.valueOpportunities')}
          icon={DollarSign}
          trend="up"
          color="bg-yellow-600"
          onClick={() => setActiveSection('value')}
          tooltip={t('dashboard.tooltip.stats.valueOpportunities')}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Today's Games */}
        <div className="lg:col-span-2">
          <div className="glass-card">
            <div className="p-6 border-b border-gray-700/50">
              <div className="flex items-center justify-between" title={t('dashboard.tooltip.todaysGames')}>
                <h2 className="text-xl font-bold text-white flex items-center space-x-2">
                  <Clock className="w-5 h-5 text-blue-400" />
                  <div className="flex flex-col leading-tight">
                    <span>{t('dashboard.section.todaysGames')}</span>
                    <span className="text-sm font-normal text-gray-400">
                      {chicagoTodayLabel} (America/Chicago)
                    </span>
                  </div>
                </h2>
                <span className="text-sm text-gray-400">{todayGames.length} {t('dashboard.section.gamesSuffix')}</span>
              </div>
            </div>
            <div className="p-6 space-y-4">
              {todayGames.map((game) => (
                <GameCard key={game.id} game={game} />
              ))}
            </div>
          </div>
        </div>

        {/* Focus Teams Performance */}
        <div>
          <div className="glass-card">
            <div className="p-6 border-b border-gray-700/50">
              <h2 className="text-xl font-bold text-white flex items-center space-x-2" title={t('dashboard.tooltip.focusTeams')}>
                <BarChart3 className="w-5 h-5 text-green-400" />
                <span>{t('dashboard.section.focusTeams')}</span>
              </h2>
            </div>
            <div className="p-6 space-y-4">
              {focusTeams.map((team) => (
                <div key={`${team.game_id}:${team.team}`} className="flex items-center justify-between p-3 hover:bg-white/5 rounded-lg transition-colors">
                  <div>
                    <div className="font-semibold text-white">
                      {team.team}
                    </div>
                    <div className="text-xs text-gray-400">
                      {t('betting.pick.vs')} {team.opponent} • {t('betting.pick.edge')}: {((team.edge || 0) * 100).toFixed(1)}%
                    </div>
                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      <MetricBadge
                        label={t('badges.value')}
                        tooltip={t('badges.valueTooltip')}
                        tone={team.edge > 0
                          ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-200'
                          : 'border-gray-600/40 bg-gray-700/40 text-gray-300'
                        }
                      />
                      <MetricBadge
                        label={`${t('badges.edge')} ${formatPercentOrNoData(team.edge ?? null)}`}
                        tooltip={t('badges.edgeTooltip')}
                        tone="border-blue-500/40 bg-blue-500/10 text-blue-200"
                      />
                      <MetricBadge
                        label={`${t('badges.confidence')} ${formatPercentOrNoData(team.consensus_prob ?? null)}`}
                        tooltip={t('badges.confidenceTooltip')}
                        tone="border-purple-500/40 bg-purple-500/10 text-purple-200"
                      />
                      <a
                        href={methodologyLink}
                        target="_blank"
                        rel="noreferrer"
                        className="text-[10px] uppercase tracking-widest text-blue-300 hover:text-blue-200"
                        title={t('badges.methodologyTooltip')}
                      >
                        {t('badges.methodologyLink')}
                      </a>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className={`px-2 py-1 rounded text-xs ${
                      team.edge > 0 ? 'bg-green-600/20 text-green-400' :
                      team.edge < 0 ? 'bg-red-600/20 text-red-400' :
                      'bg-yellow-600/20 text-yellow-400'
                    }`}>
                      {team.best_price.toFixed(2)} ({team.best_book || t('common.noData')})
                    </div>
                    {team.edge > 0 ? <TrendingUp className="w-4 h-4 text-green-400" /> :
                     team.edge < 0 ? <TrendingDown className="w-4 h-4 text-red-400" /> :
                     <Activity className="w-4 h-4 text-yellow-400" />}
                  </div>
                </div>
              ))}

              {focusTeams.length === 0 && (
                <div className="text-sm text-gray-400">
                  {t('common.noData')}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* League Spotlight */}
      <div className="glass-card">
        <div className="p-6 border-b border-gray-700/50">
          <h2 className="text-xl font-bold text-white flex items-center space-x-2" title={t('dashboard.tooltip.leagueSpotlight')}>
            <Target className="w-5 h-5 text-red-400" />
            <span>{t('dashboard.section.leagueSpotlight')}</span>
            <div className="ml-auto flex items-center space-x-2">
              <Zap className="w-4 h-4 text-yellow-400" />
              <span className="text-sm text-gray-400" title={t('dashboard.tooltip.liveMatchup')}>{t('dashboard.section.liveMatchup')}</span>
            </div>
          </h2>
        </div>
        <div className="p-6">
          {todayGames.length === 0 ? (
            <div className="text-sm text-gray-400">{t('common.noData')}</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-400 mb-2">
                  {todayGames[0].homeTeam} {t('betting.pick.vs')} {todayGames[0].awayTeam}
                </div>
                <div className="text-gray-400">{todayGames[0].time}</div>
                <div className="text-sm text-gray-500 mt-2">{t('dashboard.spotlight.featuredGame')}</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-white mb-2">{t('dashboard.spotlight.last5')}</div>
                <div className="text-gray-400">
                  {spotlightGame
                    ? `${teamLabel(spotlightHome, spotlightGame.homeTeam)} ${formatLast5(spotlightHome)} / ${teamLabel(spotlightAway, spotlightGame.awayTeam)} ${formatLast5(spotlightAway)}`
                    : t('common.noData')}
                </div>
                <div className="text-sm text-gray-500 mt-2">{t('dashboard.spotlight.strongForm')}</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-white mb-2">{t('dashboard.spotlight.keyPlayers')}</div>
                <div className="text-gray-400">
                  {spotlightGame
                    ? `${teamLabel(spotlightHome, spotlightGame.homeTeam)}: ${formatKeyPlayers(spotlightHome)} | ${teamLabel(spotlightAway, spotlightGame.awayTeam)}: ${formatKeyPlayers(spotlightAway)}`
                    : t('common.noData')}
                </div>
                <div className="text-sm text-gray-500 mt-2">{t('dashboard.spotlight.fullRotation')}</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Risk Alerts */}
      <div className="glass-card border-yellow-400/20">
        <div className="p-6 border-b border-gray-700/50">
          <h2 className="text-xl font-bold text-white flex items-center space-x-2" title={t('dashboard.tooltip.riskAlerts')}>
            <AlertTriangle className="w-5 h-5 text-yellow-400" />
            <span>{t('dashboard.section.riskAlerts')}</span>
          </h2>
        </div>
        <div className="p-6">
          <div className="text-sm text-gray-400">{t('common.noData')}</div>
        </div>
      </div>
        </>
      )}
    </div>
  );
};

export default Dashboard;
