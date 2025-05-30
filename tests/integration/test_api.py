"""Test API endpoints."""

import pytest
from httpx import AsyncClient

@pytest.mark.integration
class TestAPIIntegration:
    @pytest.mark.timeout(5)
    async def test_health_check(self, async_client: AsyncClient):
        """Test health check endpoint."""
        response = await async_client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    @pytest.mark.timeout(5)
    async def test_ping(self, async_client: AsyncClient):
        """Test ping endpoint."""
        response = await async_client.get("/api/health/ping")
        assert response.status_code == 200
        assert response.json()["message"] == "pong"

    @pytest.mark.timeout(45)  # Search flow includes reindexing
    async def test_search_flow(self, async_client: AsyncClient, auth_headers):
        """Test complete search flow."""
        # First reindex both brains
        for brain in ["ideas", "marketing"]:
            reindex_response = await async_client.post(
                "/api/reindex",
                headers=auth_headers,
                json={"brain": brain}
            )
            assert reindex_response.status_code == 200
            assert reindex_response.json()["status"] == "success"

        # Then search in both brains
        for brain in ["ideas", "marketing"]:
            search_response = await async_client.post(
                "/api/search",
                headers=auth_headers,
                json={
                    "query": "test query",
                    "top_k": 5,
                    "brain": brain
                }
            )
            assert search_response.status_code == 200
            results = search_response.json()
            assert isinstance(results["results"], list)
            assert len(results["results"]) <= 5
            assert results["count"] == len(results["results"])
            assert results["query"] == "test query"

    @pytest.mark.timeout(10)
    async def test_unauthorized_access(self, async_client: AsyncClient):
        """Test unauthorized access to protected endpoints."""
        endpoints = ["/api/search", "/api/reindex"]
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
                "error_contains": "string should have at least 1 character"
            },
            {
                "payload": {"query": "test", "top_k": -1},
                "expected_status": 422,
                "error_contains": "greater than 0"
            },
            {
                "payload": {"query": "test", "brain": "invalid_brain"},
                "expected_status": 422,  # Brain validation happens at request level
                "error_contains": "input should be 'ideas' or 'marketing'"
            }
        ]

        for case in test_cases:
            response = await async_client.post(
                "/api/search",
                headers=auth_headers,
                json=case["payload"]
            )
            assert response.status_code == case["expected_status"]
            error_detail = str(response.json()["detail"]).lower()
            assert case["error_contains"].lower() in error_detail

    @pytest.mark.timeout(30)
    async def test_reindex_without_credentials(self, async_client: AsyncClient, auth_headers):
        """Test reindex endpoint with missing Roam credentials."""
        response = await async_client.post(
            "/api/reindex",
            headers=auth_headers,
            json={"brain": "marketing"}  # Test with marketing brain
        )
        assert response.status_code == 200
        assert response.json()["status"] == "success"

    @pytest.mark.timeout(30)
    async def test_single_brain_search(self, async_client: AsyncClient, auth_headers):
        """Test searching in a single brain."""
        # First reindex marketing brain
        reindex_response = await async_client.post(
            "/api/reindex",
            headers=auth_headers,
            json={"brain": "marketing"}
        )
        assert reindex_response.status_code == 200
        assert reindex_response.json()["status"] == "success"

        # Search only in marketing brain
        search_response = await async_client.post(
            "/api/search",
            headers=auth_headers,
            json={
                "query": "test query",
                "top_k": 5,
                "brain": "marketing"  # Explicitly only search marketing brain
            }
        )
        assert search_response.status_code == 200
        results = search_response.json()
        assert isinstance(results["results"], list)
        assert len(results["results"]) <= 5
        assert results["count"] == len(results["results"])
        assert results["query"] == "test query"
        
        # Verify results only come from marketing brain
        for result in results["results"]:
            assert "brain" in result
            assert result["brain"] == "marketing"

    @pytest.mark.timeout(30)
    async def test_brain_isolation(self, async_client: AsyncClient, auth_headers):
        """Test that brains are properly isolated and content is not leaked between them."""
        # First reindex both brains
        for brain in ["ideas", "marketing"]:
            reindex_response = await async_client.post(
                "/api/reindex",
                headers=auth_headers,
                json={"brain": brain}
            )
            assert reindex_response.status_code == 200
            assert reindex_response.json()["status"] == "success"

        # Search in marketing brain
        marketing_response = await async_client.post(
            "/api/search",
            headers=auth_headers,
            json={
                "query": "test query",
                "top_k": 10,  # Larger number to increase chance of catching leaks
                "brain": "marketing"
            }
        )
        assert marketing_response.status_code == 200
        marketing_results = marketing_response.json()
        
        # Verify no ideas content in marketing results
        for result in marketing_results["results"]:
            assert "brain" in result, "Each result must specify its source brain"
            assert result["brain"] == "marketing", "Marketing results must only come from marketing brain"
            assert "TOC - ideas" not in result["content"], "Marketing results must not contain ideas content"

        # Search in ideas brain
        ideas_response = await async_client.post(
            "/api/search",
            headers=auth_headers,
            json={
                "query": "test query",
                "top_k": 10,
                "brain": "ideas"
            }
        )
        assert ideas_response.status_code == 200
        ideas_results = ideas_response.json()
        
        # Verify no marketing content in ideas results
        for result in ideas_results["results"]:
            assert "brain" in result, "Each result must specify its source brain"
            assert result["brain"] == "ideas", "Ideas results must only come from ideas brain"
            assert "TOC - marketing" not in result["content"], "Ideas results must not contain marketing content"

    @pytest.mark.timeout(10)
    async def test_brain_access_control(self, async_client: AsyncClient, auth_headers):
        """Test that brain access can be controlled independently."""
        # Test basic access control
        test_cases = [
            {
                "brain": "ideas",
                "expected_status": 200,  # Admin token should have access
            },
            {
                "brain": "marketing",
                "expected_status": 200,  # Admin token should have access
            },
            {
                "brain": "invalid",
                "expected_status": 422,  # Invalid brain should be rejected at validation
                "error_contains": "input should be 'ideas' or 'marketing'"
            }
        ]

        for case in test_cases:
            response = await async_client.post(
                "/api/search",
                headers=auth_headers,
                json={
                    "query": "test",
                    "brain": case["brain"]
                }
            )
            assert response.status_code == case["expected_status"], f"Unexpected status for brain: {case['brain']}"
            if case.get("error_contains"):
                error_detail = str(response.json()["detail"]).lower()
                assert case["error_contains"].lower() in error_detail 