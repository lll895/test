<!-- ============================================================
     企业知识库 RAG 问答系统 - 管理员仪表盘（高级版）
     ============================================================ -->

<template>
  <div class="admin-home page-container">
    <!-- 欢迎横幅 -->
    <el-card class="welcome-card" shadow="never">
      <div class="welcome-content">
        <div>
          <div class="welcome-badge">管理员</div>
          <h2>👋 你好，{{ userStore.displayName }}</h2>
          <p class="welcome-sub">这是系统的运行概况，所有数据一目了然</p>
        </div>
        <div class="welcome-actions">
          <el-button class="glow-btn" type="primary" @click="$router.push('/documents/upload')">
            <el-icon><Upload /></el-icon>上传文档
          </el-button>
          <el-button @click="$router.push('/qa')">
            <el-icon><ChatLineSquare /></el-icon>测试问答
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 加载中 -->
    <div v-if="loading" class="loading-wrapper">
      <el-skeleton :rows="6" animated />
    </div>

    <template v-else>
      <!-- 统计卡片 -->
      <el-row :gutter="20" class="stat-row">
        <el-col :xs="12" :sm="8" :md="6" :lg="4" v-for="(card, i) in statCards" :key="card.label"
          class="card-animate" :style="{ animationDelay: `${0.06 * i}s` }">
          <el-card shadow="never" class="stat-card" @click="card.action && $router.push(card.action)">
            <div class="stat-card-inner">
              <div class="stat-icon" :style="{ background: card.bg + '18', color: card.bg }">
                <el-icon :size="22"><component :is="card.icon" /></el-icon>
              </div>
              <div class="stat-info">
                <p class="stat-value">{{ card.value }}</p>
                <p class="stat-label">{{ card.label }}</p>
              </div>
            </div>
            <div class="stat-trend" v-if="card.trend !== undefined">
              <span :class="card.trend >= 0 ? 'up' : 'down'">
                {{ card.trend >= 0 ? '↑' : '↓' }} {{ Math.abs(card.trend) }}%
              </span>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 快捷操作（工作流） -->
      <el-card v-if="workflowActions.length > 0" class="section-card" shadow="never">
        <template #header>
          <div class="section-header">
            <div class="section-title">
              <el-icon color="var(--primary)"><Lightning /></el-icon>
              <span>快捷操作</span>
            </div>
            <el-tag size="small" effect="plain">{{ workflowActions.length }} 个快捷入口</el-tag>
          </div>
        </template>
        <el-row :gutter="16">
          <el-col :xs="12" :sm="8" :md="6" :lg="4" v-for="act in workflowActions" :key="act.id"
            class="card-animate">
            <div class="workflow-btn" @click="openWorkflowUrl(act)">
              <div class="wf-icon">
                <el-icon :size="24"><Link /></el-icon>
              </div>
              <span class="wf-label">{{ act.label.replace(/^[^\s]+\s/, '') }}</span>
              <span class="wf-desc">{{ act.description }}</span>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 图表区域 -->
      <el-row :gutter="20" class="chart-row">
        <el-col :xs="24" :lg="16">
          <el-card shadow="never" class="chart-card">
            <template #header>
              <div class="section-header">
                <div class="section-title">
                  <el-icon color="var(--primary)"><TrendCharts /></el-icon>
                  <span>近7天问答趋势</span>
                </div>
                <el-tag size="small" effect="plain">
                  总计 {{ dashboardData?.summary?.total_qa || 0 }} 次
                </el-tag>
              </div>
            </template>
            <v-chart :option="qaTrendOption" class="chart" autoresize />
          </el-card>
        </el-col>
        <el-col :xs="24" :lg="8">
          <el-card shadow="never" class="chart-card">
            <template #header>
              <div class="section-header">
                <div class="section-title">
                  <el-icon color="#67c23a"><DataAnalysis /></el-icon>
                  <span>文档状态</span>
                </div>
              </div>
            </template>
            <v-chart :option="statusOption" class="chart chart-sm" autoresize />
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="20" class="chart-row">
        <el-col :xs="24" :lg="12">
          <el-card shadow="never" class="chart-card">
            <template #header>
              <div class="section-header">
                <div class="section-title">
                  <el-icon color="#e6a23c"><FolderOpened /></el-icon>
                  <span>分类文档 TOP5</span>
                </div>
              </div>
            </template>
            <v-chart :option="categoryOption" class="chart" autoresize />
          </el-card>
        </el-col>
        <el-col :xs="24" :lg="6">
          <el-card shadow="never" class="chart-card">
            <template #header>
              <div class="section-header">
                <div class="section-title">
                  <el-icon color="#f56c6c"><UserFilled /></el-icon>
                  <span>用户角色</span>
                </div>
              </div>
            </template>
            <v-chart :option="roleOption" class="chart chart-sm" autoresize />
          </el-card>
        </el-col>
        <el-col :xs="24" :lg="6">
          <el-card shadow="never" class="chart-card">
            <template #header>
              <div class="section-header">
                <div class="section-title">
                  <el-icon color="#67c23a"><StarFilled /></el-icon>
                  <span>问答反馈</span>
                </div>
              </div>
            </template>
            <v-chart :option="feedbackOption" class="chart chart-sm" autoresize />
          </el-card>
        </el-col>
      </el-row>

      <!-- 知识盲区 -->
      <el-card shadow="never" class="section-card">
        <template #header>
          <div class="section-header">
            <div class="section-title">
              <el-icon color="#f56c6c"><WarningFilled /></el-icon>
              <span>知识盲区分析</span>
            </div>
            <el-tag v-if="gapSummary" :type="gapSummary.total_gaps > 0 ? 'danger' : 'success'" size="small">
              {{ gapSummary.total_gaps > 0 ? `近30天 ${gapSummary.total_gaps} 个未命中` : '覆盖良好' }}
            </el-tag>
          </div>
        </template>
        <div v-if="!gapSummary" class="empty-state"><el-skeleton :rows="2" animated /></div>
        <div v-else-if="gapSummary.total_gaps === 0" class="empty-state">
          <el-icon :size="48" color="#67c23a"><CircleCheck /></el-icon>
          <p>知识库覆盖良好 🎉</p>
        </div>
        <el-row v-else :gutter="20">
          <el-col :xs="24" :lg="12">
            <p class="gap-title">🔥 高频提问关键词</p>
            <div class="tag-cloud">
              <el-tag v-for="kw in gapSummary.top_keywords" :key="kw.word"
                :type="kw.count > 5 ? 'danger' : kw.count > 2 ? 'warning' : 'info'"
                size="small" effect="plain" class="tag-cloud-item">
                {{ kw.word }}
                <em>{{ kw.count }}</em>
              </el-tag>
            </div>
          </el-col>
          <el-col :xs="24" :lg="12">
            <p class="gap-title">💡 建议补充的知识点</p>
            <div class="suggestion-list">
              <div v-for="kw in gapSummary.top_keywords.slice(0, 8)" :key="kw.word" class="suggestion-item">
                <el-icon color="#e6a23c"><Link /></el-icon>
                <span>用户频繁搜索"<strong>{{ kw.word }}</strong>"，建议添加相关文档</span>
              </div>
            </div>
          </el-col>
        </el-row>
      </el-card>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, PieChart, LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { adminAPI, workflowAPI } from '../../api'
