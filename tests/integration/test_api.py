import pytest
from httpx import AsyncClient

@pytest.mark.integration
class TestAPIIntegration:
    async def test_health_check(self, async_client: AsyncClient):
        """Test health check endpoint."""
        response = await async_client.get("/")
        assert response.status_code == 200
        assert response.json() == {"status": "running"}

    async def test_ping(self, async_client: AsyncClient):
        """Test ping endpoint."""
        response = await async_client.get("/ping")
        assert response.status_code == 200
        assert response.json() == {"ping": "pong"}

    async def test_search_flow(self, async_client: AsyncClient, auth_headers):
        """Test complete search flow."""
        # First reindex
        reindex_response = await async_client.post(
            "/reindex",
            headers=auth_headers
        )
        assert reindex_response.status_code == 200
        assert reindex_response.json()["status"] == "success"

        # Then search
        search_response = await async_client.post(
            "/search",
            headers=auth_headers,
            json={
                "query": "test query",
                "top_k": 5,
                "brain": "ideas"
            }
        )
        assert search_response.status_code == 200
        data = search_response.json()
        assert "results" in data
        assert "count" in data
        assert "query" in data

    async def test_unauthorized_access(self, async_client: AsyncClient):
        """Test unauthorized access to protected endpoints."""
        endpoints = ["/search", "/reindex"]
        for endpoint in endpoints:
            response = await async_client.post(endpoint)
            assert response.status_code == 401
            assert "Not authenticated" in response.json()["detail"]

    async def test_invalid_search_params(self, async_client: AsyncClient, auth_headers):
        """Test search with invalid parameters."""
        test_cases = [
            {
                "payload": {"query": "", "top_k": 5},
                "expected_status": 422,
                "error_contains": "empty"
            },
            {
                "payload": {"query": "test", "top_k": -1},
                "expected_status": 422,
                "error_contains": "greater than 0"
            },
            {
                "payload": {"query": "test", "brain": "invalid_brain"},
                "expected_status": 500,
                "error_contains": "Missing files"
            }
        ]
        
        for case in test_cases:
            response = await async_client.post(
                "/search",
                headers=auth_headers,
                json=case["payload"]
            )
            assert response.status_code == case["expected_status"]
            assert case["error_contains"] in response.json()["detail"].lower()

    async def test_reindex_without_credentials(self, async_client: AsyncClient, auth_headers):
        """Test reindex endpoint with missing Roam credentials."""
        response = await async_client.post(
            "/reindex",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "401 Unauthorized" in data["error"] 