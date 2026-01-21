import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    exclude: ['lucide-react'],
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          react: ['react', 'react-dom'],
          lucide: ['lucide-react'],
          charts: ['recharts'],
        },
      },
    },
    sourcemap: false,
    minify: 'terser',
    target: 'es2015',
  },
  server: {
    host: '0.0.0.0',
    port: 8080,
    strictPort: true,
    allowedHosts: ['mareknba.pl', 'api.mareknba.pl'],
    watch: {
      ignored: [
        '**/backend/.venv/**',
        '**/backend/venv/**',
        '**/dist/**',
        '**/logs/**',
      ],
    },
  },
  preview: {
    host: '0.0.0.0',
    port: 8080,
    strictPort: true,
    allowedHosts: ['mareknba.pl', 'api.mareknba.pl'],
  },
});
