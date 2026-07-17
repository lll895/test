// ============================================================================
// API 请求模块单元测试
// 测试目标：client/src/api/index.js
// ============================================================================

import { describe, it, expect, vi, beforeEach } from 'vitest'

/**
 * 使用 vi.hoisted 创建 Mock Axios 实例。
 * hoisted 回调在 vi.mock 工厂之前执行，确保工厂函数能引用该实例。
 */
const mockSetup = vi.hoisted(() => {
  /** 请求拦截器处理器列表 */
  const requestHandlers = []
  /** 响应拦截器处理器列表 */
  const responseHandlers = []

  /** Mock Axios 实例，模拟 axios.create() 的返回值 */
  const instance = {
    interceptors: {
      request: {
        handlers: requestHandlers,
        use(fulfilled, rejected) {
          requestHandlers.push({ fulfilled, rejected })
          return requestHandlers.length - 1
        },
      },
      response: {
        handlers: responseHandlers,
        use(fulfilled, rejected) {
          responseHandlers.push({ fulfilled, rejected })
          return responseHandlers.length - 1
        },
      },
    },
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  }

  return { mockAxiosInstance: instance, requestHandlers, responseHandlers }
})

// Mock axios 模块 —— 使 axios.create() 返回我们控制的 Mock 实例
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => mockSetup.mockAxiosInstance),
  },
}))

// Mock vue-router —— api/index.js 在 401 时会调用 router.push()
vi.mock('../router', () => ({
  default: {
    push: vi.fn(),
  },
}))

// 导入被测试模块（此时 axios 和 router 已被 mock）
import { authAPI, documentAPI, qaAPI, adminAPI, bookmarkAPI, workflowAPI } from '../api/index.js'

describe('API 请求模块', () => {
  beforeEach(() => {
    // 每次测试前清空 localStorage 和所有 mock 调用记录
    localStorage.clear()
    vi.clearAllMocks()
    // 恢复 localStorage 默认状态 —— 清空后无 token
  })

  // ==========================================================================
  // 请求拦截器
  // ==========================================================================
  describe('请求拦截器 (Request Interceptor)', () => {
    it('当 localStorage 中有 token 时，自动添加 Bearer 认证头', () => {
      // 准备：写入 token
      localStorage.setItem('token', 'my-test-token-123')

      // 执行：调用请求拦截器的 fulfilled 处理函数
      const [handler] = mockSetup.requestHandlers
      const config = { headers: {} }
      const result = handler.fulfilled(config)

      // 断言：Authorization 头正确设置
      expect(result.headers.Authorization).toBe('Bearer my-test-token-123')
    })

    it('当 localStorage 中无 token 时不添加 Authorization 头', () => {
      // 准备：确保 localStorage 是空的
      expect(localStorage.getItem('token')).toBeNull()

      // 执行
      const [handler] = mockSetup.requestHandlers
      const config = { headers: {} }
      const result = handler.fulfilled(config)

      // 断言：没有 Authorization 头
      expect(result.headers.Authorization).toBeUndefined()
    })
  })

  // ==========================================================================
  // 响应拦截器
  // ==========================================================================
  describe('响应拦截器 (Response Interceptor)', () => {
    it('成功响应时直接返回 response.data', () => {
      // 准备：模拟一个成功响应
      const [handler] = mockSetup.responseHandlers
      const mockResponse = {
        data: { code: 200, data: { id: 1, username: 'admin' } },
      }

      // 执行
      const result = handler.fulfilled(mockResponse)

      // 断言：返回的是 response.data
      expect(result).toEqual({ code: 200, data: { id: 1, username: 'admin' } })
    })

    it('401 错误时清除 token、跳转登录页并弹出错误提示', async () => {
      // 准备：先在 localStorage 中放入 token/user
      localStorage.setItem('token', 'expired-token')
      localStorage.setItem('user', '{"id":1}')

      // 动态导入 element-plus 和 router 以获取 mock 实例
      const { ElMessage } = await import('element-plus')
      const routerModule = await import('../router')

      const [handler] = mockSetup.responseHandlers
      const networkError = {
        response: {
          status: 401,
          data: { message: '登录已过期' },
        },
      }

      // 执行：调用 rejected 处理函数
      await expect(handler.rejected(networkError)).rejects.toBe(networkError)

      // 断言：清除了 localStorage
      expect(localStorage.getItem('token')).toBeNull()
      expect(localStorage.getItem('user')).toBeNull()

      // 断言：跳转到登录页
      expect(routerModule.default.push).toHaveBeenCalledWith('/login')

      // 断言：弹出错误消息
      expect(ElMessage.error).toHaveBeenCalledWith('登录已失效，请重新登录')
    })
  })

  // ==========================================================================
  // API 模块导出检查
  // ==========================================================================
  describe('API 接口导出', () => {
    it('导出 authAPI 并包含 login/register/getProfile 方法', () => {
      expect(authAPI).toBeDefined()
      expect(typeof authAPI.login).toBe('function')
      expect(typeof authAPI.register).toBe('function')
      expect(typeof authAPI.getProfile).toBe('function')
    })

    it('导出 documentAPI 并包含 list/upload/detail/delete 方法', () => {
      expect(documentAPI).toBeDefined()
      expect(typeof documentAPI.list).toBe('function')
      expect(typeof documentAPI.upload).toBe('function')
      expect(typeof documentAPI.detail).toBe('function')
      expect(typeof documentAPI.delete).toBe('function')
    })

    it('导出 qaAPI 并包含 ask/askStream/getHistory 方法', () => {
      expect(qaAPI).toBeDefined()
      expect(typeof qaAPI.ask).toBe('function')
      expect(typeof qaAPI.askStream).toBe('function')
      expect(typeof qaAPI.getHistory).toBe('function')
    })

    it('导出 adminAPI、bookmarkAPI、workflowAPI', () => {
      expect(adminAPI).toBeDefined()
      expect(typeof adminAPI.getDashboard).toBe('function')
      expect(bookmarkAPI).toBeDefined()
      expect(typeof bookmarkAPI.list).toBe('function')
      expect(workflowAPI).toBeDefined()
      expect(typeof workflowAPI.getActions).toBe('function')
    })
  })
})