import { useUserStore } from '../../stores/user'
import {
  UserFilled, Document, ChatLineSquare, Connection, Reading,
  StarFilled, WarningFilled, Link, Upload, TrendCharts, DataAnalysis,
  FolderOpened, Lightning, CircleCheck,
} from '@element-plus/icons-vue'

use([CanvasRenderer, BarChart, PieChart, LineChart, GridComponent, TooltipComponent, LegendComponent])

const router = useRouter()
const userStore = useUserStore()
const loading = ref(true)
const dashboardData = ref(null)
const gapSummary = ref(null)
const workflowActions = ref([])

const statCards = computed(() => {
  if (!dashboardData.value) return []
  const s = dashboardData.value.summary
  return [
    { label: '用户总数', value: s.total_users, icon: UserFilled, bg: '#409eff', trend: 12, action: '/admin/users' },
    { label: '知识文档', value: s.ready_docs, icon: Document, bg: '#67c23a', trend: 5, action: '/documents' },
    { label: '向量数量', value: s.vector_count, icon: Connection, bg: '#e6a23c', trend: undefined },
    { label: '今日问答', value: s.today_qa, icon: ChatLineSquare, bg: '#f56c6c', trend: -8 },
    { label: '累计问答', value: s.total_qa, icon: StarFilled, bg: '#909399', trend: 25 },
    { label: '今日新增', value: s.today_new_users, icon: UserFilled, bg: '#8e44ad', trend: 0 },
  ]
})

const chartTheme = {
  color: ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#8e44ad', '#00c9a7'],
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(255,255,255,0.95)',
    borderColor: '#e4e7ed',
    borderWidth: 1,
    textStyle: { color: '#303133', fontSize: 12 },
    boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
  },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true, top: 20 },
}

