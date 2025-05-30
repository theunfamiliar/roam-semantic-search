"""Security service for token validation and access control."""

import time
from typing import Dict, Optional, Set
from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import secrets
import os
import logging
from datetime import datetime, timedelta

# Configure audit logging
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)
audit_handler = logging.FileHandler("audit.log")
audit_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
)
audit_logger.addHandler(audit_handler)

class SecurityService:
    """Service for handling security-related functionality."""
    
    def __init__(self):
        self.admin_tokens: Set[str] = {os.getenv("ADMIN_TOKEN", "admin-test-token")}
        self.marketing_tokens: Set[str] = {os.getenv("MARKETING_TOKEN", "marketing-test-token")}
        self.security = HTTPBearer(auto_error=False)
    
    async def validate_token(
        self, 
        credentials: Optional[HTTPAuthorizationCredentials],
        request: Request
    ) -> str:
        """
        Validate the authentication token.
        
        Args:
            credentials: The authorization credentials
            request: The FastAPI request object
            
        Returns:
            str: The validated token
            
        Raises:
            HTTPException: If authentication fails
        """
        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(
                status_code=401,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check authentication scheme
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail="Bearer authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = parts[1]
        
        # Validate token
        if token not in self.admin_tokens and token not in self.marketing_tokens:
            raise HTTPException(
                status_code=401,
                detail="Unauthorized",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Audit log the request
        await self._audit_log(token, request)
        
        return token
    
    def validate_brain_access(self, token: str, brain: str):
        """
        Validate access to a specific brain.
        
        Args:
            token: The authentication token
            brain: The brain to access
            
        Raises:
            HTTPException: If access is denied
        """
        if token in self.marketing_tokens and brain != "marketing":
            raise HTTPException(
                status_code=403,
                detail=f"Access denied to brain: {brain}"
            )
    
    async def _audit_log(self, token: str, request: Request):
        """Log request details for audit purposes."""
        # Get request body if available
        body = {}
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.json()
            except:
                pass  # Body might not be JSON

        audit_logger.info(
            f"Request - Token: {token}, "
            f"Method: {request.method}, "
            f"Endpoint: {request.url.path}, "
            f"Query Params: {dict(request.query_params)}, "
            f"Body: {body}, "
            f"Client: {request.client.host if request.client else 'unknown'}"
        ) 