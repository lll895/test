<!-- ============================================================
     企业知识库 RAG 问答系统 - 问答历史记录页面
     ============================================================ -->

<template>
  <div class="qa-history">
    <div class="page-header">
      <h2>问答历史</h2>
      <p>查看您的历史问答记录</p>
    </div>

    <!-- 统计摘要卡片 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :xs="12" :sm="6" v-for="stat in statsCards" :key="stat.label">
        <el-card shadow="hover" class="stat-card" :body-style="{ padding: '16px' }">
          <div class="stat-inner">
            <el-icon :size="24" :color="stat.color"><component :is="stat.icon" /></el-icon>
            <div class="stat-info">
              <p class="stat-value">{{ stat.value }}</p>
              <p class="stat-label">{{ stat.label }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 操作栏 -->
    <div class="action-bar">
      <el-button type="primary" @click="exportHistory" :loading="exporting">
        <el-icon><Download /></el-icon> 导出最近7天
      </el-button>
    </div>

    <!-- 历史记录列表 -->
    <el-card shadow="hover">
      <el-table :data="historyList" v-loading="loading" stripe style="width: 100%">
        <el-table-column label="问题" min-width="250">
          <template #default="{ row }">
            <div class="question-cell" @click="showDetail(row)">
              <el-icon color="#409eff"><ChatLineSquare /></el-icon>
              <span class="question-text">{{ truncate(row.question, 60) }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="回答预览" min-width="300">
          <template #default="{ row }">
            <span class="answer-preview">{{ truncate(row.answer, 80) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="检索块数" width="100" align="center">
          <template #default="{ row }">
            {{ row.chunks_retrieved }}
          </template>
        </el-table-column>
        <el-table-column label="耗时" width="100" align="center">
          <template #default="{ row }">
            {{ row.cost_time_ms }}ms
          </template>
        </el-table-column>
        <el-table-column label="反馈" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.feedback === 1" type="success" size="small">有用</el-tag>
            <el-tag v-else-if="row.feedback === 0" type="danger" size="small">无用</el-tag>
            <span v-else class="no-feedback">-</span>
          </template>
        </el-table-column>
        <el-table-column label="时间" width="180">
          <template #default="{ row }">
            {{ row.created_at?.slice(0, 19)?.replace('T', ' ') }}
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="perPage"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @change="loadHistory"
        />
      </div>
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="问答详情" width="700px">
      <div v-if="detailData" class="qa-detail">
        <div class="detail-section">
          <h4>问题：</h4>
          <p>{{ detailData.question }}</p>
        </div>
        <div class="detail-section">
          <h4>回答：</h4>
          <div class="detail-answer">{{ detailData.answer }}</div>
        </div>
        <div v-if="detailData.sources?.length" class="detail-section">
          <h4>引用的知识来源：</h4>
          <ul>
            <li v-for="(s, i) in detailData.sources" :key="i">{{ s.title }} (相似度: {{ Math.round(s.similarity * 100) }}%)</li>
          </ul>
        </div>
        <div class="detail-meta">
          <el-tag size="small" type="info">⏱ 耗时: {{ detailData.cost_time_ms }}ms</el-tag>
          <el-tag size="small" type="info">📄 检索: {{ detailData.chunks_retrieved }} 块</el-tag>
          <el-tag size="small" type="info">🤖 模型: {{ detailData.model_used }}</el-tag>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ChatLineSquare, Download, ChatDotSquare, Timer, CircleCheck, DataBoard } from '@element-plus/icons-vue'
import { qaAPI } from '../../api'

const historyList = ref([])
const loading = ref(false)
const page = ref(1)
const perPage = ref(10)
const total = ref(0)
const exporting = ref(false)

const detailVisible = ref(false)
const detailData = ref(null)

// 统计数据
const statsCards = ref([
  { label: '总问答数', value: '-', icon: ChatDotSquare, color: '#409eff' },
  { label: '今日问答', value: '-', icon: DataBoard, color: '#67c23a' },
  { label: '有用回答', value: '-', icon: CircleCheck, color: '#e6a23c' },
  { label: '平均响应', value: '-', icon: Timer, color: '#8e44ad' },
])

function truncate(text, maxLen) {
  if (!text) return ''
  return text.length > maxLen ? text.slice(0, maxLen) + '...' : text
}

/** 加载统计数据 */
async function loadStats() {
  try {
    const res = await qaAPI.getStats()
    if (res.code === 200) {
      statsCards.value = [
        { label: '总问答数', value: res.data.total_qa, icon: ChatDotSquare, color: '#409eff' },
        { label: '今日问答', value: res.data.today_qa, icon: DataBoard, color: '#67c23a' },
        { label: '有用率', value: `${res.data.useful_rate}%`, icon: CircleCheck, color: '#e6a23c' },
        { label: '平均响应', value: `${res.data.avg_response_time_ms}ms`, icon: Timer, color: '#8e44ad' },
      ]
    }
  } catch (e) {
    console.error('加载统计失败:', e)
  }
}

/** 加载问答历史 */
async function loadHistory() {
  loading.value = true
  try {
    const res = await qaAPI.getHistory({
      page: page.value,
      per_page: perPage.value,
    })
    if (res.code === 200) {
      historyList.value = res.data.list
      total.value = res.data.total
    }
  } catch (e) {
    console.error('加载问答历史失败:', e)
  } finally {
    loading.value = false
  }
}

/** 查看详情 */
async function showDetail(row) {
  try {
    const res = await qaAPI.getDetail(row.id)
    if (res.code === 200) {
      detailData.value = res.data
      detailVisible.value = true
    }
  } catch (e) {
    console.error('加载详情失败:', e)
  }
}

/** 导出问答历史 */
async function exportHistory() {
  exporting.value = true
  try {
    const res = await qaAPI.exportHistory({ days: 7 })
    // 创建下载链接
    const blob = new Blob([res], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `问答历史_${new Date().toISOString().slice(0, 10)}.md`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    console.error('导出失败:', e)
  } finally {
    exporting.value = false
  }
}

onMounted(() => {
  loadStats()
  loadHistory()
})
</script>

<style scoped>
.qa-history {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 20px;
}
.page-header h2 {
  font-size: 22px;
  color: #303133;
  margin-bottom: 4px;
}
.page-header p {
  color: #909399;
  font-size: 14px;
}

/* 统计卡片 */
.stats-row {
  margin-bottom: 16px;
}
.stat-card {
  margin-bottom: 8px;
  border-radius: 8px;
}
.stat-inner {
  display: flex;
  align-items: center;
  gap: 12px;
}
.stat-info {
  flex: 1;
}
.stat-value {
  font-size: 22px;
  font-weight: 700;
  color: #303133;
  margin: 0;
  line-height: 1.2;
}
.stat-label {
  font-size: 13px;
  color: #909399;
  margin: 2px 0 0;
}

/* 操作栏 */
.action-bar {
  margin-bottom: 12px;
  display: flex;
  justify-content: flex-end;
}

.question-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}
.question-cell:hover .question-text {
  color: #409eff;
}
.question-text {
  color: #303133;
  transition: color 0.3s;
}

.answer-preview {
  color: #909399;
  font-size: 13px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.no-feedback {
  color: #c0c4cc;
}

.qa-detail {
  max-height: 60vh;
  overflow-y: auto;
}
.detail-section {
  margin-bottom: 20px;
}
.detail-section h4 {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}
.detail-section p {
  color: #303133;
  line-height: 1.6;
}
.detail-answer {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 8px;
  line-height: 1.6;
  white-space: pre-wrap;
}
.detail-section ul {
  padding-left: 20px;
  color: #409eff;
}
.detail-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
</style>

<style scoped>
.qa-history {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 20px;
}
.page-header h2 {
  font-size: 22px;
  color: #303133;
  margin-bottom: 4px;
}
.page-header p {
  color: #909399;
  font-size: 14px;
}

.question-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}
.question-cell:hover .question-text {
  color: #409eff;
}
.question-text {
  color: #303133;
  transition: color 0.3s;
}

.answer-preview {
  color: #909399;
  font-size: 13px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.no-feedback {
  color: #c0c4cc;
}

/* 详情样式 */
.qa-detail {
  max-height: 60vh;
  overflow-y: auto;
}

.detail-section {
  margin-bottom: 20px;
}
.detail-section h4 {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}
.detail-section p {
  color: #303133;
  line-height: 1.6;
}
.detail-answer {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 8px;
  line-height: 1.6;
  white-space: pre-wrap;
}
.detail-section ul {
  padding-left: 20px;
  color: #409eff;
}

.detail-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
</style>
