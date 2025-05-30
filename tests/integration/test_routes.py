"""Test route configurations."""

import pytest
from httpx import AsyncClient

@pytest.mark.integration
class TestRouteConfiguration:
    """Test suite for verifying route configurations."""

    @pytest.mark.timeout(5)
    async def test_root_endpoints(self, async_client: AsyncClient):
        """Test root level endpoints."""
        # Test root health check
        response = await async_client.get("/")
        assert response.status_code == 200
        assert response.json() == {"status": "running"}

        # Test root ping
        response = await async_client.get("/ping")
        assert response.status_code == 200
        assert response.json() == {"ping": "pong"}

    @pytest.mark.timeout(5)
    async def test_api_v1_endpoints(self, async_client: AsyncClient):
        """Test API v1 endpoints are correctly mounted."""
        # Test health endpoints
        response = await async_client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

        response = await async_client.get("/api/v1/ping")
        assert response.status_code == 200
        assert response.json() == {"message": "pong"}

        # Test search endpoint (should return 401 without auth)
        response = await async_client.post("/api/v1/search", json={"query": "test"})
        assert response.status_code == 401

        # Test reindex endpoint (should return 401 without auth)
        response = await async_client.post("/api/v1/reindex")
        assert response.status_code == 401

    @pytest.mark.timeout(5)
    async def test_invalid_paths(self, async_client: AsyncClient):
        """Test invalid paths return 404."""
        invalid_paths = [
            "/api",
            "/api/v1",
            "/api/v2",
            "/health",
            "/api/v1/invalid",
            "/api/search",  # Should be /api/v1/search
            "/api/reindex",  # Should be /api/v1/reindex
        ]

        for path in invalid_paths:
            response = await async_client.get(path)
            assert response.status_code == 404, f"Path {path} should return 404"

    @pytest.mark.timeout(5)
    async def test_method_not_allowed(self, async_client: AsyncClient):
        """Test endpoints reject incorrect HTTP methods."""
        test_cases = [
            # (path, method, expected_status)
            ("/api/v1/health", "post", 405),
            ("/api/v1/ping", "post", 405),
            ("/api/v1/search", "get", 405),
            ("/api/v1/reindex", "get", 405),
            ("/", "post", 405),
            ("/ping", "post", 405),
        ]

        for path, method, expected_status in test_cases:
            response = await getattr(async_client, method)(path)
            assert response.status_code == expected_status, \
                f"{method.upper()} {path} should return {expected_status}" 