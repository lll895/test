// ============================================================================
// Vitest 测试环境初始化
// 功能：全局 mock 和测试环境配置，在每个测试文件运行前执行
// ============================================================================

import { vi } from 'vitest'

// ---------------------------------------------------------------------------
// 1. Mock Element Plus
// ---------------------------------------------------------------------------
// api/index.js 中使用了 ElMessage，所有测试都需要 mock element-plus 模块
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn(),
  },
  ElMessageBox: {
    confirm: vi.fn(),
    alert: vi.fn(),
    prompt: vi.fn(),
  },
  ElNotification: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn(),
  },
  ElLoading: {
    service: vi.fn(() => ({
      close: vi.fn(),
    })),
  },
  ElInput: vi.fn(),
  ElButton: vi.fn(),
  ElForm: vi.fn(),
  ElFormItem: vi.fn(),
  default: {
    install(app) {
      // noop — 避免安装真实组件
    },
  },
}))

// ---------------------------------------------------------------------------
// 2. 确保 jsdom 环境可用
// ---------------------------------------------------------------------------
// vitest.config.js 中已配置 environment: 'jsdom'，jsdom 提供了完整的
// DOM API、localStorage、sessionStorage 等。无需额外 polyfill。
