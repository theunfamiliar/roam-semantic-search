import pytest
from fastapi import HTTPException
from app.routes.search import search_endpoint
from app.models.api import SearchRequest, SearchResult, SearchResponse

@pytest.mark.unit
class TestSearchRoutes:
    async def test_search_endpoint_success(self, monkeypatch):
        """Test successful search endpoint response."""
        # Create test results
        test_results = [
            SearchResult(
                content="Test content 1",
                score=0.95,
                brain="ideas",
                metadata={"uid": "test-1"}
            ),
            SearchResult(
                content="Test content 2",
                score=0.85,
                brain="ideas",
                metadata={"uid": "test-2"}
            )
        ]
        
        async def mock_search(*args, **kwargs):
            return test_results
        monkeypatch.setattr("app.routes.search.search", mock_search)
        
        request = SearchRequest(query="test", brain="ideas", top_k=5)
        response = await search_endpoint(request, auth=True)
        
        # Verify response is a valid SearchResponse
        assert isinstance(response, SearchResponse)
        assert response.results == test_results
        assert response.count == len(test_results)
        assert response.query == "test"
        
        # Verify each result matches the model
        for result in response.results:
            assert isinstance(result, SearchResult)
            assert isinstance(result.content, str)
            assert isinstance(result.score, float)
            assert result.brain == "ideas"
            assert isinstance(result.metadata, dict)
            assert "uid" in result.metadata

    async def test_search_endpoint_error(self, monkeypatch):
        """Test search endpoint error handling."""
        async def mock_search(*args, **kwargs):
            raise ValueError("Search failed")
        monkeypatch.setattr("app.routes.search.search", mock_search)
        
        request = SearchRequest(query="test", brain="ideas", top_k=5)
        with pytest.raises(HTTPException) as exc:
            await search_endpoint(request, auth=True)
        assert exc.value.status_code == 422
        assert "Search failed" in str(exc.value.detail)

    async def test_search_endpoint_not_found(self, monkeypatch):
        """Test search endpoint file not found error."""
        async def mock_search(*args, **kwargs):
            raise FileNotFoundError("Index not found")
        monkeypatch.setattr("app.routes.search.search", mock_search)
        
        request = SearchRequest(query="test", brain="ideas", top_k=5)
        with pytest.raises(HTTPException) as exc:
            await search_endpoint(request, auth=True)
        assert exc.value.status_code == 404
        assert "Index not found" in str(exc.value.detail) 