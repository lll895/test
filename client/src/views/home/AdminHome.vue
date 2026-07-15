<!-- ============================================================
     企业知识库 RAG 问答系统 - 管理员首页仪表盘
     包含数据统计卡片和趋势图表
     ============================================================ -->

<template>
  <div class="admin-home">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>管理首页</h2>
      <p>欢迎回来，{{ userStore.displayName }}！以下是系统运行概况</p>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="loading-wrapper">
      <el-skeleton :rows="5" animated />
    </div>

    <template v-else>
      <!-- 统计卡片 -->
      <el-row :gutter="20" class="stat-cards">
        <el-col :xs="12" :sm="8" :md="6" :lg="4" v-for="card in statCards" :key="card.label">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-card-inner">
              <div class="stat-icon" :style="{ background: card.bg }">
                <el-icon :size="24" color="#fff">
                  <component :is="card.icon" />
                </el-icon>
              </div>
              <div class="stat-info">
                <p class="stat-value">{{ card.value }}</p>
                <p class="stat-label">{{ card.label }}</p>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 图表区域 -->
      <el-row :gutter="20" class="chart-row">
        <!-- 近7天问答趋势 -->
        <el-col :xs="24" :lg="16">
          <el-card shadow="hover" class="chart-card">
            <template #header>
              <div class="card-header">
                <span>近7天问答趋势</span>
              </div>
            </template>
            <v-chart :option="qaTrendOption" class="chart" autoresize />
          </el-card>
        </el-col>

        <!-- 文档状态分布 -->
        <el-col :xs="24" :lg="8">
          <el-card shadow="hover" class="chart-card">
            <template #header>
              <div class="card-header">
                <span>文档状态分布</span>
              </div>
            </template>
            <v-chart :option="statusOption" class="chart" autoresize />
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="20" class="chart-row">
        <!-- 分类文档数量 -->
        <el-col :xs="24" :lg="12">
          <el-card shadow="hover" class="chart-card">
            <template #header>
              <div class="card-header">
                <span>分类文档数量 TOP5</span>
              </div>
            </template>
            <v-chart :option="categoryOption" class="chart" autoresize />
          </el-card>
        </el-col>

        <!-- 用户角色分布 -->
        <el-col :xs="24" :lg="6">
          <el-card shadow="hover" class="chart-card">
            <template #header>
              <div class="card-header">
                <span>用户角色分布</span>
              </div>
            </template>
            <v-chart :option="roleOption" class="chart" autoresize />
          </el-card>
        </el-col>

        <!-- 反馈统计 -->
        <el-col :xs="24" :lg="6">
          <el-card shadow="hover" class="chart-card">
            <template #header>
              <div class="card-header">
                <span>问答反馈</span>
              </div>
            </template>
            <v-chart :option="feedbackOption" class="chart" autoresize />
          </el-card>
        </el-col>
      </el-row>

      <!-- 知识盲区分析 -->
      <el-card shadow="hover" class="chart-card" style="margin-top:20px">
        <template #header>
          <div class="card-header">
            <span><el-icon><WarningFilled /></el-icon> 知识盲区分析</span>
            <el-tag v-if="gapSummary" type="danger" size="small">
              近30天 {{ gapSummary.total_gaps }} 个未命中问题
            </el-tag>
          </div>
        </template>
        <div v-if="!gapSummary" class="loading-wrapper" style="padding:20px">
          <el-skeleton :rows="2" animated />
        </div>
        <div v-else-if="gapSummary.total_gaps === 0" style="text-align:center;padding:20px;color:#909399">
          暂无知识盲区，知识库覆盖良好 🎉
        </div>
        <div v-else>
          <el-row :gutter="20">
            <el-col :xs="24" :lg="12">
              <div class="gap-keywords">
                <p class="gap-section-title">🔥 高频提问关键词</p>
                <div class="keyword-tags">
                  <el-tag v-for="kw in gapSummary.top_keywords" :key="kw.word"
                    :type="kw.count > 5 ? 'danger' : kw.count > 2 ? 'warning' : 'info'"
                    size="small" class="keyword-tag" effect="plain">
                    {{ kw.word }} ({{ kw.count }})
                  </el-tag>
                </div>
              </div>
            </el-col>
            <el-col :xs="24" :lg="12">
              <div class="gap-suggest">
                <p class="gap-section-title">💡 建议补充的知识点</p>
                <div v-if="gapSummary.top_keywords.length > 0" class="suggest-list">
                  <div v-for="kw in gapSummary.top_keywords.slice(0, 8)" :key="kw.word" class="suggest-item">
                    <el-icon color="#e6a23c"><Link /></el-icon>
                    <span>用户频繁搜索"<strong>{{ kw.word }}</strong>"，建议添加相关文档</span>
                  </div>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>
      </el-card>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, PieChart, LineChart } from 'echarts/charts'
