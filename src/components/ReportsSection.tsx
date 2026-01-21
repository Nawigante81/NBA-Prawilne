import React, { useState, useEffect, useCallback } from 'react';
import { Calendar, Clock, TrendingUp, FileText, Download } from 'lucide-react';
import api from '../services/api';
import { useI18n } from '../i18n/useI18n';

interface Report {
  id: string;
  type: '750am' | '800am' | '1100am';
  title: string;
  generated: string;
  status: 'ready' | 'generating' | 'error';
  content?: Record<string, unknown>;
  contentError?: string;
}

const ReportsSection: React.FC = () => {
  const { t, locale } = useI18n();
  const trendLabelMap: Record<string, string> = {
    pace_trends: t('reports.trends.label.pace_trends'),
    offensive_efficiency: t('reports.trends.label.offensive_efficiency'),
    defensive_efficiency: t('reports.trends.label.defensive_efficiency'),
    three_point_shooting: t('reports.trends.label.three_point_shooting'),
    free_throw_trends: t('reports.trends.label.free_throw_trends'),
    ats_performance: t('reports.trends.label.ats_performance'),
    bulls: t('reports.trends.label.bulls'),
    focus_teams: t('reports.trends.label.focus_teams'),
    league_context: t('reports.trends.label.league_context'),
    betting_impact: t('reports.trends.label.betting_impact'),
    current: t('reports.trends.label.current'),
    avg: t('reports.trends.label.avg'),
    range: t('reports.trends.label.range'),
    trend: t('reports.trends.label.trend'),
    significance: t('reports.trends.label.significance'),
    ortg: t('reports.trends.label.ortg'),
    drtg: t('reports.trends.label.drtg'),
    pct: t('reports.trends.label.pct'),
    volume: t('reports.trends.label.volume'),
    attempts: t('reports.trends.label.attempts'),
    record: t('reports.trends.label.record'),
    home: t('reports.trends.label.home'),
    road: t('reports.trends.label.road'),
    combined: t('reports.trends.label.combined'),
    percentage: t('reports.trends.label.percentage'),
    rank: t('reports.trends.label.rank'),
    top: t('reports.trends.label.top'),
    bottom: t('reports.trends.label.bottom'),
    best: t('reports.trends.label.best'),
    worst: t('reports.trends.label.worst'),
    avg_ortg: t('reports.trends.label.avg_ortg'),
    avg_drtg: t('reports.trends.label.avg_drtg'),
    '7day_avg': t('reports.trends.label.7day_avg'),
    '7day_change': t('reports.trends.label.7day_change'),
  };

  const formatLabel = (value: string) => {
    if (!value) return value;
    if (trendLabelMap[value]) return trendLabelMap[value];
    const normalized = value.replace(/([a-z])([A-Z])/g, '$1_$2').toLowerCase();
    if (trendLabelMap[normalized]) return trendLabelMap[normalized];
    return value
      .replace(/_/g, ' ')
      .replace(/([a-z])([A-Z])/g, '$1 $2');
  };

  const isRatingKey = (key?: string) => {
    if (!key) return false;
    return /(^|_)(offrtg|defrtg|netrtg|ortg|drtg|rtg)(_|$)/i.test(key);
  };

  const formatInlineValue = (value: unknown, key?: string): string => {
    if (value === null || value === undefined) return '-';
    if (typeof value === 'number' && Number.isFinite(value)) {
      return isRatingKey(key) ? value.toFixed(1) : String(value);
    }
    if (typeof value === 'string' || typeof value === 'boolean') {
      return String(value);
    }
    if (Array.isArray(value)) {
      return value.map((item) => formatInlineValue(item, key)).join(', ');
    }
    if (typeof value === 'object') {
      return Object.entries(value as Record<string, unknown>)
        .map(([k, v]) => `${formatLabel(k)}: ${formatInlineValue(v, k)}`)
        .join(' | ');
    }
    return String(value);
  };

  const parseReportContent = (raw: unknown): { content?: Record<string, unknown>; error?: string } => {
    if (!raw) return {};
    if (typeof raw === 'string') {
      try {
        const parsed = JSON.parse(raw);
        return typeof parsed === 'object' && parsed !== null
          ? { content: parsed as Record<string, unknown> }
          : { error: 'invalid_json' };
      } catch {
        return { error: 'invalid_json' };
      }
    }
    if (typeof raw === 'object') {
      return { content: raw as Record<string, unknown> };
    }
    return { error: 'unsupported_content' };
  };

  const formatCompactValue = (value: unknown) => {
    if (typeof value === 'number' && Number.isFinite(value)) return value.toFixed(1);
    if (typeof value === 'string') {
      const parts = value.split(':');
      return parts.length > 1 ? parts[1].trim() : value;
    }
    return t('common.noData');
  };

  const renderTrendValue = (value: unknown, key?: string) => {
    if (value === null || value === undefined) {
      return <span className="text-gray-500">-</span>;
    }
    if (typeof value === 'number' && Number.isFinite(value)) {
      return <span className="text-white font-medium">{isRatingKey(key) ? value.toFixed(1) : String(value)}</span>;
    }
    if (typeof value === 'string' || typeof value === 'boolean') {
      return <span className="text-white font-medium">{String(value)}</span>;
    }
    if (Array.isArray(value)) {
      return (
        <div className="space-y-1 text-sm text-gray-200">
          {value.map((item, idx) => (
            <div key={idx}>{formatInlineValue(item, key)}</div>
          ))}
        </div>
      );
    }
    if (typeof value === 'object') {
      return (
        <div className="space-y-1 text-sm text-gray-200">
          {Object.entries(value as Record<string, unknown>).map(([k, v]) => (
            <div key={k}>
              <span className="text-gray-400">{formatLabel(k)}:</span>{' '}
              <span className="text-white">{formatInlineValue(v, k)}</span>
            </div>
          ))}
        </div>
      );
    }
    return <span className="text-white font-medium">{String(value)}</span>;
  };

  const asRecord = (value: unknown): Record<string, unknown> =>
    value && typeof value === 'object' ? (value as Record<string, unknown>) : {};

  const asString = (value: unknown, fallback = ''): string =>
    typeof value === 'string' ? value : fallback;

  const ensureRecordArray = (value: unknown): Record<string, unknown>[] =>
    Array.isArray(value) ? value.map(asRecord) : [];

  const ensureArray = <T,>(value: unknown): T[] => {
    return Array.isArray(value) ? (value as T[]) : [];
  };
  const [reports, setReports] = useState<Report[]>([]);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({});

  const fetchReports = useCallback(async () => {
    setLoading(true);
    
    try {
      const response = await api.reports.getSaved(20);
      const mapped: Report[] = (response.reports || []).map((row) => {
        const rowData = asRecord(row);
        const reportType = String(rowData.report_type || '');
        let type: Report['type'] | null = null;
        let title = t('reports.title.generic');

        if (reportType.startsWith('750am')) {
          type = '750am';
          title = t('reports.title.750am');
        } else if (reportType.startsWith('800am')) {
          type = '800am';
          title = t('reports.title.800am');
        } else if (reportType.startsWith('1100am')) {
          type = '1100am';
          title = t('reports.title.1100am');
        }

        const parsed = parseReportContent(rowData.content);
        const status: Report['status'] = parsed.error ? 'error' : (parsed.content ? 'ready' : 'error');

        return {
          id: String(rowData.id || ''),
          type: type || '750am',
          title,
          generated: asString(rowData.created_at, ''),
          status,
          content: parsed.content || undefined,
          contentError: parsed.error,
        };
      });

      setReports(mapped);
      const firstReady = mapped.find((r) => r.status === 'ready') || mapped[0] || null;
      setSelectedReport(firstReady);
    } catch (error) {
      console.error('Failed to load reports:', error);
      setReports([]);
      setSelectedReport(null);
    }
    
    setLoading(false);
  }, [t]);

  useEffect(() => {
    fetchReports();
  }, [fetchReports]);

  const getReportIcon = (type: string) => {
    switch (type) {
      case '750am': return TrendingUp;
      case '800am': return FileText;
      case '1100am': return Calendar;
      default: return FileText;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready': return 'text-green-400';
      case 'generating': return 'text-yellow-400';
      case 'error': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString(locale, {
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'America/Chicago',
    });
  };

  const ReportCard = ({ report }: { report: Report }) => {
    const Icon = getReportIcon(report.type);
    const content = asRecord(report.content);
    
    return (
      <div 
        className={`glass-card p-4 cursor-pointer transition-all duration-300 hover:bg-white/10 ${
          selectedReport?.id === report.id ? 'neon-border' : ''
        }`}
        onClick={() => setSelectedReport(report)}
      >
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-600/20 rounded-lg">
              <Icon className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h3 className="text-white font-semibold">{report.title}</h3>
              <p className="text-sm text-gray-400">
                {t('reports.generated')}: {formatTime(report.generated)}
              </p>
            </div>
          </div>
          <div className={`text-sm font-medium ${getStatusColor(report.status)}`}>
            {report.status === 'generating' && (
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 border-2 border-yellow-400/30 border-t-yellow-400 rounded-full animate-spin"></div>
                <span>{t('reports.status.generating')}</span>
              </div>
            )}
            {report.status === 'ready' && t('reports.status.ready')}
            {report.status === 'error' && t('reports.status.error')}
          </div>
        </div>

        {report.status === 'ready' && report.content && (
          <div className="space-y-2 text-sm text-gray-300">
            {report.type === '750am' && (
              <div>
                <div>{t('reports.summary.gamesAnalyzed')}: {asString(content.gamesAnalyzed, t('common.noData'))}</div>
                <div>{t('reports.summary.featuredTeamLastGame')}: {asString(asRecord(content.bullsAnalysis).lastGame, t('common.noData'))}</div>
              </div>
            )}
            {report.type === '800am' && (
              <div>
                <div>{t('reports.summary.yesterdayResults')}: {ensureArray<unknown>(content.yesterdayResults).length} {t('reports.summary.gamesSuffix')}</div>
                <div>{t('reports.summary.teamOffRtg')}: {formatCompactValue(asRecord(content.trends7Day).offRtg)}</div>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  const downloadReport = (report: Report) => {
    // Export as PDF (client-side)
    (async () => {
      const { jsPDF } = await import('jspdf');
      const doc = new jsPDF({ unit: 'pt', format: 'a4' });

      const marginX = 40;
      const marginY = 48;
      const pageWidth = doc.internal.pageSize.getWidth();
      const pageHeight = doc.internal.pageSize.getHeight();
      const usableWidth = pageWidth - marginX * 2;

      const addWrappedLine = (text: string, y: number, fontSize: number) => {
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(fontSize);
        const lines = doc.splitTextToSize(text, usableWidth);
        for (const line of lines) {
          if (y > pageHeight - marginY) {
            doc.addPage();
            y = marginY;
          }
          doc.text(String(line), marginX, y);
          y += fontSize + 4;
        }
        return y;
      };

      const addHeading = (text: string, y: number) => {
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(12);
        if (y > pageHeight - marginY) {
          doc.addPage();
          y = marginY;
        }
        doc.text(String(text), marginX, y);
        return y + 16;
      };

      const addKv = (key: string, value: unknown, y: number, indent: number = 0) => {
        const prefix = indent > 0 ? ' '.repeat(indent) : '';
        if (value === null || value === undefined) {
          return addWrappedLine(`${prefix}${key}:`, y, 10);
        }
        if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
          return addWrappedLine(`${prefix}${key}: ${String(value)}`, y, 10);
        }
        // For objects/arrays, print a compact JSON string (still readable, not full raw dump)
        try {
          const compact = JSON.stringify(value);
          return addWrappedLine(`${prefix}${key}: ${compact}`, y, 9);
        } catch {
          return addWrappedLine(`${prefix}${key}: [object]`, y, 9);
        }
      };

      const safeTitle = report.title || report.type;
      const generated = report.generated ? new Date(report.generated) : new Date();

      let y = marginY;
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(16);
      doc.text(String(safeTitle), marginX, y);
      y += 22;

      y = addWrappedLine(`${t('reports.generated')}: ${generated.toLocaleString(locale)}`, y, 10);
      y += 6;

      const content = asRecord(report.content);

      // Readable export per report type; avoid dumping raw JSON.
      if (report.type === '750am') {
        const results = ensureRecordArray(content.resultsVsLine ?? content.results_vs_line);
        if (results.length) {
          y = addHeading(t('reports.section.resultsVsClosingLine'), y);
          for (const r of results) {
            y = addWrappedLine(
              `- ${asString(r.team)}: ${asString(r.result)}, ATS: ${asString(r.ats)}, O/U: ${asString(r.ou)}`,
              y,
              10
            );
          }
          y += 8;
        }

        const trends = ensureArray<unknown>(content.topTrends ?? content.top_trends);
        if (trends.length) {
          y = addHeading(t('reports.section.topTrends'), y);
          for (const tline of trends) {
            y = addWrappedLine(`- ${String(tline)}`, y, 10);
          }
          y += 8;
        }

        const bulls = asRecord(content.bullsAnalysis ?? content.bulls_analysis);
        if (Object.keys(bulls).length) {
          y = addHeading(`${t('reports.section.teamPlayerAnalysis')} (Bulls)`, y);
          const lastGame = asString(bulls.lastGame);
          if (lastGame) {
            y = addWrappedLine(`Last Game: ${lastGame}`, y, 10);
          }
          const players = ensureRecordArray(bulls.keyPlayers ?? bulls.key_players);
          if (players.length) {
            for (const p of players) {
              y = addWrappedLine(
                `- ${asString(p.name)}: ${asString(p.stats)} (${asString(p.minutes)} min)`,
                y,
                10
              );
            }
          }
          y += 8;
        }
      } else if (report.type === '800am') {
        const exec = asRecord(content.executive_summary ?? content.executiveSummary);
        if (Object.keys(exec).length) {
          y = addHeading(t('reports.section.executiveSummary'), y);
          const headline = asString(exec.headline);
          if (headline) y = addWrappedLine(String(headline), y, 10);
          const takeaways = ensureArray<unknown>(exec.key_takeaways ?? exec.keyTakeaways);
          if (takeaways.length) {
            for (const item of takeaways) {
              y = addWrappedLine(`- ${String(item)}`, y, 10);
            }
          }
          const marketImpact = asString(exec.market_impact);
          const bullsHighlight = asString(exec.bulls_highlight);
          if (marketImpact) y = addWrappedLine(`Market impact: ${String(marketImpact)}`, y, 10);
          if (bullsHighlight) y = addWrappedLine(`Bulls highlight: ${String(bullsHighlight)}`, y, 10);
          y += 8;
        }

        const yesterday = ensureArray<unknown>(
          content.yesterday_performance ??
            content.yesterdayPerformance ??
            content.yesterdayResults ??
            content.yesterday_results
        );
        if (yesterday.length) {
          y = addHeading(t('reports.section.yesterdayResults'), y);
          for (const item of yesterday) {
            if (typeof item === 'string') {
              y = addWrappedLine(`- ${item}`, y, 10);
            } else {
              const row = asRecord(item);
              y = addWrappedLine(
                `- ${asString(row.game)} | ATS: ${asString(row.ats)} | O/U: ${asString(row.ou)}`,
                y,
                10
              );
              const keyStats = asString(row.key_stats);
              const bettingNotes = asString(row.betting_notes);
              if (keyStats) y = addWrappedLine(`  ${String(keyStats)}`, y, 9);
              if (bettingNotes) y = addWrappedLine(`  Notes: ${String(bettingNotes)}`, y, 9);
            }
          }
          y += 8;
        }

        const trends7 = content.seven_day_trends ?? content.sevenDayTrends ?? content.trends7Day;
        if (trends7 && typeof trends7 === 'object') {
          y = addHeading(t('reports.section.sevenDayTrends'), y);
          for (const [k, v] of Object.entries(trends7)) {
            if (v && typeof v === 'object' && !Array.isArray(v)) {
              y = addWrappedLine(String(k).replace(/_/g, ' '), y, 10);
              for (const [kk, vv] of Object.entries(v as Record<string, unknown>)) {
                y = addKv(String(kk), vv, y, 2);
              }
              y += 4;
            } else {
              y = addKv(String(k), v, y);
            }
          }
          y += 8;
        }

        const bullsForm = asRecord(
          content.bulls_form_analysis ?? content.bulls_current_form ?? content.bullsFormAnalysis ?? content.bullsPlayers
        );
        if (Object.keys(bullsForm).length) {
          y = addHeading(`${t('reports.section.teamPlayersForm')} (Bulls)`, y);
          const players = ensureRecordArray(bullsForm.player_form_l5 ?? bullsForm.playerFormL5 ?? bullsForm.players);
          if (players.length) {
            for (const p of players) {
              const name = asString(p.name);
              const stats = asString(p.stats) || asString(p.form);
              y = addWrappedLine(`- ${name}: ${stats}`, y, 10);
            }
          }
          y += 8;
        }
      } else if (report.type === '1100am') {
        const slate = asRecord(content.slate_overview ?? content.slateOverview);
        if (Object.keys(slate).length) {
          y = addHeading(t('reports.section.slateOverview'), y);
          for (const [k, v] of Object.entries(slate)) {
            y = addKv(String(k).replace(/_/g, ' '), v, y);
          }
          y += 8;
        }

        const injuries = asRecord(content.injury_intelligence ?? content.injuryIntelligence);
        if (Object.keys(injuries).length) {
          y = addHeading(t('reports.section.injuryIntelligence'), y);
          for (const [k, v] of Object.entries(injuries)) {
            if (Array.isArray(v)) {
              y = addWrappedLine(`${String(k).replace(/_/g, ' ')}:`, y, 10);
              for (const row of v) {
                if (typeof row === 'string') {
                  y = addWrappedLine(`- ${row}`, y, 10);
                } else {
                  const rowData = asRecord(row);
                  y = addWrappedLine(
                    `- ${asString(rowData.player)} (${asString(rowData.team)}) - ${asString(rowData.status || rowData.impact)}`,
                    y,
                    10
                  );
                }
              }
            } else {
              y = addKv(String(k).replace(/_/g, ' '), v, y);
            }
          }
          y += 8;
        }

        const matchups = ensureRecordArray(content.matchup_analysis ?? content.matchupAnalysis);
        if (matchups.length) {
          y = addHeading(t('reports.section.matchupAnalysis'), y);
          for (const m of matchups) {
            y = addWrappedLine(`- ${asString(m.game)} (${asString(m.time)})`, y, 10);
            const location = asString(m.location);
            if (location) y = addWrappedLine(`  ${location}`, y, 9);
          }
          y += 8;
        }
      } else {
        // Last resort: show a compact, readable summary rather than full pretty JSON.
        y = addHeading(t('reports.pdf.reportData'), y);
        const keys = Object.keys(content || {});
        y = addWrappedLine(`${t('reports.pdf.keys')}: ${keys.join(', ')}`, y, 10);
      }

      const iso = generated.toISOString().replace(/[:.]/g, '-');
      doc.save(`${report.type}-${iso}.pdf`);
    })().catch((e) => {
      console.error('PDF export failed:', e);
    });
  };

  const ReportDetails = ({ report }: { report: Report }) => {
    if (report.status !== 'ready' || !report.content) {
      return (
        <div className="text-center py-12">
          <div className="text-gray-400 mb-4">
            {report.status === 'generating'
              ? t('reports.empty.generating')
              : report.contentError
                ? t('reports.empty.noContent')
                : t('reports.empty.noContent')}
          </div>
        </div>
      );
    }

    const content = asRecord(report.content);

    return (
      <div className="space-y-6">
        {/* Report Header */}
        <div className="flex items-center justify-between">
          <h2
            className="text-2xl font-bold text-white"
            title={report.type === '800am' ? t('reports.tooltip.morningSummary') : undefined}
          >
            {report.title}
          </h2>
          <button 
            className="flex items-center space-x-2 glass-card px-4 py-2 hover:bg-white/10 transition-colors"
            onClick={() => downloadReport(report)}
            title={t('reports.exportPdf')}
          >
            <Download className="w-4 h-4" />
            <span>{t('reports.export')}</span>
          </button>
        </div>

        {/* 7:50 AM Report Content */}
        {report.type === '750am' && (
          <div className="space-y-6">
            <div className="glass-card p-6">
              <h3
                className="text-lg font-semibold text-white mb-4 flex items-center space-x-2 cursor-pointer"
                role="button"
                tabIndex={0}
                onClick={() => setOpenSections(s => ({ ...s, [`${report.id}:750:results`]: !(s[`${report.id}:750:results`] ?? true) }))}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    setOpenSections(s => ({ ...s, [`${report.id}:750:results`]: !(s[`${report.id}:750:results`] ?? true) }));
                  }
                }}
                title={t('reports.tooltip.resultsVsClosingLine')}
              >
                <TrendingUp className="w-5 h-5 text-green-400" />
                <span>{t('reports.section.resultsVsClosingLine')}</span>
              </h3>
              {(openSections[`${report.id}:750:results`] ?? true) && (
                <div className="space-y-3">
                  {ensureRecordArray(content.resultsVsLine ?? content.results_vs_line).map((result, index) => {
                    const team = asString(result.team, t('common.noData'));
                    const outcome = asString(result.result, '-');
                    const ats = asString(result.ats, '-');
                    const ou = asString(result.ou, '-');
                    return (
                      <div key={index} className="flex items-center justify-between p-3 bg-gray-800/30 rounded-lg">
                        <div className="font-semibold text-white">{team}</div>
                        <div className="flex items-center space-x-4">
                          <span className={`px-2 py-1 rounded text-xs ${
                            outcome === 'W' ? 'bg-green-600/20 text-green-400' : 'bg-red-600/20 text-red-400'
                          }`}>
                            {outcome}
                          </span>
                          <span className={`px-2 py-1 rounded text-xs ${
                            ats === 'COVER' ? 'bg-green-600/20 text-green-400' : 
                            ats === 'PUSH' ? 'bg-yellow-600/20 text-yellow-400' :
                            'bg-red-600/20 text-red-400'
                          }`}>
                            {ats}
                          </span>
                          <span className={`px-2 py-1 rounded text-xs ${
                            ou === 'OVER' ? 'bg-blue-600/20 text-blue-400' : 'bg-purple-600/20 text-purple-400'
                          }`}>
                            {ou}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            <div className="glass-card p-6">
              <h3
                className="text-lg font-semibold text-white mb-4 cursor-pointer"
                role="button"
                tabIndex={0}
                onClick={() => setOpenSections(s => ({ ...s, [`${report.id}:750:trends`]: !(s[`${report.id}:750:trends`] ?? true) }))}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    setOpenSections(s => ({ ...s, [`${report.id}:750:trends`]: !(s[`${report.id}:750:trends`] ?? true) }));
                  }
                }}
                title={t('reports.tooltip.topTrends')}
              >
                {t('reports.section.topTrends')}
              </h3>
              {(openSections[`${report.id}:750:trends`] ?? true) && (
                <div className="space-y-2">
                  {ensureArray<unknown>(content.topTrends ?? content.top_trends).map((trend: unknown, index: number) => (
                    <div key={index} className="flex items-center space-x-3">
                      <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                      <span className="text-gray-300">{formatInlineValue(trend)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="glass-card p-6">
              <h3
                className="text-lg font-semibold text-white mb-4 flex items-center space-x-2 cursor-pointer"
                role="button"
                tabIndex={0}
                onClick={() => setOpenSections(s => ({ ...s, [`${report.id}:750:bulls`]: !(s[`${report.id}:750:bulls`] ?? true) }))}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    setOpenSections(s => ({ ...s, [`${report.id}:750:bulls`]: !(s[`${report.id}:750:bulls`] ?? true) }));
                  }
                }}
                title={t('reports.tooltip.teamPlayerAnalysis')}
              >
                <span className="text-red-400">🐂</span>
                <span>{t('reports.section.teamPlayerAnalysis')}</span>
              </h3>
              {(openSections[`${report.id}:750:bulls`] ?? true) && (
                <div className="space-y-4">
                  <div className="text-gray-300 mb-4">
                    {t('reports.label.lastGame')}: {asString(asRecord(content.bullsAnalysis ?? content.bulls_analysis).lastGame, t('common.noData'))}
                  </div>
                  {ensureRecordArray(
                    asRecord(content.bullsAnalysis ?? content.bulls_analysis).keyPlayers ??
                      asRecord(content.bullsAnalysis ?? content.bulls_analysis).key_players
                  ).map((player, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-800/30 rounded-lg">
                      <div>
                        <div className="font-semibold text-white">{asString(player.name, t('common.noData'))}</div>
                        <div className="text-sm text-gray-400">{asString(player.stats, t('common.noData'))}</div>
                      </div>
                      <div className="text-right">
                        <div className="text-gray-300">{asString(player.minutes, t('common.noData'))} {t('reports.label.minutesShort')}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* 8:00 AM Report Content */}
        {report.type === '800am' && (
          <div className="space-y-6">
            <div className="glass-card p-6">
              <h3
                className="text-lg font-semibold text-white mb-4 cursor-pointer"
                role="button"
                tabIndex={0}
                onClick={() => setOpenSections(s => ({ ...s, [`${report.id}:800:yesterday`]: !(s[`${report.id}:800:yesterday`] ?? true) }))}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    setOpenSections(s => ({ ...s, [`${report.id}:800:yesterday`]: !(s[`${report.id}:800:yesterday`] ?? true) }));
                  }
                }}
                title={t('reports.tooltip.yesterdayResults')}
              >
                {t('reports.section.yesterdayResults')}
              </h3>
              {(openSections[`${report.id}:800:yesterday`] ?? true) && (
                <div className="space-y-2">
                  {ensureArray<unknown>(
                    content.yesterdayResults ||
                      content.yesterday_results ||
                      content.yesterdayPerformance ||
                      content.yesterday_performance
                  ).map((result, index) => {
                    const row = asRecord(result);
                    return (
                      <div key={index} className="p-3 bg-gray-800/30 rounded-lg text-gray-300">
                        {typeof result === 'string'
                          ? result
                          : `${asString(row.game)} - ATS: ${asString(row.ats)} - O/U: ${asString(row.ou)}`}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            <div className="glass-card p-6">
              <h3
                className="text-lg font-semibold text-white mb-4 cursor-pointer"
                role="button"
                tabIndex={0}
                onClick={() => setOpenSections(s => ({ ...s, [`${report.id}:800:trends`]: !(s[`${report.id}:800:trends`] ?? true) }))}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    setOpenSections(s => ({ ...s, [`${report.id}:800:trends`]: !(s[`${report.id}:800:trends`] ?? true) }));
                  }
                }}
                title={t('reports.tooltip.sevenDayTrends')}
              >
                {t('reports.section.sevenDayTrends')}
              </h3>
              {(openSections[`${report.id}:800:trends`] ?? true) && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(
                    content.trends7Day ||
                      content.sevenDayTrends ||
                      content.seven_day_trends ||
                      {}
                  ).map(([key, value]) => (
                    <div key={key} className="p-3 bg-gray-800/30 rounded-lg">
                      <div className="text-sm text-gray-400 capitalize">{formatLabel(key)}</div>
                      {renderTrendValue(value, key)}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="glass-card p-6">
              <h3
                className="text-lg font-semibold text-white mb-4 cursor-pointer"
                role="button"
                tabIndex={0}
                onClick={() => setOpenSections(s => ({ ...s, [`${report.id}:800:form`]: !(s[`${report.id}:800:form`] ?? true) }))}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    setOpenSections(s => ({ ...s, [`${report.id}:800:form`]: !(s[`${report.id}:800:form`] ?? true) }));
                  }
                }}
                title={t('reports.tooltip.teamPlayersForm')}
              >
                {t('reports.section.teamPlayersForm')}
              </h3>
              {(openSections[`${report.id}:800:form`] ?? true) && (
                <div className="space-y-3">
                  {ensureRecordArray(
                    asRecord(content.bullsPlayers).players ||
                      asRecord(content.bulls_form_analysis).player_form_l5 ||
                      asRecord(content.bulls_current_form).player_form_l5
                  ).map((player, index) => {
                    const trend = asString(player.trend);
                    const form = asString(player.form);
                    return (
                      <div key={index} className="flex items-center justify-between p-3 bg-gray-800/30 rounded-lg">
                        <div>
                          <div className="font-semibold text-white">{asString(player.name, t('common.noData'))}</div>
                          <div className="text-sm text-gray-400">{form || asString(player.stats, t('common.noData'))}</div>
                        </div>
                        <div className={`px-2 py-1 rounded text-xs ${
                          trend.toLowerCase().includes('excellent') ? 'bg-green-600/20 text-green-400' :
                          trend.toLowerCase().includes('solid') || form.toLowerCase().includes('solid') ? 'bg-blue-600/20 text-blue-400' :
                          'bg-yellow-600/20 text-yellow-400'
                        }`}>
                          {trend || form || '-'}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        )}

        {/* 11:00 AM Report Content */}
        {report.type === '1100am' && (
          <div className="space-y-6">
            <div className="glass-card p-6">
              <h3
                className="text-lg font-semibold text-white mb-4 cursor-pointer"
                role="button"
                tabIndex={0}
                onClick={() => setOpenSections(s => ({ ...s, [`${report.id}:1100:slate`]: !(s[`${report.id}:1100:slate`] ?? true) }))}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    setOpenSections(s => ({ ...s, [`${report.id}:1100:slate`]: !(s[`${report.id}:1100:slate`] ?? true) }));
                  }
                }}
                title={t('reports.tooltip.slateOverview')}
              >
                {t('reports.section.slateOverview')}
              </h3>
              {(openSections[`${report.id}:1100:slate`] ?? true) && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(content.slate_overview || content.slateOverview || {}).map(([key, value]) => (
                    <div key={key} className="p-3 bg-gray-800/30 rounded-lg">
                      <div className="text-sm text-gray-400 capitalize">{key.replace(/_/g, ' ')}</div>
                      <div className="text-white font-medium">
                        {typeof value === 'string' || typeof value === 'number' ? String(value) : JSON.stringify(value)}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="glass-card p-6">
              <h3
                className="text-lg font-semibold text-white mb-4 cursor-pointer"
                role="button"
                tabIndex={0}
                onClick={() => setOpenSections(s => ({ ...s, [`${report.id}:1100:injuries`]: !(s[`${report.id}:1100:injuries`] ?? true) }))}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    setOpenSections(s => ({ ...s, [`${report.id}:1100:injuries`]: !(s[`${report.id}:1100:injuries`] ?? true) }));
                  }
                }}
                title={t('reports.tooltip.injuryIntelligence')}
              >
                {t('reports.section.injuryIntelligence')}
              </h3>
              {(openSections[`${report.id}:1100:injuries`] ?? true) && (
                <div className="space-y-3">
                  {Object.entries(content.injury_intelligence || content.injuryIntelligence || {}).map(([key, value]) => (
                    <div key={key} className="p-3 bg-gray-800/30 rounded-lg">
                      <div className="text-sm text-gray-400 capitalize mb-2">{key.replace(/_/g, ' ')}</div>
                      {Array.isArray(value) ? (
                        <div className="space-y-2">
                          {value.map((row, idx) => {
                            const rowData = asRecord(row);
                            const player = asString(rowData.player);
                            const team = asString(rowData.team);
                            const status = asString(rowData.status);
                            const impact = asString(rowData.impact);
                            return (
                              <div key={idx} className="text-gray-300">
                                {typeof row === 'string'
                                  ? row
                                  : `${player} (${team})${status ? ` - ${status}` : ''}${impact ? ` - ${impact}` : ''}`}
                              </div>
                            );
                          })}
                        </div>
                      ) : (
                        <div className="text-gray-300">{typeof value === 'string' ? value : JSON.stringify(value)}</div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="glass-card p-6">
              <h3
                className="text-lg font-semibold text-white mb-4 cursor-pointer"
                role="button"
                tabIndex={0}
                onClick={() => setOpenSections(s => ({ ...s, [`${report.id}:1100:matchups`]: !(s[`${report.id}:1100:matchups`] ?? true) }))}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    setOpenSections(s => ({ ...s, [`${report.id}:1100:matchups`]: !(s[`${report.id}:1100:matchups`] ?? true) }));
                  }
                }}
                title={t('reports.tooltip.matchupAnalysis')}
              >
                {t('reports.section.matchupAnalysis')}
              </h3>
              {(openSections[`${report.id}:1100:matchups`] ?? true) && (
                <div className="space-y-2">
                  {ensureRecordArray(content.matchup_analysis || content.matchupAnalysis).map((m, idx) => (
                    <div key={idx} className="p-3 bg-gray-800/30 rounded-lg text-gray-300">
                      <div className="text-white font-semibold">{asString(m.game, t('common.noData'))}</div>
                      <div className="text-sm text-gray-400">
                        {asString(m.time)}
                        {asString(m.location) ? ` - ${asString(m.location)}` : ''}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-400/30 border-t-blue-400 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-400">{t('reports.loading')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
      {/* Reports List */}
      <div className="xl:col-span-1">
        <div className="glass-card">
          <div className="p-6 border-b border-gray-700/50">
            <h2 className="text-xl font-bold text-white flex items-center space-x-2" title={t('reports.tooltip.dailyReports')}>
              <Calendar className="w-5 h-5 text-blue-400" />
              <span>{t('reports.list.titleDailyReports')}</span>
            </h2>
            <p className="text-sm text-gray-400 mt-1">{t('reports.list.timezoneChicago')}</p>
            <button
              className="mt-4 w-full bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold py-2 px-4 rounded transition-colors disabled:bg-gray-600 disabled:cursor-not-allowed"
              onClick={async () => {
                setGenerating(true);
                try {
                  await Promise.all([
                    api.reports.get750Report(),
                    api.reports.get800Report(),
                    api.reports.get1100Report(),
                  ]);
                } catch (error) {
                  console.error('Failed to generate reports:', error);
                } finally {
                  await fetchReports();
                  setGenerating(false);
                }
              }}
              disabled={generating}
            >
              {generating ? t('reports.list.generatingReports') : t('reports.list.generateNow')}
            </button>
            <div className="mt-4 rounded-lg border border-gray-700/60 bg-gray-900/40 p-4">
              <div className="text-xs uppercase tracking-widest text-gray-500">{t('reports.setupChecklist.title')}</div>
              <div className="mt-3 space-y-2 text-sm text-gray-300">
                <div>[ ] {t('reports.setupChecklist.supabaseConnected')}</div>
                <div>[ ] {t('reports.setupChecklist.schedulerOn')}</div>
                <div>[ ] {t('reports.setupChecklist.scrapingEnabled')}</div>
                <div>[ ] {t('reports.setupChecklist.historicalImportDone')}</div>
              </div>
            </div>
          </div>
          <div className="p-6 space-y-4">
            {reports.map((report) => (
              <ReportCard key={report.id} report={report} />
            ))}
          </div>
        </div>
      </div>

      {/* Report Details */}
      <div className="xl:col-span-2">
        <div className="glass-card">
          {selectedReport ? (
            <div className="p-6">
              <ReportDetails report={selectedReport} />
            </div>
          ) : (
            <div className="p-12 text-center">
              <Clock className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-400 mb-2">{t('reports.selectReport.title')}</h3>
              <p className="text-gray-500">{t('reports.selectReport.subtitle')}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ReportsSection;
