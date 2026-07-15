# ============================================================================
# 企业知识库 RAG 问答系统 - Redis 缓存服务
# 功能：提供统一的缓存访问接口，支持 LLM 响应缓存、向量缓存、业务数据缓存
# ============================================================================

import redis
import json
import hashlib
import time
from config import Config


class CacheService:
    """
    Redis 缓存服务
    提供缓存读写、失效、热点数据预加载等功能
    """

    def __init__(self):
        """初始化 Redis 连接"""
        self._client = None
        self._connected = False
        self._connect()

    def _connect(self):
        """建立 Redis 连接"""
        try:
            self._client = redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                db=Config.REDIS_DB,
                password=Config.REDIS_PASSWORD,
                decode_responses=Config.REDIS_DECODE_RESPONSES,
                socket_connect_timeout=2,
                socket_timeout=3,
                retry_on_timeout=False,
            )
            # 测试连接
            self._client.ping()
            self._connected = True
            print(f"[缓存服务] Redis 连接成功 ({Config.REDIS_HOST}:{Config.REDIS_PORT})")
        except redis.ConnectionError:
            self._connected = False
            print(f"[缓存服务] Redis 连接失败，缓存功能将降级为直读模式")
        except Exception as e:
            self._connected = False
            print(f"[缓存服务] Redis 初始化异常: {e}")

    @property
    def is_connected(self) -> bool:
        """检查 Redis 是否连接正常"""
        if not self._connected:
            return False
        try:
            self._client.ping()
            return True
        except redis.ConnectionError:
            self._connected = False
            return False

    def _make_key(self, prefix: str, *parts) -> str:
        """
        生成统一的缓存键
        Args:
            prefix: 缓存前缀（如 'qa', 'vector', 'dashboard'）
            parts: 键组成部分（将被拼接）
        Returns:
            格式化的缓存键
        """
        key_parts = [prefix]
        for part in parts:
            if part is not None:
                key_parts.append(str(part))
        return ":".join(key_parts)

    # ==================== 通用缓存操作 ====================

    def get(self, key: str) -> any:
        """获取缓存"""
        if not self._connected:
            return None
        try:
            data = self._client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"[缓存服务] 读取失败 ({key}): {e}")
            return None

    def set(self, key: str, value: any, ttl: int = 300) -> bool:
        """设置缓存"""
        if not self._connected:
            return False
        try:
            self._client.setex(key, ttl, json.dumps(value, ensure_ascii=False))
            return True
        except Exception as e:
            print(f"[缓存服务] 写入失败 ({key}): {e}")
            return False

    def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self._connected:
            return False
        try:
            self._client.delete(key)
            return True
        except Exception:
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        按模式删除缓存（如 'qa:*' 删除所有问答缓存）
        Args:
            pattern: 匹配模式
        Returns:
            删除的键数量
        """
        if not self._connected:
            return 0
        try:
            cursor = 0
            deleted = 0
            while True:
                cursor, keys = self._client.scan(cursor, match=pattern, count=100)
                if keys:
                    deleted += self._client.delete(*keys)
                if cursor == 0:
                    break
            return deleted
        except Exception as e:
            print(f"[缓存服务] 模式删除失败 ({pattern}): {e}")
            return 0

    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self._connected:
            return False
        try:
            return bool(self._client.exists(key))
        except Exception:
            return False

    # ==================== 问答缓存 ====================

    def get_qa_cache(self, question: str, user_id: int = None) -> dict:
        """
        获取缓存的问答结果
        支持精确匹配缓存
        """
        if not self._connected:
            return None

        # 清理问题文本
        clean_q = question.strip().lower()
        q_hash = hashlib.md5(clean_q.encode()).hexdigest()

        # 尝试精确匹配缓存
        key = self._make_key("qa", "exact", q_hash)
        cached = self.get(key)
        if cached:
            print(f"[缓存服务] 命中精确问答缓存: {clean_q[:30]}...")
            return cached

        return None

    def set_qa_cache(self, question: str, result: dict, user_id: int = None):
        """缓存问答结果"""
        if not self._connected:
            return

        clean_q = question.strip().lower()
        q_hash = hashlib.md5(clean_q.encode()).hexdigest()
        key = self._make_key("qa", "exact", q_hash)
        self.set(key, result, Config.CACHE_TTL_QA)

    def invalidate_qa_cache(self):
        """使所有问答缓存失效（新增文档时调用）"""
        self.delete_pattern("qa:*")
        print("[缓存服务] 已清除所有问答缓存")

    # ==================== 向量检索缓存 ====================

    def get_vector_cache(self, query: str) -> list:
        """获取缓存的向量检索结果"""
        if not self._connected:
            return None

        clean_q = query.strip().lower()
        q_hash = hashlib.md5(clean_q.encode()).hexdigest()
        key = self._make_key("vector", q_hash)
        return self.get(key)

    def set_vector_cache(self, query: str, results: list):
        """缓存向量检索结果"""
        if not self._connected:
            return

        clean_q = query.strip().lower()
        q_hash = hashlib.md5(clean_q.encode()).hexdigest()
        key = self._make_key("vector", q_hash)
        self.set(key, results, Config.CACHE_TTL_VECTOR)

    def invalidate_vector_cache(self):
        """使所有向量缓存失效（新增文档时调用）"""
        self.delete_pattern("vector:*")
        print("[缓存服务] 已清除所有向量检索缓存")

    # ==================== 业务数据缓存 ====================

    def get_dashboard_cache(self) -> dict:
        """获取缓存的仪表盘数据"""
        return self.get("dashboard:stats")

    def set_dashboard_cache(self, data: dict):
        """缓存仪表盘数据"""
        self.set("dashboard:stats", data, Config.CACHE_TTL_DASHBOARD)

    def get_categories_cache(self) -> list:
        """获取缓存的分类列表"""
        return self.get("categories:tree")

    def set_categories_cache(self, data: list):
        """缓存分类列表"""
        self.set("categories:tree", data, Config.CACHE_TTL_CATEGORIES)

    def invalidate_categories_cache(self):
        """使分类缓存失效"""
        self.delete("categories:tree")

    # ==================== 用户缓存 ====================

    def get_user_cache(self, user_id: int) -> dict:
        """获取缓存的用户信息"""
        return self.get(f"user:{user_id}")

    def set_user_cache(self, user_id: int, data: dict):
        """缓存用户信息"""
        self.set(f"user:{user_id}", data, Config.CACHE_TTL_USER_STATS)

    def invalidate_user_cache(self, user_id: int):
        """使特定用户缓存失效"""
        self.delete(f"user:{user_id}")

    # ==================== 问答上下文缓存（多轮对话记忆）====================

    def get_conversation_context(self, session_id: str) -> list:
        """
        获取对话上下文历史
        Args:
            session_id: 会话ID
        Returns:
            消息历史列表
        """
        if not self._connected:
            return []
        try:
            key = self._make_key("conversation", session_id)
            data = self._client.lrange(key, -10, -1)  # 最近10条
            messages = [json.loads(m) for m in data]
            return messages
        except Exception:
            return []

    def append_conversation(self, session_id: str, role: str, content: str):
        """
        追加对话消息
        Args:
            session_id: 会话ID
            role: 角色（user/assistant）
            content: 消息内容
        """
        if not self._connected:
            return
        try:
            key = self._make_key("conversation", session_id)
            msg = json.dumps({"role": role, "content": content}, ensure_ascii=False)
            self._client.rpush(key, msg)
            self._client.expire(key, 7200)  # 2小时过期
            # 限制长度，防止无限增长
            self._client.ltrim(key, -20, -1)  # 保留最近20条
        except Exception as e:
            print(f"[缓存服务] 追加对话失败: {e}")

    def clear_conversation(self, session_id: str):
        """清除对话历史"""
        if not self._connected:
            return
        try:
            key = self._make_key("conversation", session_id)
            self._client.delete(key)
        except Exception:
            pass

    # ==================== 统计计数缓存 ====================

    def increment_counter(self, name: str, amount: int = 1) -> int:
        """
        递增计数器（用于请求计数等）
        Args:
            name: 计数器名称
            amount: 增加量
        Returns:
            当前计数值
        """
        if not self._connected:
            return 0
        try:
            key = self._make_key("counter", name)
            return self._client.incrby(key, amount)
        except Exception:
            return 0

    def get_counter(self, name: str) -> int:
        """获取计数器值"""
        if not self._connected:
            return 0
        try:
            key = self._make_key("counter", name)
            val = self._client.get(key)
            return int(val) if val else 0
        except Exception:
            return 0

    def reset_counter(self, name: str):
        """重置计数器"""
        if not self._connected:
            return
        try:
            key = self._make_key("counter", name)
            self._client.delete(key)
        except Exception:
            pass

    # ==================== 缓存预热 ====================

    def warm_up(self):
        """预热常用缓存（启动时调用）"""
        if not self._connected:
            return
        print("[缓存服务] 开始缓存预热...")
        # 可以在这里添加常用的缓存预热逻辑
        print("[缓存服务] 缓存预热完成")


# 全局单例
cache_service = CacheService()
