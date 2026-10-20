import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// GitHub Pages: the built site goes to ../docs (Settings → Pages → Branch: main, Folder: /docs).
// base './' keeps every asset path relative, so the site works at https://<id>.github.io/<repo>/.
export default defineConfig({
  base: './',
  plugins: [react()],
  build: {
    outDir: '../docs',
    emptyOutDir: true,
    chunkSizeWarningLimit: 900,
  },
  test: {
    environment: 'node',
    include: ['src/**/*.test.ts'],
  },
} as any);
