from dotenv import load_dotenv
import os
from typing import List, Dict

# Load environment variables
load_dotenv()

# API Configuration
API_VERSION = "1.0.0"
API_TITLE = "Roam Semantic Search API"

# Server Configuration
HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", "8000"))

# Authentication
USERNAME = os.getenv("USERNAME", "admin")
PASSWORD = os.getenv("PASSWORD", "secret")

# Roam Configuration
ROAM_GRAPH = os.getenv("ROAM_GRAPH")
ROAM_API_TOKEN = os.getenv("ROAM_API_TOKEN")

# Email Configuration
EMAIL_TO = "james@dunndealpr.com"
EMAIL_FROM = "316promoteam@gmail.com"
SMTP_PASS = os.getenv("SMTP_PASSWORD", "")
SMTP_USER = EMAIL_FROM

# File Paths
DATA_DIR = "data"
LOGS_DIR = "logs"

# Create necessary directories
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# CORS Configuration
CORS_ORIGINS = ["https://roamresearch.com"]

# Available Brains
BRAINS: List[str] = ["ideas", "marketing"]

def get_filenames(brain: str) -> Dict[str, str]:
    """
    Get the paths for brain-specific files.
    
    Args:
        brain: Name of the brain (must be one of BRAINS)
        
    Returns:
        Dict containing paths for index and metadata files
    """
    if brain not in BRAINS:
        raise ValueError(f"Invalid brain: {brain}. Must be one of {BRAINS}")
        
    return {
        "index": f"{DATA_DIR}/index_{brain}.faiss",
        "meta": f"{DATA_DIR}/metadata_{brain}.json"
    } 