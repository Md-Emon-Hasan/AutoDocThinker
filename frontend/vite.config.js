import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/health':      { target: 'http://localhost:8000', changeOrigin: true },
      '/domains':     { target: 'http://localhost:8000', changeOrigin: true },
      '/rag-modes':   { target: 'http://localhost:8000', changeOrigin: true },
      '/rag-profiles':{ target: 'http://localhost:8000', changeOrigin: true },
      '/rag':         { target: 'http://localhost:8000', changeOrigin: true },
      '/chat':        { target: 'http://localhost:8000', changeOrigin: true },
      '/ingest':      { target: 'http://localhost:8000', changeOrigin: true },
      '/index':       { target: 'http://localhost:8000', changeOrigin: true },
      '/admin':       { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
})
