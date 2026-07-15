<!-- ============================================================
     企业知识库 RAG 问答系统 - 知识文档列表页面
     ============================================================ -->

<template>
  <div class="document-list">
    <!-- 页面标题与操作 -->
    <div class="page-header">
      <div>
        <h2>知识文档</h2>
        <p>管理企业知识库中的所有文档</p>
      </div>
      <el-button type="primary" @click="$router.push('/documents/upload')">
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
            <el-option
              v-for="cat in categories"
              :key="cat.id"
              :label="cat.name"
              :value="cat.id"
            />
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
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="category_name" label="分类" width="120" />
        <el-table-column prop="file_type" label="类型" width="80" align="center">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ row.file_type?.toUpperCase() }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="chunk_count" label="文本块" width="80" align="center" />
        <el-table-column prop="uploader" label="上传者" width="120" />
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag
              :type="row.status === 'ready' ? 'success' : row.status === 'processing' ? 'warning' : 'danger'"
              size="small"
            >
              {{ row.status === 'ready' ? '已完成' : row.status === 'processing' ? '处理中' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="180">
          <template #default="{ row }">
            {{ row.created_at?.slice(0, 19)?.replace('T', ' ') }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="showDetail(row)">查看</el-button>
            <el-popconfirm title="确定删除此文档吗？" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button type="danger" link size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
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
    <el-dialog v-model="detailVisible" :title="detailData?.title || '文档详情'" width="800px" top="5vh">
      <div v-if="detailLoading" class="detail-loading">
        <el-skeleton :rows="6" animated />
      </div>
      <div v-else-if="detailData" class="doc-detail">
        <!-- 元信息 -->
        <el-descriptions :column="3" border size="small" class="detail-meta">
          <el-descriptions-item label="分类">{{ detailData.category_name || '未分类' }}</el-descriptions-item>
          <el-descriptions-item label="文件类型">{{ detailData.file_type?.toUpperCase() }}</el-descriptions-item>
          <el-descriptions-item label="文本块数">{{ detailData.chunk_count }}</el-descriptions-item>
          <el-descriptions-item label="上传者">{{ detailData.uploader }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag
              :type="detailData.status === 'ready' ? 'success' : 'danger'"
              size="small"
            >{{ detailData.status === 'ready' ? '已完成' : '失败' }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="上传时间">{{ detailData.created_at?.slice(0, 10) }}</el-descriptions-item>
        </el-descriptions>

        <!-- 摘要 -->
        <div v-if="detailData.summary" class="detail-section">
          <h4>摘要</h4>
          <p>{{ detailData.summary }}</p>
        </div>

        <!-- 文本内容 -->
        <div v-if="detailData.content_text" class="detail-section">
          <h4>文档内容</h4>
          <div class="content-preview">{{ detailData.content_text }}</div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload, Search, Document } from '@element-plus/icons-vue'
import { documentAPI } from '../../api'

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

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
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
  color: #66b1ff;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

/* 详情样式 */
.detail-loading {
  padding: 20px;
}

.doc-detail {
  max-height: 65vh;
  overflow-y: auto;
}

.detail-meta {
  margin-bottom: 20px;
}

.detail-section {
  margin-bottom: 16px;
}
.detail-section h4 {
  font-size: 15px;
  color: #303133;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid #ebeef5;
}
.detail-section p {
  color: #606266;
  line-height: 1.6;
  font-size: 14px;
}

.content-preview {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.7;
  white-space: pre-wrap;
  max-height: 400px;
  overflow-y: auto;
  color: #303133;
}
</style>
