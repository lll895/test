// ============================================================================
// 企业知识库 RAG 问答系统 - 用户状态管理（Pinia Store）
// ============================================================================

import { defineStore } from 'pinia'
import { authAPI } from '../api'

export const useUserStore = defineStore('user', {
  // 状态
  state: () => ({
    token: localStorage.getItem('token') || '',
    userInfo: JSON.parse(localStorage.getItem('user') || 'null'),
  }),

  // 计算属性
  getters: {
    /** 是否已登录 */
    isLoggedIn: (state) => !!state.token,
    /** 是否为管理员 */
    isAdmin: (state) => state.userInfo?.role === 'admin',
    /** 用户显示名称 */
    displayName: (state) => state.userInfo?.real_name || state.userInfo?.username || '用户',
    /** 用户角色中文 */
    roleText: (state) => {
      return state.userInfo?.role === 'admin' ? '管理员' : '普通用户'
    },
  },

  // 操作方法
  actions: {
    /**
     * 用户登录
     * @param {string} username - 用户名
     * @param {string} password - 密码
     */
    async login(username, password) {
      const res = await authAPI.login({ username, password })
      if (res.code === 200) {
        this.token = res.data.token
        this.userInfo = res.data.user
        localStorage.setItem('token', res.data.token)
        localStorage.setItem('user', JSON.stringify(res.data.user))
      }
      return res
    },

    /** 退出登录 */
    logout() {
      this.token = ''
      this.userInfo = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    },

    /** 获取最新用户信息 */
    async fetchProfile() {
      try {
        const res = await authAPI.getProfile()
        if (res.code === 200) {
          this.userInfo = res.data
          localStorage.setItem('user', JSON.stringify(res.data))
        }
      } catch (e) {
        console.error('获取用户信息失败:', e)
      }
    },
  },
})
