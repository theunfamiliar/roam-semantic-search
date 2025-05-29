#!/usr/bin/env python3

import os
import time
import json
import logging
import requests
from datetime import datetime
from typing import Dict, Any
from requests.auth import HTTPBasicAuth

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/monitoring/search_health.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "http://localhost:8000"
USERNAME = os.getenv("USERNAME", "admin")
PASSWORD = os.getenv("PASSWORD", "secret")
CHECK_INTERVAL = 300  # 5 minutes
TIMEOUT = 30  # seconds

def check_search_health() -> Dict[str, Any]:
    """
    Check the health of the search endpoint.
    
    Returns:
        Dict containing health metrics
    """
    start_time = time.time()
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "status": "unknown",
        "response_time_ms": 0,
        "error": None
    }
    
    try:
        # Test search endpoint
        response = requests.post(
            f"{BASE_URL}/search",
            json={"query": "test query", "top_k": 1},
            auth=HTTPBasicAuth(USERNAME, PASSWORD),
            timeout=TIMEOUT
        )
        
        # Calculate response time
        metrics["response_time_ms"] = int((time.time() - start_time) * 1000)
        
        # Check response
        response.raise_for_status()
        data = response.json()
        
        if "results" in data and "count" in data:
            metrics["status"] = "healthy"
            metrics["result_count"] = data["count"]
        else:
            metrics["status"] = "degraded"
            metrics["error"] = "Invalid response format"
            
    except requests.exceptions.Timeout:
        metrics.update({
            "status": "error",
            "error": f"Timeout after {TIMEOUT}s"
        })
    except requests.exceptions.RequestException as e:
        metrics.update({
            "status": "error",
            "error": str(e)
        })
    
    return metrics

def log_metrics(metrics: Dict[str, Any]) -> None:
    """Log health check metrics."""
    if metrics["status"] == "healthy":
        logger.info(
            "Search health check passed",
            extra={
                "response_time_ms": metrics["response_time_ms"],
                "result_count": metrics.get("result_count", 0)
            }
        )
    else:
        logger.error(
            "Search health check failed",
            extra={
                "status": metrics["status"],
                "error": metrics["error"],
                "response_time_ms": metrics["response_time_ms"]
            }
        )

def main() -> None:
    """Main monitoring loop."""
    logger.info("Starting search endpoint monitoring")
    
    while True:
        try:
            metrics = check_search_health()
            log_metrics(metrics)
            
            # Write metrics to file for external monitoring
            with open('logs/monitoring/latest_metrics.json', 'w') as f:
                json.dump(metrics, f)
                
        except Exception as e:
            logger.exception("Monitoring iteration failed")
            
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    # Create monitoring directory if it doesn't exist
    os.makedirs('logs/monitoring', exist_ok=True)
    main() 