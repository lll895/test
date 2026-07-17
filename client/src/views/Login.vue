<!-- ============================================================
     企业知识库 RAG 问答系统 - 登录/注册页面（灵动版）
     ============================================================ -->

<template>
  <div class="login-page">
    <!-- 动态背景 -->
    <div class="login-bg">
      <div class="bg-orb orb-1"></div>
      <div class="bg-orb orb-2"></div>
      <div class="bg-orb orb-3"></div>
      <div class="bg-grid"></div>
    </div>

    <!-- 左侧品牌区 -->
    <div class="login-brand">
      <div class="brand-content">
        <div class="brand-icon-wrap">
          <el-icon :size="40" color="#fff"><Reading /></el-icon>
        </div>
        <h1 class="brand-title">企业知识库</h1>
        <p class="brand-desc">基于 AI 的智能知识问答系统</p>
        <div class="brand-features">
          <div class="feature-item">
            <el-icon color="#409eff"><Document /></el-icon>
            <span>文档管理</span>
          </div>
          <div class="feature-item">
            <el-icon color="#67c23a"><ChatLineSquare /></el-icon>
            <span>智能问答</span>
          </div>
          <div class="feature-item">
            <el-icon color="#e6a23c"><Search /></el-icon>
            <span>高效检索</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧登录/注册表单 -->
    <div class="login-form-wrapper">
      <div class="login-form-box">
        <h2 class="form-title">{{ isLogin ? '欢迎回来' : '创建账号' }}</h2>
        <p class="form-subtitle">
          {{ isLogin ? '请登录您的账号继续使用' : '注册一个新账号开始使用' }}
        </p>

        <el-form
          ref="formRef"
          :model="form"
          :rules="formRules"
          class="login-form"
          @keyup.enter="handleSubmit"
        >
          <el-form-item prop="username">
            <el-input
              v-model="form.username"
              placeholder="用户名"
              :prefix-icon="User"
              size="large"
            />
          </el-form-item>

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

          <template v-if="!isLogin">
            <el-form-item prop="realName">
              <el-input v-model="form.realName" placeholder="真实姓名" :prefix-icon="Edit" size="large" />
            </el-form-item>
            <el-form-item prop="email">
              <el-input v-model="form.email" placeholder="邮箱（选填）" :prefix-icon="Message" size="large" />
            </el-form-item>
          </template>

          <!-- 忘记密码链接 -->
          <div v-if="isLogin" class="form-options">
            <label class="remember-me">
              <el-checkbox v-model="rememberMe" size="small" />
              <span>记住我</span>
            </label>
            <el-link type="primary" :underline="false" @click="showForgotDialog = true">
              忘记密码？
            </el-link>
          </div>

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

        <div class="form-footer">
          <span>{{ isLogin ? '还没有账号？' : '已有账号？' }}</span>
          <el-link type="primary" @click="toggleMode">
            {{ isLogin ? '立即注册' : '去登录' }}
          </el-link>
        </div>
      </div>
    </div>

    <!-- 忘记密码对话框 -->
    <el-dialog v-model="showForgotDialog" title="重置密码" width="400px" :close-on-click-modal="false" top="25vh">
      <template v-if="!resetStep.token">
        <p class="forgot-desc">请输入您的用户名和注册邮箱，我们将为您生成重置令牌。</p>
        <el-form :model="forgotForm" label-width="80px">
          <el-form-item label="用户名">
            <el-input v-model="forgotForm.username" placeholder="请输入用户名" />
          </el-form-item>
          <el-form-item label="邮箱">
            <el-input v-model="forgotForm.email" placeholder="请输入注册邮箱" />
          </el-form-item>
        </el-form>
        <div class="dialog-footer">
          <el-button @click="showForgotDialog = false">取消</el-button>
          <el-button type="primary" :loading="forgotLoading" @click="handleForgotPassword">
            获取重置令牌
          </el-button>
        </div>
      </template>
      <template v-else>
        <p class="forgot-desc">请输入收到的重置令牌和新密码。</p>
        <el-form :model="resetForm" label-width="100px">
          <el-form-item label="重置令牌">
            <el-input v-model="resetForm.token" placeholder="请输入重置令牌" />
          </el-form-item>
          <el-form-item label="新密码">
            <el-input v-model="resetForm.new_password" type="password" placeholder="至少6位" show-password />
          </el-form-item>
          <el-form-item label="确认密码">
            <el-input v-model="resetForm.confirm_password" type="password" placeholder="再次输入" show-password />
          </el-form-item>
        </el-form>
        <div class="dialog-footer">
          <el-button @click="resetStep.token = ''">返回</el-button>
          <el-button type="primary" :loading="resetLoading" @click="handleResetPassword">
            重置密码
          </el-button>
        </div>
      </template>
    </el-dialog>
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

const isLogin = ref(true)
const loading = ref(false)
const formRef = ref(null)
const rememberMe = ref(true)

const form = reactive({
  username: '', password: '', confirmPassword: '', realName: '', email: '',
})

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
      { validator: (rule, value, cb) => value === form.password ? cb() : cb(new Error('两次密码不一致')), trigger: 'blur' },
    ]
    rules.realName = [{ required: true, message: '请输入姓名', trigger: 'blur' }]
  }
  return rules
})

// 忘记密码
const showForgotDialog = ref(false)
const forgotLoading = ref(false)
const forgotForm = reactive({ username: '', email: '' })
const resetStep = reactive({ token: '' })
const resetForm = reactive({ token: '', new_password: '', confirm_password: '' })
const resetLoading = ref(false)

