<!-- ============================================================
     企业知识库 RAG 问答系统 - 工作流申请表单
     功能：请假/报销/出差/入职/加班等申请表单
     ============================================================ -->

<template>
  <div class="workflow-form-page">
    <div class="page-header">
      <el-button text @click="$router.back()">
        <el-icon><ArrowLeft /></el-icon> 返回
      </el-button>
      <h2>{{ action?.label || '申请' }}</h2>
      <p>{{ action?.description || '请填写以下信息提交申请' }}</p>
    </div>

    <el-row :gutter="24">
      <el-col :xs="24" :md="16">
        <el-card shadow="hover">
          <template #header>
            <span>{{ action?.label || '申请表单' }}</span>
          </template>

          <el-form :model="form" :rules="rules" ref="formRef" label-width="100px" v-loading="loading">
            <!-- 根据动作类型显示不同字段 -->
            <el-form-item v-if="showField('applicant')" label="申请人">
              <el-input v-model="form.applicant" :placeholder="userStore.displayName" disabled />
            </el-form-item>

            <el-form-item v-if="showField('title')" label="标题" prop="title">
              <el-input v-model="form.title" :placeholder="`请输入${actionName}标题`" />
            </el-form-item>

            <!-- 请假类型 -->
            <el-form-item v-if="showField('leaveType')" label="请假类型" prop="leaveType">
              <el-select v-model="form.leaveType" placeholder="请选择" style="width:100%">
                <el-option label="年假" value="annual" />
                <el-option label="病假" value="sick" />
                <el-option label="事假" value="personal" />
                <el-option label="调休" value="compensatory" />
                <el-option label="婚假" value="marriage" />
                <el-option label="产假" value="maternity" />
              </el-select>
            </el-form-item>

            <!-- 费用类型 -->
            <el-form-item v-if="showField('expenseType')" label="费用类型" prop="expenseType">
              <el-select v-model="form.expenseType" placeholder="请选择" style="width:100%">
                <el-option label="交通费" value="transport" />
                <el-option label="住宿费" value="hotel" />
                <el-option label="餐饮补贴" value="meal" />
                <el-option label="办公用品" value="office" />
                <el-option label="其他" value="other" />
              </el-select>
            </el-form-item>

            <!-- 出差目的地 -->
            <el-form-item v-if="showField('destination')" label="目的地" prop="destination">
              <el-input v-model="form.destination" placeholder="请输入出差地点" />
            </el-form-item>

            <!-- 时间范围 -->
            <el-form-item v-if="showField('dateRange')" label="日期范围" prop="dateRange">
              <el-date-picker
                v-model="form.dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                style="width:100%"
              />
            </el-form-item>

            <!-- 单日日期 -->
            <el-form-item v-if="showField('date')" label="日期" prop="date">
              <el-date-picker v-model="form.date" type="date" placeholder="选择日期" style="width:100%" />
            </el-form-item>

            <!-- 金额 -->
            <el-form-item v-if="showField('amount')" label="金额(元)" prop="amount">
              <el-input-number v-model="form.amount" :min="0" :precision="2" style="width:200px" />
            </el-form-item>

            <!-- 说明 -->
            <el-form-item v-if="showField('reason')" label="事由" prop="reason">
              <el-input v-model="form.reason" type="textarea" :rows="4" placeholder="请详细说明申请原因" :maxlength="500" show-word-limit />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" :loading="submitting" @click="submitForm">
                提交申请
              </el-button>
              <el-button @click="$router.back()">取消</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="8">
        <!-- 提示信息 -->
        <el-card shadow="hover">
          <template #header>
            <span>💡 提示</span>
          </template>
          <ul class="tips-list">
            <li>请如实填写申请信息</li>
            <li>带 <span class="required">*</span> 的为必填项</li>
            <li>提交后将由管理员审批</li>
            <li>审批结果将通过系统通知</li>
            <li v-if="actionName === '请假'">请假需提前 1 个工作日提交</li>
            <li v-if="actionName === '报销'">请保留所有发票原件</li>
          </ul>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { useUserStore } from '../../stores/user'
