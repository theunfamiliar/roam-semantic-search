"""Integration tests for security features."""

import pytest
from httpx import AsyncClient
from typing import Dict
import logging
from pathlib import Path
import asyncio

@pytest.fixture
async def admin_token(async_client: AsyncClient) -> str:
    """Fixture to get an admin token."""
    # In a real implementation, this would call an admin token generation endpoint
    return "admin-test-token"

@pytest.fixture
async def marketing_token(async_client: AsyncClient) -> str:
    """Fixture to get a marketing-only token."""
    # In a real implementation, this would call a restricted token generation endpoint
    return "marketing-test-token"

@pytest.fixture
def admin_headers(admin_token: str) -> Dict[str, str]:
    """Get headers with admin token."""
    return {"Authorization": f"Bearer {admin_token}"}

@pytest.fixture
def marketing_headers(marketing_token: str) -> Dict[str, str]:
    """Get headers with marketing token."""
    return {"Authorization": f"Bearer {marketing_token}"}

@pytest.fixture
def audit_log_path(tmp_path: Path) -> Path:
    """Get path for audit log file."""
    log_path = tmp_path / "audit.log"
    handler = logging.FileHandler(str(log_path))
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    audit_logger = logging.getLogger("audit")
    audit_logger.addHandler(handler)
    yield log_path
    audit_logger.removeHandler(handler)

@pytest.mark.integration
class TestSecurityIntegration:
    """Test suite for security-related features."""

    @pytest.mark.timeout(30)
    async def test_token_validation(self, async_client: AsyncClient):
        """Test token validation."""
        # Test invalid token
        response = await async_client.post(
            "/api/search",
            headers={"Authorization": "Bearer invalid"},
            json={"query": "test", "brain": "ideas"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Unauthorized"

        # Test missing token
        response = await async_client.post(
            "/api/search",
            json={"query": "test", "brain": "ideas"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

        # Test invalid scheme
        response = await async_client.post(
            "/api/search",
            headers={"Authorization": "Basic invalid"},
            json={"query": "test", "brain": "ideas"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Bearer authentication required"

    @pytest.mark.timeout(30)
    async def test_admin_access(self, async_client: AsyncClient, admin_headers: Dict[str, str]):
        """Test admin access to all brains."""
        # Test access to ideas brain
        response = await async_client.post(
            "/api/search",
            headers=admin_headers,
            json={"query": "test", "brain": "ideas"}
        )
        assert response.status_code == 200

        # Test access to marketing brain
        response = await async_client.post(
            "/api/search",
            headers=admin_headers,
            json={"query": "test", "brain": "marketing"}
        )
        assert response.status_code == 200

    @pytest.mark.timeout(30)
    async def test_marketing_token_restrictions(
        self,
        async_client: AsyncClient,
        marketing_headers: Dict[str, str]
    ):
        """Test marketing token restrictions."""
        # Test access to marketing brain (allowed)
        response = await async_client.post(
            "/api/search",
            headers=marketing_headers,
            json={"query": "test", "brain": "marketing"}
        )
        assert response.status_code == 200

        # Test access to ideas brain (forbidden)
        response = await async_client.post(
            "/api/search",
            headers=marketing_headers,
            json={"query": "test", "brain": "ideas"}
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "Access denied to brain: ideas"

    @pytest.mark.timeout(30)
    async def test_audit_logging(
        self,
        async_client: AsyncClient,
        marketing_headers: Dict[str, str],
        audit_log_path: Path
    ):
        """Test audit logging for third-party access."""
        # Make a request that should be logged
        response = await async_client.post(
            "/api/search",
            headers=marketing_headers,
            json={"query": "test", "brain": "marketing"}
        )
        assert response.status_code == 200

        # Verify audit log contains the request
        assert audit_log_path.exists()
        log_content = audit_log_path.read_text()
        assert "marketing-test-token" in log_content
        assert "'brain': 'marketing'" in log_content 