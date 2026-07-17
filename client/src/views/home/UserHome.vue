<!-- ============================================================
     企业知识库 RAG 问答系统 - 用户首页（灵动版）
     ============================================================ -->

<template>
  <div class="user-home page-container">
    <!-- 欢迎横幅 -->
    <el-card class="welcome-card card-animate" shadow="never">
      <div class="welcome-content">
        <div class="welcome-text">
          <h2>你好，{{ userStore.displayName }} 👋</h2>
          <p class="welcome-desc">欢迎使用企业知识库智能问答系统</p>
          <p class="welcome-tip">你可以上传知识文档，也可以直接向我提问</p>
          <div class="welcome-actions">
            <el-button type="primary" size="large" class="action-btn primary-btn" @click="$router.push('/qa')">
              <el-icon><ChatLineSquare /></el-icon>开始提问
            </el-button>
            <el-button size="large" class="action-btn" @click="$router.push('/documents')">
              <el-icon><Document /></el-icon>浏览文档
            </el-button>
          </div>
        </div>
        <div class="welcome-icon">
          <el-icon :size="80" color="var(--primary)"><Reading /></el-icon>
        </div>
      </div>
    </el-card>

    <!-- 快捷入口 -->
    <el-row :gutter="20" class="quick-entries">
      <el-col :xs="12" :lg="6" v-for="(entry, i) in quickEntries" :key="entry.title" class="card-animate" :style="{ animationDelay: `${0.08 * (i + 1)}s` }">
        <el-card shadow="never" class="quick-card" @click="$router.push(entry.path)">
          <div class="quick-card-inner">
            <div class="quick-icon" :style="{ background: entry.bg }">
              <el-icon :size="24" :color="entry.color"><component :is="entry.icon" /></el-icon>
            </div>
            <div>
              <p class="quick-title">{{ entry.title }}</p>
              <p class="quick-desc">{{ entry.desc }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快捷操作（工作流按钮） -->
    <el-card v-if="workflowActions.length > 0" class="workflow-card card-animate" shadow="never">
      <template #header>
        <div class="card-header">
          <el-icon color="var(--primary)"><Connection /></el-icon>
          <span>快捷操作</span>
        </div>
      </template>
      <el-row :gutter="12">
        <el-col :xs="12" :sm="8" :md="6" v-for="act in workflowActions" :key="act.id">
          <div class="workflow-item" @click="openWorkflowUrl(act)">
            <div class="workflow-item-icon">
              <el-icon :size="22" color="var(--primary)"><Link /></el-icon>
            </div>
            <div>
              <p class="workflow-item-title">{{ act.label }}</p>
              <p v-if="act.description" class="workflow-item-desc">{{ act.description }}</p>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 系统公告 -->
    <el-card class="announcement-card card-animate" shadow="never">
      <template #header>
        <div class="card-header">
          <el-icon color="#e6a23c"><Bell /></el-icon>
          <span>系统公告</span>
        </div>
      </template>
      <div v-if="announcements.length === 0" class="empty-state">
        <el-icon :size="48" color="#c0c4cc"><Bell /></el-icon>
        <p>暂无公告</p>
      </div>
      <div v-for="ann in announcements" :key="ann.id" class="announcement-item">
        <div class="ann-title">
          <el-tag
            :type="ann.priority === 'high' ? 'danger' : ann.priority === 'normal' ? 'warning' : 'info'"
            size="small" effect="dark"
          >
            {{ ann.priority === 'high' ? '重要' : ann.priority === 'normal' ? '普通' : '低' }}
          </el-tag>
          <span class="ann-title-text">{{ ann.title }}</span>
          <span class="ann-time">{{ ann.created_at?.slice(0, 10) }}</span>
        </div>
        <p class="ann-content">{{ ann.content }}</p>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ChatLineSquare, Document, Reading, Bell, TrendCharts, Connection, Link } from '@element-plus/icons-vue'
import { useUserStore } from '../../stores/user'
import { adminAPI, workflowAPI } from '../../api'

const router = useRouter()
const userStore = useUserStore()
const announcements = ref([])
const workflowActions = ref([])

const quickEntries = [
  { title: '智能问答', desc: '向知识库提问', path: '/qa', icon: ChatLineSquare, color: '#409eff', bg: 'rgba(64,158,255,0.12)' },
  { title: '知识文档', desc: '浏览知识文档', path: '/documents', icon: Document, color: '#67c23a', bg: 'rgba(103,194,58,0.12)' },
  { title: '问答历史', desc: '查看问答记录', path: '/qa/history', icon: TrendCharts, color: '#e6a23c', bg: 'rgba(230,162,60,0.12)' },
  { title: '上传文档', desc: '贡献知识文档', path: '/documents/upload', icon: Connection, color: '#8e44ad', bg: 'rgba(142,68,173,0.12)' },
]

