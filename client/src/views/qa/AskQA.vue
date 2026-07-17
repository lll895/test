<!-- ============================================================
     企业知识库 RAG 问答系统 - 智能问答页面（修复版）
     支持：标准问答 + 流式升级、多轮对话、缓存加速
     ============================================================ -->

<template>
  <div class="qa-chat">
    <div class="chat-header">
      <div class="header-info">
        <el-icon :size="20" color="#409eff"><ChatLineSquare /></el-icon>
        <span class="header-title">智能问答</span>
        <el-tag v-if="sessionId" size="small" type="info" effect="plain">多轮对话已开启</el-tag>
        <el-tag v-if="isRetrying" size="small" type="warning" effect="plain">重试中...</el-tag>
      </div>
      <div class="header-actions">
        <el-button size="small" @click="clearSession" :disabled="!sessionId || isAsking">
          <el-icon><Refresh /></el-icon> 重置对话
        </el-button>
      </div>
    </div>

    <div class="chat-messages" ref="messagesRef">
      <!-- 欢迎消息 -->
      <div v-if="messages.length === 0" class="welcome-msg">
        <div class="welcome-avatar">
          <el-icon :size="56" color="#409eff"><Reading /></el-icon>
        </div>
        <h3>你好！我是小知 👋</h3>
        <p class="welcome-desc">我是企业知识库智能助手，可以帮你解答以下问题：</p>
        <div class="quick-questions">
          <el-tag v-for="q in quickQuestions" :key="q" class="quick-tag"
            :class="{ 'is-asking': isAsking }" @click="askQuestion(q)">
            {{ q }}
          </el-tag>
        </div>
      </div>

      <div v-for="(msg, index) in messages" :key="msg.id || index" class="message-wrapper">
        <!-- 用户消息 -->
        <div v-if="msg.role === 'user'" class="message-row user-row">
          <div class="message-bubble user">
            <div class="bubble-text">{{ msg.content }}</div>
          </div>
          <el-avatar :size="36" icon="UserFilled" class="msg-avatar user-avatar" />
        </div>

        <!-- 助手消息 -->
        <div v-else class="message-row assistant-row">
          <el-avatar :size="36" class="msg-avatar assistant-avatar">
            <el-icon :size="20" color="#409eff"><Reading /></el-icon>
          </el-avatar>
          <div class="assistant-content-wrapper">
            <div class="message-bubble assistant">
              <!-- 加载中（搜索知识库阶段） -->
              <div v-if="msg.status === 'searching'" class="thinking">
                <el-icon class="is-loading"><Loading /></el-icon>
                <span>正在检索知识库...</span>
              </div>
              <!-- 加载中（LLM 生成阶段） -->
              <div v-else-if="msg.status === 'generating'" class="thinking">
                <el-icon class="is-loading"><Loading /></el-icon>
                <span>小知正在思考中</span>
                <span class="thinking-dots"><span class="dot">.</span><span class="dot">.</span><span class="dot">.</span></span>
              </div>
              <!-- 回答完成 -->
              <div v-else class="assistant-content">
                <div class="answer-text markdown-body" v-html="renderMarkdown(msg.content)"></div>

                <!-- 缓存提示 -->
                <div v-if="msg.meta?.from_cache" class="cache-badge">
                  <el-tag size="small" type="warning" effect="plain" round>⚡ 缓存命中（秒回）</el-tag>
                </div>

                <!-- 来源引用 -->
                <div v-if="msg.sources && msg.sources.length > 0" class="sources">
                  <div class="sources-header" @click="msg.showSources = !msg.showSources">
                    <el-icon :size="14"><FolderOpened /></el-icon>
                    <span>引用了 {{ msg.sources.length }} 个知识来源</span>
                    <el-icon :class="{ 'is-reverse': msg.showSources }" :size="14"><ArrowDown /></el-icon>
                  </div>
                  <transition name="slide-fade">
                    <div v-if="msg.showSources" class="sources-list">
                      <div v-for="(s, si) in msg.sources" :key="si" class="source-item">
                        <el-tag size="small" type="primary" effect="plain" class="source-tag">{{ s.title }}</el-tag>
                        <el-progress :percentage="Math.round(s.similarity * 100)" :stroke-width="4" size="small" />
                      </div>
                    </div>
                  </transition>
                </div>

                <!-- 元信息 -->
                <div v-if="msg.meta" class="meta-info">
                  <el-tag size="small" effect="plain" type="info" round>⏱ {{ msg.meta.cost_time_ms }}ms</el-tag>
                  <el-tag size="small" effect="plain" type="info" round>📄 {{ msg.meta.chunks_retrieved }} 个文档</el-tag>
                  <el-button size="small" link type="primary" @click="copyAnswer(msg.content)">
                    📋 复制回答
                  </el-button>
                </div>

                <!-- 反馈按钮 -->
                <div v-if="msg.qaId" class="feedback-btns">
                  <span class="feedback-label">这个回答对你有帮助吗？</span>
                  <el-button :type="msg.feedback === 1 ? 'success' : 'default'" link size="small"
                    @click="submitFeedback(msg.qaId, 1, index)">
                    👍 有帮助
                  </el-button>
                  <el-button :type="msg.feedback === 0 ? 'danger' : 'default'" link size="small"
                    @click="submitFeedback(msg.qaId, 0, index)">
                    👎 没帮助
                  </el-button>
                  <el-button link size="small" @click="toggleBookmark(msg)" :type="msg.bookmarked ? 'warning' : 'default'">
                    {{ msg.bookmarked ? '⭐ 已收藏' : '☆ 收藏' }}
                  </el-button>
                  <el-button link size="small" @click="regenerate(index)" :disabled="isAsking">
                    🔄 重新生成
                  </el-button>
                </div>

                <!-- 工作流操作按钮 -->
                <div v-if="msg.workflowActions && msg.workflowActions.length > 0" class="workflow-actions">
                  <div v-for="act in msg.workflowActions" :key="act.id" class="wf-btn-wrap">
                    <el-button type="primary" size="small" @click="openWorkflowUrl(act)">
                      🔗 {{ act.label }}
                    </el-button>
                    <span v-if="act.description" class="wf-desc">{{ act.description }}</span>
                  </div>
                </div>

                <!-- 推荐问题 -->
                <div v-if="msg.suggestions && msg.suggestions.length > 0" class="suggestions">
                  <div class="suggestions-title">💡 您可能还想了解：</div>
                  <div class="suggestions-list">
                    <el-tag v-for="(sg, si) in msg.suggestions" :key="si"
                      class="suggestion-tag" @click="askQuestion(sg)">
                      {{ sg }}
                    </el-tag>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="chat-input-area">
      <el-input v-model="question" type="textarea" :rows="2"
        :placeholder="isAsking ? '小知正在回答中...' : '请输入您的问题...'"
        :disabled="isAsking" resize="none"
        @keydown="handleInputKeydown" />
      <div class="input-actions">
        <el-button type="primary" :icon="Promotion" :loading="isAsking"
          :disabled="!question.trim() || isAsking" @click="handleSend" class="send-btn">
          发送
        </el-button>
        <span class="input-hint">Enter 发送 / Shift+Enter 换行</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ChatLineSquare, Loading, Promotion, Reading, UserFilled,
  Refresh, FolderOpened, ArrowDown,
} from '@element-plus/icons-vue'
import { qaAPI, bookmarkAPI, workflowAPI } from '../../api'