const qaTrendOption = computed(() => ({
  ...chartTheme,
  xAxis: { type: 'category', data: dashboardData.value?.qa_trend?.map(d => d.date) || [], axisLine: { lineStyle: { color: '#e4e7ed' } } },
  yAxis: { type: 'value', minInterval: 1, splitLine: { lineStyle: { color: '#f5f5f5', type: 'dashed' } } },
  series: [{
    data: dashboardData.value?.qa_trend?.map(d => d.count) || [],
    type: 'line',
    smooth: true,
    showSymbol: true,
    symbolSize: 8,
    areaStyle: {
      color: {
        type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [{ offset: 0, color: 'rgba(64,158,255,0.25)' }, { offset: 1, color: 'rgba(64,158,255,0.02)' }],
      },
    },
    lineStyle: { width: 3, color: '#409eff' },
    itemStyle: { color: '#409eff', borderWidth: 2 },
  }],
}))

const statusOption = computed(() => ({
  ...chartTheme,
  series: [{
    type: 'pie', radius: ['35%', '65%'], center: ['50%', '50%'],
    data: dashboardData.value?.status_distribution || [],
    label: { formatter: '{b}\n{c}', fontSize: 12 },
    color: ['#67c23a', '#e6a23c', '#f56c6c'],
    emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.15)' } },
  }],
}))

