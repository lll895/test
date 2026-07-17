"""
Tests for LLMService
=====================
Covers:
  - _is_greeting detection  (greeting, thanks, farewell patterns)
  - _get_greeting_response  (returns expected strings for each type)
  - _build_prompt structure
  - generate_answer skips LLM for social messages
"""

import pytest


class TestIsGreeting:
    """LLMService._is_greeting static method."""

    # ---- Greeting patterns ----

    @pytest.mark.parametrize('text', [
        '你好',
        '您好',
        '你好！',
        '嗨',
        'hi',
        'hello',
        'hey',
        '早上好',
        '下午好',
        '晚上好',
        '在吗',
        '在不在',
        '嗨喽',
        '哈喽',
        '你好啊',
        '您好呀',
        '你们好',
    ])
    def test_greeting_detected(self, text):
        """Common Chinese/English greetings return 'greeting'."""
        from services.llm_service import LLMService
        assert LLMService._is_greeting(text) == 'greeting'

    @pytest.mark.parametrize('text', [
        'HELLO',
        'HI',
        'Hello',
        'Hi ',
        'Hey ',
    ])
    def test_greeting_case_insensitive(self, text):
        """Greeting detection is case-insensitive."""
        from services.llm_service import LLMService
        assert LLMService._is_greeting(text) == 'greeting'

    # ---- Thanks patterns ----

    @pytest.mark.parametrize('text', [
        '谢谢',
        '感谢',
        '多谢',
        '谢谢了',
        '谢谢你',
        'thanks',
        'thank you',
        '好的谢谢',
        '好的感谢',
        'ok谢谢',
    ])
    def test_thanks_detected(self, text):
        """Thanks expressions return 'thanks'."""
        from services.llm_service import LLMService
        assert LLMService._is_greeting(text) == 'thanks'

    # ---- Farewell patterns ----

    @pytest.mark.parametrize('text', [
        '再见',
        '拜拜',
        'bye',
        'see you',
        '下次见',
        '明天见',
    ])
    def test_farewell_detected(self, text):
        """Farewell expressions return 'farewell'."""
        from services.llm_service import LLMService
        assert LLMService._is_greeting(text) == 'farewell'

    # ---- Non-greeting patterns ----
    # Note: 'hello world' IS a greeting because pattern (2) matches 'hello '.
    # Only truly non-greeting text should return None.

    @pytest.mark.parametrize('text', [
        '公司考勤制度是什么',
        'hi, could you help me',
        '谢谢你帮我',
        '再见朋友',
        'bye bye',
    ])
    def test_non_greeting_returns_none(self, text):
        """Regular questions with greeting-like fragments return None."""
        from services.llm_service import LLMService
        assert LLMService._is_greeting(text) is None

    def test_empty_string(self):
        """Empty string returns None."""
        from services.llm_service import LLMService
        assert LLMService._is_greeting('') is None

    def test_whitespace_only(self):
        """Whitespace-only input returns None."""
        from services.llm_service import LLMService
        assert LLMService._is_greeting('   ') is None


class TestGetGreetingResponse:
    """LLMService._get_greeting_response static method."""

    def test_greeting_response_type(self):
        """_get_greeting_response returns a non-empty string for 'greeting'."""
        from services.llm_service import LLMService
        response = LLMService._get_greeting_response('greeting')
        assert isinstance(response, str)
        assert len(response) > 10

    def test_greeting_mentions_xiao_zhi(self):
        """Greeting response mentions '小知' (the assistant name)."""
        from services.llm_service import LLMService
        response = LLMService._get_greeting_response('greeting')
        assert '小知' in response

    def test_thanks_response(self):
        """Thanks response is friendly and acknowledges the thanks."""
        from services.llm_service import LLMService
        response = LLMService._get_greeting_response('thanks')
        assert isinstance(response, str)
        assert len(response) > 5
        assert '谢谢' in response or '不客气' in response or '高兴' in response

    def test_farewell_response(self):
        """Farewell response bids goodbye."""
        from services.llm_service import LLMService
        response = LLMService._get_greeting_response('farewell')
        assert isinstance(response, str)
        assert len(response) > 5

    def test_unknown_type_fallback(self):
        """Unknown greet_type returns a generic greeting."""
        from services.llm_service import LLMService
        response = LLMService._get_greeting_response('unknown_type')
        assert isinstance(response, str)
        assert '你好' in response or '有什么可以帮你的' in response

    def test_responses_are_distinct(self):
        """Different greet_types produce different responses."""
        from services.llm_service import LLMService
        greeting_resp = LLMService._get_greeting_response('greeting')
        thanks_resp = LLMService._get_greeting_response('thanks')
        farewell_resp = LLMService._get_greeting_response('farewell')
        # All three should be different strings
        assert greeting_resp != thanks_resp
        assert thanks_resp != farewell_resp


