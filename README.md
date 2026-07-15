# 企业知识库 RAG 问答系统（v2.0 🚀）

基于 LangChain 的 RAG（检索增强生成）企业内部知识库问答系统。支持上传文档、智能问答、知识搜索、收藏夹、对话同步、工作流审批、知识盲区分析等。

## 技术栈

### 后端
| 组件 | 技术 |
|------|------|
| Web框架 | Python Flask |
| 数据库 | MySQL 8.0 + SQLAlchemy |
| 缓存 | Redis 5.x |
| 认证 | JWT (Flask-JWT-Extended) |
| LLM | Ollama + Qwen2.5:3b |
| 嵌入 | Ollama + Qwen3-embedding:4b |
| 向量库 | Chroma + LangChain |
| RAG框架 | LangChain 0.3 |

### 前端
| 组件 | 技术 |
|------|------|
| 框架 | Vue 3 (Composition API) |
| 构建 | Vite |
| UI | Element Plus |
| 状态 | Pinia |
| 路由 | Vue Router 4 |
| 图表 | ECharts + Vue-Echarts |
| HTTP | Axios |

## 项目结构

```
EnterpriseOA/
├── server/
│   ├── app.py                       # 应用入口（注册所有蓝图+模型）
│   ├── config.py                    # 配置（DB/Redis/Ollama/Chroma）
│   ├── requirements.txt             # Python 依赖
│   ├── sql/                         # 建表+测试数据
│   ├── models/                      # 11个数据模型
│   │   ├── user.py                  # 用户
│   │   ├── document.py              # 文档/分类/块
│   │   ├── qa_log.py                # 问答日志
│   │   ├── announcement.py          # 公告
│   │   ├── bookmark.py              # 【新增】收藏夹+笔记
│   │   ├── conversation.py          # 【新增】对话持久化
│   │   ├── workflow.py              # 【新增】工作流按钮
│   │   └── knowledge_gap.py         # 【新增】知识盲区
│   ├── routes/                      # 6个路由模块
│   │   ├── auth.py                  # 认证
│   │   ├── document.py              # 文档+搜索
│   │   ├── qa.py                    # 问答+流式+会话+统计
│   │   ├── admin.py                 # 管理+盲区
│   │   ├── bookmark.py              # 【新增】收藏API
│   │   └── workflow.py              # 【新增】工作流API
│   ├── services/                    # 业务逻辑
│   │   ├── llm_service.py           # LLM（多轮对话+人设）
│   │   ├── vector_service.py        # 向量检索（带缓存）
│   │   ├── rag_service.py           # RAG编排（带缓存+盲区追踪）
│   │   ├── cache_service.py         # Redis缓存服务
│   │   └── document_service.py      # 文档处理
│   ├── scripts/
│   │   ├── warm_cache.py            # 缓存预热
│   │   ├── reindex_docs.py          # 重新索引
│   │   └── seed_workflow.py         # 【新增】工作流种子数据
│   └── utils/__init__.py
│
├── client/
│   ├── src/
│   │   ├── api/index.js             # 统一API封装
│   │   ├── router/index.js          # 路由配置
│   │   ├── stores/user.js           # Pinia状态
│   │   └── views/
│   │       ├── Login.vue            # 登录
│   │       ├── Layout.vue           # 主布局
│   │       ├── home/                # 首页（含盲区分析）
│   │       ├── document/            # 文档管理
│   │       ├── qa/                  # 问答+流式+收藏
│   │       ├── search/              # 知识搜索
│   │       ├── bookmark/            # 【新增】收藏夹页面
│   │       └── conversation/        # 【新增】对话同步页面
│   └── vite.config.js
│
├── README.md
├── API.md                           # 【新增】API文档
├── prompt_log.md                    # 【新增】提示词日志
└── .gitignore
```

## 版本演进

### v1.0 - 基础版
- 文档上传（PDF/Word/TXT/MD）
- 基础 RAG 问答（qwen3:8b）
- 管理员仪表盘
- 用户管理

### v2.0 - 升级版（当前）
#### 性能优化
- ⚡ **Redis 缓存层**：相同问题秒回（2ms vs 44s）
- ⚡ **模型升级**：qwen2.5:3b（3B快模型），回答速度 13秒（原来44秒）
- ⚡ **流式输出**：SSE 实时逐字显示，不用等待完整回答

#### 智能升级
- 💬 **多轮对话**：支持上下文关联的连续对话（记忆最近20轮）
- 🧠 **AI人设"小知"**：自然语气，问候/感谢/告别智能识别
- 📡 **SSE流式**：首字节10秒超时，失败自动降级

#### 新增功能
| 功能 | 说明 |
|------|------|
| ⭐ **收藏夹+笔记** | 收藏问答/文档，添加个人笔记 |
| 💾 **对话跨设备同步** | 对话保存到服务器，登录任何设备都能继续 |
| 🔗 **工作流审批按钮** | 回答关键词匹配，自动显示审批操作按钮 |
| 🔍 **知识盲区分析** | 自动追踪未命中问题，管理员查看知识缺口 |
| 🔎 **全文搜索** | 关键词+语义双引擎混合搜索 |
| 📤 **问答导出** | 导出历史问答为 Markdown |
| 📊 **个人统计** | 个人问答趋势、有用率、响应时间 |

## 快速开始

### 环境要求
- Python 3.10+
- Node.js 18+
- MySQL 8.0
- Redis 7.x
- Ollama（含 qwen2.5:3b + qwen3-embedding:4b）

### 启动后端
```bash
cd server
.venv/Scripts/pip install -r requirements.txt
.venv/Scripts/python app.py
```

### 启动前端
```bash
cd client
npm install
npm run dev
```

访问 http://localhost:5173

### 测试账号
| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | 123456 | 管理员 |
| zhangsan | 123456 | 普通用户 |

## 配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| LLM_MODEL | qwen2.5:3b | 大语言模型 |
| REDIS_HOST | 127.0.0.1 | Redis地址 |
| DB_HOST | 127.0.0.1 | 数据库地址 |
| OLLAMA_BASE_URL | http://127.0.0.1:11434 | Ollama地址 |

详见 `server/config.py` 和 `API.md`
