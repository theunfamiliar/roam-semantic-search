"""Performance metrics aggregation and analysis."""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

class MetricsAggregator:
    """Aggregates and analyzes performance metrics from logs."""
    
    def __init__(self, perf_log_path: str = "logs/performance/perf.log"):
        self.perf_log_path = Path(perf_log_path)
        self.cache_duration = timedelta(minutes=5)
        self._cache = {}
        self._last_cache_update = None
    
    def _should_refresh_cache(self) -> bool:
        """Determine if the cache needs refreshing."""
        if self._last_cache_update is None:
            return True
        return datetime.now() - self._last_cache_update > self.cache_duration
    
    def _parse_log_line(self, line: str) -> Optional[Dict]:
        """Parse a single log line into a metric entry."""
        try:
            data = json.loads(line)
            # Ensure required fields exist
            if all(k in data for k in ['timestamp', 'operation', 'duration_seconds']):
                return {
                    'timestamp': datetime.strptime(data['timestamp'], '%Y-%m-%d %H:%M:%S'),
                    'operation': data['operation'],
                    'duration': float(data['duration_seconds']),
                    'success': data.get('success', True)
                }
        except (json.JSONDecodeError, ValueError, KeyError):
            return None
        return None

    def get_metrics(self, time_window: timedelta = timedelta(hours=1)) -> Dict:
        """
        Get aggregated metrics for the specified time window.
        
        Args:
            time_window: Time window to analyze
            
        Returns:
            Dict containing aggregated metrics
        """
        if self._should_refresh_cache():
            self._refresh_metrics()
        
        cutoff_time = datetime.now() - time_window
        recent_metrics = [
            m for m in self._cache.get('raw_metrics', [])
            if m['timestamp'] > cutoff_time
        ]
        
        # Initialize aggregation structures
        operations = defaultdict(lambda: {
            'count': 0,
            'success_count': 0,
            'total_duration': 0.0,
            'min_duration': float('inf'),
            'max_duration': 0.0
        })
        
        # Aggregate metrics
        for metric in recent_metrics:
            op = metric['operation']
            duration = metric['duration']
            
            operations[op]['count'] += 1
            if metric['success']:
                operations[op]['success_count'] += 1
            operations[op]['total_duration'] += duration
            operations[op]['min_duration'] = min(operations[op]['min_duration'], duration)
            operations[op]['max_duration'] = max(operations[op]['max_duration'], duration)
        
        # Calculate averages and success rates
        results = {}
        for op, stats in operations.items():
            if stats['count'] > 0:
                results[op] = {
                    'total_requests': stats['count'],
                    'success_rate': (stats['success_count'] / stats['count']) * 100,
                    'avg_duration': stats['total_duration'] / stats['count'],
                    'min_duration': stats['min_duration'],
                    'max_duration': stats['max_duration']
                }
        
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'time_window_hours': time_window.total_seconds() / 3600,
            'operations': results
        }
    
    def _refresh_metrics(self) -> None:
        """Refresh the metrics cache from log files."""
        raw_metrics = []
        
        if self.perf_log_path.exists():
            with open(self.perf_log_path, 'r') as f:
                for line in f:
                    metric = self._parse_log_line(line.strip())
                    if metric:
                        raw_metrics.append(metric)
        
        self._cache = {
            'raw_metrics': raw_metrics
        }
        self._last_cache_update = datetime.now()

def get_metrics_aggregator() -> MetricsAggregator:
    """Get or create a MetricsAggregator instance."""
    if not hasattr(get_metrics_aggregator, '_instance'):
        get_metrics_aggregator._instance = MetricsAggregator()
    return get_metrics_aggregator._instance 