"""Test authentication service."""

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from app.services.auth import authenticate

@pytest.mark.unit
class TestAuthService:
    async def test_valid_credentials(self):
        """Test authentication with valid token."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="test-token"
        )
        result = await authenticate(credentials)
        assert result is True

    async def test_invalid_token(self):
        """Test authentication with invalid token."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="wrong-token"
        )
        with pytest.raises(HTTPException) as exc:
            await authenticate(credentials)
        assert exc.value.status_code == 401
        assert exc.value.detail == "Unauthorized"
        assert exc.value.headers["WWW-Authenticate"] == "Bearer"

    async def test_invalid_scheme(self):
        """Test authentication with invalid scheme."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Basic",
            credentials="test-token"
        )
        with pytest.raises(HTTPException) as exc:
            await authenticate(credentials)
        assert exc.value.status_code == 401
        assert exc.value.detail == "Bearer authentication required" 