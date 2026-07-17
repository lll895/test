<!-- ============================================================
     企业知识库 RAG 问答系统 - 个人信息页面
     ============================================================ -->

<template>
  <div class="profile-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>个人信息</h2>
      <p>查看和编辑您的个人资料</p>
    </div>

    <el-row :gutter="24">
      <!-- 左侧：头像与基本信息 -->
      <el-col :xs="24" :md="8">
        <el-card shadow="hover" class="avatar-card">
          <div class="avatar-section">
            <el-avatar :size="100" :icon="UserFilled" class="profile-avatar" />
            <h3>{{ userStore.displayName }}</h3>
            <el-tag :type="userStore.isAdmin ? 'danger' : 'info'" size="small">
              {{ userStore.roleText }}
            </el-tag>
          </div>
          <el-divider />
          <div class="info-list">
            <div class="info-item">
              <span class="label">用户名</span>
              <span class="value">{{ userProfile.username }}</span>
            </div>
            <div class="info-item">
              <span class="label">角色</span>
              <span class="value">{{ userStore.roleText }}</span>
            </div>
            <div class="info-item">
              <span class="label">注册时间</span>
              <span class="value">{{ userProfile.created_at?.slice(0, 10) || '未知' }}</span>
            </div>
            <div class="info-item">
              <span class="label">最后登录</span>
              <span class="value">{{ userProfile.last_login?.slice(0, 19)?.replace('T', ' ') || '未知' }}</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：编辑表单 -->
      <el-col :xs="24" :md="16">
        <el-card shadow="hover">
          <template #header>
            <span>编辑资料</span>
          </template>

          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            label-width="100px"
            class="profile-form"
          >
            <el-form-item label="真实姓名" prop="real_name">
              <el-input v-model="form.real_name" placeholder="请输入真实姓名" />
            </el-form-item>

            <el-form-item label="邮箱" prop="email">
              <el-input v-model="form.email" placeholder="请输入邮箱" />
            </el-form-item>

            <el-divider content-position="left">修改密码（选填）</el-divider>

            <el-form-item label="原密码" prop="old_password">
              <el-input
                v-model="form.old_password"
                type="password"
                placeholder="输入原密码以修改密码"
                show-password
              />
            </el-form-item>

            <el-form-item label="新密码" prop="new_password">
              <el-input
                v-model="form.new_password"
                type="password"
                placeholder="留空则不修改"
                show-password
              />
            </el-form-item>

            <el-form-item label="确认密码" prop="confirm_password">
              <el-input
                v-model="form.confirm_password"
                type="password"
                placeholder="再次输入新密码"
                show-password
              />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" :loading="saving" @click="handleSave">
                保存修改
              </el-button>
              <el-button @click="resetForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 问答统计卡片 -->
        <el-card shadow="hover" class="stats-card">
          <template #header>
            <span>我的问答统计</span>
          </template>
          <el-row :gutter="16">
            <el-col :span="6" v-for="stat in qaStats" :key="stat.label">
              <div class="stat-item">
                <span class="stat-value">{{ stat.value }}</span>
                <span class="stat-label">{{ stat.label }}</span>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { UserFilled } from '@element-plus/icons-vue'
import { useUserStore } from '../../stores/user'
import { authAPI, qaAPI } from '../../api'

const userStore = useUserStore()
const formRef = ref(null)
const saving = ref(false)

// 当前用户信息
const userProfile = ref({})

// 表单数据
const form = reactive({
  real_name: '',
  email: '',
  old_password: '',
  new_password: '',
  confirm_password: '',
})

// 表单验证
const rules = {
  real_name: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
  email: [{ type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }],
  new_password: [{ min: 6, message: '密码至少6位', trigger: 'blur' }],
  confirm_password: [
    {
      validator: (rule, value, callback) => {
        if (value && value !== form.new_password) {
          callback(new Error('两次密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

// 问答统计数据
const qaStats = ref([
  { label: '总问答', value: 0 },
  { label: '今日', value: 0 },
  { label: '有用率', value: '0%' },
  { label: '平均响应', value: '0ms' },
])

/** 加载个人信息 */
async function loadProfile() {
  try {
    const res = await authAPI.getProfile()
    if (res.code === 200) {
      userProfile.value = res.data
      form.real_name = res.data.real_name || ''
      form.email = res.data.email || ''
    }
  } catch (e) {
    console.error('加载个人信息失败:', e)
  }
}

/** 加载问答统计 */
async function loadStats() {
  try {
    const res = await qaAPI.getStats()
    if (res.code === 200) {
      qaStats.value = [
        { label: '总问答', value: res.data.total_qa },
        { label: '今日', value: res.data.today_qa },
        { label: '有用率', value: `${res.data.useful_rate}%` },
        { label: '平均响应', value: `${res.data.avg_response_time_ms}ms` },
      ]
    }
  } catch (e) {
    console.error('加载统计失败:', e)
  }
}

/** 保存修改 */
async function handleSave() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    const payload = {
      real_name: form.real_name,
      email: form.email,
    }
    if (form.old_password && form.new_password) {
      payload.old_password = form.old_password
      payload.new_password = form.new_password
    }

    const res = await authAPI.updateProfile(payload)
    if (res.code === 200) {
      ElMessage.success('个人信息已更新')
      // 刷新 store 中的用户信息
      await userStore.fetchProfile()
      // 重置密码字段
      form.old_password = ''
      form.new_password = ''
      form.confirm_password = ''
    }
  } catch (e) {
    console.error('保存失败:', e)
  } finally {
    saving.value = false
  }
}

/** 重置表单 */
function resetForm() {
  form.real_name = userProfile.value.real_name || ''
  form.email = userProfile.value.email || ''
  form.old_password = ''
  form.new_password = ''
  form.confirm_password = ''
}

onMounted(() => {
  loadProfile()
  loadStats()
})
</script>

<style scoped>
.profile-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
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

/* 头像卡片 */
.avatar-card {
  margin-bottom: 24px;
}
.avatar-section {
  text-align: center;
  padding: 20px 0;
}
.avatar-section h3 {
  margin-top: 16px;
  font-size: 18px;
  color: #303133;
}
.profile-avatar {
  background: #409eff;
}

/* 信息列表 */
.info-list {
  padding: 0 8px;
}
.info-item {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid #f5f5f5;
}
.info-item:last-child {
  border-bottom: none;
}
.info-item .label {
  color: #909399;
  font-size: 14px;
}
.info-item .value {
  color: #303133;
  font-size: 14px;
  font-weight: 500;
}

/* 表单 */
.profile-form {
  max-width: 500px;
}

/* 统计卡片 */
.stats-card {
  margin-top: 24px;
}
.stat-item {
  text-align: center;
  padding: 12px 0;
}
.stat-value {
  display: block;
  font-size: 28px;
  font-weight: 700;
  color: #409eff;
}
.stat-label {
  display: block;
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}
</style>