class TestGenerateAnswer:
    """LLMService.generate_answer flow."""

    def test_greeting_returns_directly_no_llm(self, app):
        """
        When the question is a greeting, generate_answer returns the greeting
        response without invoking the LLM.
        """
        from services.llm_service import LLMService

        svc = LLMService()
        # _llm is None initially -- if the greeting shortcut works,
        # _llm should stay None (never accessed).
        answer = svc.generate_answer('你好', context='')
        assert svc._llm is None  # LLM was never initialized
        assert '小知' in answer

    def test_non_greeting_attempts_llm(self):
        """
        When the question is not a greeting, generate_answer tries to call
        the LLM.  Since ChatOllama is mocked, the invoke returns a
        MagicMock object rather than a real response.
        """
        from services.llm_service import LLMService
        svc = LLMService()
        answer = svc.generate_answer('公司考勤制度是什么', context='Some context')
        # Because the mock ChatOllama returns a MagicMock with a .content
        # attribute that is also a MagicMock (not a string), the answer
        # will be the fallback error message.  We just confirm we got past
        # the greeting check and didn't crash.
        assert answer is not None
        # _llm was accessed (lazy init attempted)
        assert svc._llm is not None


class TestBuildPrompt:
    """LLMService._build_prompt internal method."""

    def test_build_prompt_includes_system_prompt(self):
        """The built prompt contains the system prompt text."""
        from services.llm_service import LLMService
        svc = LLMService()
        prompt = svc._build_prompt('Test question?', 'Some context')
        assert svc.system_prompt in prompt

    def test_build_prompt_includes_question(self):
        """The built prompt contains the user question."""
        from services.llm_service import LLMService
        svc = LLMService()
        prompt = svc._build_prompt('What is the policy?', 'Context here')
        assert 'What is the policy?' in prompt

    def test_build_prompt_includes_context(self):
        """The built prompt contains the knowledge base context."""
        from services.llm_service import LLMService
        svc = LLMService()
        prompt = svc._build_prompt('Question?', 'Relevant context content')
        assert 'Relevant context content' in prompt

    def test_build_prompt_empty_context(self):
        """When context is empty, the prompt notes the lack of references."""
        from services.llm_service import LLMService
        svc = LLMService()
        prompt = svc._build_prompt('Question?', '')
        assert '没有检索到' in prompt or '没有找到' in prompt or '注意' in prompt

    def test_build_prompt_with_history(self):
        """Conversation history is included when provided."""
        from services.llm_service import LLMService
        svc = LLMService()
        history = [
            {'role': 'user', 'content': 'Previous question'},
            {'role': 'assistant', 'content': 'Previous answer'},
        ]
        prompt = svc._build_prompt('New question?', 'Context', history)
        assert 'Previous question' in prompt
        assert 'Previous answer' in prompt


class TestPostProcess:
    """LLMService._post_process helper (instance method)."""

    @pytest.fixture
    def svc(self):
        from services.llm_service import LLMService
        return LLMService()

    def test_strips_whitespace(self, svc):
        """Leading/trailing whitespace is removed."""
        result = svc._post_process('  \nHello  \n')
        assert result == 'Hello'

    def test_removes_answer_prefix(self, svc):
        """'回答：' or '小知：' prefix is stripped."""
        assert svc._post_process('回答：Hello') == 'Hello'
        assert svc._post_process('小知：Hello') == 'Hello'

    def test_removes_prefix_with_colon(self, svc):
        """'小知:Hello' (no space after colon) is also stripped."""
        assert svc._post_process('小知:Hello') == 'Hello'

    def test_removes_prefix_with_space(self, svc):
        """'小知： Hello' (space after colon) is stripped."""
        assert svc._post_process('小知： Hello') == 'Hello'

    def test_normalizes_excess_newlines(self, svc):
        """More than 2 consecutive newlines are collapsed."""
        result = svc._post_process('Line1\n\n\n\nLine2')
        assert result == 'Line1\n\nLine2'

    def test_no_change_for_normal_text(self, svc):
        """Normal text without special prefixes is returned unchanged."""
        text = 'This is a normal response.'
        assert svc._post_process(text) == text