const categoryOption = computed(() => ({
  ...chartTheme,
  xAxis: { type: 'category', data: dashboardData.value?.category_stats?.map(d => d.name) || [], axisLabel: { rotate: 12 }, axisLine: { lineStyle: { color: '#e4e7ed' } } },
  yAxis: { type: 'value', minInterval: 1, splitLine: { lineStyle: { color: '#f5f5f5', type: 'dashed' } } },
  series: [{
    type: 'bar', data: (dashboardData.value?.category_stats || []).map((d, i) => ({
      value: d.doc_count,
      itemStyle: { color: ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#8e44ad'][i], borderRadius: [6, 6, 0, 0] },
    })),
    barWidth: '55%', showBackground: true, backgroundStyle: { color: '#f5f7fa', borderRadius: [6, 6, 0, 0] },
  }],
}))

const roleOption = computed(() => ({
  ...chartTheme,
  series: [{
    type: 'pie', radius: ['35%', '65%'],
    data: dashboardData.value?.role_distribution || [],
    color: ['#f56c6c', '#409eff'],
    label: { formatter: '{b}: {c}人' },
  }],
}))

const feedbackOption = computed(() => {
  const f = dashboardData.value?.feedback_stats
  if (!f) return {}
  const data = []
  if (f.useful > 0) data.push({ name: '有用', value: f.useful })
  if (f.useless > 0) data.push({ name: '无用', value: f.useless })
  const unrated = f.total - f.useful - f.useless
  if (unrated > 0) data.push({ name: '未评价', value: unrated })
  return {
    ...chartTheme,
    series: [{ type: 'pie', radius: ['35%', '65%'], data, color: ['#67c23a', '#f56c6c', '#e6a23c'], label: { formatter: '{b}: {c}' } }],
  }
})

function openWorkflowUrl(action) {
  if (!action.url) return
  if (action.url.startsWith('/')) { router.push(`/workflow/${action.id}`); return }
  window.open(action.url, '_blank')
}

async function loadDashboard() {
  loading.value = true
  try { const r = await adminAPI.getDashboard(); if (r.code === 200) dashboardData.value = r.data }
  catch (e) { console.error(e) }
  finally { loading.value = false }
}

async function loadGaps() {
  try { const r = await adminAPI.getKnowledgeGaps({ days: 30, per_page: 1 }); if (r.code === 200) gapSummary.value = r.data.summary }
  catch (e) { console.error(e) }
}

async function loadWorkflowActions() {
  try { const r = await workflowAPI.getActions(); if (r.code === 200) workflowActions.value = r.data || [] }
  catch (e) { console.error(e) }
}

onMounted(() => { loadDashboard(); loadGaps(); loadWorkflowActions() })
</script>

<style scoped>
.admin-home { padding-bottom: 24px; }

/* 欢迎横幅 */
.welcome-card {
  margin-bottom: 24px;
  border-radius: var(--radius-lg) !important;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  border: none !important;
  position: relative;
  overflow: hidden;
}
.welcome-card::before {
  content: '';
  position: absolute; top: -40%; right: -10%;
  width: 400px; height: 400px;
  background: radial-gradient(circle, rgba(64,158,255,0.12), transparent);
  border-radius: 50%;
  pointer-events: none;
}
.welcome-card::after {
  content: '';
  position: absolute; bottom: -30%; left: 20%;
  width: 300px; height: 300px;
  background: radial-gradient(circle, rgba(103,194,58,0.08), transparent);
  border-radius: 50%;
  pointer-events: none;
}
.welcome-content {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 4px; position: relative; z-index: 1;
}
.welcome-badge {
  display: inline-block;
  background: rgba(255,255,255,0.12); color: rgba(255,255,255,0.85);
  font-size: 11px; font-weight: 600; padding: 2px 10px; border-radius: 10px;
  margin-bottom: 8px; letter-spacing: 0.5px;
  backdrop-filter: blur(4px); border: 1px solid rgba(255,255,255,0.08);
}
.welcome-content h2 { font-size: 24px; font-weight: 700; color: #fff; margin-bottom: 4px; }
.welcome-sub { color: rgba(255,255,255,0.6); font-size: 14px; }
.welcome-actions { display: flex; gap: 10px; }
.glow-btn {
  box-shadow: 0 4px 16px rgba(64,158,255,0.35);
  transition: all var(--transition-normal);
}
.glow-btn:hover { box-shadow: 0 6px 24px rgba(64,158,255,0.5); transform: translateY(-1px); }

/* 统计卡片 */
.stat-row { margin-bottom: 20px; }
.stat-card {
  margin-bottom: 20px; cursor: pointer;
  border-radius: var(--radius-md) !important;
  transition: all var(--transition-normal);
  position: relative; overflow: hidden;
}
.stat-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-hover) !important; }
.stat-card-inner { display: flex; align-items: center; gap: 14px; }
.stat-icon {
  width: 46px; height: 46px;
  display: flex; align-items: center; justify-content: center;
  border-radius: 12px; flex-shrink: 0;
  transition: all var(--transition-fast);
}
.stat-card:hover .stat-icon { transform: scale(1.05); }
.stat-value { font-size: 26px; font-weight: 800; color: var(--text-primary); line-height: 1.2; }
.stat-label { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }
.stat-trend {
  position: absolute; top: 12px; right: 14px; font-size: 12px;
}
.stat-trend .up { color: #67c23a; }
.stat-trend .down { color: #f56c6c; }

/* 快捷操作 */
.section-card { margin-bottom: 20px; border-radius: var(--radius-lg) !important; }
.section-header { display: flex; align-items: center; justify-content: space-between; }
.section-title { display: flex; align-items: center; gap: 8px; font-size: 16px; font-weight: 700; color: var(--text-primary); }
.workflow-btn {
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  padding: 18px 12px; border-radius: 12px; cursor: pointer;
  transition: all var(--transition-fast);
  border: 1px solid var(--border-lighter); text-align: center;
  margin-bottom: 12px;
}
.workflow-btn:hover {
  background: var(--primary-bg); border-color: var(--primary);
  transform: translateY(-3px); box-shadow: 0 6px 16px rgba(64,158,255,0.12);
}
.wf-icon {
  width: 44px; height: 44px;
  background: var(--primary-bg); border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  color: var(--primary);
}
.workflow-btn:hover .wf-icon { background: var(--primary); color: #fff; }
.wf-label { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.wf-desc { font-size: 11px; color: var(--text-secondary); line-height: 1.2; }

/* 图表 */
.chart-row { margin-bottom: 16px; }
.chart-card { margin-bottom: 16px; border-radius: var(--radius-md) !important; }
.chart { height: 280px; }
.chart-sm { height: 240px; }

/* 知识盲区 */
.gap-title { font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 12px; display: flex; align-items: center; gap: 6px; }
.tag-cloud { display: flex; flex-wrap: wrap; gap: 6px; }
.tag-cloud-item { display: flex; align-items: center; gap: 4px !important; }
.tag-cloud-item em { font-style: normal; font-size: 11px; opacity: 0.7; margin-left: 2px; }
.suggestion-list { display: flex; flex-direction: column; gap: 8px; }
.suggestion-item { display: flex; align-items: flex-start; gap: 6px; font-size: 13px; color: var(--text-regular); line-height: 1.5; }

.loading-wrapper { padding: 40px; background: #fff; border-radius: var(--radius-md); }
.empty-state { text-align: center; color: var(--text-secondary); padding: 24px; display: flex; flex-direction: column; align-items: center; gap: 8px; }

/* 卡片动画 - 覆盖全局 */
:deep(.card-animate) { animation: cardFadeInUp 0.5s ease both; }
@keyframes cardFadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
</style>
