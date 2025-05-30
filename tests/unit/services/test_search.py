"""Test search service."""

import pytest
import os
from app.services.search import search
from app.models.search import SearchRequest
from app.config import get_filenames

@pytest.mark.unit
class TestSearchService:
    async def test_search_valid_query(self, test_index, test_metadata, monkeypatch):
        """Test search with valid query returns expected results."""
        # Mock file operations
        def mock_get_filenames(brain):
            return {
                "index": test_index,
                "meta": test_metadata
            }
        monkeypatch.setattr("app.services.search.get_filenames", mock_get_filenames)
        monkeypatch.setattr("os.path.exists", lambda x: True)
        
        request = SearchRequest(query="test query", top_k=5)
        results = await search(request)
        assert len(results) > 0
        # Check that results are SearchResult objects with required fields
        for result in results:
            assert result.content is not None
            assert result.score is not None
            assert result.brain is not None

    async def test_search_missing_index(self, monkeypatch):
        """Test search with missing index file."""
        def mock_get_filenames(brain):
            return {
                "index": "/nonexistent/index.faiss",
                "meta": "/nonexistent/meta.json"
            }
        monkeypatch.setattr("app.services.search.get_filenames", mock_get_filenames)
        monkeypatch.setattr("os.path.exists", lambda x: False)  # All files are missing
        
        request = SearchRequest(query="test query", top_k=5)
        with pytest.raises(FileNotFoundError) as exc:
            await search(request)
        assert "Missing files" in str(exc.value)

    async def test_search_empty_query(self):
        """Test search with empty query."""
        request = SearchRequest(query="   ", top_k=5)
        with pytest.raises(ValueError) as exc:
            await search(request)
        assert "empty" in str(exc.value)

    async def test_search_faiss_error(self, test_index, test_metadata, monkeypatch):
        """Test search with FAISS error."""
        def mock_get_filenames(brain):
            return {
                "index": test_index,
                "meta": test_metadata
            }
        monkeypatch.setattr("app.services.search.get_filenames", mock_get_filenames)
        monkeypatch.setattr("os.path.exists", lambda x: True)
        
        def mock_read_index(*args):
            raise RuntimeError("FAISS error")
        monkeypatch.setattr("faiss.read_index", mock_read_index)
        
        request = SearchRequest(query="test query", top_k=5)
        with pytest.raises(Exception) as exc:
            await search(request)
        assert "FAISS error" in str(exc.value) 