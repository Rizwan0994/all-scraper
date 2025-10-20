#!/usr/bin/env python3
"""
Force chunk consolidation script to fix the stuck chunk manager issue
"""

import logging
import json
from chunk_manager import ChunkManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def force_consolidate_chunks():
    """Force consolidate all chunks and re-enable chunk manager"""
    
    logger.info("🔧 FORCE FIX: Re-enabling chunk manager and consolidating data...")
    
    # Initialize chunk manager
    chunk_manager = ChunkManager()
    
    # Force re-enable chunk manager
    chunk_manager.set_scraping_active(False)
    logger.info("✅ Chunk manager re-enabled")
    
    # Force consolidate all existing data
    try:
        logger.info("🔄 Force consolidating all existing products...")
        chunk_manager.force_consolidate_all_chunks()
        logger.info("✅ Force consolidation completed")
        
        # Get final count
        total_products = chunk_manager.get_total_products_count()
        logger.info(f"📊 Total products after consolidation: {total_products:,}")
        
    except Exception as e:
        logger.error(f"❌ Error during force consolidation: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = force_consolidate_chunks()
    if success:
        print("🎉 SUCCESS: Chunk manager fixed and data consolidated!")
    else:
        print("❌ FAILED: Could not fix chunk manager")
