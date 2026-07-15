<!-- ============================================================
     企业知识库 RAG 问答系统 - 知识搜索页面
     支持全文搜索 + 语义搜索混合检索
     ============================================================ -->

<template>
  <div class="search-page">
    <div class="search-container">
      <!-- 搜索框 -->
      <div class="search-box">
        <el-input
          v-model="keyword"
          placeholder="搜索知识库中的文档..."
          size="large"
          clearable
          @keydown.enter="handleSearch"
          @clear="handleClear"
        >
          <template #prefix>
            <el-icon><SearchIcon /></el-icon>
          </template>
          <template #append>
            <el-button @click="handleSearch" :loading="isSearching">
              搜索
            </el-button>
          </template>
        </el-input>
      </div>

      <!-- 筛选条件 -->
      <div class="search-filters" v-if="showFilters">
        <el-select v-model="categoryFilter" placeholder="全部分类" clearable size="small">
          <el-option
            v-for="cat in categories"
            :key="cat.id"
            :label="cat.name"
            :value="cat.id"
          />
        </el-select>
      </div>

      <!-- 搜索结果 -->
      <div v-if="searchResult" class="search-results">
        <div class="result-stats">
          搜索 <strong>"{{ searchResult.keyword }}"</strong>，
          找到 {{ searchResult.total }} 个结果
        </div>

        <div v-if="searchResult.list.length === 0" class="empty-result">
          <el-empty description="没有找到相关文档" />
        </div>

        <div v-else class="result-list">
          <el-card
            v-for="item in searchResult.list"
            :key="item.id"
            class="result-card"
            shadow="hover"
            @click="viewDocument(item.id)"
          >
            <div class="result-header">
              <h3 class="result-title">
                <el-icon><Document /></el-icon>
                {{ item.title }}
              </h3>
              <el-tag v-if="item._semantic" size="small" type="success" effect="plain">
                语义匹配
              </el-tag>
              <el-tag v-else size="small" type="primary" effect="plain">
                关键词匹配
              </el-tag>
            </div>
            <div class="result-meta">
              <span v-if="item.category_name">{{ item.category_name }}</span>
              <span v-if="item.file_type">· {{ item.file_type }}</span>
              <span v-if="item.chunk_count">· {{ item.chunk_count }} 个段落</span>
            </div>
            <p class="result-summary">{{ item.summary || '暂无摘要' }}</p>
          </el-card>
        </div>

        <!-- 分页 -->
        <div v-if="searchResult.pages > 1" class="pagination">
          <el-pagination
            v-model:current-page="currentPage"
            :page-size="10"
            :total="searchResult.total"
            layout="prev, pager, next"
            @current-change="handlePageChange"
          />
        </div>
      </div>

      <!-- 初始状态提示 -->
      <div v-else class="search-hint">
        <el-icon :size="48" color="#c0c4cc"><SearchIcon /></el-icon>
        <p>输入关键词搜索知识库文档</p>
      </div>
    </div>

    <!-- 文档预览抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      :title="currentDoc?.title || '文档预览'"
      size="50%"
    >
      <div v-if="currentDoc" class="doc-preview">
        <div class="doc-meta">
          <el-descriptions :column="2" size="small" border>
            <el-descriptions-item label="文件名">{{ currentDoc.file_name }}</el-descriptions-item>
            <el-descriptions-item label="类型">{{ currentDoc.file_type }}</el-descriptions-item>
            <el-descriptions-item label="分类">{{ currentDoc.category_name || '未分类' }}</el-descriptions-item>
            <el-descriptions-item label="上传时间">{{ currentDoc.created_at?.slice(0, 10) }}</el-descriptions-item>
          </el-descriptions>
        </div>
        <div class="doc-content">
          <h4>文档内容</h4>
          <div class="content-text">{{ currentDoc.content_text || '暂无文本内容' }}</div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search as SearchIcon, Document } from '@element-plus/icons-vue'
import { documentAPI } from '../../api'

const keyword = ref('')
const isSearching = ref(false)
const showFilters = ref(false)
const categoryFilter = ref(null)
const categories = ref([])
const searchResult = ref(null)
const currentPage = ref(1)

// 文档预览
const drawerVisible = ref(false)
const currentDoc = ref(null)

/** 执行搜索 */
async function handleSearch() {
  const q = keyword.value.trim()
  if (!q) {
    ElMessage.warning('请输入搜索关键词')
    return
  }

  isSearching.value = true
  try {
    const res = await documentAPI.search({
      q,
      page: currentPage.value,
      per_page: 10,
      category_id: categoryFilter.value || undefined,
    })
    if (res.code === 200) {
      searchResult.value = res.data
    }
  } catch (e) {
    console.error('搜索失败:', e)
    ElMessage.error('搜索失败，请稍后再试')
  } finally {
    isSearching.value = false
  }
}

/** 清除搜索 */
function handleClear() {
  searchResult.value = null
  currentPage.value = 1
}

/** 翻页 */
function handlePageChange(page) {
  currentPage.value = page
  handleSearch()
}

/** 查看文档 */
async function viewDocument(id) {
  try {
    const res = await documentAPI.getContent(id)
    if (res.code === 200) {
      currentDoc.value = res.data
      drawerVisible.value = true
    }
  } catch (e) {
    ElMessage.error('获取文档内容失败')
  }
}

/** 加载分类 */
async function loadCategories() {
  try {
    const res = await documentAPI.getCategories()
    if (res.code === 200) {
      categories.value = res.data || []
      showFilters.value = categories.value.length > 0
    }
  } catch (e) {
    console.error('加载分类失败:', e)
  }
}

onMounted(loadCategories)
</script>

<style scoped>
.search-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
}

.search-box {
  margin-bottom: 20px;
}

.search-box :deep(.el-input-group__append) {
  background: #409eff;
  border-color: #409eff;
}
.search-box :deep(.el-input-group__append .el-button) {
  color: #fff;
}

.search-filters {
  margin-bottom: 16px;
  display: flex;
  gap: 12px;
}

.search-results {
  margin-top: 8px;
}

.result-stats {
  color: #909399;
  font-size: 14px;
  margin-bottom: 16px;
}

.empty-result {
  padding: 60px 0;
}

.result-card {
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.3s;
}
.result-card:hover {
  transform: translateX(4px);
}

.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.result-title {
  font-size: 16px;
  color: #303133;
  margin: 0;
  flex: 1;
  display: flex;
  align-items: center;
  gap: 6px;
}

.result-meta {
  font-size: 13px;
  color: #909399;
  margin-bottom: 6px;
}

.result-summary {
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.pagination {
  text-align: center;
  margin-top: 20px;
}

.search-hint {
  text-align: center;
  padding: 100px 0;
  color: #c0c4cc;
}
.search-hint p {
  margin-top: 12px;
  font-size: 16px;
}

/* 文档预览 */
.doc-meta {
  margin-bottom: 20px;
}
.doc-content h4 {
  margin: 0 0 12px;
  color: #303133;
}
.content-text {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 8px;
  line-height: 1.8;
  white-space: pre-wrap;
  font-size: 14px;
  color: #303133;
  max-height: 500px;
  overflow-y: auto;
}
</style>
