# ============================================================================
# 企业知识库 RAG 问答系统 - RAG 问答服务
# 功能：协调 LLM 和向量数据库，实现完整的 RAG 问答流程
# ============================================================================

from services.llm_service import llm_service
from services.vector_service import vector_service
from services.cache_service import cache_service
from config import Config
from utils import db
from models.knowledge_gap import KnowledgeGap
import time
import hashlib


class RagService:
    """
    RAG 问答服务类
    将检索（Retrieval）与生成（Generation）结合，实现知识库问答
    """

    def __init__(self):
        """初始化 RAG 服务"""
        self.model_used = Config.LLM_MODEL
        self.embedding_model = Config.EMBEDDING_MODEL

    @staticmethod
    def _track_gap(question: str, user_id: int = None):
        """记录知识盲区（未在知识库中找到答案的问题）"""
        try:
            q_hash = hashlib.md5(question.strip().lower().encode()).hexdigest()
            gap = KnowledgeGap.query.filter_by(question_hash=q_hash).first()
            if gap:
                gap.hit_count += 1
                gap.last_asked = time.strftime('%Y-%m-%d %H:%M:%S')
            else:
                gap = KnowledgeGap(
                    question=question[:500],
                    question_hash=q_hash,
                    user_id=user_id,
                    hit_count=1,
                )
                db.session.add(gap)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"[RAG服务] 记录知识盲区失败: {e}")

    def query(self, question: str, session_id: str = None) -> dict:
        """
        执行完整的 RAG 问答流程（带缓存）：
        1.  检查缓存：相同问题直接返回缓存结果（节省 LLM 调用）
        2.  向量检索：从 Chroma 中检索相关文档块
        3.  构建上下文：将检索结果组装为提示词上下文 + 对话历史
        4.  生成回答：使用 LLM 生成最终回答
        5.  缓存结果：将问答结果存入 Redis

        Args:
            question: 用户问题
            session_id: 会话ID（用于多轮对话上下文）

        Returns:
            包含 answer、sources、chunks_retrieved 和 cost_time_ms 的字典
        """
        start_time = time.time()
        print(f"[RAG服务] 开始处理问题: {question[:80]}...")

        # ---- 第一步：检查缓存（精确匹配） ----
        cached = cache_service.get_qa_cache(question)
        if cached:
            elapsed = int((time.time() - start_time) * 1000)
            cached['cost_time_ms'] = elapsed
            cached['from_cache'] = True
            print(f"[RAG服务] 命中缓存，直接返回 (耗时: {elapsed}ms)")
            return cached

        # ---- 第二步：向量检索（带缓存） ----
        print("[RAG服务] 步骤1: 向量检索...")
        relevant_chunks = vector_service.similarity_search(question)

        if not relevant_chunks:
            # 未找到相关文档 → 记录知识盲区
            elapsed = int((time.time() - start_time) * 1000)
            try:
                # 从 Flask 请求上下文中获取 user_id
                from flask import has_request_context, request as flask_req
                uid = None
                if has_request_context():
                    from flask_jwt_extended import get_jwt_identity
                    uid = int(get_jwt_identity())
                self._track_gap(question, uid)
            except Exception:
                pass  # 记录失败不影响主流程

            return {
                'answer': '抱歉，知识库中未找到与您问题相关的信息。请尝试换个问题，或联系管理员添加相关文档。',
                'sources': [],
                'chunks_retrieved': 0,
                'cost_time_ms': elapsed,
                'model_used': self.model_used,
                'embedding_model': self.embedding_model,
                'from_cache': False,
                'knowledge_gap': True,
            }

        # ---- 第三步：构建上下文 ----
        print("[RAG服务] 步骤2: 构建上下文...")
        context_parts = []
        sources = []
        seen_docs = set()  # 用于去重

        for chunk in relevant_chunks:
            # 构建上下文文本
            metadata = chunk['metadata']
            source_info = {
                'title': metadata.get('title', '未知文档'),
                'doc_id': metadata.get('doc_id'),
                'content': chunk['content'][:300] + '...' if len(chunk['content']) > 300 else chunk['content'],
                'similarity': chunk['similarity_score'],
            }
            context_parts.append(chunk['content'])

            # 记录来源（去重）
            doc_title = metadata.get('title', '未知文档')
            if doc_title not in seen_docs:
                seen_docs.add(doc_title)
                sources.append(source_info)

        # 合并上下文
        context = "\n\n---\n\n".join(context_parts)

        # ---- 第四步：获取对话上下文历史（支持多轮对话） ----
        conversation_history = []
        if session_id:
            conversation_history = cache_service.get_conversation_context(session_id)

        # ---- 第五步：生成回答 ----
        print("[RAG服务] 步骤3: 生成回答...")
        answer = llm_service.generate_answer(
            question=question,
            context=context,
            conversation_history=conversation_history,
        )

        # 计算耗时
        elapsed = int((time.time() - start_time) * 1000)

        result = {
            'answer': answer,
            'sources': sources,
            'chunks_retrieved': len(relevant_chunks),
            'cost_time_ms': elapsed,
            'model_used': self.model_used,
            'embedding_model': self.embedding_model,
            'from_cache': False,
        }

        # ---- 第六步：缓存结果 ----
        cache_service.set_qa_cache(question, result)

        # 保存对话上下文
        if session_id:
            cache_service.append_conversation(session_id, "user", question)
            cache_service.append_conversation(session_id, "assistant", answer)

        print(f"[RAG服务] 问答完成，耗时: {elapsed}ms，引用来源: {len(sources)}个")

        return result


# 全局单例
rag_service = RagService()
