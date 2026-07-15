<!-- ============================================================
     企业知识库 RAG 问答系统 - 分类管理页面（管理员）
     ============================================================ -->

<template>
  <div class="category-manage">
    <div class="page-header">
      <div>
        <h2>分类管理</h2>
        <p>管理知识文档的分类体系</p>
      </div>
      <el-button type="primary" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>新建分类
      </el-button>
    </div>

    <!-- 分类列表 -->
    <el-card shadow="hover">
      <el-table :data="categories" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="name" label="分类名称" min-width="200">
          <template #default="{ row }">
            <div class="category-name">
              <el-icon :size="18" color="#409eff"><FolderOpened /></el-icon>
              <strong>{{ row.name }}</strong>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="300" />
        <el-table-column prop="doc_count" label="文档数" width="100" align="center" />
        <el-table-column prop="sort_order" label="排序" width="80" align="center" />
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">
            {{ row.created_at?.slice(0, 10) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-popconfirm
              title="确定删除此分类吗？"
              @confirm="handleDelete(row.id)"
            >
              <template #reference>
                <el-button type="danger" link size="small">
                  <el-icon><Delete /></el-icon>删除
                </el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建分类对话框 -->
    <el-dialog v-model="dialogVisible" title="新建分类" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="分类名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入分类名称" />
        </el-form-item>
        <el-form-item label="描述说明">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="分类的描述（选填）"
          />
        </el-form-item>
        <el-form-item label="排序序号">
          <el-input-number v-model="form.sort_order" :min="0" :max="999" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleCreate">
          确定创建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Delete, FolderOpened } from '@element-plus/icons-vue'
import { documentAPI } from '../../api'

const categories = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const submitting = ref(false)

const form = ref({
  name: '',
  description: '',
  sort_order: 0,
})

const rules = {
  name: [
    { required: true, message: '请输入分类名称', trigger: 'blur' },
    { max: 50, message: '分类名称不能超过50字', trigger: 'blur' },
  ],
}

/** 加载分类列表 */
async function loadCategories() {
  loading.value = true
  try {
    const res = await documentAPI.getCategories()
    if (res.code === 200) {
      categories.value = res.data
    }
  } catch (e) {
    console.error('加载分类失败:', e)
  } finally {
    loading.value = false
  }
}

/** 显示创建对话框 */
function showCreateDialog() {
  form.value = { name: '', description: '', sort_order: 0 }
  dialogVisible.value = true
}

/** 创建分类 */
async function handleCreate() {
  submitting.value = true
  try {
    const res = await documentAPI.createCategory({
      name: form.value.name,
      description: form.value.description,
      sort_order: form.value.sort_order,
    })
    if (res.code === 200) {
      ElMessage.success('分类创建成功')
      dialogVisible.value = false
      loadCategories()
    }
  } catch (e) {
    console.error('创建分类失败:', e)
  } finally {
    submitting.value = false
  }
}

/** 删除分类 */
async function handleDelete(id) {
  try {
    const res = await documentAPI.deleteCategory(id)
    if (res.code === 200) {
      ElMessage.success('分类已删除')
      loadCategories()
    }
  } catch (e) {
    console.error('删除分类失败:', e)
  }
}

onMounted(loadCategories)
</script>

<style scoped>
.category-manage {
  max-width: 1200px;
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

.category-name {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
