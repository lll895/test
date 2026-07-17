# ============================================================================
# 企业知识库 RAG 问答系统 - 大语言模型服务（升级版）
# 功能：封装 Ollama 的 LLM 调用，提供：
#   - 人性化、有温度的回答
#   - 多轮对话上下文支持
#   - 问候语和常见问题的智能处理
#   - 流式生成（SSE）
#   - 置信度评分
# ============================================================================

from config import Config
from langchain_ollama import ChatOllama
from utils.logger import get_logger
import json
import re

logger = get_logger(__name__)


# 问候模式列表（用于快速匹配）
GREETING_PATTERNS = [
    r'^(你好|您好|嗨|hi|hello|hey|早上好|下午好|晚上好|在吗|在不在)[！!\.\s]*$',
    r'^(嗨喽|哈喽|hello|hi\s|hey\s)',
    r'^(你好啊|您好呀|你们好)',
]
THANKS_PATTERNS = [
    r'^(谢谢|感谢|多谢|谢谢了|谢谢你|thanks|thank you)[！!\.,\s]*$',
    r'^(好的谢谢|好的感谢|ok谢谢)',
]
FAREWELL_PATTERNS = [
    r'^(再见|拜拜|bye|see you|下次见|明天见)[！!\.,\s]*$',
]


