import path from 'node:path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // Admin token lives in the repo-root .env alongside the backend's
  // ADMIN_TOKEN, so both sides read the same shared secret.
  envDir: path.resolve(__dirname, '..'),
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/health':      { target: 'http://localhost:8010', changeOrigin: true },
      '/domains':     { target: 'http://localhost:8010', changeOrigin: true },
      '/rag-modes':   { target: 'http://localhost:8010', changeOrigin: true },
      '/rag-profiles':{ target: 'http://localhost:8010', changeOrigin: true },
      '/rag':         { target: 'http://localhost:8010', changeOrigin: true },
      '/chat':        { target: 'http://localhost:8010', changeOrigin: true },
      '/ingest':      { target: 'http://localhost:8010', changeOrigin: true },
      '/index':       { target: 'http://localhost:8010', changeOrigin: true },
      '/admin':       { target: 'http://localhost:8010', changeOrigin: true },
      '/governance':  { target: 'http://localhost:8010', changeOrigin: true },
      '/hitl':        { target: 'http://localhost:8010', changeOrigin: true },
      '/memory':      { target: 'http://localhost:8010', changeOrigin: true },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/setupTests.js',
  },
})
