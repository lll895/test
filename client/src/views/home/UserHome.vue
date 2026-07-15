<!-- ============================================================
     企业知识库 RAG 问答系统 - 普通用户首页
     ============================================================ -->

<template>
  <div class="user-home">
    <!-- 欢迎横幅 -->
    <el-card class="welcome-card" shadow="hover">
      <div class="welcome-content">
        <div class="welcome-text">
          <h2>你好，{{ userStore.displayName }} 👋</h2>
          <p>欢迎使用企业知识库智能问答系统</p>
          <p class="welcome-tip">你可以上传知识文档，也可以直接向我提问</p>
          <div class="welcome-actions">
            <el-button type="primary" size="large" @click="$router.push('/qa')">
              <el-icon><ChatLineSquare /></el-icon>开始提问
            </el-button>
            <el-button size="large" @click="$router.push('/documents')">
              <el-icon><Document /></el-icon>浏览文档
            </el-button>
          </div>
        </div>
        <div class="welcome-icon">
          <el-icon :size="80" color="#409eff"><Reading /></el-icon>
        </div>
      </div>
    </el-card>

    <!-- 快捷入口 -->
    <el-row :gutter="20" class="quick-entries">
      <el-col :xs="12" :lg="6" v-for="entry in quickEntries" :key="entry.title">
        <el-card shadow="hover" class="quick-card" @click="$router.push(entry.path)">
          <div class="quick-card-inner">
            <el-icon :size="32" :color="entry.color"><component :is="entry.icon" /></el-icon>
            <div>
              <p class="quick-title">{{ entry.title }}</p>
              <p class="quick-desc">{{ entry.desc }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 系统公告 -->
    <el-card class="announcement-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span><el-icon><Bell /></el-icon> 系统公告</span>
        </div>
      </template>
      <div v-if="announcements.length === 0" class="empty-announcement">
        暂无公告
      </div>
      <div v-for="ann in announcements" :key="ann.id" class="announcement-item">
        <div class="ann-title">
          <el-tag
            :type="ann.priority === 'high' ? 'danger' : ann.priority === 'normal' ? 'warning' : 'info'"
            size="small"
          >
            {{ ann.priority === 'high' ? '重要' : ann.priority === 'normal' ? '普通' : '低' }}
          </el-tag>
          <span class="ann-title-text">{{ ann.title }}</span>
          <span class="ann-time">{{ ann.created_at?.slice(0, 10) }}</span>
        </div>
        <p class="ann-content">{{ ann.content }}</p>
        <p class="ann-publisher">发布人：{{ ann.publisher }}</p>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ChatLineSquare, Document, Reading, Bell, TrendCharts, Connection } from '@element-plus/icons-vue'
import { useUserStore } from '../../stores/user'
import { adminAPI } from '../../api'

const userStore = useUserStore()
const announcements = ref([])

// 快捷入口
const quickEntries = [
  { title: '智能问答', desc: '向知识库提问', path: '/qa', icon: ChatLineSquare, color: '#409eff' },
  { title: '知识文档', desc: '浏览知识文档', path: '/documents', icon: Document, color: '#67c23a' },
  { title: '问答历史', desc: '查看问答记录', path: '/qa/history', icon: TrendCharts, color: '#e6a23c' },
  { title: '上传文档', desc: '贡献知识文档', path: '/documents/upload', icon: Connection, color: '#8e44ad' },
]

/** 加载公告 */
async function loadAnnouncements() {
  try {
    const res = await adminAPI.getAnnouncements({ per_page: 5 })
    if (res.code === 200) {
      announcements.value = res.data.list || []
    }
  } catch (e) {
    console.error('加载公告失败:', e)
  }
}

onMounted(loadAnnouncements)
</script>

<style scoped>
.user-home {
  max-width: 1200px;
  margin: 0 auto;
}

.welcome-card {
  margin-bottom: 20px;
}

.welcome-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 0;
}

.welcome-text h2 {
  font-size: 24px;
  color: #303133;
  margin-bottom: 8px;
}

.welcome-text p {
  color: #606266;
  margin-bottom: 4px;
}

.welcome-tip {
  color: #909399;
  font-size: 14px;
  margin-bottom: 20px;
}

.welcome-actions {
  display: flex;
  gap: 12px;
}

.quick-entries {
  margin-bottom: 20px;
}

.quick-card {
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 20px;
}
.quick-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.quick-card-inner {
  display: flex;
  align-items: center;
  gap: 16px;
}

.quick-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.quick-desc {
  font-size: 13px;
  color: #909399;
  margin-top: 2px;
}

.announcement-card {
  margin-bottom: 20px;
}

.card-header {
  font-weight: 600;
  color: #303133;
}

.announcement-item {
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}
.announcement-item:last-child {
  border-bottom: none;
}

.ann-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.ann-title-text {
  font-weight: 600;
  color: #303133;
  flex: 1;
}

.ann-time {
  color: #909399;
  font-size: 13px;
}

.ann-content {
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 6px;
}

.ann-publisher {
  color: #909399;
  font-size: 13px;
}

.empty-announcement {
  text-align: center;
  color: #909399;
  padding: 20px;
}
</style>
