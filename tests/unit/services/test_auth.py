import pytest
from fastapi import HTTPException
from fastapi.security import HTTPBasicCredentials
from app.services.auth import authenticate

@pytest.mark.unit
class TestAuthService:
    async def test_valid_credentials(self):
        """Test authentication with valid credentials."""
        credentials = HTTPBasicCredentials(
            username="admin",
            password="secret"
        )
        result = await authenticate(credentials)
        assert result is True

    async def test_invalid_username(self):
        """Test authentication with invalid username."""
        credentials = HTTPBasicCredentials(
            username="wrong",
            password="secret"
        )
        with pytest.raises(HTTPException) as exc:
            await authenticate(credentials)
        assert exc.value.status_code == 401

    async def test_invalid_password(self):
        """Test authentication with invalid password."""
        credentials = HTTPBasicCredentials(
            username="admin",
            password="wrong"
        )
        with pytest.raises(HTTPException) as exc:
            await authenticate(credentials)
        assert exc.value.status_code == 401 