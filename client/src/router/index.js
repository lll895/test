// ============================================================================
// 企业知识库 RAG 问答系统 - 路由配置
// 功能：定义前端所有页面的路由规则和导航守卫
// ============================================================================

import { createRouter, createWebHistory } from 'vue-router'

// 路由配置表
const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { title: '登录', noAuth: true },
  },
  {
    path: '/',
    component: () => import('../views/Layout.vue'),
    redirect: () => {
      // 根据用户角色重定向到不同首页
      try {
        const user = JSON.parse(localStorage.getItem('user') || '{}')
        return user.role === 'admin' ? '/home' : '/user-home'
      } catch {
        return '/user-home'
      }
    },
    children: [
      {
        path: 'home',
        name: 'Home',
        component: () => import('../views/home/AdminHome.vue'),
        meta: { title: '管理首页', roles: ['admin'] },
      },
      {
        path: 'user-home',
        name: 'UserHome',
        component: () => import('../views/home/UserHome.vue'),
        meta: { title: '首页', roles: ['user'] },
      },
      {
        path: 'documents',
        name: 'DocumentList',
        component: () => import('../views/document/DocumentList.vue'),
        meta: { title: '知识文档' },
      },
      {
        path: 'documents/upload',
        name: 'DocumentUpload',
        component: () => import('../views/document/DocumentUpload.vue'),
        meta: { title: '上传文档' },
      },
      {
        path: 'qa',
        name: 'AskQA',
        component: () => import('../views/qa/AskQA.vue'),
        meta: { title: '智能问答' },
      },
      {
        path: 'qa/history',
        name: 'QAHistory',
        component: () => import('../views/qa/QAHistory.vue'),
        meta: { title: '问答历史' },
      },
      {
        path: 'search',
        name: 'KnowledgeSearch',
        component: () => import('../views/search/KnowledgeSearch.vue'),
        meta: { title: '知识搜索' },
      },
      {
        path: 'bookmarks',
        name: 'BookmarkList',
        component: () => import('../views/bookmark/BookmarkList.vue'),
        meta: { title: '我的收藏' },
      },
      {
        path: 'conversations',
        name: 'ConversationList',
        component: () => import('../views/conversation/ConversationList.vue'),
        meta: { title: '我的对话' },
      },
      {
        path: 'admin/users',
        name: 'UserManage',
        component: () => import('../views/admin/UserManage.vue'),
        meta: { title: '用户管理', roles: ['admin'] },
      },
      {
        path: 'admin/categories',
        name: 'CategoryManage',
        component: () => import('../views/admin/CategoryManage.vue'),
        meta: { title: '分类管理', roles: ['admin'] },
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('../views/profile/Profile.vue'),
        meta: { title: '个人信息' },
      },
      {
        path: 'workflow/:actionId',
        name: 'WorkflowForm',
        component: () => import('../views/workflow/WorkflowForm.vue'),
        meta: { title: '申请表单' },
      },
    ],
  },
]

// 创建路由实例
const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 导航守卫：检查登录状态和角色权限
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - 企业知识库` : '企业知识库'

  const token = localStorage.getItem('token')
  const userStr = localStorage.getItem('user')

  // 无需认证的页面（如登录页）直接放行
  if (to.meta.noAuth) {
    // 已登录用户访问登录页，重定向到对应首页（由根路由redirect处理角色）
    if (token && to.path === '/login') {
      next('/')
    } else {
      next()
    }
    return
  }

  // 需要认证但未登录，重定向到登录页
  if (!token) {
    next('/login')
    return
  }

  // 检查角色权限
  if (to.meta.roles) {
    try {
      const user = JSON.parse(userStr)
      if (!to.meta.roles.includes(user.role)) {
        // 没有权限，重定向到对应用户的首页（避免循环）
        const fallback = user.role === 'admin' ? '/home' : '/user-home'
        next(fallback)
        return
      }
    } catch {
      next('/login')
      return
    }
  }

  next()
})

export default router
