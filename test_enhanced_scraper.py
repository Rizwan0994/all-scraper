#!/usr/bin/env python3
"""
Quick test script to verify the enhanced AI-powered scraper
"""

import logging
from scraper.universal_scraper import UniversalScraper

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_enhanced_scraper():
    """Test the enhanced scraper with a single product"""
    try:
        print("🚀 Testing AI-Powered Enhanced Scraper")
        print("=" * 50)
        
        # Initialize scraper
        scraper = UniversalScraper()
        
        # Test with a single Amazon product URL
        test_url = "https://www.amazon.com/Oisacirg-Toddler-Princess-Wristwatch-Birthday/dp/B0D7CQGK8X"
        
        print(f"🎯 Testing image extraction from: {test_url}")
        
        # Test image extraction
        images = scraper.scrape_product_images(test_url, site='amazon', max_images=10)
        
        print(f"✅ Results:")
        print(f"   Total images found: {len(images)}")
        print(f"   Stealth driver available: {scraper.stealth_driver is not None}")
        print(f"   Dynamic extraction enabled: {scraper.use_dynamic_extraction}")
        
        if images:
            print(f"\n📷 Image URLs:")
            for i, img_url in enumerate(images[:5], 1):
                print(f"   {i}. {img_url}")
            if len(images) > 5:
                print(f"   ... and {len(images) - 5} more images")
        
        # Test accuracy improvement
        if len(images) >= 3:
            print(f"\n🎯 SUCCESS: Found {len(images)} images (target: >=3)")
            print(f"✅ AI-Enhanced scraper is working correctly!")
        else:
            print(f"\n⚠️  Found only {len(images)} images, investigating...")
            
        return len(images)
        
    except Exception as e:
        print(f"❌ Error testing enhanced scraper: {e}")
        return 0
    finally:
        # Cleanup
        if hasattr(scraper, 'stealth_driver') and scraper.stealth_driver:
            try:
                scraper.stealth_driver.quit()
            except:
                pass

if __name__ == "__main__":
    result = test_enhanced_scraper()
    print(f"\n🏁 Test completed. Images found: {result}")
