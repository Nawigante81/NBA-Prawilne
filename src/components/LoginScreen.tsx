import React, { useState } from 'react';
import { AuthState, isSupabaseAuthEnabled, login, signUp } from '../services/auth';

type LoginScreenProps = {
  onLogin: (state: AuthState) => void;
};

const LoginScreen: React.FC<LoginScreenProps> = ({ onLogin }) => {
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [loading, setLoading] = useState(false);

  const supabaseAuthEnabled = isSupabaseAuthEnabled();

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    setNotice('');
    setLoading(true);
    try {
      if (mode === 'signup') {
        const result = await signUp(email.trim(), password);
        if (result.state) {
          onLogin(result.state);
        } else {
          setNotice('Account created. Check your email to confirm the address.');
        }
      } else {
        const auth = await login(email.trim(), password);
        onLogin(auth);
      }
    } catch {
      setError(mode === 'signup' ? 'Sign up failed. Check your email and password.' : 'Invalid username or password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex items-center justify-center px-6">
      <div className="absolute inset-0 opacity-20">
        <div className="absolute inset-0 background-gradient"></div>
      </div>

      <div className="relative z-10 w-full max-w-md">
        <div className="glass-card p-8 border border-gray-800/60">
          <div className="mb-6 text-center">
            <img
              src="/logo.png"
              alt="MarekNBA Analytics logo"
              className="mx-auto h-60 w-auto object-contain"
            />
            <h1 className="text-3xl font-semibold text-white">MarekNBA Analytics</h1>
            <p className="text-sm text-gray-400 mt-2">Sign in to continue</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-gray-300 mb-1" htmlFor="email">
                {supabaseAuthEnabled ? 'Email' : 'Username'}
              </label>
              <input
                id="email"
                type={supabaseAuthEnabled ? 'email' : 'text'}
                autoComplete={supabaseAuthEnabled ? 'email' : 'username'}
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="w-full rounded-md bg-gray-900/70 border border-gray-700/80 px-3 py-2 text-gray-100 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/60"
                placeholder={supabaseAuthEnabled ? 'name@example.com' : 'admin'}
                required
              />
            </div>

            <div>
              <label className="block text-sm text-gray-300 mb-1" htmlFor="password">
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="w-full rounded-md bg-gray-900/70 border border-gray-700/80 px-3 py-2 text-gray-100 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/60"
                placeholder="Enter your password"
                required
              />
            </div>

            {error && (
              <div className="text-sm text-red-300 bg-red-500/10 border border-red-500/20 px-3 py-2 rounded">
                {error}
              </div>
            )}

            {notice && (
              <div className="text-sm text-blue-200 bg-blue-500/10 border border-blue-500/20 px-3 py-2 rounded">
                {notice}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-md bg-blue-600/80 hover:bg-blue-600 text-white font-medium py-2 transition-colors disabled:opacity-60"
            >
              {loading ? (mode === 'signup' ? 'Creating account...' : 'Signing in...') : (mode === 'signup' ? 'Create account' : 'Sign in')}
            </button>

            {supabaseAuthEnabled && (
              <button
                type="button"
                onClick={() => {
                  setMode((prev) => (prev === 'login' ? 'signup' : 'login'));
                  setError('');
                  setNotice('');
                }}
                className="w-full text-sm text-gray-400 hover:text-gray-200 transition-colors"
              >
                {mode === 'signup' ? 'Already have an account? Sign in' : 'Need an account? Create one'}
              </button>
            )}
          </form>
        </div>
      </div>
    </div>
  );
};

export default LoginScreen;
