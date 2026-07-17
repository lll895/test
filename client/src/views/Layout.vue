<!-- ============================================================
     企业知识库 RAG 问答系统 - 主布局组件（灵动版）
     ============================================================ -->

<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '230px'" class="layout-aside">
      <!-- Logo 区域 -->
      <div class="aside-logo">
        <div class="logo-icon-wrap">
          <el-icon :size="24" color="#fff"><Reading /></el-icon>
        </div>
        <transition name="fade-slide">
          <span v-show="!isCollapse" class="logo-text">企业知识库</span>
        </transition>
      </div>

      <!-- 导航菜单 -->
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        background-color="transparent"
        text-color="rgba(255,255,255,0.65)"
        active-text-color="#fff"
        class="aside-menu"
        @select="handleMenuSelect"
      >
        <el-menu-item v-if="userStore.isAdmin" index="/home">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>管理首页</template>
        </el-menu-item>
        <el-menu-item v-if="!userStore.isAdmin" index="/user-home">
          <el-icon><HomeFilled /></el-icon>
          <template #title>首页</template>
        </el-menu-item>
        <el-menu-item index="/documents">
          <el-icon><Document /></el-icon>
          <template #title>知识文档</template>
        </el-menu-item>
        <el-menu-item index="/qa">
          <el-icon><ChatLineSquare /></el-icon>
          <template #title>智能问答</template>
        </el-menu-item>
        <el-menu-item index="/qa/history">
          <el-icon><Clock /></el-icon>
          <template #title>问答历史</template>
        </el-menu-item>
        <el-menu-item index="/search">
          <el-icon><Search /></el-icon>
          <template #title>知识搜索</template>
        </el-menu-item>
        <el-menu-item index="/bookmarks">
          <el-icon><Star /></el-icon>
          <template #title>我的收藏</template>
        </el-menu-item>
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
          <el-menu-item index="/admin/users">👥 用户管理</el-menu-item>
          <el-menu-item index="/admin/categories">🏷️ 分类管理</el-menu-item>
        </el-sub-menu>
      </el-menu>

      <!-- 底部折叠按钮 -->
      <div class="aside-collapse" @click="isCollapse = !isCollapse">
        <el-icon :size="18" :class="{ rotated: isCollapse }">
          <Fold v-if="!isCollapse" />
          <Expand v-else />
        </el-icon>
      </div>
    </el-aside>

    <!-- 主内容区 -->
    <el-container class="layout-main">
      <!-- 顶部导航栏 -->
      <el-header class="layout-header">
        <div class="header-left">
          <el-icon :size="18" class="collapse-btn" @click="isCollapse = !isCollapse">
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">
              <el-icon :size="14"><HomeFilled /></el-icon>
            </el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentTitle">{{ currentTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <!-- 右侧用户信息 -->
        <div class="header-right">
          <el-tooltip content="搜索 (Ctrl+K)" placement="bottom">
            <el-icon :size="18" class="header-action" @click="$router.push('/search')">
              <Search />
            </el-icon>
          </el-tooltip>
          <el-dropdown trigger="click" @command="handleCommand">
            <span class="user-info">
              <el-avatar :size="32" icon="UserFilled" class="user-avatar-ring" />
              <span class="user-name">{{ userStore.displayName }}</span>
              <el-tag
                :type="userStore.isAdmin ? 'danger' : 'info'"
                size="small"
                class="role-tag"
              >
                {{ userStore.roleText }}
              </el-tag>
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu class="user-dropdown">
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>个人信息
                </el-dropdown-item>
                <el-dropdown-item command="profile" divided>
                  <el-icon><Setting /></el-icon>个人设置
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
            <keep-alive :include="['AskQA']">
              <component :is="Component" />
            </keep-alive>
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'
import {
  Reading, Document, ChatLineSquare, Clock, Setting,
  DataAnalysis, HomeFilled, Fold, Expand, ArrowDown,
  User, SwitchButton, Search, Star, ChatDotSquare,
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const isCollapse = ref(false)
const activeMenu = computed(() => route.path)
const currentTitle = computed(() => route.meta?.title || '')

/** 键盘快捷键 */
function handleKeydown(e) {
  if ((e.ctrlKey && e.key === 'k') || (e.key === '/' && !['INPUT', 'TEXTAREA'].includes(e.target.tagName))) {
    e.preventDefault()
    router.push('/search')
  }
}

onMounted(() => window.addEventListener('keydown', handleKeydown))
onUnmounted(() => window.removeEventListener('keydown', handleKeydown))

function handleMenuSelect(index) {
  router.push(index)
}

async function handleCommand(command) {
  if (command === 'logout') {
    try {
      await ElMessageBox.confirm('确定要退出登录吗？', '提示')
      userStore.logout()
      ElMessage.success('已退出登录')
      router.push('/login')
    } catch { /* 取消 */ }
  } else if (command === 'profile') {
    router.push('/profile')
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
  overflow: hidden;
}

/* ===== 侧边栏 ===== */
.layout-aside {
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  display: flex;
  flex-direction: column;
  transition: width var(--transition-normal);
  overflow: hidden;
  position: relative;
  z-index: 10;
  box-shadow: 2px 0 12px rgba(0, 0, 0, 0.1);
}

.aside-logo {
  height: 60px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  gap: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  flex-shrink: 0;
}

.logo-icon-wrap {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #409eff, #2a6eb0);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
}

.logo-text {
  font-size: 17px;
  font-weight: 700;
  color: #fff;
  white-space: nowrap;
  letter-spacing: 1px;
}

.aside-menu {
  flex: 1;
  border-right: none !important;
  padding: 8px 0;
  background: transparent !important;
}

.aside-menu .el-menu-item {
  margin: 2px 8px;
  border-radius: 8px;
  transition: all var(--transition-fast);
  height: 44px;
  line-height: 44px;
}
.aside-menu .el-menu-item:hover {
  background: rgba(255, 255, 255, 0.08) !important;
}
.aside-menu .el-menu-item.is-active {
  background: rgba(64, 158, 255, 0.2) !important;
  box-shadow: inset 3px 0 0 var(--primary);
}

.aside-menu .el-sub-menu__title {
  margin: 2px 8px;
  border-radius: 8px;
  height: 44px;
  line-height: 44px;
}
.aside-menu .el-sub-menu__title:hover {
  background: rgba(255, 255, 255, 0.08) !important;
}

.aside-collapse {
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  cursor: pointer;
  color: rgba(255, 255, 255, 0.45);
  transition: all var(--transition-fast);
  flex-shrink: 0;
}
.aside-collapse:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.05);
}
.aside-collapse .rotated {
  transform: rotate(180deg);
}

