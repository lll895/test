"""
Tests for DocumentService
==========================
Covers:
  - extract_text() for .txt and .md files
  - SUPPORTED_EXTENSIONS constant
"""

import os
import tempfile
import pytest


class TestDocumentService:
    """DocumentService text extraction and supported extensions."""

    def test_supported_extensions_contains_txt(self):
        """SUPPORTED_EXTENSIONS includes .txt."""
        from services.document_service import DocumentService
        assert '.txt' in DocumentService.SUPPORTED_EXTENSIONS

    def test_supported_extensions_contains_md(self):
        """SUPPORTED_EXTENSIONS includes .md."""
        from services.document_service import DocumentService
        assert '.md' in DocumentService.SUPPORTED_EXTENSIONS

    def test_supported_extensions_contains_pdf(self):
        """SUPPORTED_EXTENSIONS includes .pdf."""
        from services.document_service import DocumentService
        assert '.pdf' in DocumentService.SUPPORTED_EXTENSIONS

    def test_supported_extensions_contains_docx(self):
        """SUPPORTED_EXTENSIONS includes .docx."""
        from services.document_service import DocumentService
        assert '.docx' in DocumentService.SUPPORTED_EXTENSIONS

    def test_supported_extensions_map_values(self):
        """SUPPORTED_EXTENSIONS maps extensions to file type strings."""
        from services.document_service import DocumentService
        ext_map = DocumentService.SUPPORTED_EXTENSIONS
        assert ext_map['.txt'] == 'txt'
        assert ext_map['.md'] == 'md'
        assert ext_map['.pdf'] == 'pdf'
        assert ext_map['.docx'] == 'docx'

    def test_extract_text_txt(self):
        """extract_text reads a .txt file correctly."""
        from services.document_service import DocumentService
        content = "Hello, this is a test document.\nWith multiple lines."
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt',
                                         delete=False, encoding='utf-8') as f:
            f.write(content)
            tmp_path = f.name
        try:
            result = DocumentService.extract_text(tmp_path, 'txt')
            assert result == content
        finally:
            os.unlink(tmp_path)

    def test_extract_text_md(self):
        """extract_text reads a .md file correctly."""
        from services.document_service import DocumentService
        content = "# Heading\n\nMarkdown content with **bold**."
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md',
                                         delete=False, encoding='utf-8') as f:
            f.write(content)
            tmp_path = f.name
        try:
            result = DocumentService.extract_text(tmp_path, 'md')
            assert result == content
        finally:
            os.unlink(tmp_path)

    def test_extract_text_utf8(self):
        """extract_text handles UTF-8 content including CJK characters."""
        from services.document_service import DocumentService
        content = "你好世界\nThis is a test.\n12345"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt',
                                         delete=False, encoding='utf-8') as f:
            f.write(content)
            tmp_path = f.name
        try:
            result = DocumentService.extract_text(tmp_path, 'txt')
            assert result == content
        finally:
            os.unlink(tmp_path)

    def test_extract_text_empty_file(self):
        """extract_text handles empty files gracefully."""
        from services.document_service import DocumentService
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt',
                                         delete=False, encoding='utf-8') as f:
            tmp_path = f.name
        try:
            result = DocumentService.extract_text(tmp_path, 'txt')
            assert result == ''
        finally:
            os.unlink(tmp_path)

    def test_extract_text_file_not_found(self):
        """extract_text raises when the file does not exist."""
        from services.document_service import DocumentService
        with pytest.raises(Exception):
            DocumentService.extract_text('/nonexistent/path/file.txt', 'txt')

    def test_document_service_upload_dir(self):
        """DocumentService has a default UPLOAD_DIR."""
        from services.document_service import DocumentService
        assert DocumentService.UPLOAD_DIR is not None
        assert isinstance(DocumentService.UPLOAD_DIR, str)

    def test_document_service_singleton(self):
        """document_service global singleton is an instance of DocumentService."""
        from services.document_service import document_service
        from services.document_service import DocumentService
        assert isinstance(document_service, DocumentService)
