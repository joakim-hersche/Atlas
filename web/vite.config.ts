import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

// base './' keeps every asset and data URL relative, so the build works from any subpath
// (GitHub Pages project site, a preview host, or a local folder server).
export default defineConfig({
  base: './',
  plugins: [svelte()],
  build: {
    outDir: 'dist',
    target: 'es2022',
    chunkSizeWarningLimit: 1300,
  },
});