function toggleMode() {
  isLogin.value = !isLogin.value
  form.password = ''
  form.confirmPassword = ''
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    if (isLogin.value) {
      const res = await userStore.login(form.username, form.password)
      if (res.code === 200) {
        ElMessage.success('登录成功！')
        router.push('/')  // 自动根据角色跳转首页
      }
    } else {
      const res = await authAPI.register({
        username: form.username, password: form.password,
        real_name: form.realName, email: form.email,
      })
      if (res.code === 200) {
        ElMessage.success('注册成功，请登录')
        isLogin.value = true
        form.password = ''
      }
    }
  } catch (e) { /* handled by interceptor */ }
  finally { loading.value = false }
}

async function handleForgotPassword() {
  if (!forgotForm.username && !forgotForm.email) { ElMessage.warning('请输入用户名或邮箱'); return }
  forgotLoading.value = true
  try {
    const res = await authAPI.forgotPassword({ username: forgotForm.username || undefined, email: forgotForm.email || undefined })
    if (res.code === 200) {
      if (res.data?.reset_token) {
        resetStep.token = res.data.reset_token
        resetForm.token = res.data.reset_token
        ElMessage.success('重置令牌已生成（开发模式）')
      } else { ElMessage.success('如果该账号存在，重置令牌将通过邮箱发送'); showForgotDialog.value = false }
    }
  } catch (e) {}
  finally { forgotLoading.value = false }
}

async function handleResetPassword() {
  if (!resetForm.token || !resetForm.new_password) { ElMessage.warning('请填写完整信息'); return }
  if (resetForm.new_password.length < 6) { ElMessage.warning('密码至少6位'); return }
  if (resetForm.new_password !== resetForm.confirm_password) { ElMessage.warning('两次密码不一致'); return }
  resetLoading.value = true
  try {
    const res = await authAPI.resetPassword({ token: resetForm.token, new_password: resetForm.new_password })
    if (res.code === 200) { ElMessage.success('密码重置成功，请使用新密码登录'); showForgotDialog.value = false; isLogin.value = true }
  } catch (e) {}
  finally { resetLoading.value = false }
}
</script>

<style scoped>
.login-page {
  display: flex;
  height: 100vh;
  position: relative;
  overflow: hidden;
}

/* 动态背景 */
.login-bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
  overflow: hidden;
}
.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.4;
  animation: orbFloat 8s ease-in-out infinite;
}
.orb-1 {
  width: 500px; height: 500px;
  background: radial-gradient(circle, #409eff, #2a6eb0);
  top: -150px; left: -100px;
  animation-delay: 0s;
}
.orb-2 {
  width: 400px; height: 400px;
  background: radial-gradient(circle, #7928ca, #4a00e0);
  bottom: -100px; right: -80px;
  animation-delay: -3s;
}
.orb-3 {
  width: 300px; height: 300px;
  background: radial-gradient(circle, #f093fb, #f5576c);
  top: 50%; left: 30%;
  animation-delay: -5s;
}
.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
  background-size: 60px 60px;
}

@keyframes orbFloat {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -30px) scale(1.1); }
  66% { transform: translate(-20px, 20px) scale(0.95); }
}

/* 左侧品牌区域 */
.login-brand {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  position: relative;
  z-index: 1;
}
.brand-content {
  text-align: center;
  padding: 40px;
  animation: cardFadeInUp 0.8s ease;
}
.brand-icon-wrap {
  width: 80px; height: 80px;
  background: rgba(255,255,255,0.12);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 24px;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.1);
  box-shadow: 0 8px 32px rgba(0,0,0,0.2);
}
.brand-title {
  font-size: 36px;
  font-weight: 700;
  margin-bottom: 12px;
  background: linear-gradient(135deg, #fff, rgba(255,255,255,0.7));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.brand-desc {
  font-size: 16px;
  opacity: 0.8;
  margin-bottom: 32px;
}
.brand-features {
  display: flex;
  gap: 24px;
  justify-content: center;
}
.feature-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  opacity: 0.7;
  transition: opacity var(--transition-fast);
}
.feature-item:hover { opacity: 1; }

/* 右侧表单 */
.login-form-wrapper {
  width: 480px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255,255,255,0.95);
  backdrop-filter: blur(20px);
  border-radius: 32px 0 0 32px;
  position: relative;
  z-index: 1;
  box-shadow: -4px 0 24px rgba(0,0,0,0.1);
}
.login-form-box {
  width: 360px;
  animation: cardFadeInUp 0.6s ease 0.1s both;
}
@keyframes cardFadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
.form-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 6px;
}
.form-subtitle {
  color: var(--text-secondary);
  font-size: 14px;
  margin-bottom: 32px;
}
.login-form { width: 100%; }
.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: -8px 0 16px;
}
.remember-me {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
}
.submit-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  border-radius: 12px !important;
  margin-top: 4px;
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  border: none;
  box-shadow: 0 4px 12px rgba(64,158,255,0.3);
  transition: all var(--transition-normal);
}
.submit-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(64,158,255,0.4);
}
.form-footer {
  text-align: center;
  margin-top: 20px;
  color: var(--text-secondary);
  font-size: 14px;
}

/* 忘记密码对话框 */
.forgot-desc {
  color: var(--text-regular);
  font-size: 14px;
  margin-bottom: 16px;
  line-height: 1.6;
}
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}

/* 响应式 */
@media (max-width: 768px) {
  .login-brand { display: none; }
  .login-form-wrapper {
    width: 100%;
    border-radius: 0;
    background: rgba(255,255,255,0.98);
  }
}
</style>
