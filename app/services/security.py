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

# Add debug logging
debug_logger = logging.getLogger("debug")
debug_logger.setLevel(logging.DEBUG)
debug_handler = logging.StreamHandler()
debug_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
)
debug_logger.addHandler(debug_handler)

class SecurityService:
    """Service for handling security-related functionality."""
    
    def __init__(self):
        self.admin_tokens: Set[str] = {os.getenv("ADMIN_TOKEN", "admin-test-token")}
        self.marketing_tokens: Set[str] = {os.getenv("MARKETING_TOKEN", "marketing-test-token")}
        self.security = HTTPBearer(auto_error=False)
        debug_logger.debug(f"Initialized SecurityService with admin tokens: {self.admin_tokens}")
    
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
        debug_logger.debug(f"Received Authorization header: {auth_header}")
        
        if not auth_header:
            debug_logger.debug("No Authorization header found")
            raise HTTPException(
                status_code=401,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check authentication scheme
        parts = auth_header.split()
        debug_logger.debug(f"Auth header parts: {parts}")
        
        if len(parts) != 2 or parts[0].lower() != "bearer":
            debug_logger.debug(f"Invalid auth scheme: {parts[0] if parts else 'no parts'}")
            raise HTTPException(
                status_code=401,
                detail="Bearer authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = parts[1]
        debug_logger.debug(f"Extracted token: {token}")
        debug_logger.debug(f"Admin tokens: {self.admin_tokens}")
        debug_logger.debug(f"Marketing tokens: {self.marketing_tokens}")
        
        # Validate token
        if token not in self.admin_tokens and token not in self.marketing_tokens:
            debug_logger.debug(f"Token not found in any token set")
            raise HTTPException(
                status_code=401,
                detail="Unauthorized",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        debug_logger.debug(f"Token validated successfully")
        
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
        debug_logger.debug(f"Validating brain access - token: {token}, brain: {brain}")
        if token in self.marketing_tokens and brain != "marketing":
            debug_logger.debug(f"Access denied to brain {brain} for marketing token")
            raise HTTPException(
                status_code=403,
                detail=f"Access denied to brain: {brain}"
            )
        debug_logger.debug(f"Brain access validated successfully")
    
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