import React, { useEffect, useState } from 'react';
import { LucideIcon } from 'lucide-react';
import { useI18n } from '../i18n/useI18n';
import { useApi } from '../services/api';

interface SidebarItem {
  id: string;
  label: string;
  icon: LucideIcon;
}

interface SidebarProps {
  items: SidebarItem[];
  activeSection: string;
  onSectionChange: (section: string) => void;
}

interface ApiGame {
  commence_time?: string;
}

const Sidebar: React.FC<SidebarProps> = ({ items, activeSection, onSectionChange }) => {
  const { t, locale } = useI18n();
  const apiHook = useApi();

  const [nextSlateCount, setNextSlateCount] = useState<number | null>(null);
  const [nextSlateTime, setNextSlateTime] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      const games = await apiHook.getTodayGames();
      if (cancelled) return;

      setNextSlateCount(games.length);

      const earliest = (games || [])
        .map((g: ApiGame) => g?.commence_time)
        .filter((v): v is string => typeof v === 'string' && v.trim() !== '')
        .map((s: string) => ({ s, ms: Date.parse(s) }))
        .filter((x) => Number.isFinite(x.ms))
        .sort((a, b) => a.ms - b.ms)[0];

      setNextSlateTime(
        earliest
          ? new Date(earliest.ms).toLocaleTimeString(locale, { hour: '2-digit', minute: '2-digit', timeZone: 'America/Chicago' })
          : null
      );
    };

    load();
    return () => {
      cancelled = true;
    };
  }, [apiHook, locale]);

  return (
    <div className="w-64 bg-gray-900/50 backdrop-blur-sm border-r border-gray-700/50 flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-gray-700/50">
        <div className="flex items-center justify-center">
          <div className="w-40 h-40 flex items-center justify-center">
            <img
              src="/logo.png"
              alt="MarekNBA Analytics logo"
              className="w-40 h-40 object-contain"
            />
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {items.map((item) => {
            const Icon = item.icon;
            const isActive = activeSection === item.id;
            
            return (
              <li key={item.id}>
                <button
                  onClick={() => onSectionChange(item.id)}
                  className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                    isActive
                      ? 'bg-blue-600/20 text-blue-400 border border-blue-400/20 shadow-lg'
                      : 'text-gray-300 hover:text-white hover:bg-gray-800/50'
                  }`}
                >
                  <Icon className={`w-5 h-5 ${isActive ? 'text-blue-400' : 'text-gray-400'}`} />
                  <span className="font-medium">{item.label}</span>
                  {isActive && (
                    <div className="ml-auto w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* League Status */}
      <div className="p-4 border-t border-gray-700/50">
        <div className="glass-card p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-300">{t('sidebar.leagueStatus')}</span>
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
          </div>
          <div className="text-xs text-gray-400">
            {nextSlateCount === null ? t('common.noData') : t('sidebar.nextSlate', { count: nextSlateCount })}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {nextSlateTime ? t('sidebar.tonight', { time: nextSlateTime }) : t('common.noData')}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
