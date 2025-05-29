"""Utilities for handling Roam data exports."""

import os
import json
import gzip
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

def get_export_filepath(brain: str, data_dir: str) -> Path:
    """
    Generate a versioned filepath for Roam data export.
    
    Args:
        brain: Brain identifier (e.g., "ideas", "work")
        data_dir: Base directory for data storage
        
    Returns:
        Path object for the export file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path(data_dir) / f"roam_export_{brain}_{timestamp}.json.gz"

def cleanup_old_exports(data_dir: str, keep_days: int = 7) -> None:
    """
    Remove export files older than specified days.
    
    Args:
        data_dir: Directory containing export files
        keep_days: Number of days to keep files (default: 7)
    """
    cutoff = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
    export_pattern = "roam_export_*.json.gz"
    
    for filepath in Path(data_dir).glob(export_pattern):
        if filepath.stat().st_mtime < cutoff:
            try:
                filepath.unlink()
                logger.info(f"Cleaned up old export: {filepath.name}")
            except OSError as e:
                logger.error(f"Failed to remove old export {filepath}: {e}")

async def save_roam_data(
    data: Dict[str, Any],
    brain: str,
    data_dir: str,
    cleanup: bool = True,
    keep_days: int = 7
) -> Path:
    """
    Save Roam data with compression and versioning.
    
    Args:
        data: Dictionary containing Roam data to save
        brain: Brain identifier (e.g., "ideas", "work")
        data_dir: Base directory for data storage
        cleanup: Whether to remove old exports (default: True)
        keep_days: Number of days to keep old exports if cleanup is True
        
    Returns:
        Path object of the saved file
        
    Raises:
        OSError: If file operations fail
    """
    # Ensure data directory exists
    os.makedirs(data_dir, exist_ok=True)
    
    # Generate filepath with timestamp
    filepath = get_export_filepath(brain, data_dir)
    
    try:
        # Save compressed data
        with gzip.open(filepath, 'wt', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved Roam export to {filepath}")
        
        # Cleanup old files if requested
        if cleanup:
            cleanup_old_exports(data_dir, keep_days)
            
        return filepath
        
    except (OSError, json.JSONEncodeError) as e:
        logger.error(f"Failed to save Roam export: {e}")
        raise

async def load_roam_data(filepath: Path) -> Optional[Dict[str, Any]]:
    """
    Load compressed Roam data export.
    
    Args:
        filepath: Path to the compressed export file
        
    Returns:
        Dictionary containing the Roam data, or None if file doesn't exist
        
    Raises:
        json.JSONDecodeError: If JSON parsing fails
        OSError: If file operations fail
    """
    if not filepath.exists():
        logger.warning(f"Export file not found: {filepath}")
        return None
        
    try:
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            data = json.load(f)
            
        logger.debug(f"Loaded Roam export from {filepath}")
        return data
        
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load Roam export from {filepath}: {e}")
        raise 