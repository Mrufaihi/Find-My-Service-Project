import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import * as path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [svelte()],
  css: {
    postcss: './postcss.config.js',
  },
  resolve: {
    alias: {
      $lib: path.resolve('./src/lib'),
    },
  },
});
