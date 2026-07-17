<!-- ============================================================
     企业知识库 RAG 问答系统 - 上传文档页面
     ============================================================ -->

<template>
  <div class="document-upload page-container card-animate">
    <div class="page-header">
      <h2>上传文档</h2>
      <p>支持 PDF、Word、TXT、Markdown 格式</p>
    </div>

    <el-alert
      title="仅管理员可上传文档"
      type="warning"
      show-icon
      :closable="false"
      class="admin-note"
    />

    <el-row :gutter="20">
      <el-col :xs="24" :lg="16">
        <el-card shadow="hover">
          <template #header>
            <span>选择文件</span>
          </template>

          <!-- 拖拽上传区域 -->
          <el-upload
            ref="uploadRef"
            drag
            :auto-upload="false"
            :limit="1"
            accept=".pdf,.docx,.txt,.md"
            :on-change="handleFileChange"
            :on-exceed="() => ElMessage.warning('每次只能上传一个文件')"
          >
            <el-icon class="upload-icon" :size="48"><UploadFilled /></el-icon>
            <div class="upload-text">
              <p>将文件拖拽到此处，或 <em>点击选择</em></p>
              <p class="upload-hint">支持 PDF、Word（.docx）、TXT、Markdown 文件</p>
            </div>
          </el-upload>

          <!-- 文件信息 -->
          <div v-if="selectedFile" class="file-info">
            <div class="file-info-header">
              <el-icon :size="24" color="#409eff"><Document /></el-icon>
              <div class="file-info-text">
                <p class="file-name">{{ selectedFile.name }}</p>
                <p class="file-size">{{ formatSize(selectedFile.size) }}</p>
              </div>
              <el-button type="danger" link @click="removeFile">移除</el-button>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 文档信息表单 -->
      <el-col :xs="24" :lg="8">
        <el-card shadow="hover">
          <template #header>
            <span>文档信息</span>
          </template>

          <el-form :model="form" label-position="top">
            <el-form-item label="文档标题">
              <el-input v-model="form.title" placeholder="留空则使用文件名" />
            </el-form-item>

            <el-form-item label="文档分类">
              <el-select v-model="form.category_id" placeholder="选择分类" style="width: 100%">
                <el-option
                  v-for="cat in categories"
                  :key="cat.id"
                  :label="cat.name"
                  :value="cat.id"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="版本说明（选填）">
              <el-input
                v-model="form.change_note"
                placeholder="例如：更新了第三章内容"
                :maxlength="200"
                show-word-limit
              />
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                :loading="uploading"
                :disabled="!selectedFile"
                style="width: 100%"
                @click="handleUpload"
              >
                {{ uploading ? '正在上传并处理...' : '开始上传' }}
              </el-button>
            </el-form-item>
          </el-form>

          <el-alert
            v-if="uploadResult"
            :title="uploadResult"
            :type="uploadSuccess ? 'success' : 'error'"
            show-icon
            closable
          />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { UploadFilled, Document } from '@element-plus/icons-vue'
import { documentAPI } from '../../api'
import { useUserStore } from '../../stores/user'

const router = useRouter()
const userStore = useUserStore()

const categories = ref([])
const selectedFile = ref(null)
const uploading = ref(false)
const uploadResult = ref('')
const uploadSuccess = ref(false)

const form = ref({
  title: '',
  category_id: null,
  change_note: '',
})

/** 文件选择 */
function handleFileChange(file) {
  selectedFile.value = file.raw
}

/** 移除文件 */
function removeFile() {
  selectedFile.value = null
  uploadResult.value = ''
}

/** 格式化文件大小 */
function formatSize(bytes) {
  if (!bytes) return ''
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let size = bytes
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024
    i++
  }
  return `${size.toFixed(1)} ${units[i]}`
}

/** 上传文档 */
async function handleUpload() {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }

  uploading.value = true
  uploadResult.value = ''

  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    if (form.value.title) {
      formData.append('title', form.value.title)
    }
    if (form.value.category_id) {
      formData.append('category_id', form.value.category_id)
    }
    if (form.value.change_note) {
      formData.append('change_note', form.value.change_note)
    }

    const res = await documentAPI.upload(formData)
    if (res.code === 200) {
      uploadSuccess.value = true
      uploadResult.value = '文档上传并处理成功！'
      ElMessage.success('上传成功')
      // 重置
      selectedFile.value = null
      form.value.title = ''
      form.value.change_note = ''
    } else {
      uploadSuccess.value = false
      uploadResult.value = res.message || '上传失败'
    }
  } catch (e) {
    uploadSuccess.value = false
    uploadResult.value = '上传失败，请重试'
  } finally {
    uploading.value = false
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
  if (!userStore.isAdmin) {
    ElMessage.error('仅管理员可上传文档')
    router.push('/documents')
    return
  }
  loadCategories()
})
</script>

<style scoped>
.document-upload {
  max-width: 1200px;
  margin: 0 auto;
}

.admin-note {
  margin-bottom: 16px;
}

.upload-icon {
  margin-bottom: 16px;
}

.upload-text p {
  color: var(--text-regular);
  font-size: 14px;
}
.upload-text em {
  color: var(--primary);
  font-style: normal;
}
.upload-hint {
  font-size: 12px !important;
  color: var(--text-secondary) !important;
  margin-top: 8px;
}

.file-info {
  margin-top: 20px;
  padding: 16px;
  background: var(--primary-bg);
  border-radius: var(--radius-sm);
}

.file-info-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-info-text {
  flex: 1;
}

.file-name {
  font-weight: 600;
  color: var(--text-primary);
}

.file-size {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 2px;
}
</style>
