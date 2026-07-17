// ============================================================================
// 用户 Pinia Store 单元测试
// 测试目标：client/src/stores/user.js
// ============================================================================

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUserStore } from '../../stores/user.js'

// 模拟 api/index.js，仅暴露 authAPI
vi.mock('../../api', () => ({
  authAPI: {
    login: vi.fn(),
    getProfile: vi.fn(),
  },
}))

// 导入（mock 后的）authAPI 供测试使用
import { authAPI } from '../../api'

describe('useUserStore — 用户状态管理', () => {
  /** 每个测试前创建新的 Pinia 实例并清空 localStorage */
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
  })

  // ==========================================================================
  // 初始状态
  // ==========================================================================
  describe('初始状态', () => {
    it('无 localStorage 数据时 token 为空字符串，userInfo 为 null', () => {
      const store = useUserStore()
      expect(store.token).toBe('')
      expect(store.userInfo).toBeNull()
    })

    it('从 localStorage 中读取已保存的 token 和 userInfo', () => {
      const savedUser = { id: 1, username: 'zhangsan', role: 'user' }
      localStorage.setItem('token', 'saved-token-456')
      localStorage.setItem('user', JSON.stringify(savedUser))

      const store = useUserStore()
      expect(store.token).toBe('saved-token-456')
      expect(store.userInfo).toEqual(savedUser)
    })

    it('localStorage 中 user 数据损坏时 state 初始化会抛出异常', () => {
      // 注意：当前 store 实现直接使用 JSON.parse 且没有 try/catch，
      // 因此 localStorage 中损坏的 JSON 会导致 useUserStore() 抛出 SyntaxError。
      localStorage.setItem('token', 'some-token')
      localStorage.setItem('user', '这不是合法 JSON')

      expect(() => useUserStore()).toThrow(SyntaxError)
    })
  })

  // ==========================================================================
  // Getters
  // ==========================================================================
  describe('Getters', () => {
    it('isLoggedIn 在 token 存在时返回 true，否则返回 false', () => {
      // 登录状态
      const store1 = useUserStore()
      store1.token = 'valid-token'
      expect(store1.isLoggedIn).toBe(true)

      // 未登录状态（显式设为空字符串）
      store1.token = ''
      expect(store1.isLoggedIn).toBe(false)
    })

    it('isAdmin 在 userInfo.role === "admin" 时返回 true', () => {
      const store = useUserStore()

      // 管理员
      store.userInfo = { role: 'admin' }
      expect(store.isAdmin).toBe(true)

      // 普通用户
      store.userInfo = { role: 'user' }
      expect(store.isAdmin).toBe(false)

      // 无用户信息
      store.userInfo = null
      expect(store.isAdmin).toBe(false)
    })

    it('roleText 返回 "管理员" 或 "普通用户"', () => {
      const store = useUserStore()

      store.userInfo = { role: 'admin' }
      expect(store.roleText).toBe('管理员')

      store.userInfo = { role: 'user' }
      expect(store.roleText).toBe('普通用户')
    })
  })

  // ==========================================================================
  // Actions — login
  // ==========================================================================
  describe('login()', () => {
    it('登录成功时设置 token 和 userInfo 并保存到 localStorage', async () => {
      const mockResponse = {
        code: 200,
        data: {
          token: 'jwt-token-abc',
          user: { id: 1, username: 'admin', role: 'admin' },
        },
      }
      authAPI.login.mockResolvedValue(mockResponse)

      const store = useUserStore()
      const result = await store.login('admin', '123456')

      // 应该调用 authAPI.login
      expect(authAPI.login).toHaveBeenCalledWith({
        username: 'admin',
        password: '123456',
      })

      // store 状态更新
      expect(store.token).toBe('jwt-token-abc')
      expect(store.userInfo).toEqual({ id: 1, username: 'admin', role: 'admin' })

      // localStorage 同步保存
      expect(localStorage.getItem('token')).toBe('jwt-token-abc')
      expect(localStorage.getItem('user')).toBe(
        JSON.stringify({ id: 1, username: 'admin', role: 'admin' })
      )

      // 返回响应
      expect(result).toBe(mockResponse)
    })

    it('登录失败时（code !== 200）不更新 store 状态', async () => {
      const mockResponse = { code: 401, message: '用户名或密码错误' }
      authAPI.login.mockResolvedValue(mockResponse)

      const store = useUserStore()
      await store.login('admin', 'wrong-password')

      // token 和 userInfo 应该保持为空
      expect(store.token).toBe('')
      expect(store.userInfo).toBeNull()
      expect(localStorage.getItem('token')).toBeNull()
    })
  })

  // ==========================================================================
  // Actions — logout
  // ==========================================================================
  describe('logout()', () => {
    it('清空 token、userInfo 及 localStorage', () => {
      // 先模拟已登录状态
      localStorage.setItem('token', 'some-token')
      localStorage.setItem('user', JSON.stringify({ id: 1, username: 'test' }))

      const store = useUserStore()
      store.token = 'some-token'
      store.userInfo = { id: 1, username: 'test' }

      // 执行登出
      store.logout()

      // store 状态清空
      expect(store.token).toBe('')
      expect(store.userInfo).toBeNull()

      // localStorage 清空
      expect(localStorage.getItem('token')).toBeNull()
      expect(localStorage.getItem('user')).toBeNull()
    })
  })

  // ==========================================================================
  // Actions — fetchProfile
  // ==========================================================================
  describe('fetchProfile()', () => {
    it('成功获取用户信息时更新 userInfo 和 localStorage', async () => {
      authAPI.getProfile.mockResolvedValue({
        code: 200,
        data: { id: 1, username: 'admin', email: 'admin@example.com' },
      })

      const store = useUserStore()
      await store.fetchProfile()

      expect(authAPI.getProfile).toHaveBeenCalledOnce()
      expect(store.userInfo).toEqual({
        id: 1,
        username: 'admin',
        email: 'admin@example.com',
      })
      expect(localStorage.getItem('user')).toBe(
        JSON.stringify({ id: 1, username: 'admin', email: 'admin@example.com' })
      )
    })

    it('请求失败时静默处理（不抛出异常）', async () => {
      authAPI.getProfile.mockRejectedValue(new Error('Network Error'))

      const store = useUserStore()
      // 应不抛出异常
      await expect(store.fetchProfile()).resolves.toBeUndefined()
    })
  })
})
