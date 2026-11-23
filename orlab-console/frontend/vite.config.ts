import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

// 开发代理：把 /api 转发到本地 TypeScript 后端（localhost:8787）
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8787',
        changeOrigin: true,
      },
    },
  },
});
