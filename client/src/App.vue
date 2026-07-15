<!-- ============================================================
     企业知识库 RAG 问答系统 - 根组件
     ============================================================ -->

<template>
  <!-- 使用路由视图渲染当前页面 -->
  <router-view />
</template>

<script setup>
/**
 * 根组件
 * 不做任何复杂逻辑，路由视图的切换由 router-view 自动处理
 */

// 页面加载时检查登录状态
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from './stores/user'

const router = useRouter()
const userStore = useUserStore()

onMounted(() => {
  // 如果没有 token，重定向到登录页
  if (!userStore.isLoggedIn) {
    router.push('/login')
  }
})
</script>
