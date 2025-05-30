"""Test search service."""

import pytest
import os
import numpy as np
from app.services.search import search, normalize_score
from app.models.api import SearchRequest, SearchResult, SearchResponse
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
        
        request = SearchRequest(query="test query", brain="ideas", top_k=5)
        results = await search(request)
        
        assert len(results) > 0
        # Check that results are SearchResult objects with required fields
        for result in results:
            assert isinstance(result, SearchResult)
            assert isinstance(result.content, str)
            assert isinstance(result.score, float)
            assert 0 <= result.score <= 1  # Score should be normalized
            assert result.brain == "ideas"
            assert isinstance(result.metadata, dict)
            assert "uid" in result.metadata

    async def test_search_result_model_consistency(self, test_index, test_metadata, monkeypatch):
        """Test that search results match the API SearchResult model exactly."""
        def mock_get_filenames(brain):
            return {
                "index": test_index,
                "meta": test_metadata
            }
        monkeypatch.setattr("app.services.search.get_filenames", mock_get_filenames)
        monkeypatch.setattr("os.path.exists", lambda x: True)
        
        # Create test metadata
        test_content = "Test content"
        test_uid = "test-uid-123"
        monkeypatch.setattr("json.load", lambda f: [{
            "content": test_content,
            "uid": test_uid
        }])
        
        # Mock FAISS index and search
        class MockIndex:
            def search(self, *args):
                return np.array([[100.0]]), np.array([[0]])
        monkeypatch.setattr("faiss.read_index", lambda x: MockIndex())
        
        request = SearchRequest(query="test", brain="ideas", top_k=1)
        results = await search(request)
        
        assert len(results) == 1
        result = results[0]
        
        # Verify exact model structure
        assert isinstance(result, SearchResult)
        assert result.content == test_content
        assert result.score == 0.5  # 1/(1 + 100/100) = 0.5
        assert result.brain == "ideas"
        assert result.metadata == {"uid": test_uid}
        
        # Verify no extra attributes
        assert set(result.dict().keys()) == {"content", "score", "brain", "metadata"}

    async def test_search_missing_index(self, monkeypatch):
        """Test search with missing index file."""
        def mock_get_filenames(brain):
            return {
                "index": "/nonexistent/index.faiss",
                "meta": "/nonexistent/meta.json"
            }
        monkeypatch.setattr("app.services.search.get_filenames", mock_get_filenames)
        monkeypatch.setattr("os.path.exists", lambda x: False)  # All files are missing
        
        request = SearchRequest(query="test query", brain="ideas", top_k=5)
        with pytest.raises(FileNotFoundError) as exc:
            await search(request)
        assert "Missing files" in str(exc.value)

    async def test_search_empty_query(self):
        """Test search with empty query."""
        request = SearchRequest(query="   ", brain="ideas", top_k=5)
        with pytest.raises(ValueError) as exc:
            await search(request)
        assert "Search query cannot be empty" in str(exc.value)

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
        
        request = SearchRequest(query="test query", brain="ideas", top_k=5)
        with pytest.raises(Exception) as exc:
            await search(request)
        assert "Search failed" in str(exc.value)

    def test_normalize_score(self):
        """Test score normalization function."""
        assert normalize_score(0) == 1.0  # Perfect match
        assert normalize_score(100) == 0.5  # Medium match
        assert normalize_score(1000) < 0.1  # Poor match
        assert 0 <= normalize_score(float("inf")) <= 1  # Always bounded 