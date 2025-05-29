import pytest
from fastapi import HTTPException
from app.routes.search import search_endpoint
from app.models.schemas import SearchRequest

@pytest.mark.unit
class TestSearchRoutes:
    async def test_search_endpoint_success(self, search_results, monkeypatch):
        """Test successful search endpoint response."""
        async def mock_search(*args, **kwargs):
            return search_results
        monkeypatch.setattr("app.routes.search.search", mock_search)
        
        request = SearchRequest(query="test", top_k=5)
        response = await search_endpoint(request, auth=True)
        
        assert response.results == search_results
        assert response.count == len(search_results)
        assert response.query == "test"

    async def test_search_endpoint_error(self, monkeypatch):
        """Test search endpoint error handling."""
        async def mock_search(*args, **kwargs):
            raise ValueError("Search failed")
        monkeypatch.setattr("app.routes.search.search", mock_search)
        
        request = SearchRequest(query="test", top_k=5)
        with pytest.raises(HTTPException) as exc:
            await search_endpoint(request, auth=True)
        assert exc.value.status_code == 500
        assert "Search failed" in str(exc.value.detail) 