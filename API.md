# API 文档 - 企业知识库 RAG 问答系统

Base URL: `http://localhost:5000/api`

所有接口（除登录注册外）需在 Header 携带：
```
Authorization: Bearer <JWT_TOKEN>
```

---

## 一、认证 Auth

### POST /api/auth/login
登录获取 Token
```json
// Request
{"username": "admin", "password": "123456"}
// Response 200
{"code": 200, "data": {"token": "xxx", "user": {...}}, "message": "登录成功"}
```

### POST /api/auth/register
```json
// Request
{"username": "xxx", "password": "xxx", "real_name": "xxx"}
```

### GET /api/auth/profile
### PUT /api/auth/profile

---

## 二、文档管理 Documents

### GET /api/documents
列表查询 `?page=1&per_page=20&status=ready&category_id=1&keyword=xxx`

### GET /api/documents/:id
### DELETE /api/documents/:id

### POST /api/documents/upload
multipart/form-data: `file`, `title`, `category_id`

### GET /api/documents/categories
分类列表（带缓存）

### POST /api/documents/categories
创建分类（管理员）

### DELETE /api/documents/categories/:id

### GET /api/documents/search `?q=xxx&page=1&category_id=1`
全文+语义混合搜索

### GET /api/documents/:id/content
文档完整内容预览

---

## 三、智能问答 Q&A

### 标准问答
#### POST /api/qa/ask
```json
// Request
{"question": "考勤时间", "session_id": "uuid（可选，多轮对话）"}
// Response
{"code":200, "data":{"answer":"...", "sources":[...], "qa_id":1, "cost_time_ms":42950, "from_cache":false}}
```

#### POST /api/qa/ask/stream
SSE 流式接口，同上。返回 `text/event-stream`：
```
data: {"type":"start"}
data: {"type":"sources","sources":[...],"chunks":5}
data: {"type":"text","content":"回答片段..."}
data: {"type":"done","qa_id":1,"cost_time_ms":12950}
```

### 对话会话管理
| 接口 | 说明 |
|------|------|
| POST /api/qa/session/start | 创建新会话，返回 session_id |
| POST /api/qa/session/:sid/clear | 清除会话历史 |
| GET /api/qa/session/:sid/history | 获取会话历史 |

### 会话持久化（跨设备同步）
| 接口 | 说明 |
|------|------|
| POST /api/qa/session/save | 保存当前 Redis 会话到 MySQL |
| GET /api/qa/sessions `?page=1` | 用户已保存的对话列表 |
| GET /api/qa/sessions/:id | 对话详情+消息 |
| DELETE /api/qa/sessions/:id | 删除对话 |
| POST /api/qa/sessions/:id/restore | 恢复对话到 Redis |

### 历史与统计
| 接口 | 说明 |
|------|------|
| GET /api/qa/history | 当前用户历史（分页） |
| GET /api/qa/history/all | 全部历史（管理员） |
| POST /api/qa/feedback | 提交反馈 `{"qa_id":1,"feedback":1}` |
| GET /api/qa/:id | 问答详情 |
| GET /api/qa/export?days=7 | 导出 Markdown |
| GET /api/qa/stats | 个人统计 |

---

## 四、收藏夹 Bookmarks

| 接口 | 说明 |
|------|------|
| GET /api/bookmarks `?type=qa&page=1` | 收藏列表 |
| POST /api/bookmarks | 添加收藏 `{"type":"qa","target_id":1,"note":""}` |
| DELETE /api/bookmarks/:id | 取消收藏 |
| PUT /api/bookmarks/:id/note | 更新笔记 `{"note":"..."}` |
| GET /api/bookmarks/check `?type=qa&target_id=1` | 检查是否已收藏 |

---

## 五、工作流审批 Workflow

| 接口 | 说明 |
|------|------|
| GET /api/workflow/actions | 获取启用的操作按钮 |
| POST /api/workflow/match | 匹配按钮 `{"question":"请假...","answer":"..."}` |

管理员 CRUD：
| 接口 | 说明 |
|------|------|
| POST /api/workflow/actions | 创建按钮 |
| PUT /api/workflow/actions/:id | 更新 |
| DELETE /api/workflow/actions/:id | 删除 |

---

## 六、管理后台 Admin

### GET /api/admin/dashboard
仪表盘统计（缓存5分钟）
```json
{"summary":{"total_users":5,"total_docs":6,...},"qa_trend":[...],"category_stats":[...]}
```

### GET /api/admin/users `?page=1&role=user&keyword=xxx`
### PUT /api/admin/users/:id/status

### 公告管理
| 接口 | 说明 |
|------|------|
| GET /api/admin/announcements | 公告列表（登录可看） |
| POST /api/admin/announcements | 发布（管理员） |
| DELETE /api/admin/announcements/:id | 删除（管理员） |

### 知识盲区分析
#### GET /api/admin/knowledge-gaps `?days=30&page=1`
```json
{"list":[...], "summary":{"total_gaps":15, "total_questions":23, "top_keywords":[{"word":"年假","count":5}]}}
```

---

## 七、数据模型

### 数据库表（共11张）
| 表名 | 说明 | 新增 |
|------|------|------|
| users | 用户 | - |
| documents | 文档 | - |
| document_chunks | 文档块 | - |
| categories | 分类 | - |
| qa_logs | 问答日志 | - |
| announcements | 公告 | - |
| bookmarks | 收藏夹+笔记 | ✅ v2.0 |
| conversations | 对话会话 | ✅ v2.0 |
| conversation_messages | 对话消息 | ✅ v2.0 |
| workflow_actions | 工作流按钮 | ✅ v2.0 |
| knowledge_gaps | 知识盲区 | ✅ v2.0 |

### Redis 缓存键
| 键模式 | 用途 | TTL |
|--------|------|-----|
| qa:exact:{md5} | 问答缓存 | 1h |
| vector:{md5} | 向量检索缓存 | 30min |
| dashboard:stats | 仪表盘 | 5min |
| categories:tree | 分类 | 10min |
| conversation:{sid} | 对话上下文 | 2h |

---

## 八、配置说明

| 变量 | 默认值 | 说明 |
|------|--------|------|
| DB_HOST | 127.0.0.1 | MySQL 地址 |
| DB_PORT | 3306 | MySQL 端口 |
| DB_NAME | dbenterprise | 数据库名 |
| REDIS_HOST | 127.0.0.1 | Redis 地址 |
| REDIS_PORT | 6379 | Redis 端口 |
| OLLAMA_BASE_URL | http://127.0.0.1:11434 | Ollama 地址 |
| LLM_MODEL | qwen2.5:3b | 大语言模型 |
| EMBEDDING_MODEL | qwen3-embedding:4b | 嵌入模型 |
| CACHE_TTL_QA | 3600 | 问答缓存(TTL秒) |
| CACHE_TTL_DASHBOARD | 300 | 仪表盘缓存 |
