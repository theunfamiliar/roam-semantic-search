import pytest
from app.services.search import search
from app.models.schemas import SearchRequest
import os

@pytest.mark.unit
class TestSearchService:
    async def test_search_valid_query(self, test_index, test_metadata, monkeypatch):
        """Test search with valid query returns expected results."""
        # Mock file operations
        def mock_exists(path): return True
        monkeypatch.setattr(os.path, "exists", mock_exists)
        
        request = SearchRequest(query="test query", top_k=5)
        results = await search(request)
        
        assert len(results) <= 5
        assert all(hasattr(r, 'text') for r in results)
        assert all(hasattr(r, 'ref') for r in results)

    async def test_search_missing_index(self, monkeypatch):
        """Test search with missing index files raises error."""
        def mock_exists(path): return False
        monkeypatch.setattr(os.path, "exists", mock_exists)
        
        request = SearchRequest(query="test", top_k=1)
        with pytest.raises(FileNotFoundError) as exc:
            await search(request)
        assert "Missing files" in str(exc.value)

    async def test_search_empty_query(self):
        """Test search with empty query."""
        request = SearchRequest(query="   ", top_k=1)
        with pytest.raises(ValueError) as exc:
            await search(request)
        assert "Search query cannot be empty" in str(exc.value)

    async def test_search_faiss_error(self, monkeypatch):
        """Test handling of FAISS errors."""
        def mock_exists(path): return True
        monkeypatch.setattr(os.path, "exists", mock_exists)
        
        def mock_read_index(path):
            raise RuntimeError("FAISS error")
        monkeypatch.setattr("faiss.read_index", mock_read_index)
        
        request = SearchRequest(query="test", top_k=1)
        with pytest.raises(Exception) as exc:
            await search(request)
        assert "Search failed" in str(exc.value)
        assert "FAISS error" in str(exc.value) 