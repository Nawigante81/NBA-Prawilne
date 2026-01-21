import { supabase, supabaseEnabled } from './supabase';

const API_BASE =
  (typeof import.meta.env.VITE_API_BASE_URL === 'string' && import.meta.env.VITE_API_BASE_URL.trim() !== ''
    ? import.meta.env.VITE_API_BASE_URL.trim()
    : (
        typeof window !== 'undefined'
          ? `http://${window.location.hostname}:8000`
          : 'http://localhost:8000'
      ));

const AUTH_STORAGE_KEY = 'app.auth';

export type AuthState = {
  username: string;
  accessToken: string;
  role?: string;
  scheme?: 'bearer' | 'basic';
};

export type SignUpResult = {
  state: AuthState | null;
  needsEmailConfirmation: boolean;
};

export function getAuthState(): AuthState | null {
  try {
    const raw = window.localStorage.getItem(AUTH_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as AuthState;
    if (!parsed?.username || !parsed?.accessToken) return null;
    return parsed;
  } catch {
    return null;
  }
}

export function setAuthState(state: AuthState) {
  window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(state));
  window.dispatchEvent(new CustomEvent('auth:changed', { detail: state }));
}

export function clearAuthState() {
  window.localStorage.removeItem(AUTH_STORAGE_KEY);
  window.dispatchEvent(new CustomEvent('auth:changed', { detail: null }));
}

export function getAuthHeader(): Record<string, string> {
  const auth = getAuthState();
  if (!auth?.accessToken) return {};
  if (auth.scheme === 'basic') {
    return { Authorization: `Basic ${auth.accessToken}` };
  }
  return { Authorization: `Bearer ${auth.accessToken}` };
}

export async function login(email: string, password: string): Promise<AuthState> {
  if (supabaseEnabled && supabase) {
    const { data, error } = await supabase.auth.signInWithPassword({ email, password });
    if (error || !data?.session || !data?.user) {
      throw new Error(error?.message || 'Login failed');
    }
    const state: AuthState = {
      username: data.user.email || data.user.id,
      role: data.user.role || 'user',
      accessToken: data.session.access_token,
      scheme: 'bearer',
    };
    setAuthState(state);
    return state;
  }

  const basicToken = toBase64(`${email}:${password}`);
  const response = await fetch(`${API_BASE}/api/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Basic ${basicToken}`,
    },
    body: JSON.stringify({ username: email, password }),
  });

  if (!response.ok) {
    throw new Error('Login failed');
  }

  const data = (await response.json()) as { username?: string; role?: string };
  const state: AuthState = {
    username: data.username || email,
    role: data.role || 'user',
    accessToken: basicToken,
    scheme: 'basic',
  };
  setAuthState(state);
  return state;
}

export async function signUp(email: string, password: string): Promise<SignUpResult> {
  if (!supabaseEnabled || !supabase) {
    throw new Error('Sign up is not available');
  }
  const { data, error } = await supabase.auth.signUp({ email, password });
  if (error || !data?.user) {
    throw new Error(error?.message || 'Sign up failed');
  }

  if (data.session) {
    const state: AuthState = {
      username: data.user.email || data.user.id,
      role: data.user.role || 'user',
      accessToken: data.session.access_token,
    };
    setAuthState(state);
    return { state, needsEmailConfirmation: false };
  }

  return { state: null, needsEmailConfirmation: true };
}

export async function logout() {
  if (supabaseEnabled && supabase) {
    await supabase.auth.signOut();
  }
  clearAuthState();
}

export function initAuthListener() {
  if (!supabaseEnabled || !supabase) {
    return { data: { subscription: { unsubscribe: () => undefined } } };
  }
  return supabase.auth.onAuthStateChange((_event, session) => {
    if (session?.access_token && session?.user) {
      setAuthState({
        username: session.user.email || session.user.id,
        role: session.user.role || 'user',
        accessToken: session.access_token,
        scheme: 'bearer',
      });
    } else {
      clearAuthState();
    }
  });
}

export function isSupabaseAuthEnabled() {
  return supabaseEnabled;
}

function toBase64(value: string): string {
  try {
    return window.btoa(value);
  } catch {
    const encoder = new TextEncoder();
    const bytes = encoder.encode(value);
    let binary = '';
    for (const byte of bytes) {
      binary += String.fromCharCode(byte);
    }
    return window.btoa(binary);
  }
}
