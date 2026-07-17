# 提示词开发日志 (Prompt Log)

## 项目概述
企业知识库 RAG（检索增强生成）问答系统，基于 LangChain + Ollama + Flask + Vue3 实现。

---

## Prompt 记录

### 1. RAG 问答系统提示词（llm_service.py）

**用途**：LLM 回答生成的核心系统提示词，定义 AI 助手的角色和行为准则。

```
你是一个专业友善的企业知识库助手"小知"，帮员工解答公司制度、技术文档等问题。

回答原则：
1. 基于知识库内容回答，不编造信息。引用内容时自然融入回答
2. 如果知识库没有相关信息，如实告知并建议联系管理员或换个问法
3. 用通俗易懂的语言，条理清晰，适当分段
4. 回答中文问题时使用中文
5. 对于问候、感谢等社交对话，自然回应即可
```

---

### 2. 提交项目到 GitHub

**对应功能**：项目版本管理
**对应文件**：项目根目录（Git 配置）

**Prompt**：
> 将我这个项目提交到GitHub上面https://github.com/lll895/test.git这是我的仓库...这是第二次提交记得备注第二天我所写的新功能

**AI 处理**：
- 通过生成临时 SSH 密钥、GitHub API 添加公钥、git push 完成提交
- 由于环境网络限制，采用了 Python + SSH 方式绕过

---

### 3. 实现 CI/CD、单元测试、工程化实践

**对应功能**：工程化基础设施
**对应文件**：
- `.github/workflows/backend-ci.yml`, `.github/workflows/frontend-ci.yml`, `.github/workflows/deploy.yml`
- `server/tests/`（9 个测试文件，149 个测试）
- `client/src/__tests__/`（3 个测试文件，23 个测试）
- `server/utils/logger.py`, `server/utils/exceptions.py`
- `server/routes/health.py`
- `server/.env.example`, `client/.env.*`

**Prompt**：
> (1)项目实现了CI/CD（如GitHubActions自动部署）；
> (2)项目包含单元测试（如Jest/PyTest）；
> (3)项目使用了环境变量、日志、错误监控等工程化。实现这些

**AI 返回摘要**：
- 创建了 3 个 GitHub Actions 工作流文件
- 后端 pytest 测试：149 个测试覆盖所有 API 和服务
- 前端 vitest 测试：23 个测试覆盖 API 模块和状态管理
- 统一日志系统（彩色控制台 + 文件轮转）
- 自定义异常体系 + Sentry 集成
- 健康检查端点（/api/health, /api/health/live, /api/health/ready）
- 环境变量示例文件

---

### 4. 创建个人信息页面

**对应功能**：用户个人信息管理
**对应文件**：`client/src/views/profile/Profile.vue`, `client/src/router/index.js`, `client/src/views/Layout.vue`

**Prompt**：
> 9. 完善个人信息页面...10. 忘记密码/密码重置...12. 文档版本管理...13. 文档在线编辑

**AI 返回摘要**：
- 创建 `Profile.vue`：头像/基本信息卡片、编辑表单、密码修改、问答统计
- 添加路由 `/profile`，Layout 下拉菜单改为跳转
- 复用已有 `GET/PUT /api/auth/profile` 接口

---

### 5. 实现忘记密码/重置密码

**对应功能**：密码重置流程
**对应文件**：`server/routes/auth.py`, `server/models/password_reset.py`, `client/src/views/Login.vue`, `client/src/api/index.js`

**Prompt**：
> 10. 忘记密码/密码重置（同上面第4条一起提出）

**AI 返回摘要**：
- 后端：`POST /api/auth/forgot-password` 生成重置令牌存入 `password_reset_tokens` 表（30分钟 TTL）
- `POST /api/auth/reset-password` 验证令牌并重置密码
- 前端：Login.vue 添加"忘记密码？"链接 + 两步对话框（申请令牌→重置密码）
- 开发模式直接返回令牌，生产环境通过邮件发送

---

### 6. 实现文档版本管理

**对应功能**：文档版本管理
**对应文件**：`server/models/document.py`, `server/routes/document.py`, `client/src/views/document/DocumentList.vue`, `client/src/views/document/DocumentUpload.vue`

**Prompt**：
> 12. 文档版本管理（同上面第4条一起提出）

**AI 返回摘要**：
- Document 模型新增 `version`、`version_group_id`、`change_note` 字段
- 上传逻辑改为：检测同标题文档→自动创建新版本（递增版本号）
- 新增 `GET /api/documents/:id/versions` 版本历史接口
- 前端列表显示 v1/v2 标签、详情对话框有版本说明、版本历史时间轴弹窗
- 上传页新增"版本说明"输入框

---

### 7. 实现文档在线编辑

**对应功能**：文档在线编辑
**对应文件**：`server/routes/document.py`, `client/src/views/document/DocumentList.vue`

**Prompt**：
> 13. 文档在线编辑（同上面第4条一起提出）

**AI 返回摘要**：
- 后端新增 `PUT /api/documents/:id` 更新元信息
- `PUT /api/documents/:id/content` 更新内容 + 自动删除旧向量 + 重新向量化
- 前端详情对话框新增编辑按钮，切换为文本域，保存后重新索引