const messages = ref([])
const question = ref('')
const isAsking = ref(false)
const isRetrying = ref(false)
const messagesRef = ref(null)
const sessionId = ref(null)
const router = useRouter()

const quickQuestions = [
  '公司考勤时间是怎么规定的？',
  '请假有哪些类型？',
  '如何申请加班？',
  '财务报销的流程是什么？',
  '员工福利有哪些？',
]

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

/** 简易 Markdown 渲染 */
function renderMarkdown(text) {
  if (!text) return ''
  let html = text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/```(\w*)\n?([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>').replace(/^## (.+)$/gm, '<h2>$1</h2>').replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^\d+\.\s(.+)$/gm, '<li>$1</li>').replace(/^[-*]\s(.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>\n?)+/g, (m) => m.match(/^\d+\./m) ? '<ol>' + m + '</ol>' : '<ul>' + m + '</ul>')
    .replace(/\n/g, '<br>')
    .replace(/(<\/(ul|ol|pre|h[1-3])>)<br>/g, '$1').replace(/<br>(<(ul|ol|pre|h[1-3]|li>))/g, '$1')
  return html
}

/** 初始化会话 */
async function initSession(restoreId) {
  try {
    const res = await qaAPI.startSession()
    if (res.code === 200) sessionId.value = res.data.session_id
    // 如果有恢复的会话ID，加载历史消息
    if (restoreId) {
      const convRes = await qaAPI.getSessionMessages(restoreId)
      if (convRes.code === 200 && convRes.data.messages) {
        messages.value = convRes.data.messages.map((m, i) => ({
          role: m.role, content: m.content, sources: m.sources || [],
          qaId: null, feedback: m.feedback, meta: null,
          showSources: false, status: 'done', id: Date.now() + i,
        }))
      }
    }
  } catch (e) { console.error('创建会话失败:', e) }
}

/** 切换收藏状态 */
async function toggleBookmark(msg) {
  if (!msg.qaId) return
  if (msg.bookmarked) {
    if (msg._bookmarkId) {
      try {
        await bookmarkAPI.remove(msg._bookmarkId)
        msg.bookmarked = false
        msg._bookmarkId = null
        ElMessage.success('已取消收藏')
      } catch (e) { console.error(e) }
    }
  } else {
    try {
      const res = await bookmarkAPI.add({ type: 'qa', target_id: msg.qaId })
      if (res.code === 200) {
        msg.bookmarked = true
        msg._bookmarkId = res.data.id
        ElMessage.success('已收藏')
      }
    } catch (e) { console.error(e) }
  }
}

/** 打开工作流链接 - 内部页面直接路由，外部链接新窗口打开 */
function openWorkflowUrl(action) {
  if (!action.url) {
    ElMessage.info('该操作暂未配置')
    return
  }
  // 内部路由（以 / 开头）
  if (action.url.startsWith('/')) {
    router.push(`/workflow/${action.id}`)
    return
  }
  // 外部占位链接
  if (action.url.includes('company.com') || action.url.includes('example.com')) {
    ElMessage.info(`「${action.label}」功能尚未对接，请联系管理员配置`)
    return
  }
  window.open(action.url, '_blank')
}

/** 匹配工作流按钮 */
async function matchWorkflowActions(msg) {
  try {
    const res = await workflowAPI.matchActions({
      question: messages.value[messages.value.indexOf(msg) - 1]?.content || '',
      answer: msg.content,
    })
    if (res.code === 200) {
      msg.workflowActions = res.data
    }
  } catch (e) { console.error(e) }
}

/** 自动保存对话（防抖） */
let saveTimer = null
function autoSaveConversation() {
  if (!sessionId.value) return
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(async () => {
    try {
      await qaAPI.saveSession({ session_id: sessionId.value })
    } catch (e) { /* 静默保存 */ }
  }, 5000) // 5秒防抖
}

/** 复制回答到剪贴板 */
function copyAnswer(text) {
  if (!text) return
  navigator.clipboard.writeText(text).then(() => {
    ElMessage.success('已复制到剪贴板')
  }).catch(() => {
    // fallback
    const ta = document.createElement('textarea')
    ta.value = text
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
    ElMessage.success('已复制到剪贴板')
  })
}

/** 输入框键盘事件处理：Enter发送，Shift+Enter换行 */
function handleInputKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

/** 发送问题 - 先试 SSE 流式，失败则走标准 API */
async function handleSend() {
  const q = question.value.trim()
  if (!q || isAsking.value) return
  if (!sessionId.value) await initSession()

  // 添加用户消息
  messages.value.push({ role: 'user', content: q, id: Date.now() })
  question.value = ''
  scrollToBottom()

  const assistantIndex = messages.value.length
  const msgId = Date.now() + 1
  // 先显示"搜索中"状态
  messages.value.push({ role: 'assistant', content: '', sources: [], qaId: null,
    feedback: null, meta: null, showSources: false, status: 'searching', id: msgId })
  scrollToBottom()
  isAsking.value = true

  try {
    // ---- 方案 A：SSE 流式 ----
    const token = localStorage.getItem('token')
    const controller = new AbortController()
    // 设置 10 秒超时等待第一个字节（之后流式不限制）
    const timeoutId = setTimeout(() => controller.abort(), 10000)

    const response = await fetch('/api/qa/ask/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({ question: q, session_id: sessionId.value }),
      signal: controller.signal,
    })
    clearTimeout(timeoutId)

    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    if (!response.body) throw new Error('浏览器不支持流式')

    // 流式开始，切换到"生成中"状态
    messages.value[assistantIndex].status = 'generating'
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let fullAnswer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try {
          const data = JSON.parse(line.slice(6))
          if (data.type === 'sources') {
            messages.value[assistantIndex].sources = data.sources || []
            messages.value[assistantIndex].meta = { chunks_retrieved: data.chunks || 0, cost_time_ms: 0, from_cache: false }
          } else if (data.type === 'text') {
            fullAnswer += data.content
            messages.value[assistantIndex].content = fullAnswer
            scrollToBottom()
          } else if (data.type === 'done') {
            messages.value[assistantIndex].qaId = data.qa_id
            if (messages.value[assistantIndex].meta) {
              messages.value[assistantIndex].meta.cost_time_ms = data.cost_time_ms || 0
              messages.value[assistantIndex].meta.from_cache = data.from_cache || false
            }
            messages.value[assistantIndex].status = 'done'
            // 自动匹配工作流按钮 + 自动保存
            matchWorkflowActions(messages.value[assistantIndex])
            autoSaveConversation()
          } else if (data.type === 'error') {
            throw new Error(data.content)
          }
        } catch (e) {
          if (e.message.startsWith('data:') === false) console.warn('SSE解析:', e.message)
        }
      }
    }
    // 如果流式结束时状态还没变，设为 done
    if (messages.value[assistantIndex].status === 'generating') {
      messages.value[assistantIndex].status = 'done'
    }

  } catch (sseErr) {
    console.warn('SSE 流式失败，回退到标准 API:', sseErr.message)
    isRetrying.value = true
    messages.value[assistantIndex].status = 'searching'
    messages.value[assistantIndex].content = ''

    // ---- 方案 B：标准 API（有缓存加速）- 用更长的超时 ----
    try {
      const res = await qaAPI.ask({ question: q, session_id: sessionId.value })
      if (res.code === 200) {
        messages.value[assistantIndex] = {
          role: 'assistant', content: res.data.answer, sources: res.data.sources || [],
          qaId: res.data.qa_id, feedback: null, showSources: false,
          meta: { cost_time_ms: res.data.cost_time_ms, chunks_retrieved: res.data.chunks_retrieved, from_cache: res.data.from_cache },
          status: 'done', id: msgId,
        }
        // 工作流匹配 + 自动保存
        matchWorkflowActions(messages.value[assistantIndex])
        autoSaveConversation()
      } else {
        throw new Error(res.message || 'API错误')
      }
    } catch (fallbackErr) {
      console.error('标准 API 也失败:', fallbackErr)
      messages.value[assistantIndex] = {
        role: 'assistant',
        content: '抱歉，服务暂时不可用。' + (fallbackErr.message?.includes('timeout') ? '回答超时，请稍后重试。' : '请检查后端服务是否正常运行。'),
        sources: [], qaId: null, feedback: null, status: 'done', id: msgId,
      }
    }
  } finally {
    isAsking.value = false
    isRetrying.value = false
    scrollToBottom()
  }
}

function askQuestion(q) {
  if (isAsking.value) return
  question.value = q
  handleSend()
}

/** 重新生成回答 */
async function regenerate(index) {
  const msg = messages.value[index]
  if (!msg || !msg.qaId || isAsking.value) return
  // 获取该消息对应的用户问题（前一条消息）
  const userMsg = messages.value[index - 1]
  if (!userMsg || userMsg.role !== 'user') return
  // 先删除旧消息，再重新提问
  messages.value.splice(index, 1)
  if (userMsg.questionForRegen) {
    question.value = userMsg.questionForRegen
  } else {
    question.value = userMsg.content
  }
  // 删除用户消息
  messages.value.splice(index - 1, 1)
  // 重新发送
  handleSend()
}

async function clearSession() {
  if (!sessionId.value) return
  try { await qaAPI.clearSession(sessionId.value) } catch (e) { console.error(e) }
  sessionId.value = null
  messages.value = []
  ElMessage.success('对话已重置')
}

async function submitFeedback(qaId, feedback, index) {
  try {
    await qaAPI.submitFeedback({ qa_id: qaId, feedback })
    messages.value[index].feedback = feedback
    ElMessage.success('感谢你的反馈！')
  } catch (e) { console.error('反馈失败:', e) }
}

onMounted(() => {
  scrollToBottom()
  // 检查是否有从对话历史恢复的 session
  const route = useRoute()
  const router = useRouter()
  if (route.query.session) {
    sessionId.value = route.query.session
    ElMessage.success('对话已恢复')
  }
})
</script>

<style scoped>
.qa-chat {
  height: calc(100vh - 140px);
  display: flex;
  flex-direction: column;
  max-width: 1000px;
  margin: 0 auto;
  background: #f5f7fa;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}
.chat-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 20px; background: #fff;
  border-bottom: 1px solid #ebeef5;
}
.header-info { display: flex; align-items: center; gap: 10px; }
.header-title { font-size: 16px; font-weight: 600; color: #303133; }
.header-actions { display: flex; gap: 8px; }
.chat-messages { flex: 1; overflow-y: auto; padding: 20px; background: #f5f7fa; }

.welcome-msg { text-align: center; padding: 50px 20px; }
.welcome-avatar { margin-bottom: 16px; animation: float 3s ease-in-out infinite; }
@keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-8px); } }
.welcome-msg h3 { font-size: 22px; color: #303133; margin: 0 0 8px; }
.welcome-desc { color: #909399; font-size: 14px; margin-bottom: 24px; }
.quick-questions { display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; }
.quick-tag { cursor: pointer; padding: 8px 18px; font-size: 14px; border-radius: 20px !important;
  transition: all 0.3s; border: 1px solid #d9ecff !important;
  background: #ecf5ff !important; color: #409eff !important; }
.quick-tag:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2); }
.quick-tag.is-asking { pointer-events: none; opacity: 0.5; }

.message-wrapper { margin-bottom: 4px; }
.message-row { display: flex; gap: 12px; margin-bottom: 20px; }
.user-row { justify-content: flex-end; }
.assistant-row { justify-content: flex-start; }
.msg-avatar { flex-shrink: 0; margin-top: 4px; }
.user-avatar { background: #409eff; }
.assistant-avatar { background: #ecf5ff; }

.message-bubble { border-radius: 16px; padding: 14px 20px; max-width: 78%;
  line-height: 1.7; white-space: pre-wrap; word-wrap: break-word; font-size: 14px; }
.message-bubble.user { background: linear-gradient(135deg, #409eff, #337ecc); color: #fff;
  border-bottom-right-radius: 4px; box-shadow: 0 2px 8px rgba(64,158,255,0.2); }
.message-bubble.assistant { background: #fff; color: #303133;
  border-bottom-left-radius: 4px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }

.thinking { color: #909399; display: flex; align-items: center; gap: 8px; padding: 4px 0; }
.thinking-dots { display: inline-flex; }
.thinking-dots .dot { animation: dot-bounce 1.4s ease-in-out infinite; font-size: 20px; line-height: 1; margin: 0 1px; }
.thinking-dots .dot:nth-child(2) { animation-delay: 0.2s; }
.thinking-dots .dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes dot-bounce { 0%, 60%, 100% { opacity: 0.3; transform: translateY(0); } 30% { opacity: 1; transform: translateY(-4px); } }

.answer-text { white-space: normal; word-wrap: break-word; }
.answer-text :deep(h2) { font-size: 17px; margin: 12px 0 6px; color: #303133; }
.answer-text :deep(h3) { font-size: 15px; margin: 12px 0 6px; color: #303133; }
.answer-text :deep(p) { margin: 6px 0; line-height: 1.7; }
.answer-text :deep(ul), .answer-text :deep(ol) { margin: 6px 0; padding-left: 22px; }
.answer-text :deep(li) { margin: 3px 0; line-height: 1.6; }
.answer-text :deep(code) { background: #f5f7fa; padding: 2px 6px; border-radius: 4px; font-size: 13px; color: #e6465a; }
.answer-text :deep(pre) { background: #f5f7fa; padding: 14px 16px; border-radius: 8px; overflow-x: auto; margin: 10px 0; border: 1px solid #e4e7ed; }
.answer-text :deep(pre code) { background: transparent; color: #303133; padding: 0; }
.answer-text :deep(strong) { font-weight: 600; }

.cache-badge { margin-top: 8px; }

.sources { margin-top: 14px; padding-top: 12px; border-top: 1px solid #f0f0f0; }
.sources-header { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #909399; cursor: pointer; user-select: none; }
.sources-header .is-reverse { transform: rotate(180deg); transition: transform 0.3s; }
.sources-list { margin-top: 8px; display: flex; flex-direction: column; gap: 6px; }
.source-item { display: flex; align-items: center; gap: 8px; padding: 4px 0; }
.source-tag { min-width: 80px; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.slide-fade-enter-active { transition: all 0.3s ease; }
.slide-fade-leave-active { transition: all 0.2s ease; }
.slide-fade-enter-from, .slide-fade-leave-to { opacity: 0; transform: translateY(-6px); }

.meta-info { display: flex; gap: 6px; margin-top: 10px; padding-top: 8px; border-top: 1px solid #f0f0f0; flex-wrap: wrap; align-items: center; }
.feedback-btns { margin-top: 10px; padding-top: 8px; border-top: 1px solid #f0f0f0; display: flex; align-items: center; gap: 8px; }
.feedback-label { font-size: 13px; color: #909399; }

.workflow-actions { margin-top: 12px; padding-top: 10px; border-top: 1px solid #f0f0f0; display: flex; flex-direction: column; gap: 6px; }
.wf-btn-wrap { display: flex; align-items: center; gap: 8px; }
.wf-desc { font-size: 12px; color: #909399; }

.suggestions { margin-top: 12px; padding-top: 10px; border-top: 1px solid #f0f0f0; }
.suggestions-title { font-size: 13px; color: #909399; margin-bottom: 6px; }
.suggestions-list { display: flex; flex-wrap: wrap; gap: 6px; }
.suggestion-tag { cursor: pointer; transition: all 0.2s; background: #f0f9eb !important; border-color: #e1f3d8 !important; color: #67c23a !important; }
.suggestion-tag:hover { transform: translateY(-1px); box-shadow: 0 2px 6px rgba(103,194,58,0.2); }

.chat-input-area { padding: 16px 20px; background: #fff; border-top: 1px solid #ebeef5; display: flex; gap: 12px; align-items: flex-start; }
.chat-input-area .el-textarea { flex: 1; }
.chat-input-area .el-textarea :deep(.el-textarea__inner) { border-radius: 12px; padding: 12px 16px; font-size: 14px; line-height: 1.5; border: 1px solid #dcdfe6; transition: all 0.3s; resize: none; }
.chat-input-area .el-textarea :deep(.el-textarea__inner:focus) { border-color: #409eff; box-shadow: 0 0 0 2px rgba(64,158,255,0.1); }
.input-actions { display: flex; flex-direction: column; gap: 8px; }
.send-btn { height: 56px; min-width: 100px; border-radius: 12px; font-size: 15px; }
.input-hint { font-size: 11px; color: #c0c4cc; text-align: center; display: block; margin-top: 2px; white-space: nowrap; }
</style>
