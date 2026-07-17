<!-- ============================================================
     企业知识库 RAG 问答系统 - 知识文档列表页面
     ============================================================ -->

<template>
  <div class="document-list page-container card-animate">
    <!-- 页面标题与操作 -->
    <div class="page-header">
      <div>
        <h2>知识文档</h2>
        <p>管理企业知识库中的所有文档</p>
      </div>
      <el-button v-if="userStore.isAdmin" type="primary" @click="$router.push('/documents/upload')">
        <el-icon><Upload /></el-icon>上传文档
      </el-button>
    </div>

    <!-- 搜索与筛选 -->
    <el-card shadow="hover" class="filter-card">
      <el-row :gutter="16" align="middle">
        <el-col :xs="24" :sm="8">
          <el-input
            v-model="keyword"
            placeholder="搜索文档标题..."
            :prefix-icon="Search"
            clearable
            @input="handleSearch"
          />
        </el-col>
        <el-col :xs="12" :sm="6">
          <el-select v-model="categoryId" placeholder="选择分类" clearable @change="loadDocuments">
            <el-option v-for="cat in categories" :key="cat.id" :label="cat.name" :value="cat.id" />
          </el-select>
        </el-col>
        <el-col :xs="12" :sm="4">
          <el-select v-model="statusFilter" placeholder="文档状态" clearable @change="loadDocuments">
            <el-option label="已完成" value="ready" />
            <el-option label="处理中" value="processing" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-col>
      </el-row>
    </el-card>

    <!-- 文档列表 -->
    <el-card shadow="hover">
      <el-table :data="documents" v-loading="loading" stripe style="width: 100%">
        <el-table-column label="文档标题" min-width="220">
          <template #default="{ row }">
            <el-link type="primary" :underline="false" class="doc-title-link" @click="showDetail(row)">
              <el-icon :size="18" color="#409eff"><Document /></el-icon>
              <span class="doc-title-text">{{ row.title }}</span>
              <el-tag v-if="row.version > 1" size="small" type="warning" class="version-badge">
                v{{ row.version }}
              </el-tag>
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="category_name" label="分类" width="110" />
        <el-table-column label="类型" width="70" align="center">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ row.file_type?.toUpperCase() || 'N/A' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="chunk_count" label="块数" width="65" align="center" />
        <el-table-column label="版本" width="70" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.version > 1 ? 'warning' : 'info'">
              v{{ row.version || 1 }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="uploader" label="上传者" width="110" />
        <el-table-column label="状态" width="95" align="center">
          <template #default="{ row }">
            <el-tag
              :type="row.status === 'ready' ? 'success' : row.status === 'processing' ? 'warning' : 'danger'"
              size="small"
            >
              {{ row.status === 'ready' ? '已完成' : row.status === 'processing' ? '处理中' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="175">
          <template #default="{ row }">
            {{ row.created_at?.slice(0, 19)?.replace('T', ' ') }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="showDetail(row)">查看</el-button>
            <el-button v-if="row.status === 'ready' && userStore.isAdmin" type="warning" link size="small" @click="startEdit(row)">编辑</el-button>
            <el-popconfirm v-if="userStore.isAdmin" title="确定删除此文档吗？" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button type="danger" link size="small">删除</el-button>
              </template>
            </el-popconfirm>
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
          @change="loadDocuments"
        />
      </div>
    </el-card>

    <!-- 文档详情对话框 -->
    <el-dialog v-model="detailVisible" :title="detailData?.title || '文档详情'" width="820px" top="5vh">
      <div v-if="detailLoading" class="detail-loading">
        <el-skeleton :rows="6" animated />
      </div>
      <div v-else-if="detailData" class="doc-detail">
        <!-- 元信息 -->
        <el-descriptions :column="3" border size="small" class="detail-meta">
          <el-descriptions-item label="分类">{{ detailData.category_name || '未分类' }}</el-descriptions-item>
          <el-descriptions-item label="文件类型">{{ detailData.file_type?.toUpperCase() }}</el-descriptions-item>
          <el-descriptions-item label="版本">
            <el-tag :type="(detailData.version || 1) > 1 ? 'warning' : 'info'" size="small">
              v{{ detailData.version || 1 }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="文本块数">{{ detailData.chunk_count }}</el-descriptions-item>
          <el-descriptions-item label="上传者">{{ detailData.uploader }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="detailData.status === 'ready' ? 'success' : 'danger'" size="small">
              {{ detailData.status === 'ready' ? '已完成' : '失败' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="版本说明" :span="3">
            {{ detailData.change_note || '无' }}
          </el-descriptions-item>
          <el-descriptions-item label="上传时间" :span="3">
            {{ detailData.created_at?.slice(0, 19)?.replace('T', ' ') }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 版本历史按钮 -->
        <div v-if="detailData.version_group_id" class="version-history-btn">
          <el-button size="small" @click="showVersionHistory(detailData)">
            <el-icon><Clock /></el-icon>查看版本历史
          </el-button>
        </div>

        <!-- 摘要（可编辑） -->
        <div class="detail-section">
          <h4>摘要</h4>
          <el-input
            v-if="editingDoc?.id === detailData.id"
            v-model="editForm.summary"
            type="textarea"
            :rows="2"
            placeholder="文档摘要"
          />
          <p v-else>{{ detailData.summary || '暂无摘要' }}</p>
        </div>

        <!-- 文档内容（可编辑） -->
        <div class="detail-section">
          <div class="section-header">
            <h4>文档内容</h4>
            <el-button
              v-if="editingDoc?.id === detailData.id"
              type="primary"
              size="small"
              :loading="savingEdit"
              @click="saveEdit"
            >
              保存修改
            </el-button>
            <el-button
              v-else-if="detailData.status === 'ready'"
              type="warning"
              size="small"
              @click="startEdit(detailData)"
            >
              <el-icon><Edit /></el-icon>编辑内容
            </el-button>
          </div>
          <el-input
            v-if="editingDoc?.id === detailData.id"
            v-model="editForm.content_text"
            type="textarea"
            :rows="15"
            placeholder="文档内容"
            class="content-editor"
          />
          <div v-else class="content-preview">{{ detailData.content_text || '暂无内容' }}</div>
        </div>
      </div>
    </el-dialog>

    <!-- 版本历史对话框 -->
    <el-dialog v-model="versionVisible" title="版本历史" width="600px">
      <div v-if="versionsLoading" class="detail-loading">
        <el-skeleton :rows="4" animated />
      </div>
      <el-timeline v-else v-loading="versionsLoading">
        <el-timeline-item
          v-for="ver in versionList"
          :key="ver.id"
          :timestamp="ver.created_at?.slice(0, 19)?.replace('T', ' ')"
          :color="ver.id === currentVersionId ? '#409eff' : '#e4e7ed'"
          placement="top"
        >
          <div class="version-item" :class="{ 'current-version': ver.id === currentVersionId }">
            <div class="version-header">
              <el-tag :type="ver.id === currentVersionId ? 'primary' : 'info'" size="small">
                v{{ ver.version }}
              </el-tag>
              <span v-if="ver.id === currentVersionId" class="current-tag">当前版本</span>
              <span class="version-uploader">{{ ver.uploader }}</span>
            </div>
            <p class="version-note">{{ ver.change_note || '无说明' }}</p>
          </div>
        </el-timeline-item>
      </el-timeline>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload, Search, Document, Clock, Edit } from '@element-plus/icons-vue'
import { documentAPI } from '../../api'
import { useUserStore } from '../../stores/user'

const userStore = useUserStore()

const documents = ref([])
const categories = ref([])
const loading = ref(false)
const keyword = ref('')
const categoryId = ref(null)
const statusFilter = ref(null)
const page = ref(1)
const perPage = ref(10)
const total = ref(0)

// 详情相关
const detailVisible = ref(false)
const detailLoading = ref(false)
const detailData = ref(null)

// 编辑相关
const editingDoc = ref(null)
const savingEdit = ref(false)
const editForm = ref({ summary: '', content_text: '' })

// 版本历史
const versionVisible = ref(false)
const versionsLoading = ref(false)
const versionList = ref([])
const currentVersionId = ref(null)

let searchTimer = null

/** 加载文档列表 */
async function loadDocuments() {
  loading.value = true
  try {
    const params = {
      page: page.value,
      per_page: perPage.value,
      keyword: keyword.value || undefined,
      category_id: categoryId.value || undefined,
      status: statusFilter.value || undefined,
    }
    const res = await documentAPI.list(params)
    if (res.code === 200) {
      documents.value = res.data.list
      total.value = res.data.total
    }
  } catch (e) {
    console.error('加载文档失败:', e)
  } finally {
    loading.value = false
  }
}

/** 搜索防抖 */
function handleSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    page.value = 1
    loadDocuments()
  }, 300)
}

/** 查看文档详情 */
async function showDetail(row) {
  detailVisible.value = true
  detailLoading.value = true
  detailData.value = null
  editingDoc.value = null
  editForm.value = { summary: '', content_text: '' }
  try {
    const res = await documentAPI.detail(row.id)
    if (res.code === 200) {
      detailData.value = res.data
    }
  } catch (e) {
    console.error('加载文档详情失败:', e)
  } finally {
    detailLoading.value = false
  }
}

/** 开始编辑 - 先加载完整文档详情，再进入编辑模式 */
async function startEdit(doc) {
  detailVisible.value = true
  detailLoading.value = true
  editingDoc.value = doc  // 标记为编辑模式
  try {
    const res = await documentAPI.detail(doc.id)
    if (res.code === 200) {
      detailData.value = res.data
      editForm.value = {
        summary: res.data.summary || '',
        content_text: res.data.content_text || '',
      }
    }
  } catch (e) {
    console.error('加载文档详情失败:', e)
  } finally {
    detailLoading.value = false
  }
}

/** 保存编辑 */
async function saveEdit() {
  if (!editForm.value.content_text) {
    ElMessage.warning('内容不能为空')
    return
  }
  savingEdit.value = true
  try {
    const res = await documentAPI.updateContent(detailData.value.id, {
      content_text: editForm.value.content_text,
      summary: editForm.value.summary,
    })
    if (res.code === 200) {
      ElMessage.success('文档已更新并重新索引')
      detailData.value = res.data
      editingDoc.value = null
      loadDocuments()
    }
  } catch (e) {
    console.error('保存失败:', e)
  } finally {
    savingEdit.value = false
  }
}

/** 查看版本历史 */
async function showVersionHistory(doc) {
  versionVisible.value = true
  versionsLoading.value = true
  versionList.value = []
  currentVersionId.value = doc.id
  try {
    const res = await documentAPI.getVersions(doc.id)
    if (res.code === 200) {
      versionList.value = res.data.versions || []
      currentVersionId.value = res.data.current_id
    }
  } catch (e) {
    console.error('加载版本历史失败:', e)
  } finally {
    versionsLoading.value = false
  }
}

/** 删除文档 */
async function handleDelete(id) {
  try {
    const res = await documentAPI.delete(id)
    if (res.code === 200) {
      ElMessage.success('文档已删除')
      loadDocuments()
    }
  } catch (e) {
    console.error('删除失败:', e)
  }
}

/** 加载分类 */
async function loadCategories() {
  try {
    const res = await documentAPI.getCategories()
    if (res.code === 200) {
      categories.value = res.data
    }
  } catch (e) {
    console.error('加载分类失败:', e)
  }
}

onMounted(() => {
  loadCategories()
  loadDocuments()
})
</script>

<style scoped>
.document-list {
  max-width: 1400px;
  margin: 0 auto;
}

.filter-card {
  margin-bottom: 20px;
}

.doc-title-link {
  font-size: 14px;
}
.doc-title-text {
  margin-left: 6px;
}
.doc-title-link:hover .doc-title-text {
  color: var(--primary-light);
}
.version-badge {
  margin-left: 6px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

/* 详情 */
.detail-loading {
  padding: 20px;
}
.doc-detail {
  max-height: 68vh;
  overflow-y: auto;
}
.detail-meta {
  margin-bottom: 16px;
}
.detail-section {
  margin-bottom: 16px;
}
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.detail-section h4 {
  font-size: 15px;
  color: var(--text-primary);
  padding-bottom: 6px;
  border-bottom: 1px solid var(--border-lighter);
}
.detail-section p {
  color: var(--text-regular);
  line-height: 1.6;
  font-size: 14px;
}
.content-preview {
  background: var(--primary-bg);
  padding: 16px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  line-height: 1.7;
  white-space: pre-wrap;
  max-height: 400px;
  overflow-y: auto;
  color: var(--text-primary);
}
.content-editor {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
}

/* 版本历史 */
.version-history-btn {
  margin: 12px 0;
  text-align: right;
}
.version-item {
  padding: 8px 0;
}
.version-item.current-version {
  background: var(--primary-bg);
  border-radius: var(--radius-sm);
  padding: 8px 12px;
}
.version-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.current-tag {
  font-size: 12px;
  color: var(--primary);
  font-weight: 600;
}
.version-uploader {
  margin-left: auto;
  color: var(--text-secondary);
  font-size: 13px;
}
.version-note {
  color: var(--text-regular);
  font-size: 13px;
  margin: 4px 0 0 12px;
}
</style>
