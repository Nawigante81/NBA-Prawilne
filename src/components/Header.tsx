import React, { useState } from 'react';
import { Bell, RefreshCw, Settings, Users, Menu } from 'lucide-react';
import { useI18n } from '../i18n/useI18n';

interface HeaderProps {
  activeSection: string;
  lastUpdate: Date;
  onRefresh: () => void;
  currentUser?: string | null;
  onLogout?: () => void;
  onToggleSidebar?: () => void;
}

const Header: React.FC<HeaderProps> = ({
  activeSection,
  lastUpdate,
  onRefresh,
  currentUser,
  onLogout,
  onToggleSidebar,
}) => {
  const { language, setLanguage, locale, t, supportedLanguages } = useI18n();
  const [showNotifications, setShowNotifications] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showProfile, setShowProfile] = useState(false);

  // Notifications are not implemented in backend yet; do not show demo/sample items.
  const notifications: string[] = [];
  const getSectionTitle = (section: string) => {
    switch (section) {
      case 'dashboard': return t('header.section.dashboard');
      case 'reports': return t('header.section.reports');
      case 'teams': return t('header.section.teams');
      case 'betting': return t('header.section.betting');
      case 'odds': return t('header.section.odds');
      case 'players': return t('header.section.players');
      case 'analytics': return t('header.section.analytics');
      default: return t('header.section.default');
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString(locale, {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      timeZone: 'America/Chicago',
    });
  };

  return (
    <header className="bg-gray-900/30 backdrop-blur-sm border-b border-gray-700/50 px-6 py-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">{getSectionTitle(activeSection)}</h1>
          <p className="text-gray-400 text-sm mt-1">
            {t('header.lastUpdated')}: {formatTime(lastUpdate)} CT
          </p>
        </div>

        <div className="flex items-center space-x-4">
          {/* Mobile Menu */}
          {onToggleSidebar && (
            <button
              onClick={onToggleSidebar}
              className="glass-card p-2 hover:bg-white/10 transition-colors duration-200 md:hidden"
              title="Menu"
              aria-label="Toggle sidebar"
            >
              <Menu className="w-5 h-5 text-gray-400 hover:text-white" />
            </button>
          )}
          {/* Language Switch */}
          <div className="flex items-center space-x-2 glass-card px-3 py-2">
            <span className="text-sm text-gray-400">{t('header.language')}:</span>
            <div className="flex items-center">
              {supportedLanguages.map((lng) => (
                <button
                  key={lng.id}
                  type="button"
                  onClick={() => setLanguage(lng.id)}
                  className={`px-2 py-1 text-xs rounded-md transition-colors duration-200 ${
                    language === lng.id
                      ? 'bg-blue-600/20 text-blue-300 border border-blue-400/30'
                      : 'text-gray-300 hover:text-white hover:bg-white/10'
                  }`}
                >
                  {lng.label}
                </button>
              ))}
            </div>
          </div>

          {/* Live Status */}
          <div className="flex items-center space-x-2 glass-card px-3 py-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span className="text-sm text-gray-300">{t('app.status.liveData')}</span>
          </div>

          {/* Refresh Button */}
          <button
            onClick={onRefresh}
            className="glass-card p-2 hover:bg-white/10 transition-colors duration-200"
            title={t('header.refreshData')}
          >
            <RefreshCw className="w-5 h-5 text-gray-400 hover:text-white" />
          </button>

          {/* Notifications */}
          <button 
            className="glass-card p-2 hover:bg-white/10 transition-colors duration-200 relative"
            onClick={() => {
              setShowNotifications(v => !v);
              setShowSettings(false);
              setShowProfile(false);
            }}
            title={t('header.notifications')}
          >
            <Bell className="w-5 h-5 text-gray-400 hover:text-white" />
            {notifications.length > 0 && (
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full"></div>
            )}
          </button>
          {showNotifications && (
            <div className="absolute right-28 top-16 z-50 w-80 glass-card p-4 border border-gray-700/50">
              <div className="text-sm font-semibold text-white mb-2">{t('header.notifications')}</div>
              <div className="space-y-2 text-sm">
                {notifications.length > 0 ? (
                  notifications.map((msg, idx) => (
                    <div key={idx} className="p-2 bg-gray-800/50 rounded">{msg}</div>
                  ))
                ) : (
                  <div className="p-2 bg-gray-800/50 rounded text-gray-400">{t('common.noData')}</div>
                )}
              </div>
              <div className="mt-3 text-right">
                <button className="text-xs text-gray-400 hover:text-white" onClick={() => setShowNotifications(false)}>{t('header.close')}</button>
              </div>
            </div>
          )}

          {/* Settings */}
          <button 
            className="glass-card p-2 hover:bg-white/10 transition-colors duration-200"
            onClick={() => {
              setShowSettings(v => !v);
              setShowNotifications(false);
              setShowProfile(false);
            }}
            title={t('header.settings')}
          >
            <Settings className="w-5 h-5 text-gray-400 hover:text-white" />
          </button>
          {showSettings && (
            <div className="absolute right-16 top-16 z-50 w-72 glass-card p-4 border border-gray-700/50">
              <div className="text-sm font-semibold text-white mb-3">{t('header.quickSettings')}</div>
              <div className="text-sm text-gray-400 py-2">{t('common.noData')}</div>
              <div className="mt-3 text-right">
                <button className="text-xs text-gray-400 hover:text-white" onClick={() => setShowSettings(false)}>{t('header.close')}</button>
              </div>
            </div>
          )}

          {/* User Profile */}
          <button 
            className="flex items-center space-x-2 glass-card px-3 py-2 hover:bg-white/10 transition-colors duration-200"
            onClick={() => {
              setShowProfile(v => !v);
              setShowNotifications(false);
              setShowSettings(false);
            }}
            title={t('header.profile')}
          >
            <Users className="w-5 h-5 text-gray-400" />
            <span className="text-sm text-gray-300">{currentUser || t('header.analyst')}</span>
          </button>
          {showProfile && (
            <div className="absolute right-4 top-16 z-50 w-56 glass-card p-2 border border-gray-700/50">
              <div className="px-3 py-2 text-sm text-gray-400">{currentUser || t('header.analyst')}</div>
              {onLogout && (
                <button
                  className="w-full text-left px-3 py-2 rounded hover:bg-white/10 text-sm text-red-300"
                  onClick={() => {
                    setShowProfile(false);
                    onLogout();
                  }}
                >
                  Sign out
                </button>
              )}
              <button className="w-full text-left px-3 py-2 rounded hover:bg-white/10 text-sm" onClick={() => setShowProfile(false)}>{t('header.close')}</button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;
