import { useEffect, useMemo, useState } from 'react';
import { Zap, BarChart3, FileText, Users, DollarSign, TrendingUp, Activity, UserCircle } from 'lucide-react';

import Dashboard from './components/Dashboard';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import LoginScreen from './components/LoginScreen';
import ReportsSection from './components/ReportsSection';
import AllTeams from './components/AllTeams';
import BettingRecommendations from './components/BettingRecommendations';
import LiveOdds from './components/LiveOdds';
import PlayersBrowser from './components/PlayersBrowser';
import Analytics from './components/Analytics';
import BullsAnalysis from './components/BullsAnalysis';
import { useI18n } from './i18n/useI18n';
import { AuthState, clearAuthState, getAuthState, initAuthListener, logout } from './services/auth';

const API_BASE =
  (typeof import.meta.env.VITE_API_BASE_URL === 'string' && import.meta.env.VITE_API_BASE_URL.trim() !== ''
    ? import.meta.env.VITE_API_BASE_URL.trim()
    : (
        typeof window !== 'undefined'
          ? `http://${window.location.hostname}:8000`
          : 'http://localhost:8000'
      ));

type Section = 'dashboard' | 'reports' | 'teams' | 'betting' | 'odds' | 'analytics' | 'players' | 'bulls';
type HealthResponse = { supabase_connected?: boolean };

function App() {
  const { t } = useI18n();
  const [auth, setAuth] = useState<AuthState | null>(() => getAuthState());
  const [activeSection, setActiveSection] = useState<Section>('dashboard');
  const [selectedGameId, setSelectedGameId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  
  const sidebarItems = [
    { id: 'dashboard', label: t('nav.dashboard'), icon: BarChart3 },
    { id: 'reports', label: t('nav.reports'), icon: FileText },
    { id: 'teams', label: t('nav.teams'), icon: Users },
    { id: 'betting', label: t('nav.betting'), icon: DollarSign },
    { id: 'odds', label: t('nav.odds'), icon: TrendingUp },
    { id: 'players', label: t('nav.players'), icon: UserCircle },
    { id: 'analytics', label: t('nav.analytics'), icon: Activity },
    { id: 'bulls', label: t('nav.bulls'), icon: Zap }
  ];
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [supabaseConnected, setSupabaseConnected] = useState<boolean | null>(null);
  const [backendCheckedAt, setBackendCheckedAt] = useState<Date | null>(null);

  const statusText = useMemo(() => {
    if (backendOnline === null) return t('app.status.checking');
    if (!backendOnline) return t('app.status.offline');
    if (supabaseConnected === null) return t('app.status.online');
    return supabaseConnected ? t('app.status.onlineData') : t('app.status.onlineNoData');
  }, [backendOnline, supabaseConnected, t]);

  useEffect(() => {
    let cancelled = false;

    const check = async () => {
      try {
        const resp = await fetch(`${API_BASE}/health`, { cache: 'no-store' });
        if (!resp.ok) throw new Error(`Health failed: ${resp.status}`);
        const data = (await resp.json()) as { supabase_connected?: boolean };
        if (cancelled) return;
        setBackendOnline(true);
        setSupabaseConnected(typeof data.supabase_connected === 'boolean' ? data.supabase_connected : null);
        setBackendCheckedAt(new Date());
      } catch {
        if (cancelled) return;
        setBackendOnline(false);
        setSupabaseConnected(null);
        setBackendCheckedAt(new Date());
      }
    };

    // initial + periodic polling
    check();
    const id = window.setInterval(check, 30_000);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, []);

  useEffect(() => {
    const handleAuthChange = (event: Event) => {
      const detail = (event as CustomEvent).detail as AuthState | null | undefined;
      setAuth(detail ?? getAuthState());
    };
    window.addEventListener('auth:changed', handleAuthChange);
    const { data } = initAuthListener();
    return () => {
      window.removeEventListener('auth:changed', handleAuthChange);
      data?.subscription?.unsubscribe();
    };
  }, []);

  const renderContent = () => {
    switch (activeSection) {
      case 'dashboard':
        return <Dashboard onViewOdds={(gameId: string) => { setSelectedGameId(gameId); setActiveSection('odds'); }} />;
      case 'reports':
        return <ReportsSection />;
      case 'teams':
        return <AllTeams />;
      case 'betting':
        return <BettingRecommendations />;
      case 'odds':
        return <LiveOdds selectedGameId={selectedGameId || undefined} />;
      case 'players':
        return <PlayersBrowser />;
      case 'analytics':
        return <Analytics />;
      case 'bulls':
        return <BullsAnalysis />;
      default:
        return <Dashboard />;
    }
  };

  if (!auth) {
    return <LoginScreen onLogin={setAuth} />;
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Background Pattern */}
      <div className="fixed inset-0 opacity-5">
        <div className="absolute inset-0 background-gradient"></div>
      </div>

      <div className="relative z-10 flex h-screen">
        {/* Mobile Overlay */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 z-30 bg-black/60 md:hidden"
            onClick={() => setSidebarOpen(false)}
            aria-hidden="true"
          />
        )}

        {/* Sidebar */}
        <div
          className={`fixed inset-y-0 left-0 z-40 transform transition-transform duration-300 md:static md:translate-x-0 ${
            sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
        >
          <Sidebar
            items={sidebarItems}
            activeSection={activeSection}
            onSectionChange={(section: string) => {
              setActiveSection(section as Section);
              setSidebarOpen(false);
            }}
          />
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden w-full">
          <Header 
            activeSection={activeSection}
            lastUpdate={lastUpdate}
            currentUser={auth?.username}
            onLogout={() => {
              logout().finally(() => {
                clearAuthState();
                setAuth(null);
              });
            }}
            onToggleSidebar={() => setSidebarOpen((prev) => !prev)}
            onRefresh={() => {
              setLastUpdate(new Date());
              // Trigger a quick status refresh on manual refresh
              fetch(`${API_BASE}/health`, { cache: 'no-store' })
                .then((r) => (r.ok ? r.json() : Promise.reject()))
                .then((d: HealthResponse) => {
                  setBackendOnline(true);
                  setSupabaseConnected(typeof d?.supabase_connected === 'boolean' ? d.supabase_connected : null);
                  setBackendCheckedAt(new Date());
                })
                .catch(() => {
                  setBackendOnline(false);
                  setSupabaseConnected(null);
                  setBackendCheckedAt(new Date());
                });
            }}
          />
          
          <main className="flex-1 overflow-auto p-6">
            {renderContent()}
          </main>
        </div>
      </div>

      {/* Backend Status Indicator (real health) */}
      <div className="fixed bottom-4 right-4 z-50">
        <div className="glass-card px-3 py-1.5 md:px-4 md:py-2 flex items-center space-x-2">
          <div
            className={`w-2 h-2 rounded-full ${
              backendOnline === null
                ? 'bg-gray-400'
                : backendOnline
                  ? (supabaseConnected === false ? 'bg-yellow-400' : 'bg-green-400')
                  : 'bg-red-400'
            }`}
          ></div>
          <span className="text-xs md:text-sm text-gray-300">{statusText}</span>
          {backendCheckedAt && (
            <span className="hidden md:inline text-xs text-gray-500">
              {t('app.status.checkedAt', { time: backendCheckedAt.toLocaleTimeString('en-US', { timeZone: 'America/Chicago' }) })}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
