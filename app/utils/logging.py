"""Centralized logging configuration and utilities."""

import logging
import logging.config
import yaml
from pathlib import Path
from functools import lru_cache
from typing import Optional, Dict, Any

@lru_cache()
def load_logging_config() -> Dict[str, Any]:
    """Load logging configuration from YAML file."""
    config_path = Path(__file__).parent.parent.parent / "config" / "logging.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    return config

def setup_logging():
    """Initialize logging configuration."""
    config = load_logging_config()
    logging.config.dictConfig(config)

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name.
    
    Args:
        name: The name of the logger to retrieve.
        
    Returns:
        A configured logger instance.
    """
    return logging.getLogger(f"app.{name}")

class LoggerMixin:
    """Mixin to add logging capabilities to any class."""
    
    @property
    def logger(self) -> logging.Logger:
        """Get a logger for the current class."""
        if not hasattr(self, "_logger"):
            self._logger = get_logger(self.__class__.__name__.lower())
        return self._logger

def log_error(logger: logging.Logger, error: Exception, context: Optional[Dict] = None):
    """Centralized error logging function.
    
    Args:
        logger: The logger instance to use
        error: The exception to log
        context: Optional dictionary of additional context
    """
    extra = {
        "error_type": error.__class__.__name__,
        "error_message": str(error),
        **(context or {})
    }
    logger.error(f"Error occurred: {error}", extra=extra, exc_info=True)

def log_performance(logger: logging.Logger, operation: str, duration: float, context: Optional[Dict] = None):
    """Log performance metrics.
    
    Args:
        logger: The logger instance to use
        operation: Name of the operation being measured
        duration: Duration in seconds
        context: Optional dictionary of additional context
    """
    extra = {
        "operation": operation,
        "duration_seconds": duration,
        **(context or {})
    }
    logger.info(f"Performance metric: {operation}", extra=extra)

# Performance logging context manager
class PerfLogger:
    """Context manager for performance logging."""
    
    def __init__(self, operation: str):
        self.operation = operation
        self.logger = get_logger("perf")
        
    def __enter__(self):
        self.start_time = logging.Formatter.converter()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = logging.Formatter.converter() - self.start_time
        self.logger.info(
            "Performance measurement",
            extra={
                "operation": self.operation,
                "duration_seconds": duration,
                "success": exc_type is None
            }
        )

# Audit logging function
def audit_log(
    event: str,
    user: str,
    action: str,
    resource: str,
    status: str,
    details: Optional[dict] = None
) -> None:
    """
    Log an audit event.
    
    Args:
        event: Type of event (e.g., "access", "modify", "delete")
        user: User performing the action
        action: Specific action taken
        resource: Resource being acted upon
        status: Outcome status
        details: Additional details to log
    """
    logger = get_logger("audit")
    logger.info(
        f"{event}: {action} on {resource}",
        extra={
            "event_type": event,
            "user": user,
            "action": action,
            "resource": resource,
            "status": status,
            **(details or {})
        }
    ) 