import React, { useState, useEffect } from 'react';
import { DollarSign, Target, AlertTriangle, Star, Calculator, Percent } from 'lucide-react';
import { useI18n } from '../i18n/useI18n';
import { api } from '../services/api';

type ApiPick = {
  market: 'h2h';
  team: string;
  opponent: string;
  game_id: string;
  commence_time: string | null;
  best_price: number;
  best_book: string | null;
  consensus_prob: number;
  edge: number;
};

type ApiResponse = {
  generated_at: string;
  picks: ApiPick[];
  count: number;
};

type CategoryFilter = 'all' | 'featured' | 'general' | 'value';

const BettingRecommendations: React.FC = () => {
  const { t, locale } = useI18n();
  const [picks, setPicks] = useState<ApiPick[]>([]);
  const [bankroll, setBankroll] = useState(1000);
  const [selectedCategory, setSelectedCategory] = useState<CategoryFilter>('all');
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [kellyOdds, setKellyOdds] = useState<string>('');
  const [kellyProb, setKellyProb] = useState<string>('');
  const [kellyResult, setKellyResult] = useState<{ fraction: number; percentage: number; stake: number } | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setErrorMessage(null);

      try {
        const resp = await api.betting.getRecommendations() as ApiResponse;
        setPicks(Array.isArray(resp?.picks) ? resp.picks : []);
      } catch {
        setPicks([]);
        setErrorMessage(t('common.error'));
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [t]);

  const decimalToAmerican = (decimalOdds: number): number | null => {
    if (!Number.isFinite(decimalOdds) || decimalOdds <= 1) return null;
    if (decimalOdds >= 2) return Math.round((decimalOdds - 1) * 100);
    return -Math.round(100 / (decimalOdds - 1));
  };

  const formatAmerican = (american: number | null) => {
    if (american === null || !Number.isFinite(american)) return t('common.noData');
    return american > 0 ? `+${american}` : `${american}`;
  };

  const formatPercent = (value: number | null, digits: number = 1) => {
    if (value === null || !Number.isFinite(value)) return t('common.noData');
    return `${(value * 100).toFixed(digits)}%`;
  };

  const formatEdgePercent = (edge: number) => {
    if (!Number.isFinite(edge)) return t('common.noData');
    return `${(edge * 100).toFixed(1)}%`;
  };

  const parseCommence = (iso: string | null) => {
    if (!iso) return null;
    const d = new Date(iso);
    return Number.isNaN(d.getTime()) ? null : d;
  };

  const featuredIds = new Set(
    [...picks]
      .sort((a, b) => (b.edge ?? 0) - (a.edge ?? 0))
      .slice(0, 3)
      .map((p) => `${p.game_id}:${p.team}`)
  );

  const filteredPicks = (() => {
    if (selectedCategory === 'all') return picks;
    if (selectedCategory === 'value') return picks.filter((p) => (p.edge ?? 0) > 0);
    if (selectedCategory === 'featured') return picks.filter((p) => featuredIds.has(`${p.game_id}:${p.team}`));
    // general
    return picks.filter((p) => !featuredIds.has(`${p.game_id}:${p.team}`));
  })();

  const valuePicks = [...picks]
    .filter((p) => (p.edge ?? 0) > 0)
    .sort((a, b) => (b.edge ?? 0) - (a.edge ?? 0))
    .slice(0, 5);

  const calculateKelly = () => {
    const odds = parseFloat(kellyOdds);
    const prob = parseFloat(kellyProb) / 100;

    if (isNaN(odds) || isNaN(prob) || prob <= 0 || prob >= 1) {
      setKellyResult(null);
      return;
    }

    // Convert American odds to decimal
    const decimalOdds = odds > 0 ? (odds / 100) + 1 : (100 / Math.abs(odds)) + 1;

    // Kelly formula: (bp - q) / b
    // b = decimal odds - 1, p = probability, q = 1 - p
    const b = decimalOdds - 1;
    const q = 1 - prob;
    const kellyFraction = (b * prob - q) / b;

    // Only bet if positive expectation
    if (kellyFraction <= 0) {
      setKellyResult({ fraction: 0, percentage: 0, stake: 0 });
      return;
    }

    // Apply fractional Kelly (typically 0.25 or 0.5 for safety)
    const fractionalKelly = kellyFraction * 0.25; // Quarter Kelly for safety
    const stake = fractionalKelly * bankroll;

    setKellyResult({
      fraction: fractionalKelly,
      percentage: fractionalKelly * 100,
      stake: stake
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-green-400/30 border-t-green-400 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-400">{t('betting.loading')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Bankroll */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white flex items-center space-x-2">
          <DollarSign className="w-6 h-6 text-green-400" />
          <span>{t('betting.title')}</span>
        </h2>
        <div className="glass-card px-4 py-2">
          <div className="flex items-center space-x-4">
            <div className="text-sm text-gray-400">{t('betting.bankroll')}:</div>
            <div className="text-lg font-bold text-green-400">${bankroll}</div>
            <input
              type="number"
              value={bankroll}
              onChange={(e) => setBankroll(Number(e.target.value))}
              aria-label={t('betting.bankroll')}
              title={t('betting.bankroll')}
              className="w-20 bg-gray-800 border border-gray-600 rounded px-2 py-1 text-sm text-white"
            />
          </div>
        </div>
      </div>

      {/* Category Filter */}
      <div className="flex space-x-2">
        {(['all', 'featured', 'general', 'value'] as CategoryFilter[]).map((category) => (
          <button
            key={category}
            onClick={() => setSelectedCategory(category)}
            className={`px-4 py-2 rounded-lg text-sm transition-colors capitalize ${
              selectedCategory === category
                ? 'bg-blue-600/20 text-blue-400 border border-blue-400/30'
                : 'glass-card text-gray-300 hover:text-white hover:bg-white/10'
            }`}
          >
            {t(`betting.category.${category}`)}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Betting Recommendations */}
        <div className="xl:col-span-2">
          <div className="glass-card">
            <div className="p-6 border-b border-gray-700/50">
              <h3 className="text-xl font-bold text-white flex items-center justify-between" title={t('betting.tooltip.recommendedBets')}>
                <div className="flex items-center space-x-2">
                  <Target className="w-5 h-5 text-blue-400" />
                  <span>{t('betting.section.recommendedBets')}</span>
                </div>
                <span className="text-sm text-gray-400">{filteredPicks.length} {t('betting.section.betsSuffix')}</span>
              </h3>
            </div>
            <div className="p-6 space-y-4">
              {errorMessage && (
                <div className="glass-card p-4 border border-red-500/30 text-red-300">
                  {errorMessage}
                </div>
              )}

              {filteredPicks.length === 0 && !errorMessage ? (
                <div className="glass-card p-4 text-gray-400">{t('common.noData')}</div>
              ) : (
                filteredPicks.map((pick) => {
                  const commence = parseCommence(pick.commence_time);
                  const american = decimalToAmerican(pick.best_price);

                  const isFeatured = featuredIds.has(`${pick.game_id}:${pick.team}`);
                  const isValue = (pick.edge ?? 0) > 0;
                  const borderClass = isFeatured
                    ? 'border-purple-400/30 bg-purple-600/5'
                    : isValue
                      ? 'border-green-400/30 bg-green-600/5'
                      : 'border-blue-400/30 bg-blue-600/5';

                  return (
                    <div key={`${pick.game_id}:${pick.team}`} className={`glass-card p-4 border ${borderClass}`}>
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h4 className="text-lg font-semibold text-white">
                            {pick.team} {t('betting.pick.vs')} {pick.opponent}
                          </h4>
                          <div className="text-sm text-gray-400">
                            {t('betting.pick.market')}: {t('betting.pick.market.h2h')}
                            {commence ? ` • ${commence.toLocaleTimeString(locale, { timeZone: 'America/Chicago' })}` : ''}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-bold text-green-400">{formatAmerican(american)}</div>
                          <div className="text-xs text-gray-400">
                            {t('betting.pick.book')}: {pick.best_book || t('common.noData')}
                          </div>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                        <div className="bg-gray-800/30 rounded p-3">
                          <div className="text-xs text-gray-400">{t('betting.pick.edge')}</div>
                          <div className="text-white font-semibold">{formatEdgePercent(pick.edge)}</div>
                        </div>
                        <div className="bg-gray-800/30 rounded p-3">
                          <div className="text-xs text-gray-400">{t('betting.pick.consensusProb')}</div>
                          <div className="text-white font-semibold">{formatPercent(pick.consensus_prob, 1)}</div>
                        </div>
                        <div className="bg-gray-800/30 rounded p-3">
                          <div className="text-xs text-gray-400">{t('betting.pick.bestPrice')}</div>
                          <div className="text-white font-semibold">{pick.best_price.toFixed(3)}</div>
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* Value Bets & Tools */}
        <div className="space-y-6">
          {/* Value Bets */}
          <div className="glass-card">
            <div className="p-6 border-b border-gray-700/50">
              <h3 className="text-xl font-bold text-white flex items-center space-x-2" title={t('betting.tooltip.valueBets')}>
                <Percent className="w-5 h-5 text-green-400" />
                <span>{t('betting.section.valueBets')}</span>
              </h3>
            </div>
            <div className="p-6 space-y-3">
              {valuePicks.length === 0 ? (
                <div className="glass-card p-3 text-gray-400">{t('common.noData')}</div>
              ) : valuePicks.map((pick) => {
                const american = decimalToAmerican(pick.best_price);
                return (
                <div key={`${pick.game_id}:${pick.team}`} className="glass-card p-3 border border-green-400/20">
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-sm font-medium text-white">{pick.team} {t('betting.pick.mlShort')}</div>
                    <div className="text-green-400 font-bold">{formatEdgePercent(pick.edge)}</div>
                  </div>
                  <div className="text-xs text-gray-400 mb-2">{pick.team} {t('betting.pick.vs')} {pick.opponent}</div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-gray-400">{t('betting.value.book')}:</span> {formatAmerican(american)}
                    </div>
                    <div>
                      <span className="text-gray-400">{t('betting.value.fairProb')}:</span> {formatPercent(pick.consensus_prob, 1)}
                    </div>
                    <div>
                      <span className="text-gray-400">{t('betting.pick.book')}:</span> {pick.best_book || t('common.noData')}
                    </div>
                    <div>
                      <span className="text-gray-400">{t('betting.pick.bestPrice')}:</span> {pick.best_price.toFixed(3)}
                    </div>
                  </div>
                </div>
                );
              })}
            </div>
          </div>

          {/* Kelly Calculator */}
          <div className="glass-card">
            <div className="p-6 border-b border-gray-700/50">
              <h3 className="text-xl font-bold text-white flex items-center space-x-2" title={t('betting.tooltip.kellyCalculator')}>
                <Calculator className="w-5 h-5 text-purple-400" />
                <span>{t('betting.section.kellyCalculator')}</span>
              </h3>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">{t('betting.kelly.oddsLabel')}</label>
                  <input
                    type="number"
                    placeholder="-110"
                    value={kellyOdds}
                    onChange={(e) => setKellyOdds(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">{t('betting.kelly.winProbLabel')}</label>
                  <input
                    type="number"
                    placeholder="55"
                    value={kellyProb}
                    onChange={(e) => setKellyProb(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white"
                  />
                </div>
                <button 
                  onClick={calculateKelly}
                  className="w-full bg-purple-600 hover:bg-purple-700 text-white font-semibold py-2 px-4 rounded transition-colors"
                >
                  {t('betting.kelly.calculate')}
                </button>
                {kellyResult ? (
                <div className="text-center p-3 bg-purple-600/10 border border-purple-600/30 rounded">
                  <div className="text-sm text-gray-400">{t('betting.kelly.recommendedStake')}</div>
                  <div className="text-lg font-bold text-purple-400">
                    {kellyResult.percentage.toFixed(2)}% {t('betting.kelly.ofBankroll')}
                  </div>
                  <div className="text-sm text-gray-400 mt-1">
                    ${kellyResult.stake.toFixed(2)} {t('betting.kelly.from')} ${bankroll}
                  </div>
                  {kellyResult.fraction === 0 && (
                    <div className="text-xs text-red-400 mt-2">{t('betting.kelly.negativeExpectation')}</div>
                  )}
                </div>
                ) : (
                <div className="text-center p-3 bg-purple-600/10 border border-purple-600/30 rounded">
                  <div className="text-sm text-gray-400">{t('betting.kelly.enterToCalculate')}</div>
                </div>
                )}
              </div>
            </div>
          </div>

          {/* Betting Stats */}
          <div className="glass-card">
            <div className="p-6 border-b border-gray-700/50">
              <h3 className="text-xl font-bold text-white flex items-center space-x-2" title={t('betting.tooltip.sessionStats')}>
                <Star className="w-5 h-5 text-yellow-400" />
                <span>{t('betting.section.sessionStats')}</span>
              </h3>
            </div>
            <div className="p-6">
              <div className="glass-card p-4 text-gray-400">{t('common.noData')}</div>
            </div>
          </div>

          {/* Risk Management */}
          <div className="glass-card border-yellow-400/20">
            <div className="p-6 border-b border-gray-700/50">
              <h3 className="text-xl font-bold text-white flex items-center space-x-2" title={t('betting.tooltip.riskAlerts')}>
                <AlertTriangle className="w-5 h-5 text-yellow-400" />
                <span>{t('betting.section.riskAlerts')}</span>
              </h3>
            </div>
            <div className="p-6">
              <div className="glass-card p-4 text-gray-400">{t('common.noData')}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BettingRecommendations;