---

### 8. 前端 UI 美化

**对应功能**：前端界面全面升级
**对应文件**：`client/src/style.css`, `client/src/views/Layout.vue`, `client/src/views/Login.vue`, `client/src/views/home/UserHome.vue`, `client/src/views/home/AdminHome.vue`, 以及其他所有页面

**Prompt**：
> 前端界面优化更好看，更灵动一些
> 页面能不能设计好看高级一些，管理员页面也接上快捷操作的界面

**AI 返回摘要**：
- 全局 CSS 变量系统（颜色、圆角、阴影、过渡）
- 登录页：动态光晕呼吸动画 + 网格背景 + 毛玻璃品牌区域
- 侧边栏：深色渐变 + 圆角菜单项 + 底部折叠按钮
- 顶部栏：毛玻璃效果（backdrop-filter）+ 搜索快捷键提示
- 首页：浅蓝渐变欢迎横幅 + 彩色图标快捷入口 + 卡片飞入动画
- 管理首页：深色渐变欢迎横幅 + 快捷操作卡片 + 趋势箭头
- 所有页面统一使用 `page-container` + `card-animate` 动画

---

### 9. 修复数据库迁移问题

**对应功能**：数据库兼容性修复
**对应文件**：`server/scripts/migrate.py`, `server/models/user.py`, `server/models/password_reset.py`

**Prompt**：
> 1.知识文档还是进不去...2.重置密码明明是刚生成的令牌反而显示过期不能用...3.请假申请和新员工入职的页面进不去

**AI 返回摘要**：
- 创建 `scripts/migrate.py`：自动检测数据库缺失字段并添加
- 将 `reset_token` 从 User 模型移到独立的 `password_reset_tokens` 表
- 创建 `PasswordResetToken` 模型，密码重置不再依赖 Redis
- 运行迁移脚本：添加了 `documents.version`、`version_group_id`、`change_note` 字段

---

### 10. 修复路由重定向循环

**对应功能**：登录路由修复
**对应文件**：`client/src/router/index.js`, `client/src/views/Login.vue`

**Prompt**：
> 普通用户登录了为什么一直显示登录失效登陆不进去

**AI 返回摘要**：
- 根因：`/` 路由固定重定向到 `/home`（仅 admin 可访问），普通用户触发无限重定向循环
- 修复：根路由 redirect 改为函数，根据 `user.role` 自动跳转
- 角色检查失败时不再 `next('/')`，而是跳转到对应的首页
- 登录后统一 `router.push('/')`，由路由自动判断角色

---

### 11. 文档权限控制

**对应功能**：管理员/用户权限分离
**对应文件**：`server/routes/document.py`, `client/src/views/document/DocumentList.vue`, `client/src/views/document/DocumentUpload.vue`

**Prompt**：
> 1.文档操作只能管理员来普通用户只能查询

**AI 返回摘要**：
- 后端：上传/编辑/删除接口全部添加 `@admin_required()` 装饰器
- 前端：上传/编辑/删除按钮根据 `userStore.isAdmin` 条件渲染
- 上传页：非管理员访问弹出提示并自动跳转

---

### 12. 实现工作流申请表单页面

**对应功能**：快捷操作页面
**对应文件**：`client/src/views/workflow/WorkflowForm.vue`, `client/src/router/index.js`, `server/scripts/seed_workflow.py`

**Prompt**：
> 3.给我把快捷操作的那几个功能的页面和功能实现

**AI 返回摘要**：
- 创建通用 `WorkflowForm.vue`：根据 actionId 动态显示不同表单字段
- 请假：请假类型选择（年假/病假/事假等）+ 日期范围 + 事由
- 报销：费用类型选择 + 金额 + 事由
- 出差：目的地 + 日期范围 + 事由
- 入职/加班：日期 + 事由
- 路由 `/workflow/:actionId`，种子数据 URL 改为内部路由
- 首页和问答页的工作流按钮点击后跳转到内部表单

---

### 13. 第三次提交到 GitHub

**对应功能**：项目版本管理
**对应文件**：所有变更文件

**Prompt**：
> 先把现在的项目提交到GitHub上写上备注第三天的基于RAG的问答系统还有新增的功能

**AI 处理**：
- `git add -A && git commit` 提交所有变更
- 临时 SSH 密钥 + GitHub API 推送
- 提交信息涵盖所有第三天新增功能

---

### 14. 系统提示词（LLM 回答生成）

**对应功能**：AI 问答角色定义
**对应文件**：`server/services/llm_service.py`

**系统提示词**（完整版）：
```
你是一个专业友善的企业知识库助手"小知"，帮员工解答公司制度、技术文档等问题。

回答原则：
1. 基于知识库内容回答，不编造信息。引用内容时自然融入回答
2. 如果知识库没有相关信息，如实告知并建议联系管理员或换个问法
3. 用通俗易懂的语言，条理清晰，适当分段
4. 回答中文问题时使用中文
5. 对于问候、感谢等社交对话，自然回应即可
```
