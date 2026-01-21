import React, { useEffect, useMemo, useState } from 'react';
import { Activity, Stethoscope, Target, TrendingUp, Users, Sparkles, Shield, LineChart, ArrowRight } from 'lucide-react';
import { PropBetAnalyzer } from './PropBetAnalyzer';
import { FormTracker } from './FormTracker';
import { useI18n } from '../i18n/useI18n';
import { getAuthHeader } from '../services/auth';

const API_BASE =
  (typeof import.meta.env.VITE_API_BASE_URL === 'string' && import.meta.env.VITE_API_BASE_URL.trim() !== ''
    ? import.meta.env.VITE_API_BASE_URL.trim()
    : (
        typeof window !== 'undefined'
          ? `http://${window.location.hostname}:8000`
          : 'http://localhost:8000'
      ));

type Tab = 'overview' | 'props' | 'form' | 'matchup' | 'injury';

interface TeamMatchupResult {
  team: string;
  opponent: string;
  total_games: number;
  averages?: {
    points?: number;
    rebounds?: number;
    assists?: number;
  };
  home_away_split?: {
    home_ppg?: number;
    away_ppg?: number;
    home_advantage?: number;
  };
}

interface PlayerMatchupResult {
  player: string;
  opponent: string;
  games_played: number;
  averages?: {
    points?: number;
    rebounds?: number;
    assists?: number;
  };
}

interface InjuryImpactResult {
  missing_player: string;
  team: string;
  team_impact?: {
    points_difference?: number;
    description?: string;
  };
  beneficiaries?: Array<{
    player: string;
    increase?: number;
    percent_increase?: number;
  }>;
}

type Insight = {
  title: string;
  description: string;
  metricPrimary: string;
  metricSecondary: string;
  signal: string;
  focus: string;
};

