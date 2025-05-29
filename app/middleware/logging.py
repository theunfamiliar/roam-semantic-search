"""Centralized logging middleware."""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging
from app.utils.logging import get_logger

logger = get_logger("http")

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for centralized request/response logging."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process a request and log relevant information."""
        start_time = time.time()
        
        # Extract request details
        request_id = request.headers.get("X-Request-ID", "")
        user_agent = request.headers.get("User-Agent", "")
        
        # Log request
        logger.info(
            f"Incoming {request.method} {request.url.path}",
            extra={
                "event_type": "request_start",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_host": request.client.host if request.client else None,
                "user_agent": user_agent
            }
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log successful response
            logger.info(
                f"Completed {request.method} {request.url.path}",
                extra={
                    "event_type": "request_complete",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_seconds": duration
                }
            )
            
            return response
            
        except Exception as e:
            # Calculate duration for failed requests
            duration = time.time() - start_time
            
            # Log error
            logger.error(
                f"Error processing {request.method} {request.url.path}",
                extra={
                    "event_type": "request_error",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "duration_seconds": duration
                },
                exc_info=True
            )
            raise 