function openWorkflowUrl(action) {
  if (!action.url) { ElMessage.info('该操作暂未配置'); return }
  if (action.url.startsWith('/')) { router.push(`/workflow/${action.id}`); return }
  if (action.url.includes('company.com') || action.url.includes('example.com')) {
    ElMessage.info(`「${action.label}」功能尚未对接，请联系管理员配置`); return
  }
  window.open(action.url, '_blank')
}

async function loadWorkflowActions() {
  try { const res = await workflowAPI.getActions(); if (res.code === 200) workflowActions.value = res.data || [] }
  catch (e) { console.error('加载工作流按钮失败:', e) }
}

async function loadAnnouncements() {
  try { const res = await adminAPI.getAnnouncements({ per_page: 5 }); if (res.code === 200) announcements.value = res.data.list || [] }
  catch (e) { console.error('加载公告失败:', e) }
}

onMounted(() => { loadAnnouncements(); loadWorkflowActions() })
</script>

<style scoped>
.user-home { padding-bottom: 24px; }

/* 欢迎横幅 */
.welcome-card {
  margin-bottom: 20px;
  border-radius: var(--radius-lg) !important;
  background: linear-gradient(135deg, #f0f7ff 0%, #e8f4fd 100%);
  border: 1px solid rgba(64,158,255,0.15) !important;
  overflow: hidden;
  position: relative;
}
.welcome-card::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -20%;
  width: 300px; height: 300px;
  background: radial-gradient(circle, rgba(64,158,255,0.08), transparent);
  border-radius: 50%;
}
.welcome-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 0;
  position: relative;
  z-index: 1;
}
.welcome-text h2 { font-size: 24px; color: var(--text-primary); margin-bottom: 6px; }
.welcome-desc { color: var(--text-regular); margin-bottom: 2px; }
.welcome-tip { color: var(--text-secondary); font-size: 14px; margin-bottom: 20px; }
.welcome-actions { display: flex; gap: 12px; }
.action-btn { border-radius: 12px !important; height: 44px; font-size: 15px; padding: 0 24px; }
.primary-btn { box-shadow: 0 4px 12px rgba(64,158,255,0.3); }
.welcome-icon { opacity: 0.4; }

/* 快捷入口 */
.quick-entries { margin-bottom: 20px; }
.quick-card {
  cursor: pointer;
  transition: all var(--transition-normal);
  margin-bottom: 20px;
  border-radius: var(--radius-md) !important;
}
.quick-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-hover) !important;
}
.quick-card-inner { display: flex; align-items: center; gap: 14px; }
.quick-icon {
  width: 48px; height: 48px;
  display: flex; align-items: center; justify-content: center;
  border-radius: 12px;
  flex-shrink: 0;
}
.quick-title { font-size: 15px; font-weight: 600; color: var(--text-primary); }
.quick-desc { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }

/* 工作流卡片 */
.workflow-card { margin-bottom: 20px; border-radius: var(--radius-lg) !important; }
.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 16px;
}
.workflow-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border-radius: 10px;
  cursor: pointer;
  transition: all var(--transition-fast);
  border: 1px solid var(--border-lighter);
  margin-bottom: 8px;
}
.workflow-item:hover { background: var(--primary-bg); border-color: var(--primary); transform: translateY(-1px); }
.workflow-item-icon {
  width: 40px; height: 40px;
  display: flex; align-items: center; justify-content: center;
  background: var(--primary-bg); border-radius: 10px; flex-shrink: 0;
}
.workflow-item-title { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.workflow-item-desc { font-size: 12px; color: var(--text-secondary); margin-top: 1px; }

/* 公告 */
.announcement-card { border-radius: var(--radius-lg) !important; }
.announcement-item { padding: 14px 0; border-bottom: 1px solid var(--border-lighter); }
.announcement-item:last-child { border-bottom: none; }
.ann-title { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.ann-title-text { font-weight: 600; color: var(--text-primary); flex: 1; }
.ann-time { color: var(--text-secondary); font-size: 12px; }
.ann-content { color: var(--text-regular); font-size: 14px; line-height: 1.6; }
.empty-state { text-align: center; color: var(--text-secondary); padding: 20px; display: flex; flex-direction: column; align-items: center; gap: 8px; }
</style>
