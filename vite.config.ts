import { defineConfig } from 'vite';

export default defineConfig({
  // Względna baza: build działa spod podścieżki (GitHub Pages: dubel.dev/estadio/)
  base: './',
  server: {
    port: 3000,
    open: false,
    host: true
  },
  build: {
    target: 'esnext'
  }
});
