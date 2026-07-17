// ============================================================================
// 企业知识库 RAG 问答系统 - API 请求封装
// 功能：统一管理所有后端 API 调用，包含请求拦截和响应处理
// ============================================================================

import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

// 创建 axios 实例
const request = axios.create({
  baseURL: '/api',      // 通过 vite proxy 转发到后端
  timeout: 120000,      // 超时时间：120秒（LLM 生成可能较慢）
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器：自动添加 JWT Token
request.interceptors.request.use(
  (config) => {
    // 从 localStorage 获取 token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    // 如果是文件上传，设置 multipart 格式
    if (config.upload) {
      config.headers['Content-Type'] = 'multipart/form-data'
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器：统一处理错误
request.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      switch (status) {
        case 401:
          // Token 失效或未登录，跳转到登录页
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          router.push('/login')
          ElMessage.error('登录已失效，请重新登录')
          break
        case 403:
          ElMessage.error('没有权限执行此操作')
          break
        case 404:
          ElMessage.warning('请求的资源不存在')
          break
        case 500:
          ElMessage.error(data?.message || '服务器错误，请稍后再试')
          break
        default:
          ElMessage.error(data?.message || '请求失败')
      }
    } else if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时，请检查网络或稍后再试')
    } else {
      ElMessage.error('网络错误，请检查连接')
    }
    return Promise.reject(error)
  }
)

// ============================================================================
// API 接口定义
// ============================================================================

// ---------- 认证接口 ----------
export const authAPI = {
  login(data) { return request.post('/auth/login', data) },
  register(data) { return request.post('/auth/register', data) },
  getProfile() { return request.get('/auth/profile') },
  updateProfile(data) { return request.put('/auth/profile', data) },
  forgotPassword(data) { return request.post('/auth/forgot-password', data) },
  resetPassword(data) { return request.post('/auth/reset-password', data) },
}

// ---------- 文档接口 ----------
export const documentAPI = {
  list(params) { return request.get('/documents', { params }) },
  detail(id) { return request.get(`/documents/${id}`) },
  upload(formData) {
    return request.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 300000, // 上传超时5分钟
    })
  },
  update(id, data) { return request.put(`/documents/${id}`, data) },
  updateContent(id, data) { return request.put(`/documents/${id}/content`, data) },
  delete(id) { return request.delete(`/documents/${id}`) },
  getCategories() { return request.get('/documents/categories') },
  createCategory(data) { return request.post('/documents/categories', data) },
  deleteCategory(id) { return request.delete(`/documents/categories/${id}`) },
  search(params) { return request.get('/documents/search', { params }) },
  getContent(id) { return request.get(`/documents/${id}/content`) },
  getVersions(id) { return request.get(`/documents/${id}/versions`) },
}

// ---------- 问答接口 ----------
export const qaAPI = {
  ask(data) { return request.post('/qa/ask', data, { timeout: 300000 }) },
  askStream(data) { return request.post('/qa/ask/stream', data, { timeout: 300000 }) },
  startSession() { return request.post('/qa/session/start') },
  clearSession(sessionId) { return request.post(`/qa/session/${sessionId}/clear`) },
  getSessionHistory(sessionId) { return request.get(`/qa/session/${sessionId}/history`) },
  getHistory(params) { return request.get('/qa/history', { params }) },
  getAllHistory(params) { return request.get('/qa/history/all', { params }) },
  getDetail(id) { return request.get(`/qa/${id}`) },
  submitFeedback(data) { return request.post('/qa/feedback', data) },
  exportHistory(params) { return request.get('/qa/export', { params, responseType: 'blob' }) },
  getStats() { return request.get('/qa/stats') },
  // 跨设备对话同步
  saveSession(data) { return request.post('/qa/session/save', data) },
  listSessions(params) { return request.get('/qa/sessions', { params }) },
  getSessionMessages(id) { return request.get(`/qa/sessions/${id}`) },
  deleteSession(id) { return request.delete(`/qa/sessions/${id}`) },
  restoreSession(id) { return request.post(`/qa/sessions/${id}/restore`) },
}

// ---------- 管理后台接口 ----------
export const adminAPI = {
  getDashboard() { return request.get('/admin/dashboard') },
  getUsers(params) { return request.get('/admin/users', { params }) },
  toggleUserStatus(id) { return request.put(`/admin/users/${id}/status`) },
  getAnnouncements(params) { return request.get('/admin/announcements', { params }) },
  createAnnouncement(data) { return request.post('/admin/announcements', data) },
  deleteAnnouncement(id) { return request.delete(`/admin/announcements/${id}`) },
  getKnowledgeGaps(params) { return request.get('/admin/knowledge-gaps', { params }) },
}

// ---------- 收藏夹接口 ----------
export const bookmarkAPI = {
  list(params) { return request.get('/bookmarks', { params }) },
  add(data) { return request.post('/bookmarks', data) },
  remove(id) { return request.delete(`/bookmarks/${id}`) },
  updateNote(id, data) { return request.put(`/bookmarks/${id}/note`, data) },
  check(params) { return request.get('/bookmarks/check', { params }) },
}

// ---------- 工作流接口 ----------
export const workflowAPI = {
  getActions() { return request.get('/workflow/actions') },
  matchActions(data) { return request.post('/workflow/match', data) },
  createAction(data) { return request.post('/workflow/actions', data) },
  updateAction(id, data) { return request.put(`/workflow/actions/${id}`, data) },
  deleteAction(id) { return request.delete(`/workflow/actions/${id}`) },
}

export default request
