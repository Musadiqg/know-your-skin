import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Use base: './' so assets resolve on GitHub Pages (project or user site) without extra config.
// If you use a custom domain at repo root, './' still works.
export default defineConfig({
  plugins: [react()],
  base: './',
})
