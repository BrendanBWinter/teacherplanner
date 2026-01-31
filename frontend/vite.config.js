// =============================================================================
// vite.config.js - Vite Build Configuration
// =============================================================================
// This file configures the Vite development server and build process.
//
// KEY CONFIGURATION:
// - Proxy: Routes API calls to the backend server during development
// - This avoids CORS issues and mimics the production setup
// =============================================================================

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],

  // ---------------------------------------------------------------------------
  // Development Server Configuration
  // ---------------------------------------------------------------------------
  server: {
    // The port the dev server runs on
    port: 3000,

    // Proxy configuration for API calls
    // When the frontend makes a request to /api/*, Vite forwards it to the
    // backend server. This means:
    // - Frontend code can use "/api/settings" instead of "http://localhost:8000/settings"
    // - No CORS issues during development
    // - Same URL structure works in production when both are served together
    proxy: {
      '/api': {
        target: 'http://localhost:8000',  // Backend server address
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),  // Remove /api prefix
      },
    },
  },

  // ---------------------------------------------------------------------------
  // Build Configuration
  // ---------------------------------------------------------------------------
  build: {
    // Output directory for production build
    outDir: 'dist',

    // Generate source maps for debugging
    sourcemap: true,
  },
})
