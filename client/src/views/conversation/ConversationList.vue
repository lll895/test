<template>
  <div class="conv-list page-container card-animate">
    <div class="page-header">
      <h2><el-icon><ChatDotSquare /></el-icon> 我的对话</h2>
      <p>已保存的对话历史，登录任何设备都能继续</p>
    </div>

    <el-card shadow="hover">
      <div v-if="conversations.length === 0" class="empty">
        <el-empty description="还没有保存的对话" />
      </div>

      <div v-for="conv in conversations" :key="conv.id" class="conv-item">
        <div class="conv-info" @click="restore(conv)">
          <el-icon :size="20" color="var(--primary)"><ChatDotSquare /></el-icon>
          <div class="conv-detail">
            <span class="conv-title">{{ conv.title || '新对话' }}</span>
            <span class="conv-meta">{{ conv.message_count }} 条消息 · {{ conv.updated_at?.slice(0, 16)?.replace('T', ' ') }}</span>
          </div>
        </div>
        <div class="conv-actions">
          <el-button link type="primary" size="small" @click="restore(conv)">继续对话</el-button>
          <el-popconfirm title="确定删除？" @confirm="remove(conv.id)">
            <template #reference>
              <el-button link type="danger" size="small"><el-icon><Delete /></el-icon></el-button>
            </template>
          </el-popconfirm>
        </div>
      </div>

      <el-pagination v-if="total > perPage" v-model:current-page="page"
        :page-size="perPage" :total="total" layout="prev,pager,next" @change="load"
        style="margin-top:16px;justify-content:center" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ChatDotSquare, Delete } from '@element-plus/icons-vue'
import { qaAPI } from '../../api'

const router = useRouter()
const conversations = ref([])
const page = ref(1)
const perPage = ref(20)
const total = ref(0)

async function load() {
  try {
    const res = await qaAPI.listSessions({ page: page.value, per_page: perPage.value })
    if (res.code === 200) {
      conversations.value = res.data.list
      total.value = res.data.total
    }
  } catch (e) { console.error(e) }
}

async function restore(conv) {
  try {
    const res = await qaAPI.restoreSession(conv.id)
    if (res.code === 200) {
      ElMessage.success('对话已恢复')
      // 跳转到问答页，携带 session_id
      router.push({ path: '/qa', query: { session: res.data.session_id, title: res.data.title } })
    }
  } catch (e) { console.error(e) }
}

async function remove(id) {
  try {
    await qaAPI.deleteSession(id)
    ElMessage.success('已删除')
    load()
  } catch (e) { console.error(e) }
}

onMounted(load)
</script>

<style scoped>
.conv-list {
  max-width: 1000px;
  margin: 0 auto;
}

.empty {
  padding: 40px 0;
}
.conv-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid var(--border-lighter);
  transition: background var(--transition-fast);
}
.conv-item:hover {
  background: var(--primary-bg);
}
.conv-item:last-child {
  border-bottom: none;
}
.conv-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  cursor: pointer;
}
.conv-detail {
  display: flex;
  flex-direction: column;
}
.conv-title {
  font-weight: 600;
  color: var(--text-primary);
}
.conv-meta {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 2px;
}
.conv-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
