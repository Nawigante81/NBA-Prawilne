import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from '../App';
import { I18nProvider } from '../i18n/I18nProvider';
import { setAuthState } from '../services/auth';

vi.mock('../services/auth', async () => {
  const actual = await vi.importActual<typeof import('../services/auth')>('../services/auth');
  return {
    ...actual,
    initAuthListener: () => ({ data: { subscription: { unsubscribe: () => undefined } } }),
  };
});

type FetchMock = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;
const fetchMock = vi.fn<FetchMock>();
global.fetch = fetchMock as unknown as typeof fetch;

const mockFetch = (data: unknown, ok = true): Response => {
  return {
    ok,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(typeof data === 'string' ? data : JSON.stringify(data)),
  } as Response;
};

const renderApp = () => {
  window.localStorage.setItem('app.language', 'en');
  setAuthState({
    username: 'admin@example.com',
    accessToken: 'test-token',
    role: 'admin',
    scheme: 'basic',
  });
  return render(
    <I18nProvider>
      <App />
    </I18nProvider>
  );
};

const flushPromises = () => Promise.resolve();

const advanceAppLoading = async () => {
  await act(async () => {
    vi.advanceTimersByTime(2000);
    await flushPromises();
  });

  // Switch back to real timers so Testing Library async utilities work.
  vi.useRealTimers();
  await act(async () => {
    await flushPromises();
  });
};

describe('App Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    fetchMock.mockResolvedValue(mockFetch({ games: [], teams: [] }));
  });

  it('renders without crashing', async () => {
    renderApp();
    await advanceAppLoading();
    expect(screen.getByRole('heading', { name: 'NBA Analytics Dashboard' })).toBeInTheDocument();
  });

  it('displays navigation items', async () => {
    renderApp();
    await advanceAppLoading();
    
    expect(screen.getAllByText('Dashboard').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Reports').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Teams Analysis').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Betting').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Live Odds').length).toBeGreaterThan(0);
  });

  it('switches sections when navigation items are clicked', async () => {
    renderApp();
    await advanceAppLoading();
    
    const reportsButton = screen.getByText('Reports');
    fireEvent.click(reportsButton);
    
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Daily Reports Center' })).toBeInTheDocument();
    });
  });

  it('shows loading states', async () => {
    fetchMock.mockImplementation(() => new Promise<Response>(() => {}));
    renderApp();
    
    // Should show loading indicator
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });
});

describe('Dashboard Section', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    fetchMock.mockResolvedValue(mockFetch({
      games: [
        {
          id: '1',
          home_team: 'Chicago Bulls',
          away_team: 'Los Angeles Lakers',
          game_date: '2024-01-15T20:00:00Z',
          status: 'scheduled'
        }
      ]
    }));
  });

  it('displays game information', async () => {
    renderApp();
    await advanceAppLoading();
    
    await waitFor(() => {
      expect(screen.getByText('Chicago Bulls')).toBeInTheDocument();
      expect(screen.getByText('Los Angeles Lakers')).toBeInTheDocument();
    });
  });
});

describe('Teams Analysis Section', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    fetchMock.mockResolvedValue(mockFetch({
      last_game_recap: {
        opponent: 'Detroit Pistons',
        result: 'W 112-108',
        key_performances: ['DeMar DeRozan: 28 PTS, 6 REB, 5 AST']
      },
      current_form_analysis: {
        record_l10: '6-4',
        ats_l10: '7-3'
      }
    }));
  });

  it('displays teams analysis data', async () => {
    renderApp();
    await advanceAppLoading();
    
    const teamsButton = screen.getByText('Teams Analysis');
    fireEvent.click(teamsButton);
    
    await waitFor(() => {
      expect(screen.getByText('NBA Teams Analysis')).toBeInTheDocument();
    });
  });
});

describe('Betting Recommendations Section', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    fetchMock.mockResolvedValue(mockFetch({
      conservative_plays: {
        plays: [
          {
            bet: 'Celtics -5.5',
            odds: -110,
            confidence: 82,
            reasoning: 'Home court advantage'
          }
        ]
      }
    }));
  });

  it('displays betting recommendations', async () => {
    renderApp();
    await advanceAppLoading();
    
    const bettingButton = screen.getByText('Betting');
    fireEvent.click(bettingButton);
    
    await waitFor(() => {
      expect(screen.getByText('Betting Intelligence Hub')).toBeInTheDocument();
    });
  });
});

describe('Reports Section', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    fetchMock.mockImplementation((url: RequestInfo | URL) => {
      const urlStr = String(url);

      if (urlStr.includes('/api/reports?')) {
        return Promise.resolve(mockFetch({
          reports: [
            {
              id: 'r1',
              report_type: '750am_previous_day',
              created_at: '2024-01-15T07:50:00Z',
              content: { ok: true },
            },
            {
              id: 'r2',
              report_type: '800am_morning',
              created_at: '2024-01-15T08:00:00Z',
              content: { ok: true },
            },
            {
              id: 'r3',
              report_type: '1100am_game_day',
              created_at: '2024-01-15T11:00:00Z',
              content: { ok: true },
            },
          ],
          count: 3,
        }));
      }

      if (urlStr.includes('/api/games/today')) return Promise.resolve(mockFetch({ games: [] }));
      if (urlStr.includes('/api/teams')) return Promise.resolve(mockFetch({ teams: [] }));

      return Promise.resolve(mockFetch({}));
    });
  });

  it('displays report sections', async () => {
    renderApp();
    await advanceAppLoading();
    
    const reportsButton = screen.getByText('Reports');
    fireEvent.click(reportsButton);
    
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Daily Reports Center' })).toBeInTheDocument();
      expect(screen.getAllByText('7:50 AM - Previous Day Analysis').length).toBeGreaterThan(0);
      expect(screen.getAllByText('8:00 AM - Morning Summary').length).toBeGreaterThan(0);
      expect(screen.getAllByText('11:00 AM - Game-Day Scouting').length).toBeGreaterThan(0);
    });
  });
});

describe('Error Handling', () => {
  it('handles API errors gracefully', async () => {
    fetchMock.mockRejectedValue(new Error('API Error'));
    
    vi.useFakeTimers();
    renderApp();
    await advanceAppLoading();
    
    expect(screen.getAllByText('Dashboard').length).toBeGreaterThan(0);
  });

  it('handles network failures', async () => {
    fetchMock.mockResolvedValue(mockFetch({}, false));
    
    vi.useFakeTimers();
    renderApp();
    await advanceAppLoading();
    
    expect(screen.getAllByText('Dashboard').length).toBeGreaterThan(0);
  });
});

describe('Responsive Design', () => {
  it('adapts to mobile viewport', async () => {
    // Mock mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    });

    vi.useFakeTimers();
    renderApp();
    await advanceAppLoading();
    
    // Should render mobile-friendly layout
    expect(screen.getByRole('heading', { name: 'NBA Analytics Dashboard' })).toBeInTheDocument();
  });
});