import {
  GridComponent, TooltipComponent, LegendComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'
import { adminAPI } from '../../api'
import { useUserStore } from '../../stores/user'
import {
  UserFilled, Document, ChatLineSquare, Connection, Reading, StarFilled, WarningFilled, Link
} from '@element-plus/icons-vue'

// 注册 ECharts 组件
use([
  CanvasRenderer, BarChart, PieChart, LineChart,
  GridComponent, TooltipComponent, LegendComponent,
])

const userStore = useUserStore()
const loading = ref(true)
const dashboardData = ref(null)
const gapSummary = ref(null)

// 统计卡片配置
const statCards = computed(() => {
  if (!dashboardData.value) return []
  const s = dashboardData.value.summary
  return [
    { label: '用户总数', value: s.total_users, icon: UserFilled, bg: '#409eff' },
    { label: '知识文档', value: s.ready_docs, icon: Document, bg: '#67c23a' },
    { label: '向量数量', value: s.vector_count, icon: Connection, bg: '#e6a23c' },
    { label: '今日问答', value: s.today_qa, icon: ChatLineSquare, bg: '#f56c6c' },
    { label: '累计问答', value: s.total_qa, icon: StarFilled, bg: '#909399' },
    { label: '今日新增', value: s.today_new_users, icon: UserFilled, bg: '#8e44ad' },
  ]
})

// 问答趋势折线图
const qaTrendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: {
    type: 'category',
    data: dashboardData.value?.qa_trend?.map(d => d.date) || [],
  },
  yAxis: { type: 'value', minInterval: 1 },
  series: [{
    data: dashboardData.value?.qa_trend?.map(d => d.count) || [],
    type: 'line',
    smooth: true,
    areaStyle: { opacity: 0.3 },
    lineStyle: { width: 3, color: '#409eff' },
    itemStyle: { color: '#409eff' },
  }],
}))

// 文档状态饼图
const statusOption = computed(() => ({
  tooltip: { trigger: 'item' },
  series: [{
    type: 'pie',
    radius: ['40%', '70%'],
    center: ['50%', '50%'],
    data: dashboardData.value?.status_distribution || [],
    label: { formatter: '{b}: {c}' },
    color: ['#67c23a', '#e6a23c', '#f56c6c'],
  }],
}))

// 分类文档柱状图
const categoryOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: {
    type: 'category',
    data: dashboardData.value?.category_stats?.map(d => d.name) || [],
    axisLabel: { rotate: 15 },
  },
  yAxis: { type: 'value', minInterval: 1 },
  series: [{
    type: 'bar',
    data: dashboardData.value?.category_stats?.map(d => d.doc_count) || [],
    barWidth: '50%',
    itemStyle: {
      color: '#409eff',
      borderRadius: [4, 4, 0, 0],
    },
  }],
}))

// 用户角色饼图
const roleOption = computed(() => ({
  tooltip: { trigger: 'item' },
  series: [{
    type: 'pie',
    radius: ['40%', '70%'],
    data: dashboardData.value?.role_distribution || [],
    color: ['#f56c6c', '#409eff'],
    label: { formatter: '{b}: {c}人' },
  }],
}))

// 反馈饼图
const feedbackOption = computed(() => {
  const f = dashboardData.value?.feedback_stats
  if (!f) return {}
  const data = []
  if (f.useful > 0) data.push({ name: '有用', value: f.useful })
  if (f.useless > 0) data.push({ name: '无用', value: f.useless })
  const unrated = f.total - f.useful - f.useless
  if (unrated > 0) data.push({ name: '未评价', value: unrated })
  return {
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      data,
      color: ['#67c23a', '#f56c6c', '#e6a23c'],
      label: { formatter: '{b}: {c}' },
    }],
  }
})

/** 加载仪表盘数据 */
async function loadDashboard() {
  loading.value = true
  try {
    const res = await adminAPI.getDashboard()
    if (res.code === 200) {
      dashboardData.value = res.data
    }
  } catch (e) {
    console.error('加载仪表盘数据失败:', e)
  } finally {
    loading.value = false
  }
}

/** 加载知识盲区数据 */
async function loadKnowledgeGaps() {
  try {
    const res = await adminAPI.getKnowledgeGaps({ days: 30, per_page: 1 })
    if (res.code === 200) {
      gapSummary.value = res.data.summary
    }
  } catch (e) {
    console.error('加载知识盲区失败:', e)
  }
}

onMounted(() => {
  loadDashboard()
  loadKnowledgeGaps()
})
</script>

<style scoped>
.admin-home {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}
.page-header h2 {
  font-size: 22px;
  color: #303133;
  margin-bottom: 6px;
}
.page-header p {
  color: #909399;
  font-size: 14px;
}

.loading-wrapper {
  padding: 40px;
  background: #fff;
  border-radius: 8px;
}

.stat-cards {
  margin-bottom: 20px;
}

.stat-card-inner {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.chart-row {
  margin-bottom: 20px;
}

.chart-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  color: #303133;
}

.chart {
  height: 300px;
}

/* 知识盲区样式 */
.gap-keywords, .gap-suggest { padding: 0 8px; }
.gap-section-title { font-size: 14px; font-weight: 600; color: #303133; margin-bottom: 12px; }
.keyword-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.keyword-tag { margin: 2px; }
.suggest-list { display: flex; flex-direction: column; gap: 8px; }
.suggest-item { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #606266; line-height: 1.4; }
</style>