/* ===== 头部导航 ===== */
.layout-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border-lighter);
  height: 60px;
  position: sticky;
  top: 0;
  z-index: 9;
  transition: box-shadow var(--transition-normal);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.collapse-btn {
  cursor: pointer;
  color: var(--text-secondary);
  padding: 6px;
  border-radius: 6px;
  transition: all var(--transition-fast);
}
.collapse-btn:hover {
  background: var(--primary-bg);
  color: var(--primary);
}

/* 头部右侧 */
.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-action {
  cursor: pointer;
  color: var(--text-secondary);
  padding: 8px;
  border-radius: 8px;
  transition: all var(--transition-fast);
}
.header-action:hover {
  background: var(--primary-bg);
  color: var(--primary);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 10px 4px 4px;
  border-radius: 20px;
  transition: all var(--transition-fast);
}
.user-info:hover {
  background: var(--primary-bg);
}

.user-avatar-ring {
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  color: #fff;
  font-weight: 600;
  font-size: 13px;
  box-shadow: 0 2px 6px rgba(64, 158, 255, 0.3);
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.role-tag {
  border-radius: 4px !important;
}

/* 内容区域 */
.layout-content {
  background: var(--bg-page);
  padding: 20px 24px;
  overflow-y: auto;
  height: calc(100vh - 60px);
}

/* 过渡动画 */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.25s ease;
}
.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(-10px);
}
</style>
