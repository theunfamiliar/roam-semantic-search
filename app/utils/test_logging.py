"""Test execution logging utilities."""

import time
from datetime import datetime
from typing import Optional, Dict, Any
from functools import wraps
from app.utils.logging import get_logger

logger = get_logger("test")

class TestLogger:
    """Context manager for test suite logging."""
    
    def __init__(self, suite_name: str):
        self.suite_name = suite_name
        self.start_time = None
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        
    def __enter__(self):
        self.start_time = time.time()
        logger.info(
            f"Starting test suite: {self.suite_name}",
            extra={
                "suite": self.suite_name,
                "timestamp": datetime.now().isoformat()
            }
        )
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        logger.info(
            f"Test suite completed: {self.suite_name}",
            extra={
                "suite": self.suite_name,
                "duration_seconds": duration,
                "tests_run": self.tests_run,
                "tests_passed": self.tests_passed,
                "tests_failed": self.tests_failed,
                "success_rate": (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
            }
        )
        
    def log_test_result(self, test_name: str, passed: bool, error: Optional[Exception] = None) -> None:
        """
        Log individual test result.
        
        Args:
            test_name: Name of the test
            passed: Whether the test passed
            error: Exception if test failed
        """
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            logger.info(
                f"Test passed: {test_name}",
                extra={
                    "suite": self.suite_name,
                    "test": test_name,
                    "result": "pass"
                }
            )
        else:
            self.tests_failed += 1
            logger.error(
                f"Test failed: {test_name}",
                extra={
                    "suite": self.suite_name,
                    "test": test_name,
                    "result": "fail",
                    "error": str(error) if error else None
                }
            )

def log_test(test_name: str):
    """
    Decorator for logging test execution.
    
    Args:
        test_name: Name of the test
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            error = None
            
            try:
                result = func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                error = e
                success = False
                raise
            finally:
                duration = time.time() - start_time
                log_level = logging.INFO if success else logging.ERROR
                logger.log(
                    log_level,
                    f"Test {'passed' if success else 'failed'}: {test_name}",
                    extra={
                        "test": test_name,
                        "duration_seconds": duration,
                        "result": "pass" if success else "fail",
                        "error": str(error) if error else None
                    }
                )
        return wrapper
    return decorator 