class LLMService:
    """
    大语言模型服务类（升级版）
    提供有温度、有上下文的智能问答能力
    """

    def __init__(self):
        """初始化 LLM 服务"""
        self.model_name = Config.LLM_MODEL
        self.base_url = Config.OLLAMA_BASE_URL
        self._llm = None  # 延迟初始化

        # 系统提示词（定义 AI 助手的角色和行事准则）
        self.system_prompt = """你是一个专业友善的企业知识库助手"小知"，帮员工解答公司制度、技术文档等问题。

回答原则：
1. 基于知识库内容回答，不编造信息。引用内容时自然融入回答
2. 如果知识库没有相关信息，如实告知并建议联系管理员或换个问法
3. 用通俗易懂的语言，条理清晰，适当分段
4. 回答中文问题时使用中文
5. 对于问候、感谢等社交对话，自然回应即可
"""

    @property
    def llm(self):
        """
        获取 ChatOllama 实例（延迟加载）
        """
        if self._llm is None:
            print(f"[LLM服务] 初始化模型: {self.model_name} (URL: {self.base_url})")
            self._llm = ChatOllama(
                model=self.model_name,
                base_url=self.base_url,
                temperature=0.3,
                top_p=0.8,
                num_predict=2048,
                top_k=30,
                repeat_penalty=1.1,
                num_ctx=4096,
            )
        return self._llm

    @staticmethod
    def _is_greeting(question: str) -> str | None:
        """
        检测是否为问候/感谢/告别等社交性消息
        Returns:
            匹配到的消息类型: 'greeting', 'thanks', 'farewell' 或 None
        """
        clean_q = question.strip().lower()
        for pattern in GREETING_PATTERNS:
            if re.match(pattern, clean_q):
                return 'greeting'
        for pattern in THANKS_PATTERNS:
            if re.match(pattern, clean_q):
                return 'thanks'
        for pattern in FAREWELL_PATTERNS:
            if re.match(pattern, clean_q):
                return 'farewell'
        return None

    @staticmethod
    def _get_greeting_response(greet_type: str) -> str:
        """获取社交性消息的快速回复"""
        responses = {
            'greeting': (
                "你好呀！👋 我是企业知识库助手**小知**，很高兴为你服务！\n\n"
                "你可以问我以下类型的问题：\n"
                "- 📋 **公司制度**：考勤、请假、报销等流程\n"
                "- 📚 **技术文档**：开发规范、系统架构等\n"
                "- 🏷️ **产品使用**：功能说明、操作指南等\n\n"
                "有什么我可以帮你的吗？😊"
            ),
            'thanks': (
                "不客气！很高兴能帮到你 😊\n\n"
                "如果还有其他问题，随时问我哦！"
            ),
            'farewell': (
                "再见！👋 有需要随时找我，祝你工作愉快！😊"
            ),
        }
        return responses.get(greet_type, "你好！有什么可以帮你的吗？😊")

    def _build_prompt(self, question: str, context: str,
                      conversation_history: list = None) -> str:
        """
        构建带上下文的提示词

        Args:
            question: 用户问题
            context: 检索到的文档上下文
            conversation_history: 对话历史（多轮对话用）

        Returns:
            构建好的提示词
        """
        # 1. 系统角色定义（顶部固定指令）
        parts = [self.system_prompt]

        # 2. 多轮对话历史（如果有）
        if conversation_history and len(conversation_history) > 0:
            history_text = "\n".join([
                f"{'用户' if msg['role'] == 'user' else '小知'}: {msg['content']}"
                for msg in conversation_history[-4:]  # 取最近4轮（减少上下文长度，加速生成）
            ])
            parts.append(f"""
【之前的对话记录】
{history_text}
""")

        # 3. 知识库上下文（如果有）
        if context and context.strip():
            parts.append(f"""
【知识库参考内容】
{context}

请基于以上参考内容回答用户的问题。如果参考内容不足以完整回答，请说明你知道的部分，并指出不确定的地方。引用相关内容时，自然融入回答，不要生硬地标注来源编号。
""")
        else:
            parts.append("""
【注意】当前没有检索到相关的知识库内容。如果用户问的是知识性问题，请如实告知没有找到相关信息，并建议换个问法或联系管理员。如果是日常对话则正常回复即可。
""")

        # 4. 用户问题
        parts.append(f"""
【用户问题】
{question}

【你的回答】请以"小知"的身份，用自然亲切的语气回答：""")

        return "\n\n".join(parts)

    def generate_answer(self, question: str, context: str,
                        conversation_history: list = None) -> str:
        """
        根据问题、上下文和对话历史生成回答

        Args:
            question: 用户问题
            context: 检索到的相关文档上下文
            conversation_history: 多轮对话历史

        Returns:
            生成的回答文本
        """
        # 第一步：检测是否为社交性消息（问候、感谢、告别）
        social_type = self._is_greeting(question)
        if social_type:
            logger.info(f"检测到{social_type}消息，快速回复")
            return self._get_greeting_response(social_type)

        # 第二步：构建带上下文的提示词
        prompt = self._build_prompt(question, context, conversation_history)

        # 第三步：调用 LLM 生成回答
        logger.info(f"开始生成回答 (上下文长度: {len(context)}字符, "
                    f"对话历史: {len(conversation_history or [])}条)")
        try:
            response = self.llm.invoke(prompt)
            answer = response.content

            # 后处理：清理回答
            answer = self._post_process(answer)

            logger.info(f"回答生成完成 ({len(answer)}字符)")
            return answer

        except Exception as e:
            logger.error(f"生成失败: {e}")
            return ("抱歉，我遇到了一个技术故障 😅 请稍后再试一次。"
                    "如果问题持续存在，请联系系统管理员。")

    def _post_process(self, answer: str) -> str:
        """
        后处理回答文本
        - 去除多余的空白行
        - 确保以合适的语气结尾
        - 处理特殊标记
        """
        # 去除开头结尾的空白
        answer = answer.strip()

        # 如果回答以 "回答：" 或 "小知：" 开头，去除前缀
        answer = re.sub(r'^(回答|小知)[：:\s]*', '', answer)

        # 合并多余的空行（超过2个换行符的合并为2个）
        answer = re.sub(r'\n{3,}', '\n\n', answer)

        return answer

    def generate_stream(self, question: str, context: str,
                        conversation_history: list = None):
        """
        流式生成回答（用于 SSE）

        Args:
            question: 用户问题
            context: 检索到的文档上下文
            conversation_history: 多轮对话历史

        Yields:
            生成的文本片段
        """
        # 检测社交消息
        social_type = self._is_greeting(question)
        if social_type:
            yield self._get_greeting_response(social_type)
            return

        # 构建提示词
        prompt = self._build_prompt(question, context, conversation_history)

        logger.info("开始流式生成...")
        try:
            # 使用 stream 方法逐片生成
            for chunk in self.llm.stream(prompt):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"流式生成失败: {e}")
            yield "抱歉，回答生成过程中出现了问题，请稍后再试。"


# 全局单例
llm_service = LLMService()
