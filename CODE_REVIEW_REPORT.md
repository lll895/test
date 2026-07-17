# Code Review Report — 企业知识库 RAG 问答系统

**审查日期**: 2026-07-17
**审查范围**: 全量代码（70 个文件，7731 行新增）
**审查工具**: AI 代码审查（多角度扫描 + 验证）

---

## 审查摘要

| 严重级别 | 数量 | 说明 |
|---------|------|------|
| 🔴 CRITICAL | 4 | 安全漏洞、数据丢失风险 |
| 🟠 HIGH | 5 | 安全缺失、逻辑缺陷 |
| 🟡 MEDIUM | 4 | 性能问题、数据完整性 |
| 🔵 LOW | 11 | 代码质量、死代码 |

---

## 🔴 CRITICAL（严重）

### C1. MD5 密码哈希 — 密码存储方式不安全

**位置**: `server/routes/auth.py:22-30`
**问题**: 使用 `hashlib.md5()` 对密码加密。MD5 是已被破解的算法，可在秒级被暴力破解。
**危害**: 数据库泄露后所有用户密码直接暴露。
**建议**: 改用 `werkzeug.security.generate_password_hash()` (PBKDF2-SHA256)。

```python
# 当前（不安全）
user.password = hashlib.md5(password.encode()).hexdigest()

# 建议
from werkzeug.security import generate_password_hash
user.password = generate_password_hash(password)
```

### C2. 硬编码密钥 — JWT 和数据库密码写在源码中

**位置**: `server/config.py:12,18,29`
**问题**: `SECRET_KEY`、`JWT_SECRET_KEY`、`DB_PASSWORD` 的默认值都是硬编码字符串。
**危害**: 攻击者可伪造 JWT Token 冒充任意用户，或直接连接数据库。
**建议**: 移除默认值，环境变量缺失时直接报错：

```python
SECRET_KEY = os.environ['SECRET_KEY']  # 无默认值
```

### C3. 文档编辑失败导致数据永久丢失

**位置**: `server/routes/document.py:575-577`
**问题**: 编辑文档内容时，旧向量数据在重新处理前已提交删除。若重新向量化失败，文档块永久丢失。
**危害**: 用户编辑文档保存失败后，该文档在向量搜索中永远消失。
**建议**: 将删除和重新处理放在同一事务中，处理成功后才提交。

### C4. 无上传文件大小限制

**位置**: `server/config.py`（缺少 `MAX_CONTENT_LENGTH`）
**问题**: 未设置 Flask 的最大请求体限制。
**危害**: 攻击者可上传超大文件耗尽服务器磁盘。
**建议**: 添加 `MAX_CONTENT_LENGTH = 50 * 1024 * 1024`

---

## 🟠 HIGH（高）

### H1. 异常信息泄露到客户端

**位置**: `server/routes/document.py:211,253,420,598`
**问题**: 错误响应中包含 `str(e)` 原始异常信息。
**危害**: 泄露 Python 堆栈、文件路径、SQL 片段等，帮助攻击者进一步利用。
**建议**: 服务端记录完整日志，客户端返回通用错误信息。

### H2. 认证接口无速率限制

**位置**: `server/routes/auth.py:33,82,144`
**问题**: 登录、注册、忘记密码接口均无防刷机制。
**危害**: 可被暴力破解密码，或批量发送重置请求。
**建议**: 引入 Flask-Limiter，登录限制 5次/分钟/IP。

### H3. FLASK_ENV 缺失导致令牌泄露

**位置**: `server/routes/auth.py:180-183`
**问题**: `Config` 类没有 `FLASK_ENV` 属性，导致 `getattr` 取不到值，始终回退到 `'development'`。密码重置令牌在生产环境会直接返回给客户端。
**建议**: 在 Config 中添加 `FLASK_ENV` 或简化逻辑。

### H4. 上传失败产生孤立文件

**位置**: `server/routes/document.py:164-165`
**问题**: 文件保存到磁盘后才进行后续处理（文本提取、向量化），任何一个步骤失败文件都不会被清理。
**建议**: 使用 try/finally 确保失败时清理文件。

---

## 🟡 MEDIUM（中）

### M1. N+1 查询问题

**位置**: `server/routes/document.py:74` + `server/models/document.py:81-82`
**问题**: 文档列表每页 20 条时，`to_dict()` 中的 `self.category` 和 `self.uploader` 触发 40+ 次额外 SQL 查询。
**建议**: 使用 `joinedload()` 预加载关联关系。

```python
from sqlalchemy.orm import joinedload
query = Document.query.options(joinedload(Document.category), joinedload(Document.uploader))
```

### M2. LLM 健康检查始终返回 OK

**位置**: `server/routes/health.py:56-64`
**问题**: `_check_llm()` 只检查对象是否初始化，不实际连接 Ollama，Ollama 宕机也返回正常。
**建议**: 添加实际连通性检测。

### M3. 版本分组仅依赖标题匹配

**位置**: `server/routes/document.py:149-157`
**问题**: 不同用户上传同名文档会被错误归为同一版本组。
**建议**: 加入 `uploaded_by` 或其他去重条件。

### M4. 分类创建存在竞态条件

**位置**: `server/routes/document.py:296-297`
**问题**: 先查后插无唯一约束，两个管理员同时创建同名分类会重复。
**建议**: 给 `Category.name` 添加 `unique=True` 约束。

---

## 🔵 LOW（低）

### L1. 死代码：健康检查缓存变量
**位置**: `server/routes/health.py:20-21` — `_health_cache` 和 `_health_cache_ttl` 定义了但从未使用。

### L2. `print()` 代替日志
**位置**: `server/services/llm_service.py:64` — `print()` 绕过了统一日志系统。

### L3. 内联 `__import__()`
**位置**: `server/routes/health.py:90`, `server/models/password_reset.py:53,55` — 使用 `__import__('datetime')` 而非模块级导入。

### L4. 对话上下文长度不一致
**位置**: `server/services/cache_service.py:263,285` — 读取 10 条但存储保留 20 条。

### L5. 双重 JSON 序列化
**位置**: `server/routes/qa.py:80,152,215` — MySQL JSON 类型自动序列化，额外 `json.dumps()` 导致双编码。

### L6. 会话无所有权检查
**位置**: `server/routes/qa.py:40-45,258-265` — 任何用户可访问任意 session_id 的对话历史。

### L7. 缺少 `exc_info=True`
**位置**: `server/routes/document.py:210` — 错误日志未记录堆栈。

### L8. 分类 ID 未验证存在性
**位置**: `server/routes/document.py:522-526` — 可设置不存在的 `category_id`。

### L9. 未使用的参数
**位置**: `server/services/cache_service.py:151` — `get_qa_cache` 的 `user_id` 参数从未使用。

### L10. Chroma 私有 API 调用
**位置**: `server/services/vector_service.py:197` — 访问 `_collection` 私有属性。

---

## 审查结论

**总体评价**: 项目功能完整、架构清晰，工程化设施完善（CI/CD、测试、日志、监控）。

**需要优先修复的 TOP 5**:
1. 🔴 **MD5 密码改为 bcrypt/werkzeug** — 安全底线
2. 🔴 **硬编码密钥移到环境变量** — 防止凭据泄露
3. 🔴 **文档编辑事务问题** — 防止数据丢失
4. 🟠 **异常信息不要泄露给客户端** — 信息安全
5. 🟠 **认证接口加限流** — 防暴力破解

---

*报告生成于 2026-07-17 | 审查范围: 70 files, +7731 / -1033 lines*
