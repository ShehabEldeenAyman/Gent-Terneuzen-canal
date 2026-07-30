import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
// https://vite.dev/config/
export default defineConfig({
  server: {
    allowedHosts: [
      'ed-pretelephone-unpleasantly.ngrok-free.dev'
    ]
  },
  plugins: [react(),tailwindcss()],
  worker: {
    format: 'es'
  },
  optimizeDeps: {
    // This prevents Vite from trying to pre-bundle the heavy pyodide files
    exclude: ['react-py']
  }

});
