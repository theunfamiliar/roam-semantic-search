"""Authentication service."""

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import secrets
import os
from typing import Optional

security = HTTPBearer(auto_error=False)  # Don't auto-raise 403, we'll handle it

async def authenticate(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> bool:
    """
    Authenticate user with bearer token.
    
    Args:
        credentials: The authorization credentials
        
    Returns:
        bool: True if authentication successful
        
    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Bearer authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    correct_token = os.getenv("ADMIN_TOKEN", "admin-test-token")
    
    is_token_correct = secrets.compare_digest(
        credentials.credentials.encode("utf8"),
        correct_token.encode("utf8")
    )
    
    if not is_token_correct:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return True 