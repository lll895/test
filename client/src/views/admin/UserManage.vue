<!-- ============================================================
     企业知识库 RAG 问答系统 - 用户管理页面（管理员）
     ============================================================ -->

<template>
  <div class="user-manage page-container card-animate">
    <div class="page-header">
      <h2>用户管理</h2>
      <p>管理系统中的所有用户账号</p>
    </div>

    <!-- 搜索 -->
    <el-card shadow="hover" class="filter-card">
      <el-row :gutter="16" align="middle">
        <el-col :xs="24" :sm="8">
          <el-input
            v-model="keyword"
            placeholder="搜索用户名/姓名/邮箱..."
            :prefix-icon="Search"
            clearable
            @input="handleSearch"
          />
        </el-col>
        <el-col :xs="12" :sm="4">
          <el-select v-model="roleFilter" placeholder="角色" clearable @change="loadUsers">
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
          </el-select>
        </el-col>
      </el-row>
    </el-card>

    <!-- 用户列表 -->
    <el-card shadow="hover">
      <el-table :data="userList" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="real_name" label="姓名" width="120" />
        <el-table-column prop="email" label="邮箱" min-width="200" />
        <el-table-column label="角色" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'info'" size="small">
              {{ row.role === 'admin' ? '管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status ? 'success' : 'danger'" size="small">
              {{ row.status ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="最后登录" width="180">
          <template #default="{ row }">
            {{ row.last_login?.slice(0, 19)?.replace('T', ' ') || '从未登录' }}
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">
            {{ row.created_at?.slice(0, 19)?.replace('T', ' ') }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-popconfirm
              :title="`确定${row.status ? '禁用' : '启用'}用户 ${row.username} 吗？`"
              @confirm="handleToggleStatus(row.id)"
            >
              <template #reference>
                <el-button
                  :type="row.status ? 'warning' : 'success'"
                  link
                  size="small"
                >
                  {{ row.status ? '禁用' : '启用' }}
                </el-button>
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
          @change="loadUsers"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { adminAPI } from '../../api'

const userList = ref([])
const loading = ref(false)
const keyword = ref('')
const roleFilter = ref(null)
const page = ref(1)
const perPage = ref(10)
const total = ref(0)

let searchTimer = null

/** 加载用户列表 */
async function loadUsers() {
  loading.value = true
  try {
    const params = {
      page: page.value,
      per_page: perPage.value,
      keyword: keyword.value || undefined,
      role: roleFilter.value || undefined,
    }
    const res = await adminAPI.getUsers(params)
    if (res.code === 200) {
      userList.value = res.data.list
      total.value = res.data.total
    }
  } catch (e) {
    console.error('加载用户列表失败:', e)
  } finally {
    loading.value = false
  }
}

/** 搜索防抖 */
function handleSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    page.value = 1
    loadUsers()
  }, 300)
}

/** 切换用户状态 */
async function handleToggleStatus(id) {
  try {
    const res = await adminAPI.toggleUserStatus(id)
    if (res.code === 200) {
      ElMessage.success('操作成功')
      loadUsers()
    }
  } catch (e) {
    console.error('操作失败:', e)
  }
}

onMounted(loadUsers)
</script>

<style scoped>
.user-manage {
  max-width: 1400px;
  margin: 0 auto;
}

.filter-card {
  margin-bottom: 20px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