const Analytics: React.FC = () => {
  const { t } = useI18n();

  const [activeTab, setActiveTab] = useState<Tab>('overview');

  const [team, setTeam] = useState('CHI');
  const [opponent, setOpponent] = useState('LAL');
  const [seasonsBack, setSeasonsBack] = useState(3);
  const [teamMatchup, setTeamMatchup] = useState<TeamMatchupResult | null>(null);
  const [teamMatchupLoading, setTeamMatchupLoading] = useState(false);
  const [teamMatchupError, setTeamMatchupError] = useState<string | null>(null);

  const [playerName, setPlayerName] = useState('Zach LaVine');
  const [playerOpponent, setPlayerOpponent] = useState('LAL');
  const [playerSeasonsBack, setPlayerSeasonsBack] = useState(3);
  const [playerMatchup, setPlayerMatchup] = useState<PlayerMatchupResult | null>(null);
  const [playerMatchupLoading, setPlayerMatchupLoading] = useState(false);
  const [playerMatchupError, setPlayerMatchupError] = useState<string | null>(null);

  const [injuryTeam, setInjuryTeam] = useState('CHI');
  const [missingPlayer, setMissingPlayer] = useState('Zach LaVine');
  const [injurySeasonsBack, setInjurySeasonsBack] = useState(2);
  const [injuryImpact, setInjuryImpact] = useState<InjuryImpactResult | null>(null);
  const [injuryLoading, setInjuryLoading] = useState(false);
  const [injuryError, setInjuryError] = useState<string | null>(null);

  const tabs: Array<{ id: Tab; label: string; icon: React.ElementType; helper: string }> = useMemo(
    () => [
      { id: 'overview', label: t('analytics.tabs.overview.label'), icon: Sparkles, helper: t('analytics.tabs.overview.helper') },
      { id: 'props', label: t('analytics.tabs.props.label'), icon: Target, helper: t('analytics.tabs.props.helper') },
      { id: 'form', label: t('analytics.tabs.form.label'), icon: LineChart, helper: t('analytics.tabs.form.helper') },
      { id: 'matchup', label: t('analytics.tabs.matchup.label'), icon: Users, helper: t('analytics.tabs.matchup.helper') },
      { id: 'injury', label: t('analytics.tabs.injury.label'), icon: Stethoscope, helper: t('analytics.tabs.injury.helper') },
    ],
    [t]
  );

  const formatStat = (value?: number) => (value === undefined || value === null ? '—' : value);
  const toNumber = (value?: number) => (typeof value === 'number' && !Number.isNaN(value) ? value : 0);

  const baseInsights: Insight[] = useMemo(
    () => [
      {
        title: t('analytics.insights.base1.title'),
        description: t('analytics.insights.base1.description'),
        metricPrimary: t('analytics.insights.base1.metricPrimary'),
        metricSecondary: t('analytics.insights.base1.metricSecondary'),
        signal: t('analytics.insights.base1.signal'),
        focus: t('analytics.insights.base1.focus'),
      },
      {
        title: t('analytics.insights.base2.title'),
        description: t('analytics.insights.base2.description'),
        metricPrimary: t('analytics.insights.base2.metricPrimary'),
        metricSecondary: t('analytics.insights.base2.metricSecondary'),
        signal: t('analytics.insights.base2.signal'),
        focus: t('analytics.insights.base2.focus'),
      },
      {
        title: t('analytics.insights.base3.title'),
        description: t('analytics.insights.base3.description'),
        metricPrimary: t('analytics.insights.base3.metricPrimary'),
        metricSecondary: t('analytics.insights.base3.metricSecondary'),
        signal: t('analytics.insights.base3.signal'),
        focus: t('analytics.insights.base3.focus'),
      },
    ],
    [t]
  );

  const [insight, setInsight] = useState<Insight>(baseInsights[0]);
  const [insightHistory, setInsightHistory] = useState<Insight[]>([]);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [insightTick, setInsightTick] = useState(0);
  const [showInsightToast, setShowInsightToast] = useState(false);

  const sparklinePoints = (values: number[], width = 140, height = 36, padding = 4) => {
    const safeValues = values.length ? values : [0];
    const min = Math.min(...safeValues);
    const max = Math.max(...safeValues);
    const range = max - min || 1;
    return safeValues
      .map((value, index) => {
        const x = padding + (index / Math.max(safeValues.length - 1, 1)) * (width - padding * 2);
        const y = padding + (1 - (value - min) / range) * (height - padding * 2);
        return `${x},${y}`;
      })
      .join(' ');
  };

  const Sparkline = ({
    values,
    stroke,
    fill,
  }: {
    values: number[];
    stroke: string;
    fill?: string;
  }) => (
    <svg width="100%" height="40" viewBox="0 0 140 36" className="block">
      <polyline
        fill={fill || 'none'}
        stroke={stroke}
        strokeWidth="2"
        strokeLinejoin="round"
        strokeLinecap="round"
        points={sparklinePoints(values)}
      />
    </svg>
  );

  const InsightCard = useMemo(() => insight, [insight]);
  const hasDataInsight = Boolean(
    injuryImpact?.team_impact?.points_difference !== undefined ||
    playerMatchup?.averages?.points !== undefined ||
    teamMatchup?.home_away_split?.home_advantage !== undefined
  );

  useEffect(() => {
    if (injuryImpact?.team_impact?.points_difference !== undefined) {
      const diff = injuryImpact.team_impact.points_difference;
      setInsight({
        title: t('analytics.insights.dynamic.injury.title'),
        description: t('analytics.insights.dynamic.injury.description'),
        metricPrimary: t('analytics.insights.dynamic.injury.metricPrimary', { value: `${diff > 0 ? '+' : ''}${diff.toFixed(1)}` }),
        metricSecondary: t('analytics.insights.dynamic.injury.metricSecondary', { count: (injuryImpact.beneficiaries || []).length }),
        signal: t('analytics.insights.dynamic.injury.signal'),
        focus: t('analytics.insights.dynamic.injury.focus'),
      });
      setLastUpdated(new Date());
      return;
    }

    if (playerMatchup?.averages?.points !== undefined) {
      const points = playerMatchup.averages.points;
      setInsight({
        title: t('analytics.insights.dynamic.player.title'),
        description: t('analytics.insights.dynamic.player.description'),
        metricPrimary: t('analytics.insights.dynamic.player.metricPrimary', { value: points.toFixed(1) }),
        metricSecondary: t('analytics.insights.dynamic.player.metricSecondary', { games: playerMatchup.games_played }),
        signal: t('analytics.insights.dynamic.player.signal'),
        focus: t('analytics.insights.dynamic.player.focus'),
      });
      setLastUpdated(new Date());
      return;
    }

    if (teamMatchup?.home_away_split?.home_advantage !== undefined) {
      const advantage = teamMatchup.home_away_split.home_advantage;
      setInsight({
        title: t('analytics.insights.dynamic.team.title'),
        description: t('analytics.insights.dynamic.team.description'),
        metricPrimary: t('analytics.insights.dynamic.team.metricPrimary', { value: `${advantage > 0 ? '+' : ''}${advantage.toFixed(1)}` }),
        metricSecondary: t('analytics.insights.dynamic.team.metricSecondary', { games: teamMatchup.total_games }),
        signal: t('analytics.insights.dynamic.team.signal'),
        focus: t('analytics.insights.dynamic.team.focus'),
      });
      setLastUpdated(new Date());
      return;
    }

    const fallback = baseInsights[insightTick % baseInsights.length];
    setInsight(fallback);
    setLastUpdated(new Date());
  }, [injuryImpact, playerMatchup, teamMatchup, insightTick, baseInsights, t]);

  useEffect(() => {
    setInsightHistory((prev) => {
      if (prev[0]?.title === InsightCard.title) return prev;
      return [InsightCard, ...prev].slice(0, 5);
    });
  }, [InsightCard]);

  useEffect(() => {
    if (!showInsightToast) return;
    const timer = setTimeout(() => setShowInsightToast(false), 2000);
    return () => clearTimeout(timer);
  }, [showInsightToast]);

  const loadTeamMatchup = async () => {
    setTeamMatchupLoading(true);
    setTeamMatchupError(null);
    setTeamMatchup(null);

    try {
      const params = new URLSearchParams({
        team,
        opponent,
        seasons_back: seasonsBack.toString(),
      });
      const response = await fetch(`${API_BASE}/api/analytics/matchup/team?${params}`, {
        headers: getAuthHeader(),
      });
      const data = await response.json();
      if (data.error) {
        setTeamMatchupError(data.error);
      } else {
        setTeamMatchup(data);
      }
    } catch {
      setTeamMatchupError(t('analytics.error.teamMatchupFailed'));
    } finally {
      setTeamMatchupLoading(false);
    }
  };

  const loadPlayerMatchup = async () => {
    setPlayerMatchupLoading(true);
    setPlayerMatchupError(null);
    setPlayerMatchup(null);

    try {
      const params = new URLSearchParams({
        player_name: playerName,
        opponent: playerOpponent,
        seasons_back: playerSeasonsBack.toString(),
      });
      const response = await fetch(`${API_BASE}/api/analytics/matchup/player?${params}`, {
        headers: getAuthHeader(),
      });
      const data = await response.json();
      if (data.error) {
        setPlayerMatchupError(data.error);
      } else {
        setPlayerMatchup(data);
      }
    } catch {
      setPlayerMatchupError(t('analytics.error.playerMatchupFailed'));
    } finally {
      setPlayerMatchupLoading(false);
    }
  };

  const loadInjuryImpact = async () => {
    setInjuryLoading(true);
    setInjuryError(null);
    setInjuryImpact(null);

    try {
      const params = new URLSearchParams({
        team: injuryTeam,
        missing_player: missingPlayer,
        seasons_back: injurySeasonsBack.toString(),
      });
      const response = await fetch(`${API_BASE}/api/analytics/injury-impact?${params}`, {
        headers: getAuthHeader(),
      });
      const data = await response.json();
      if (data.error) {
        setInjuryError(data.error);
      } else {
        setInjuryImpact(data);
      }
    } catch {
      setInjuryError(t('analytics.error.injuryImpactFailed'));
    } finally {
      setInjuryLoading(false);
    }
  };

  const tabButton = (tab: Tab, label: string, Icon: React.ElementType, helper: string) => (
    <button
      onClick={() => setActiveTab(tab)}
      title={helper}
      className={`group flex items-center gap-3 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
        activeTab === tab
          ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20'
          : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
      }`}
    >
      <span className={`flex h-8 w-8 items-center justify-center rounded-md ${
        activeTab === tab ? 'bg-white/15' : 'bg-gray-800/80 group-hover:bg-gray-700/70'
      }`}>
        <Icon className="h-4 w-4" />
      </span>
      <span className="text-left">
        <div className="leading-tight">{label}</div>
        <div className="text-xs text-gray-500 group-hover:text-gray-300">{helper}</div>
      </span>
    </button>
  );

  return (
    <div className="space-y-6">
      <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-br from-slate-900/90 via-slate-950/80 to-slate-900/90 p-6 md:p-8">
        <div className="absolute -top-24 -right-16 h-56 w-56 rounded-full bg-blue-500/20 blur-3xl"></div>
        <div className="absolute -bottom-16 -left-12 h-52 w-52 rounded-full bg-cyan-400/20 blur-3xl"></div>
        <div className="relative flex flex-col gap-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs uppercase tracking-widest text-blue-200">
                {t('analytics.hero.badge')}
              </div>
              <h2 className="font-display mt-3 text-3xl font-semibold text-white">
                {t('analytics.hero.title')}
              </h2>
              <p className="mt-2 max-w-2xl text-sm text-gray-300">
                {t('analytics.hero.description')}
              </p>
            </div>
            <div className="glass-card flex items-center gap-3 px-4 py-3">
              <Shield className="h-5 w-5 text-emerald-300" />
              <div>
                <div className="text-xs text-gray-400">{t('analytics.hero.dataFreshness.label')}</div>
                <div className="text-sm font-semibold text-white">{t('analytics.hero.dataFreshness.value')}</div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div className="glass-card p-4" title={t('analytics.hero.stats.modulesOnline.helper')}>
              <div className="text-xs uppercase tracking-wider text-gray-400">{t('analytics.hero.stats.modulesOnline.label')}</div>
              <div className="mt-2 text-2xl font-semibold text-white">4</div>
              <div className="text-sm text-gray-400">{t('analytics.hero.stats.modulesOnline.helper')}</div>
            </div>
            <div className="glass-card p-4" title={t('analytics.hero.stats.historicalSeasons.helper')}>
              <div className="text-xs uppercase tracking-wider text-gray-400">{t('analytics.hero.stats.historicalSeasons.label')}</div>
              <div className="mt-2 text-2xl font-semibold text-white">2010-2024</div>
              <div className="text-sm text-gray-400">{t('analytics.hero.stats.historicalSeasons.helper')}</div>
            </div>
            <div className="glass-card p-4" title={t('analytics.hero.stats.focus.helper')}>
              <div className="text-xs uppercase tracking-wider text-gray-400">{t('analytics.hero.stats.focus.label')}</div>
              <div className="mt-2 text-2xl font-semibold text-white">{t('analytics.hero.stats.focus.value')}</div>
              <div className="text-sm text-gray-400">{t('analytics.hero.stats.focus.helper')}</div>
            </div>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap gap-3 rounded-2xl border border-white/10 bg-gray-900/40 p-2">
        {tabs.map((tab) => tabButton(tab.id, tab.label, tab.icon, tab.helper))}
      </div>

      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="relative overflow-hidden glass-card p-6" title={t('analytics.overview.props.description')}>
            <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-blue-500/20 blur-2xl"></div>
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-3 bg-blue-600/20 rounded-lg">
                <Target className="w-6 h-6 text-blue-400" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">{t('analytics.overview.props.title')}</h2>
                <p className="text-sm text-gray-400">{t('analytics.overview.props.subtitle')}</p>
              </div>
            </div>
            <p className="text-gray-300 mb-4">
              {t('analytics.overview.props.description')}
            </p>
            <button
              onClick={() => setActiveTab('props')}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-white"
            >
              {t('analytics.overview.props.action')}
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>

          <div className="relative overflow-hidden glass-card p-6" title={t('analytics.overview.form.description')}>
            <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-emerald-500/20 blur-2xl"></div>
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-3 bg-green-600/20 rounded-lg">
                <TrendingUp className="w-6 h-6 text-green-400" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">{t('analytics.overview.form.title')}</h2>
                <p className="text-sm text-gray-400">{t('analytics.overview.form.subtitle')}</p>
              </div>
            </div>
            <p className="text-gray-300 mb-4">
              {t('analytics.overview.form.description')}
            </p>
            <button
              onClick={() => setActiveTab('form')}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-white"
            >
              {t('analytics.overview.form.action')}
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>

          <div className="relative overflow-hidden glass-card p-6" title={t('analytics.overview.matchup.description')}>
            <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-purple-500/20 blur-2xl"></div>
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-3 bg-purple-600/20 rounded-lg">
                <Users className="w-6 h-6 text-purple-400" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">{t('analytics.overview.matchup.title')}</h2>
                <p className="text-sm text-gray-400">{t('analytics.overview.matchup.subtitle')}</p>
              </div>
            </div>
            <p className="text-gray-300 mb-4">
              {t('analytics.overview.matchup.description')}
            </p>
            <button
              onClick={() => setActiveTab('matchup')}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-white"
            >
              {t('analytics.overview.matchup.action')}
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>

          <div className="relative overflow-hidden glass-card p-6" title={t('analytics.overview.injury.description')}>
            <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-red-500/20 blur-2xl"></div>
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-3 bg-red-600/20 rounded-lg">
                <Stethoscope className="w-6 h-6 text-red-400" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">{t('analytics.overview.injury.title')}</h2>
                <p className="text-sm text-gray-400">{t('analytics.overview.injury.subtitle')}</p>
              </div>
            </div>
            <p className="text-gray-300 mb-4">
              {t('analytics.overview.injury.description')}
            </p>
            <button
              onClick={() => setActiveTab('injury')}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-white"
            >
              {t('analytics.overview.injury.action')}
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>

          <div className="lg:col-span-2 glass-card p-6">
            {showInsightToast && (
              <div className="mb-4 rounded-xl border border-emerald-500/30 bg-emerald-900/20 px-4 py-2 text-sm text-emerald-200">
                {t('analytics.overview.insight.toastUpdated')}
              </div>
            )}
            <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
              <div>
                <div className="text-xs uppercase tracking-widest text-gray-500">{t('analytics.overview.insight.heading')}</div>
                <h3 className="text-2xl font-semibold text-white mt-2">{InsightCard.title}</h3>
                <p className="text-sm text-gray-400 mt-2 max-w-2xl">{InsightCard.description}</p>
              </div>
              <div className="flex gap-3">
                <div className="rounded-xl border border-emerald-500/30 bg-emerald-900/20 px-4 py-3">
                  <div className="text-xs text-emerald-200 uppercase tracking-widest">{t('analytics.overview.insight.edgeBoost')}</div>
                  <div className="text-xl font-semibold text-white mt-1">{InsightCard.metricPrimary}</div>
                </div>
                <div className="rounded-xl border border-blue-500/30 bg-blue-900/20 px-4 py-3">
                  <div className="text-xs text-blue-200 uppercase tracking-widest">{t('analytics.overview.insight.confidence')}</div>
                  <div className="text-xl font-semibold text-white mt-1">{InsightCard.metricSecondary}</div>
                </div>
                <div className="rounded-xl border border-white/10 bg-white/5 px-4 py-3">
                  <div className="text-xs uppercase tracking-widest text-gray-500">{t('analytics.overview.insight.lastUpdated')}</div>
                  <div className="text-sm font-semibold text-white mt-1">
                    {lastUpdated ? lastUpdated.toLocaleString() : '—'}
                  </div>
                </div>
                <button
                  onClick={() => {
                    if (hasDataInsight) return;
                    setInsightTick((prev) => prev + 1);
                    setShowInsightToast(true);
                  }}
                  disabled={hasDataInsight}
                  className="rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-left hover:bg-white/10 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <div className="text-xs uppercase tracking-widest text-gray-500">{t('analytics.overview.insight.button.label')}</div>
                  <div className="text-sm font-semibold text-white mt-1">
                    {hasDataInsight ? t('analytics.overview.insight.button.locked') : t('analytics.overview.insight.button.refresh')}
                  </div>
                </button>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                <div className="text-xs uppercase tracking-widest text-gray-500">{t('analytics.overview.insight.signalStack')}</div>
                <div className="mt-2 text-sm text-gray-300">{InsightCard.signal}</div>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                <div className="text-xs uppercase tracking-widest text-gray-500">{t('analytics.overview.insight.idealUse')}</div>
                <div className="mt-2 text-sm text-gray-300">{t('analytics.overview.insight.idealUse.value')}</div>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                <div className="text-xs uppercase tracking-widest text-gray-500">{t('analytics.overview.insight.nextAction')}</div>
                <div className="mt-2 text-sm text-gray-300">{InsightCard.focus}</div>
              </div>
            </div>
            <div className="mt-6">
              <div className="text-xs uppercase tracking-widest text-gray-500 mb-3">{t('analytics.overview.insight.historyHeading')}</div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {insightHistory.map((item, index) => (
                  <div key={`${item.title}-${index}`} className="rounded-xl border border-white/10 bg-white/5 p-4">
                    <div className="text-sm font-semibold text-white">{item.title}</div>
                    <div className="text-xs text-gray-400 mt-1">{item.metricPrimary} • {item.metricSecondary}</div>
                  </div>
                ))}
                {!insightHistory.length && (
                  <div className="rounded-xl border border-dashed border-white/10 p-4 text-sm text-gray-400">
                    {t('analytics.overview.insight.historyEmpty')}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'props' && (
        <div className="space-y-6">
          <div className="glass-card p-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-2xl font-semibold text-white">{t('analytics.props.header.title')}</h3>
                <p className="text-sm text-gray-400">
                  {t('analytics.props.header.description')}
                </p>
              </div>
              <div className="rounded-full bg-blue-500/20 px-3 py-1 text-xs uppercase tracking-widest text-blue-200">
                {t('analytics.props.header.badge')}
              </div>
            </div>
          </div>
          <PropBetAnalyzer />
        </div>
      )}

      {activeTab === 'form' && (
        <div className="space-y-6">
          <div className="glass-card p-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-2xl font-semibold text-white">{t('analytics.form.header.title')}</h3>
                <p className="text-sm text-gray-400">
                  {t('analytics.form.header.description')}
                </p>
              </div>
              <div className="rounded-full bg-emerald-500/20 px-3 py-1 text-xs uppercase tracking-widest text-emerald-200">
                {t('analytics.form.header.badge')}
              </div>
            </div>
          </div>
          <FormTracker />
        </div>
      )}

      {activeTab === 'matchup' && (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <div className="glass-card p-6">
            <div className="flex items-center space-x-2 mb-4">
              <Users className="w-5 h-5 text-blue-400" />
              <h2 className="text-xl font-bold text-white">{t('analytics.matchup.team.title')}</h2>
              <span className="ml-auto rounded-full bg-white/10 px-2 py-1 text-xs text-gray-300">/api/analytics/matchup/team</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div>
                <label htmlFor="analytics-team" className="block text-xs uppercase tracking-widest text-gray-500 mb-2">
                  {t('analytics.matchup.team.form.team.label')}
                </label>
                <input
                  id="analytics-team"
                  value={team}
                  onChange={(event) => setTeam(event.target.value)}
                  aria-label={t('analytics.matchup.team.form.team.label')}
                  title={t('analytics.matchup.team.form.team.label')}
                  placeholder={t('analytics.matchup.team.form.team.placeholder')}
                  className="w-full px-3 py-2 rounded bg-gray-900/60 border border-gray-700 text-gray-100"
                />
              </div>
              <div>
                <label htmlFor="analytics-opponent" className="block text-xs uppercase tracking-widest text-gray-500 mb-2">
                  {t('analytics.matchup.team.form.opponent.label')}
                </label>
                <input
                  id="analytics-opponent"
                  value={opponent}
                  onChange={(event) => setOpponent(event.target.value)}
                  aria-label={t('analytics.matchup.team.form.opponent.label')}
                  title={t('analytics.matchup.team.form.opponent.label')}
                  placeholder={t('analytics.matchup.team.form.opponent.placeholder')}
                  className="w-full px-3 py-2 rounded bg-gray-900/60 border border-gray-700 text-gray-100"
                />
              </div>
              <div>
                <label htmlFor="analytics-seasonsBack" className="block text-xs uppercase tracking-widest text-gray-500 mb-2">
                  {t('analytics.matchup.team.form.seasonsBack.label')}
                </label>
                <input
                  id="analytics-seasonsBack"
                  type="number"
                  value={seasonsBack}
                  min={1}
                  onChange={(event) => setSeasonsBack(parseInt(event.target.value, 10) || 1)}
                  aria-label={t('analytics.matchup.team.form.seasonsBack.label')}
                  title={t('analytics.matchup.team.form.seasonsBack.label')}
                  className="w-full px-3 py-2 rounded bg-gray-900/60 border border-gray-700 text-gray-100"
                />
              </div>
            </div>
            <button
              onClick={loadTeamMatchup}
              disabled={teamMatchupLoading}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-white disabled:bg-gray-600"
            >
              {teamMatchupLoading ? t('analytics.actions.loading') : t('analytics.matchup.team.actions.analyze')}
            </button>

            {teamMatchupLoading && (
              <div className="mt-6 space-y-3">
                <div className="skeleton h-20"></div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div className="skeleton h-16"></div>
                  <div className="skeleton h-16"></div>
                  <div className="skeleton h-16"></div>
                </div>
                <div className="skeleton h-14"></div>
              </div>
            )}

            {teamMatchupError && (
              <div className="mt-4 p-4 border border-red-500/30 bg-red-900/20 text-red-200 rounded">
                {teamMatchupError}
              </div>
            )}

            {teamMatchup && (
              <div className="mt-6 space-y-4">
                <div className="glass-card p-4">
                  <div className="text-sm text-gray-400">{t('analytics.matchup.team.stats.totalGames')}</div>
                  <div className="text-2xl font-bold text-white">{teamMatchup.total_games}</div>
                </div>
                <div className="glass-card p-4">
                  <div className="flex items-center justify-between text-sm text-gray-400 mb-2">
                    <span>{t('analytics.matchup.team.sections.homeAwayScoring.title')}</span>
                    <span className="text-xs text-gray-500">{t('analytics.matchup.team.sections.homeAwayScoring.helper')}</span>
                  </div>
                  <Sparkline
                    values={[
                      toNumber(teamMatchup.home_away_split?.away_ppg),
                      toNumber(teamMatchup.home_away_split?.home_ppg),
                    ]}
                    stroke="#6366f1"
                  />
                  <div className="mt-2 flex items-center justify-between text-xs text-gray-400">
                    <span>{t('analytics.matchup.team.labels.away')} {formatStat(teamMatchup.home_away_split?.away_ppg)}</span>
                    <span>{t('analytics.matchup.team.labels.home')} {formatStat(teamMatchup.home_away_split?.home_ppg)}</span>
                  </div>
                </div>
                <div className="glass-card p-4">
                  <div className="flex items-center justify-between text-sm text-gray-400 mb-2">
                    <span>{t('analytics.matchup.team.sections.teamAverages.title')}</span>
                    <span className="text-xs text-gray-500">{t('analytics.matchup.team.sections.teamAverages.helper')}</span>
                  </div>
                  <Sparkline
                    values={[
                      toNumber(teamMatchup.averages?.points),
                      toNumber(teamMatchup.averages?.rebounds),
                      toNumber(teamMatchup.averages?.assists),
                    ]}
                    stroke="#38bdf8"
                  />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="glass-card p-4">
                    <div className="text-sm text-gray-400">{t('analytics.matchup.team.stats.avgPoints')}</div>
                    <div className="text-xl text-white">{formatStat(teamMatchup.averages?.points)}</div>
                  </div>
                  <div className="glass-card p-4">
                    <div className="text-sm text-gray-400">{t('analytics.matchup.team.stats.avgRebounds')}</div>
                    <div className="text-xl text-white">{formatStat(teamMatchup.averages?.rebounds)}</div>
                  </div>
                  <div className="glass-card p-4">
                    <div className="text-sm text-gray-400">{t('analytics.matchup.team.stats.avgAssists')}</div>
                    <div className="text-xl text-white">{formatStat(teamMatchup.averages?.assists)}</div>
                  </div>
                </div>
                <div className="glass-card p-4">
                  <div className="text-sm text-gray-400 mb-2">{t('analytics.matchup.team.sections.homeAwaySplit.title')}</div>
                  <div className="flex flex-wrap gap-2 text-gray-200">
                    <span className="rounded-full bg-white/10 px-3 py-1 text-xs">
                      {t('analytics.matchup.team.labels.homePpg')} {formatStat(teamMatchup.home_away_split?.home_ppg)}
                    </span>
                    <span className="rounded-full bg-white/10 px-3 py-1 text-xs">
                      {t('analytics.matchup.team.labels.awayPpg')} {formatStat(teamMatchup.home_away_split?.away_ppg)}
                    </span>
                    <span className="rounded-full bg-blue-500/20 px-3 py-1 text-xs text-blue-100">
                      {t('analytics.matchup.team.labels.advantage')} {formatStat(teamMatchup.home_away_split?.home_advantage)}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {!teamMatchup && !teamMatchupLoading && !teamMatchupError && (
              <div className="mt-6 rounded-xl border border-dashed border-white/10 p-6 text-sm text-gray-400">
                {t('analytics.matchup.team.empty')}
              </div>
            )}
          </div>

          <div className="glass-card p-6">
            <div className="flex items-center space-x-2 mb-4">
              <Activity className="w-5 h-5 text-green-400" />
              <h2 className="text-xl font-bold text-white">{t('analytics.matchup.player.title')}</h2>
              <span className="ml-auto rounded-full bg-white/10 px-2 py-1 text-xs text-gray-300">/api/analytics/matchup/player</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div>
                <label htmlFor="analytics-player" className="block text-xs uppercase tracking-widest text-gray-500 mb-2">
                  {t('analytics.matchup.player.form.player.label')}
                </label>
                <input
                  id="analytics-player"
                  value={playerName}
                  onChange={(event) => setPlayerName(event.target.value)}
                  aria-label={t('analytics.matchup.player.form.player.label')}
                  title={t('analytics.matchup.player.form.player.label')}
                  placeholder={t('analytics.matchup.player.form.player.placeholder')}
                  className="w-full px-3 py-2 rounded bg-gray-900/60 border border-gray-700 text-gray-100"
                />
              </div>
              <div>
                <label htmlFor="analytics-playerOpponent" className="block text-xs uppercase tracking-widest text-gray-500 mb-2">
                  {t('analytics.matchup.player.form.opponent.label')}
                </label>
                <input
                  id="analytics-playerOpponent"
                  value={playerOpponent}
                  onChange={(event) => setPlayerOpponent(event.target.value)}
                  aria-label={t('analytics.matchup.player.form.opponent.label')}
                  title={t('analytics.matchup.player.form.opponent.label')}
                  placeholder={t('analytics.matchup.player.form.opponent.placeholder')}
                  className="w-full px-3 py-2 rounded bg-gray-900/60 border border-gray-700 text-gray-100"
                />
              </div>
              <div>
                <label htmlFor="analytics-playerSeasonsBack" className="block text-xs uppercase tracking-widest text-gray-500 mb-2">
                  {t('analytics.matchup.player.form.seasonsBack.label')}
                </label>
                <input
                  id="analytics-playerSeasonsBack"
                  type="number"
                  value={playerSeasonsBack}
                  min={1}
                  onChange={(event) => setPlayerSeasonsBack(parseInt(event.target.value, 10) || 1)}
                  aria-label={t('analytics.matchup.player.form.seasonsBack.label')}
                  title={t('analytics.matchup.player.form.seasonsBack.label')}
                  className="w-full px-3 py-2 rounded bg-gray-900/60 border border-gray-700 text-gray-100"
                />
              </div>
            </div>
            <button
              onClick={loadPlayerMatchup}
              disabled={playerMatchupLoading}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-white disabled:bg-gray-600"
            >
              {playerMatchupLoading ? t('analytics.actions.loading') : t('analytics.matchup.player.actions.analyze')}
            </button>

            {playerMatchupLoading && (
              <div className="mt-6 space-y-3">
                <div className="skeleton h-20"></div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div className="skeleton h-16"></div>
                  <div className="skeleton h-16"></div>
                  <div className="skeleton h-16"></div>
                </div>
              </div>
            )}

            {playerMatchupError && (
              <div className="mt-4 p-4 border border-red-500/30 bg-red-900/20 text-red-200 rounded">
                {playerMatchupError}
              </div>
            )}

            {playerMatchup && (
              <div className="mt-6 space-y-4">
                <div className="glass-card p-4">
                  <div className="text-sm text-gray-400">{t('analytics.matchup.player.stats.gamesPlayed')}</div>
                  <div className="text-2xl font-bold text-white">{playerMatchup.games_played}</div>
                </div>
                <div className="glass-card p-4">
                  <div className="flex items-center justify-between text-sm text-gray-400 mb-2">
                    <span>{t('analytics.matchup.player.sections.productionMix.title')}</span>
                    <span className="text-xs text-gray-500">{t('analytics.matchup.player.sections.productionMix.helper')}</span>
                  </div>
                  <Sparkline
                    values={[
                      toNumber(playerMatchup.averages?.points),
                      toNumber(playerMatchup.averages?.rebounds),
                      toNumber(playerMatchup.averages?.assists),
                    ]}
                    stroke="#22c55e"
                  />
                  <div className="mt-2 flex items-center justify-between text-xs text-gray-400">
                    <span>PTS {formatStat(playerMatchup.averages?.points)}</span>
                    <span>REB {formatStat(playerMatchup.averages?.rebounds)}</span>
                    <span>AST {formatStat(playerMatchup.averages?.assists)}</span>
                  </div>
                </div>
                <div className="glass-card p-4">
                  <div className="flex items-center justify-between text-sm text-gray-400 mb-2">
                    <span>{t('analytics.matchup.player.sections.scoringShape.title')}</span>
                    <span className="text-xs text-gray-500">{t('analytics.matchup.player.sections.scoringShape.helper')}</span>
                  </div>
                  <Sparkline
                    values={[
                      toNumber(playerMatchup.averages?.points),
                      toNumber(playerMatchup.averages?.rebounds),
                      toNumber(playerMatchup.averages?.assists),
                    ]}
                    stroke="#34d399"
                  />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="glass-card p-4">
                    <div className="text-sm text-gray-400">{t('analytics.matchup.player.stats.avgPoints')}</div>
                    <div className="text-xl text-white">{formatStat(playerMatchup.averages?.points)}</div>
                  </div>
                  <div className="glass-card p-4">
                    <div className="text-sm text-gray-400">{t('analytics.matchup.player.stats.avgRebounds')}</div>
                    <div className="text-xl text-white">{formatStat(playerMatchup.averages?.rebounds)}</div>
                  </div>
                  <div className="glass-card p-4">
                    <div className="text-sm text-gray-400">{t('analytics.matchup.player.stats.avgAssists')}</div>
                    <div className="text-xl text-white">{formatStat(playerMatchup.averages?.assists)}</div>
                  </div>
                </div>
              </div>
            )}

            {!playerMatchup && !playerMatchupLoading && !playerMatchupError && (
              <div className="mt-6 rounded-xl border border-dashed border-white/10 p-6 text-sm text-gray-400">
                {t('analytics.matchup.player.empty')}
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'injury' && (
        <div className="glass-card p-6">
          <div className="flex items-center space-x-2 mb-4">
            <Stethoscope className="w-5 h-5 text-red-400" />
            <h2 className="text-xl font-bold text-white">{t('analytics.injury.title')}</h2>
            <span className="ml-auto rounded-full bg-white/10 px-2 py-1 text-xs text-gray-300">/api/analytics/injury-impact</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label htmlFor="analytics-injuryTeam" className="block text-xs uppercase tracking-widest text-gray-500 mb-2">
                {t('analytics.injury.form.team.label')}
              </label>
              <input
                id="analytics-injuryTeam"
                value={injuryTeam}
                onChange={(event) => setInjuryTeam(event.target.value)}
                aria-label={t('analytics.injury.form.team.label')}
                title={t('analytics.injury.form.team.label')}
                placeholder={t('analytics.injury.form.team.placeholder')}
                className="w-full px-3 py-2 rounded bg-gray-900/60 border border-gray-700 text-gray-100"
              />
            </div>
            <div>
              <label htmlFor="analytics-missingPlayer" className="block text-xs uppercase tracking-widest text-gray-500 mb-2">
                {t('analytics.injury.form.missingPlayer.label')}
              </label>
              <input
                id="analytics-missingPlayer"
                value={missingPlayer}
                onChange={(event) => setMissingPlayer(event.target.value)}
                aria-label={t('analytics.injury.form.missingPlayer.label')}
                title={t('analytics.injury.form.missingPlayer.label')}
                placeholder={t('analytics.injury.form.missingPlayer.placeholder')}
                className="w-full px-3 py-2 rounded bg-gray-900/60 border border-gray-700 text-gray-100"
              />
            </div>
            <div>
              <label htmlFor="analytics-injurySeasonsBack" className="block text-xs uppercase tracking-widest text-gray-500 mb-2">
                {t('analytics.injury.form.seasonsBack.label')}
              </label>
              <input
                id="analytics-injurySeasonsBack"
                type="number"
                value={injurySeasonsBack}
                min={1}
                onChange={(event) => setInjurySeasonsBack(parseInt(event.target.value, 10) || 1)}
                aria-label={t('analytics.injury.form.seasonsBack.label')}
                title={t('analytics.injury.form.seasonsBack.label')}
                className="w-full px-3 py-2 rounded bg-gray-900/60 border border-gray-700 text-gray-100"
              />
            </div>
          </div>
          <button
            onClick={loadInjuryImpact}
            disabled={injuryLoading}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-white disabled:bg-gray-600"
          >
            {injuryLoading ? t('analytics.actions.loading') : t('analytics.injury.actions.analyze')}
          </button>

          {injuryLoading && (
            <div className="mt-6 space-y-3">
              <div className="skeleton h-20"></div>
              <div className="skeleton h-24"></div>
            </div>
          )}

          {injuryError && (
            <div className="mt-4 p-4 border border-red-500/30 bg-red-900/20 text-red-200 rounded">
              {injuryError}
            </div>
          )}

          {injuryImpact && (
            <div className="mt-6 space-y-4">
              <div className="glass-card p-4">
                <div className="text-sm text-gray-400">{t('analytics.injury.sections.teamImpact.title')}</div>
                <div className="text-xl text-white">{injuryImpact.team_impact?.description ?? t('common.na')}</div>
                <div className="text-sm text-gray-500 mt-1">
                  {t('analytics.injury.sections.teamImpact.pointsDifference')} {injuryImpact.team_impact?.points_difference ?? t('common.na')}
                </div>
                <div className="mt-4">
                  <Sparkline
                    values={[0, Math.abs(toNumber(injuryImpact.team_impact?.points_difference))]}
                    stroke="#fb7185"
                  />
                </div>
              </div>
              <div className="glass-card p-4">
                <div className="flex items-center justify-between text-sm text-gray-400 mb-2">
                  <span>{t('analytics.injury.sections.beneficiarySurge.title')}</span>
                  <span className="text-xs text-gray-500">{t('analytics.injury.sections.beneficiarySurge.helper')}</span>
                </div>
                <Sparkline
                  values={(injuryImpact.beneficiaries || []).slice(0, 5).map((b) => toNumber(b.percent_increase))}
                  stroke="#f59e0b"
                />
              </div>
              <div className="glass-card p-4">
                <div className="text-sm text-gray-400 mb-2">{t('analytics.injury.sections.beneficiaries.title')}</div>
                <div className="space-y-2">
                  {(injuryImpact.beneficiaries || []).slice(0, 5).map((benefit) => {
                    const percent = toNumber(benefit.percent_increase);
                    const max = Math.max(
                      ...((injuryImpact.beneficiaries || []).slice(0, 5).map((b) => toNumber(b.percent_increase))),
                      1
                    );
                    return (
                      <div key={benefit.player} className="space-y-2">
                        <div className="flex items-center justify-between text-gray-200 text-sm">
                          <span>{benefit.player}</span>
                          <span className="text-gray-400">
                            +{benefit.increase ?? 0} ({percent}%)
                          </span>
                        </div>
                        <progress
                          value={Math.min(percent, max)}
                          max={max}
                          className="h-2 w-full overflow-hidden rounded-full bg-white/10"
                        />
                      </div>
                    );
                  })}
                  {!injuryImpact.beneficiaries?.length && (
                    <div className="text-sm text-gray-500">{t('analytics.injury.sections.beneficiaries.empty')}</div>
                  )}
                </div>
              </div>
            </div>
          )}

          {!injuryImpact && !injuryLoading && !injuryError && (
            <div className="mt-6 rounded-xl border border-dashed border-white/10 p-6 text-sm text-gray-400">
              {t('analytics.injury.empty')}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Analytics;
