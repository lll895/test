"""
企业知识库 RAG 问答系统 - 向量数据库服务
======================================
功能：封装 Chroma 向量数据库操作，提供文档向量化存储和相似度检索
"""

from config import Config
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from services.cache_service import cache_service
from utils.logger import get_logger

logger = get_logger(__name__)


class VectorService:
    """
    向量数据库服务类
    负责文档的向量化存储和语义检索，使用 Chroma 作为向量数据库
    """

    def __init__(self):
        """初始化向量服务，创建嵌入模型和 Chroma 客户端"""
        self.embedding_model_name = Config.EMBEDDING_MODEL
        self.base_url = Config.OLLAMA_BASE_URL
        self.persist_dir = Config.CHROMA_PERSIST_DIR
        self.collection_name = Config.CHROMA_COLLECTION_NAME

        # 初始化嵌入模型
        logger.info(f"初始化嵌入模型: {self.embedding_model_name}")
        self._embeddings = OllamaEmbeddings(
            model=self.embedding_model_name,
            base_url=self.base_url,
        )

        # 初始化文本切分器
        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""],
        )

        # 延迟初始化 Chroma 客户端
        self._vector_store = None

    @property
    def vector_store(self) -> Chroma:
        """
        获取 Chroma 向量存储实例（延迟加载）
        如果数据库文件不存在则自动创建
        """
        if self._vector_store is None:
            logger.info(f"初始化 Chroma 数据库 (持久目录: {self.persist_dir})")
            self._vector_store = Chroma(
                collection_name=self.collection_name,
                embedding_function=self._embeddings,
                persist_directory=self.persist_dir,
            )
        return self._vector_store

    def split_document(self, title: str, content: str, doc_id: int) -> list[dict]:
        """
        将文档内容切分为文本块

        Args:
            title: 文档标题
            content: 文档文本内容
            doc_id: 文档ID

        Returns:
            文本块列表，每块包含 content、metadata 和 chunk_index
        """
        # 为内容添加标题前缀，帮助模型理解上下文
        full_content = f"## {title}\n\n{content}"

        # 使用 LangChain 的文本切分器进行切分
        lc_docs = self._text_splitter.create_documents(
            texts=[full_content],
            metadatas=[{'doc_id': doc_id, 'title': title}],
        )

        chunks = []
        for idx, lc_doc in enumerate(lc_docs):
            chunks.append({
                'content': lc_doc.page_content,
                'metadata': lc_doc.metadata,
                'chunk_index': idx,
            })

        logger.info(f"文档 '{title}' 切分为 {len(chunks)} 个文本块")
        return chunks

    def add_document(self, doc_id: int, title: str, content: str) -> list[dict]:
        """
        将文档添加到向量数据库

        Args:
            doc_id: 文档ID
            title: 文档标题
            content: 文档文本内容

        Returns:
            包含向量ID的文本块列表
        """
        chunks = self.split_document(title, content, doc_id)

        lc_docs = []
        for chunk in chunks:
            lc_doc = Document(
                page_content=chunk['content'],
                metadata={
                    'doc_id': doc_id,
                    'title': title,
                    'chunk_index': chunk['chunk_index'],
                }
            )
            lc_docs.append(lc_doc)

        vector_ids = self.vector_store.add_documents(lc_docs)

        for i, chunk in enumerate(chunks):
            if i < len(vector_ids):
                chunk['vector_id'] = vector_ids[i]

        logger.info(f"文档 '{title}' 已向量化，共 {len(chunks)} 个向量")
        return chunks

    def delete_document(self, vector_ids: list[str]):
        """
        从向量数据库中删除指定向量

        Args:
            vector_ids: 要删除的向量ID列表
        """
        if not vector_ids:
            return

        try:
            self.vector_store.delete(vector_ids)
            logger.info(f"已删除 {len(vector_ids)} 个向量")
        except Exception as e:
            logger.error(f"删除向量时出错: {e}")

    def similarity_search(self, query: str, k: int = None) -> list[dict]:
        """
        执行相似度搜索，查询最相关的文档块（带缓存）

        Args:
            query: 用户查询文本
            k: 返回的最相关结果数（默认使用配置值）

        Returns:
            相关文档块列表，每块包含 content、metadata 和 similarity_score
        """
        if k is None:
            k = Config.RETRIEVAL_K

        logger.debug(f"执行相似度搜索: query='{query[:50]}...', top_k={k}")

        # 尝试从缓存获取
        cached = cache_service.get_vector_cache(query)
        if cached:
            logger.debug(f"命中向量检索缓存")
            return cached

        # 执行带分数的相似度搜索
        results = self.vector_store.similarity_search_with_score(query, k=k)

        # 格式化结果
        formatted_results = []
        for doc, score in results:
            similarity = 1.0 - (score / 2)
            formatted_results.append({
                'content': doc.page_content,
                'metadata': doc.metadata,
                'similarity_score': round(similarity, 4),
            })

        # 缓存结果
        if formatted_results:
            cache_service.set_vector_cache(query, formatted_results)

        logger.info(f"搜索完成，找到 {len(formatted_results)} 个相关结果")
        return formatted_results

    def get_document_count(self) -> int:
        """
        获取向量数据库中的文档总数

        Returns:
            向量总数
        """
        try:
            return self.vector_store._collection.count()
        except Exception:
            return 0


# 全局单例
vector_service = VectorService()
