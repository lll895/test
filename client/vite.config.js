/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue({
    // 测试环境下不转换模板中的资源 URL（避免 Windows 上 /icons.svg 路径解析失败）
    template: {
      transformAssetUrls: false,
    },
  })],
  server: {
    port: 5173,
    // 代理配置：将 /api 请求转发到 Flask 后端
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
        // SSE 流式响应不缓冲
        configure: (proxy) => {
          proxy.on('proxyReq', (proxyReq, req) => {
            if (req.url && req.url.includes('/qa/ask/stream')) {
              proxyReq.setHeader('Connection', 'keep-alive')
            }
          })
        }
      }
    }
  },
  // Vitest 配置
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/__tests__/setup.js'],
    include: ['src/**/*.test.js'],
  },
})
