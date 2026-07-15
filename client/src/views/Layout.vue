<!-- ============================================================
     企业知识库 RAG 问答系统 - 主布局组件
     包含侧边栏导航、顶部导航栏和内容区
     ============================================================ -->

<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '220px'" class="layout-aside">
      <!-- Logo 区域 -->
      <div class="aside-logo">
        <el-icon :size="28" color="#409eff"><Reading /></el-icon>
        <transition name="el-fade-in-linear">
          <span v-show="!isCollapse" class="logo-text">企业知识库</span>
        </transition>
      </div>

      <!-- 导航菜单 -->
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        background-color="#1d1e1f"
        text-color="#bfcbd9"
        active-text-color="#409eff"
        class="aside-menu"
        @select="handleMenuSelect"
      >
        <!-- 管理首页（仅管理员） -->
        <el-menu-item v-if="userStore.isAdmin" index="/home">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>管理首页</template>
        </el-menu-item>

        <!-- 普通用户首页 -->
        <el-menu-item v-if="!userStore.isAdmin" index="/user-home">
          <el-icon><HomeFilled /></el-icon>
          <template #title>首页</template>
        </el-menu-item>

        <!-- 知识文档 -->
        <el-menu-item index="/documents">
          <el-icon><Document /></el-icon>
          <template #title>知识文档</template>
        </el-menu-item>

        <!-- 智能问答 -->
        <el-menu-item index="/qa">
          <el-icon><ChatLineSquare /></el-icon>
          <template #title>智能问答</template>
        </el-menu-item>

        <!-- 问答历史 -->
        <el-menu-item index="/qa/history">
          <el-icon><Clock /></el-icon>
          <template #title>问答历史</template>
        </el-menu-item>

        <!-- 知识搜索（新功能） -->
        <el-menu-item index="/search">
          <el-icon><Search /></el-icon>
          <template #title>知识搜索</template>
        </el-menu-item>

        <!-- 我的收藏 -->
        <el-menu-item index="/bookmarks">
          <el-icon><Star /></el-icon>
          <template #title>我的收藏</template>
        </el-menu-item>

        <!-- 我的对话 -->
        <el-menu-item index="/conversations">
          <el-icon><ChatDotSquare /></el-icon>
          <template #title>我的对话</template>
        </el-menu-item>

        <!-- 管理员专属菜单 -->
        <el-sub-menu v-if="userStore.isAdmin" index="admin">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>系统管理</span>
          </template>
          <el-menu-item index="/admin/users">用户管理</el-menu-item>
          <el-menu-item index="/admin/categories">分类管理</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container class="layout-main">
      <!-- 顶部导航栏 -->
      <el-header class="layout-header">
        <!-- 折叠按钮 -->
        <div class="header-left">
          <el-icon
            :size="20"
            class="collapse-btn"
            @click="isCollapse = !isCollapse"
          >
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentTitle">{{ currentTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <!-- 右侧用户信息 -->
        <div class="header-right">
          <el-dropdown trigger="click" @command="handleCommand">
            <span class="user-info">
              <el-avatar :size="32" icon="UserFilled" />
              <span class="user-name">{{ userStore.displayName }}</span>
              <el-tag :type="userStore.isAdmin ? 'danger' : 'info'" size="small">
                {{ userStore.roleText }}
              </el-tag>
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>个人信息
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 页面内容 -->
      <el-main class="layout-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'
import {
  Reading, Document, ChatLineSquare, Clock, Setting,
  DataAnalysis, HomeFilled, Fold, Expand, ArrowDown,
  UserFilled, User, SwitchButton, Search, Star, ChatDotSquare,
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const isCollapse = ref(false)

// 当前激活的菜单项
const activeMenu = computed(() => route.path)

// 当前页面标题
const currentTitle = computed(() => route.meta?.title || '')

/** 菜单选择处理 - 手动路由跳转（比 :router="true" 更可靠） */
function handleMenuSelect(index) {
  router.push(index)
}

/** 下拉菜单命令处理 */
async function handleCommand(command) {
  if (command === 'logout') {
    try {
      await ElMessageBox.confirm('确定要退出登录吗？', '提示')
      userStore.logout()
      ElMessage.success('已退出登录')
      router.push('/login')
    } catch {
      // 取消操作
    }
  } else if (command === 'profile') {
    ElMessage.info('个人信息功能开发中')
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

/* 侧边栏样式 */
.layout-aside {
  background-color: #1d1e1f;
  overflow: hidden;
  transition: width 0.3s ease;
}

.aside-logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border-bottom: 1px solid #2a2b2c;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  color: #e6e6e6;
  white-space: nowrap;
}

.aside-menu {
  border-right: none;
}

/* 顶部导航栏 */
.layout-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  height: 60px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.collapse-btn {
  cursor: pointer;
  color: #606266;
  transition: color 0.3s;
}
.collapse-btn:hover {
  color: #409eff;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background 0.3s;
}
.user-info:hover {
  background: #f5f7fa;
}

.user-name {
  font-size: 14px;
  color: #303133;
}

/* 内容区域 */
.layout-content {
  background: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}
</style>
