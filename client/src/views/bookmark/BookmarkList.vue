<template>
  <div class="bookmark-list">
    <div class="page-header">
      <h2><el-icon><Star /></el-icon> 我的收藏</h2>
      <p>收藏的问答和文档，支持添加笔记</p>
    </div>

    <!-- 类型标签 -->
    <el-tabs v-model="activeTab" @tab-change="loadBookmarks">
      <el-tab-pane label="全部" name="all" />
      <el-tab-pane label="问答" name="qa" />
      <el-tab-pane label="文档" name="document" />
    </el-tabs>

    <!-- 收藏列表 -->
    <el-card v-if="bookmarks.length > 0" shadow="hover">
      <div v-for="item in bookmarks" :key="item.id" class="bookmark-item">
        <div class="bm-header">
          <el-tag :type="item.type === 'qa' ? 'primary' : 'success'" size="small" effect="plain">
            {{ item.type === 'qa' ? '问答' : '文档' }}
          </el-tag>
          <span class="bm-title">{{ item.target_title }}</span>
          <el-button link type="danger" size="small" @click="remove(item.id)">
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
        <p class="bm-preview">{{ item.target_preview || '暂无预览' }}</p>
        <!-- 笔记 -->
        <div class="bm-note" v-if="item.note">
          <el-icon :size="14"><EditPen /></el-icon>
          <span>{{ item.note }}</span>
        </div>
        <div class="bm-footer">
          <span class="bm-time">{{ item.created_at?.slice(0, 10) }}</span>
          <el-button link size="small" @click="editNote(item)">添加笔记</el-button>
        </div>
        <el-divider v-if="!$last" style="margin:8px 0" />
      </div>

      <el-pagination v-if="total > perPage" v-model:current-page="page"
        :page-size="perPage" :total="total" layout="prev,pager,next" @change="loadBookmarks"
        style="margin-top:16px;justify-content:center" />
    </el-card>

    <el-empty v-else description="还没有收藏，在问答或文档页点击⭐收藏" />

    <!-- 笔记编辑对话框 -->
    <el-dialog v-model="noteVisible" title="编辑笔记" width="400px">
      <el-input v-model="editingNote" type="textarea" :rows="4" placeholder="写下你的笔记..." />
      <template #footer>
        <el-button @click="noteVisible = false">取消</el-button>
        <el-button type="primary" @click="saveNote">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Star, Delete, EditPen } from '@element-plus/icons-vue'
import { bookmarkAPI } from '../../api'

const bookmarks = ref([])
const page = ref(1)
const perPage = ref(20)
const total = ref(0)
const activeTab = ref('all')
const noteVisible = ref(false)
const editingNote = ref('')
const editingId = ref(null)

async function loadBookmarks() {
  try {
    const params = { page: page.value, per_page: perPage.value }
    if (activeTab.value !== 'all') params.type = activeTab.value
    const res = await bookmarkAPI.list(params)
    if (res.code === 200) {
      bookmarks.value = res.data.list
      total.value = res.data.total
    }
  } catch (e) { console.error(e) }
}

async function remove(id) {
  try {
    await bookmarkAPI.remove(id)
    ElMessage.success('已取消收藏')
    loadBookmarks()
  } catch (e) { console.error(e) }
}

function editNote(item) {
  editingId.value = item.id
  editingNote.value = item.note || ''
  noteVisible.value = true
}

async function saveNote() {
  try {
    await bookmarkAPI.updateNote(editingId.value, { note: editingNote.value })
    ElMessage.success('笔记已更新')
    noteVisible.value = false
    loadBookmarks()
  } catch (e) { console.error(e) }
}

onMounted(loadBookmarks)
</script>

<style scoped>
.bookmark-list { max-width: 1000px; margin: 0 auto; }
.page-header { margin-bottom: 16px; }
.page-header h2 { font-size: 22px; color: #303133; display: flex; align-items: center; gap: 8px; }
.page-header p { color: #909399; font-size: 14px; margin-top: 4px; }
.bookmark-item { padding: 8px 0; }
.bm-header { display: flex; align-items: center; gap: 8px; }
.bm-title { flex: 1; font-weight: 600; color: #303133; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bm-preview { color: #909399; font-size: 13px; margin: 6px 0 4px; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
.bm-note { display: flex; align-items: center; gap: 4px; color: #e6a23c; font-size: 13px; background: #fdf6ec; padding: 4px 8px; border-radius: 4px; margin: 4px 0; }
.bm-footer { display: flex; justify-content: space-between; align-items: center; }
.bm-time { color: #c0c4cc; font-size: 12px; }
</style>
