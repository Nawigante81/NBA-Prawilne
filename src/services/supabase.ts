import { createClient } from '@supabase/supabase-js';

const supabaseUrl = (typeof import.meta.env.VITE_SUPABASE_URL === 'string' && import.meta.env.VITE_SUPABASE_URL.trim())
  ? import.meta.env.VITE_SUPABASE_URL.trim()
  : '';

const supabaseAnonKey = (typeof import.meta.env.VITE_SUPABASE_ANON_KEY === 'string' && import.meta.env.VITE_SUPABASE_ANON_KEY.trim())
  ? import.meta.env.VITE_SUPABASE_ANON_KEY.trim()
  : '';

const authMode = (typeof import.meta.env.VITE_AUTH_MODE === 'string' && import.meta.env.VITE_AUTH_MODE.trim())
  ? import.meta.env.VITE_AUTH_MODE.trim().toLowerCase()
  : '';

export const supabaseEnabled = authMode !== 'basic' && Boolean(supabaseUrl && supabaseAnonKey);

export const supabase = supabaseEnabled
  ? createClient(supabaseUrl, supabaseAnonKey, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
      },
    })
  : null;
