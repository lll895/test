<!-- ============================================================
     企业知识库 RAG 问答系统 - 登录/注册页面
     ============================================================ -->

<template>
  <div class="login-page">
    <!-- 左侧品牌区 -->
    <div class="login-brand">
      <div class="brand-content">
        <div class="brand-icon">
          <el-icon :size="48" color="#fff"><Reading /></el-icon>
        </div>
        <h1 class="brand-title">企业知识库</h1>
        <p class="brand-desc">基于 AI 的智能知识问答系统</p>
        <p class="brand-sub">上传文档 · 智能问答 · 高效检索</p>
      </div>
    </div>

    <!-- 右侧登录/注册表单 -->
    <div class="login-form-wrapper">
      <div class="login-form-box">
        <h2 class="form-title">{{ isLogin ? '欢迎登录' : '注册账号' }}</h2>
        <p class="form-subtitle">{{ isLogin ? '请输入您的账号信息' : '创建您的账号' }}</p>

        <el-form
          ref="formRef"
          :model="form"
          :rules="formRules"
          class="login-form"
          @keyup.enter="handleSubmit"
        >
          <!-- 用户名 -->
          <el-form-item prop="username">
            <el-input
              v-model="form.username"
              placeholder="用户名"
              :prefix-icon="User"
              size="large"
            />
          </el-form-item>

          <!-- 密码 -->
          <el-form-item prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="密码"
              :prefix-icon="Lock"
              size="large"
              show-password
            />
          </el-form-item>

          <!-- 确认密码（注册时显示） -->
          <el-form-item v-if="!isLogin" prop="confirmPassword">
            <el-input
              v-model="form.confirmPassword"
              type="password"
              placeholder="确认密码"
              :prefix-icon="Lock"
              size="large"
              show-password
            />
          </el-form-item>

          <!-- 真实姓名/邮箱（注册时显示） -->
          <template v-if="!isLogin">
            <el-form-item prop="realName">
              <el-input
                v-model="form.realName"
                placeholder="真实姓名"
                :prefix-icon="Edit"
                size="large"
              />
            </el-form-item>
            <el-form-item prop="email">
              <el-input
                v-model="form.email"
                placeholder="邮箱（选填）"
                :prefix-icon="Message"
                size="large"
              />
            </el-form-item>
          </template>

          <!-- 提交按钮 -->
          <el-form-item>
            <el-button
              type="primary"
              size="large"
              class="submit-btn"
              :loading="loading"
              @click="handleSubmit"
            >
              {{ isLogin ? '登 录' : '注 册' }}
            </el-button>
          </el-form-item>
        </el-form>

        <!-- 切换登录/注册 -->
        <div class="form-footer">
          <span>{{ isLogin ? '还没有账号？' : '已有账号？' }}</span>
          <el-link type="primary" @click="toggleMode">
            {{ isLogin ? '立即注册' : '去登录' }}
          </el-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Edit, Message, Reading } from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'
import { authAPI } from '../api'

const router = useRouter()
const userStore = useUserStore()

// 表单状态
const isLogin = ref(true)
const loading = ref(false)
const formRef = ref(null)

// 表单数据
const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  realName: '',
  email: '',
})

// 表单验证规则
const formRules = computed(() => {
  const rules = {
    username: [
      { required: true, message: '请输入用户名', trigger: 'blur' },
      { min: 3, max: 50, message: '用户名长度3-50位', trigger: 'blur' },
    ],
    password: [
      { required: true, message: '请输入密码', trigger: 'blur' },
      { min: 6, message: '密码至少6位', trigger: 'blur' },
    ],
  }

  if (!isLogin.value) {
    rules.confirmPassword = [
      { required: true, message: '请确认密码', trigger: 'blur' },
      {
        validator: (rule, value, callback) => {
          if (value !== form.password) {
            callback(new Error('两次密码不一致'))
          } else {
            callback()
          }
        },
        trigger: 'blur',
      },
    ]
    rules.realName = [
      { required: true, message: '请输入姓名', trigger: 'blur' },
    ]
  }

  return rules
})

/** 切换登录/注册模式 */
function toggleMode() {
  isLogin.value = !isLogin.value
  form.password = ''
  form.confirmPassword = ''
}

/** 提交表单 */
async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    if (isLogin.value) {
      // 登录
      const res = await userStore.login(form.username, form.password)
      if (res.code === 200) {
        ElMessage.success('登录成功！')
        const role = res.data.user.role
        // 根据角色跳转到不同首页
        if (role === 'admin') {
          router.push('/home')
        } else {
          router.push('/user-home')
        }
      }
    } else {
      // 注册
      const res = await authAPI.register({
        username: form.username,
        password: form.password,
        real_name: form.realName,
        email: form.email,
      })
      if (res.code === 200) {
        ElMessage.success('注册成功，请登录')
        isLogin.value = true
        form.password = ''
      }
    }
  } catch (e) {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* 登录页面布局 */
.login-page {
  display: flex;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* 左侧品牌区域 */
.login-brand {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.brand-content {
  text-align: center;
  padding: 40px;
}

.brand-icon {
  width: 96px;
  height: 96px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 24px;
  backdrop-filter: blur(10px);
}

.brand-title {
  font-size: 36px;
  font-weight: 700;
  margin-bottom: 12px;
  color: #fff;
}

.brand-desc {
  font-size: 18px;
  opacity: 0.9;
  margin-bottom: 8px;
}

.brand-sub {
  font-size: 14px;
  opacity: 0.7;
}

/* 右侧表单区域 */
.login-form-wrapper {
  width: 480px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  border-radius: 32px 0 0 32px;
}

.login-form-box {
  width: 360px;
}

.form-title {
  font-size: 28px;
  color: #303133;
  margin-bottom: 8px;
}

.form-subtitle {
  color: #909399;
  margin-bottom: 32px;
}

.login-form {
  width: 100%;
}

.submit-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  border-radius: 8px;
  margin-top: 8px;
}

.form-footer {
  text-align: center;
  margin-top: 24px;
  color: #909399;
  font-size: 14px;
}

/* 响应式 */
@media (max-width: 768px) {
  .login-brand {
    display: none;
  }
  .login-form-wrapper {
    width: 100%;
    border-radius: 0;
  }
}
</style>
