"""Code coverage logging utilities."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from app.utils.logging import get_logger

logger = get_logger("coverage")

class CoverageLogger:
    """Handles logging of code coverage metrics."""
    
    def __init__(self, coverage_dir: str = "logs/coverage"):
        self.coverage_dir = Path(coverage_dir)
        self.coverage_dir.mkdir(parents=True, exist_ok=True)
        
    def log_coverage(
        self,
        coverage_data: Dict[str, Any],
        report_type: str = "pytest",
        commit_hash: Optional[str] = None
    ) -> None:
        """
        Log code coverage data.
        
        Args:
            coverage_data: Coverage metrics
            report_type: Type of coverage report (e.g., 'pytest', 'coverage.py')
            commit_hash: Git commit hash for reference
        """
        timestamp = datetime.now()
        
        # Create coverage summary
        summary = {
            "timestamp": timestamp.isoformat(),
            "report_type": report_type,
            "commit_hash": commit_hash,
            "total_lines": coverage_data.get("total_lines", 0),
            "covered_lines": coverage_data.get("covered_lines", 0),
            "coverage_percent": coverage_data.get("coverage_percent", 0.0),
            "uncovered_files": coverage_data.get("uncovered_files", []),
            "branch_coverage": coverage_data.get("branch_coverage", None),
            "missed_branches": coverage_data.get("missed_branches", [])
        }
        
        # Log summary
        logger.info(
            f"Code coverage report generated",
            extra={
                "coverage_percent": summary["coverage_percent"],
                "total_lines": summary["total_lines"],
                "report_type": report_type,
                "commit_hash": commit_hash
            }
        )
        
        # Save detailed report
        report_file = self.coverage_dir / f"coverage_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w") as f:
            json.dump(summary, f, indent=2)
            
    def get_coverage_trend(self, days: int = 30) -> Dict[str, Any]:
        """
        Get coverage trends over time.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary containing coverage trends
        """
        reports = []
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        # Collect reports within time window
        for report_file in self.coverage_dir.glob("coverage_*.json"):
            if report_file.stat().st_mtime >= cutoff:
                with open(report_file) as f:
                    reports.append(json.load(f))
                    
        if not reports:
            return {"error": "No coverage data available"}
            
        # Calculate trends
        reports.sort(key=lambda x: x["timestamp"])
        return {
            "start_date": reports[0]["timestamp"],
            "end_date": reports[-1]["timestamp"],
            "reports_analyzed": len(reports),
            "coverage_trend": [
                {
                    "timestamp": r["timestamp"],
                    "coverage": r["coverage_percent"]
                }
                for r in reports
            ],
            "average_coverage": sum(r["coverage_percent"] for r in reports) / len(reports),
            "trend_direction": "up" if reports[-1]["coverage_percent"] > reports[0]["coverage_percent"]
                             else "down" if reports[-1]["coverage_percent"] < reports[0]["coverage_percent"]
                             else "stable"
        } 