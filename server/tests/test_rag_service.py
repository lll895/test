"""
Tests for RagService
=====================
Covers the RAG query flow, especially the knowledge-gap path when no relevant
chunks are found by the vector store.
"""

import pytest
from unittest.mock import MagicMock


class TestRagService:
    """RagService query flow tests."""

    def test_query_knowledge_gap_when_no_chunks(self, app, mock_vector_service):
        """
        When vector_service.similarity_search returns an empty list,
        the response should have knowledge_gap=True and a polite fallback answer.
        """
        from services.rag_service import RagService

        mock_vector_service.similarity_search.return_value = []

        svc = RagService()
        result = svc.query("What is the company policy on remote work?")

        assert result['knowledge_gap'] is True
        assert '抱歉' in result['answer'] or '未找到' in result['answer']
        assert result['chunks_retrieved'] == 0
        assert result['sources'] == []
        assert result['from_cache'] is False
        assert 'cost_time_ms' in result
        assert 'model_used' in result

    def test_query_with_chunks(self, app, mock_vector_service):
        """
        When relevant chunks are found, the response should include sources,
        a positive chunks_retrieved count, and NOT have a 'knowledge_gap' key.
        """
        from services.rag_service import RagService

        fake_chunks = [
            {
                'content': 'Remote work policy allows two days work from home per week.',
                'metadata': {'doc_id': 1, 'title': 'HR Policy'},
                'similarity_score': 0.92,
            },
            {
                'content': 'Employees must submit WFH requests via the HR system.',
                'metadata': {'doc_id': 1, 'title': 'HR Policy'},
                'similarity_score': 0.85,
            },
        ]
        mock_vector_service.similarity_search.return_value = fake_chunks

        svc = RagService()
        result = svc.query("Remote work policy?")

        # knowledge_gap key only appears in the no-chunks path
        assert 'knowledge_gap' not in result
        assert result['chunks_retrieved'] == 2
        assert len(result['sources']) > 0
        assert 'answer' in result

    def test_query_returns_expected_keys(self, app, mock_vector_service):
        """The response dictionary contains all expected keys."""
        from services.rag_service import RagService

        fake_chunks = [{
            'content': 'Sample content.',
            'metadata': {'doc_id': 1, 'title': 'Doc'},
            'similarity_score': 0.9,
        }]
        mock_vector_service.similarity_search.return_value = fake_chunks

        svc = RagService()
        result = svc.query("Test question?")

        expected_keys = {'answer', 'sources', 'chunks_retrieved', 'cost_time_ms',
                         'model_used', 'embedding_model', 'from_cache'}
        assert expected_keys.issubset(result.keys())

    def test_query_caches_result(self, app, mock_vector_service,
                                 mock_cache_service):
        """
        After a query with chunks, the result should be cached
        via cache_service.set_qa_cache (since the cache miss on
        get_qa_cache means a new answer was generated).
        """
        from services.rag_service import RagService

        fake_chunks = [{
            'content': 'Policy content.',
            'metadata': {'doc_id': 1, 'title': 'Policy'},
            'similarity_score': 0.9,
        }]
        mock_vector_service.similarity_search.return_value = fake_chunks

        svc = RagService()
        svc.query("Cache test?")

        # After a cache-miss query with chunks, set_qa_cache is called
        mock_cache_service.set_qa_cache.assert_called_once()

    def test_query_returns_cached_result(self, app, mock_cache_service,
                                         mock_vector_service):
        """
        When cache_service.get_qa_cache returns a cached result, the query
        returns it directly without calling vector_service.
        """
        from services.rag_service import RagService

        cached_response = {
            'answer': 'Cached answer.',
            'sources': [],
            'chunks_retrieved': 0,
            'cost_time_ms': 5,
            'model_used': 'test-model',
            'embedding_model': 'test-embedding',
            'from_cache': True,
        }
        mock_cache_service.get_qa_cache.return_value = cached_response

        svc = RagService()
        result = svc.query("Cached question?")

        assert result['from_cache'] is True
        assert result['answer'] == 'Cached answer.'
        # vector_service should NOT be called in cache-hit path
        mock_vector_service.similarity_search.assert_not_called()

    def test_global_singleton(self):
        """rag_service global singleton is an instance of RagService."""
        from services.rag_service import rag_service
        from services.rag_service import RagService
        assert isinstance(rag_service, RagService)

    def test_track_gap_creates_record(self, app):
        """_track_gap inserts a KnowledgeGap record."""
        from services.rag_service import RagService
        from models.knowledge_gap import KnowledgeGap

        with app.app_context():
            RagService._track_gap("What is the meaning of life?")

            gaps = KnowledgeGap.query.all()
            assert len(gaps) >= 1
            matching = [g for g in gaps if 'meaning of life' in g.question]
            assert len(matching) >= 1

    @pytest.mark.parametrize('question', [
        'Hello',
        'Hi there',
        'Thanks',
        'Goodbye',
    ])
    def test_greeting_questions(self, app, mock_cache_service,
                                mock_vector_service, question):
        """
        Greeting-like questions are still processed through the full RAG flow
        (not special-cased by RagService itself; LLMService handles greetings).
        This test verifies that the flow doesn't crash on short social messages.
        """
        from services.rag_service import RagService
        mock_vector_service.similarity_search.return_value = []

        svc = RagService()
        result = svc.query(question)

        # It may return knowledge_gap, but should not throw
        assert 'answer' in result
        assert result['chunks_retrieved'] == 0