import { workflowAPI } from '../../api'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const formRef = ref(null)
const loading = ref(false)
const submitting = ref(false)
const action = ref(null)

// 从路由参数获取动作ID
const actionId = computed(() => parseInt(route.params.actionId) || 0)

// 动作名称（用于字段条件显示）
const actionName = computed(() => {
  const name = action.value?.name || ''
  if (name.includes('请假')) return '请假'
  if (name.includes('报销')) return '报销'
  if (name.includes('出差')) return '出差'
  if (name.includes('入职')) return '入职'
  if (name.includes('加班')) return '加班'
  return name
})

// 表单数据
const form = reactive({
  applicant: userStore.displayName,
  title: '',
  leaveType: '',
  expenseType: '',
  destination: '',
  dateRange: null,
  date: null,
  amount: 0,
  reason: '',
})

// 表单验证
const rules = computed(() => {
  const r = {
    title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
    reason: [{ required: true, message: '请输入申请事由', trigger: 'blur' }],
  }
  if (showField('leaveType')) {
    r.leaveType = [{ required: true, message: '请选择请假类型', trigger: 'change' }]
  }
  if (showField('expenseType')) {
    r.expenseType = [{ required: true, message: '请选择费用类型', trigger: 'change' }]
  }
  if (showField('destination')) {
    r.destination = [{ required: true, message: '请输入目的地', trigger: 'blur' }]
  }
  if (showField('dateRange')) {
    r.dateRange = [{ required: true, message: '请选择日期范围', type: 'array', trigger: 'change' }]
  }
  if (showField('date')) {
    r.date = [{ required: true, message: '请选择日期', type: 'date', trigger: 'change' }]
  }
  return r
})

/** 根据动作类型判断是否显示某字段 */
function showField(field) {
  const name = actionName.value
  switch (field) {
    case 'leaveType': return name === '请假'
    case 'expenseType': return name === '报销'
    case 'destination': return name === '出差'
    case 'dateRange': return name === '出差' || name === '请假'
    case 'date': return name === '加班' || name === '入职'
    case 'amount': return name === '报销'
    case 'reason': return true
    case 'title': return name !== '入职'
    case 'applicant': return true
    default: return true
  }
}

/** 加载工作流动作信息 */
async function loadAction() {
  loading.value = true
  try {
    const res = await workflowAPI.getActions()
    if (res.code === 200) {
      action.value = (res.data || []).find(a => a.id === actionId.value)
      if (!action.value) {
        ElMessage.warning('未找到对应的快捷操作')
        router.back()
      }
    }
  } catch (e) {
    console.error('加载动作信息失败:', e)
  } finally {
    loading.value = false
  }
}

/** 提交表单 */
async function submitForm() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    // 模拟提交（实际项目应对接后端API）
    await new Promise(resolve => setTimeout(resolve, 1500))

    ElMessage.success({
      message: `「${action.value?.label || '申请'}」已提交成功，请等待审批`,
      duration: 4000,
    })
    router.push('/user-home')
  } catch (e) {
    console.error('提交失败:', e)
  } finally {
    submitting.value = false
  }
}

onMounted(loadAction)
</script>

<style scoped>
.workflow-form-page {
  max-width: 1000px;
  margin: 0 auto;
}
.page-header {
  margin-bottom: 24px;
}
.page-header h2 {
  font-size: 22px;
  color: #303133;
  margin: 8px 0 4px;
}
.page-header p {
  color: #909399;
  font-size: 14px;
}
.tips-list {
  padding-left: 20px;
  color: #606266;
  font-size: 13px;
  line-height: 2;
}
.tips-list .required {
  color: #f56c6c;
}
</style>
