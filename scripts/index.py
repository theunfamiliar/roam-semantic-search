"""Script to reindex a brain using the indexing service."""

import sys
import os
from pathlib import Path

# Add parent directory to Python path so we can import app
sys.path.append(str(Path(__file__).parent.parent))

import asyncio
import argparse
import logging
from app.services.indexing import reindex_brain
from app.utils.logging import setup_logging
from app.config import BRAINS

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)

async def main():
    """Main function to run reindexing."""
    parser = argparse.ArgumentParser(description="Reindex a brain")
    parser.add_argument("--brain", type=str, required=True, choices=BRAINS,
                      help=f"Brain to reindex (one of: {', '.join(BRAINS)})")
    args = parser.parse_args()
    
    try:
        logger.info(f"Starting reindex of {args.brain} brain")
        result = await reindex_brain(args.brain)
        logger.info(f"✅ Successfully reindexed {args.brain} brain")
        logger.info(f"Processed {result['blocks_processed']} blocks in {result['duration']:.2f} seconds")
    except Exception as e:
        logger.error(f"❌ Failed to reindex {args.brain} brain", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main())