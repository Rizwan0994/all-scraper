#!/usr/bin/env python3
"""
🔍 VARIANT DEBUGGING SCRIPT
Investigates exactly what's happening with variant extraction
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from scraper.universal_scraper import UniversalScraper
import time
import json

def debug_variant_extraction():
    """Debug variant extraction step by step"""
    print("🔍 DEBUGGING VARIANT EXTRACTION")
    print("=" * 60)
    
    # Initialize scraper
    scraper = UniversalScraper()
    
    # Initialize the selenium driver properly
    print("🚀 Initializing Selenium driver...")
    scraper.setup_selenium_driver()
    
    if not scraper.driver:
        print("❌ Failed to initialize driver")
        return []
    
    # Test with a specific Amazon URL that should have variants
    test_url = "https://www.amazon.com/dp/B0CHX1W3WQ"  # iPhone 15 - should have variants
    
    print(f"🌐 Testing with: {test_url}")
    
    try:
        print("\n📱 Step 1: Opening page...")
        scraper.driver.get(test_url)
        time.sleep(5)
        
        print("\n🔍 Step 2: Looking for variant elements...")
        
        # Check for variant elements
        from selenium.webdriver.common.by import By
        variant_selectors = [
            '.a-button-group .a-button',
            '.a-button-toggle-group .a-button', 
            '[data-action="a-dropdown-button"]',
            '.a-button[aria-label*="storage"]',
            '.a-button[aria-label*="Storage"]',
            '.a-button[aria-label*="color"]',
            '.a-button[aria-label*="Color"]'
        ]
        
        for selector in variant_selectors:
            try:
                elements = scraper.driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"   📋 {selector}: {len(elements)} elements found")
                
                for i, element in enumerate(elements[:3]):  # Check first 3
                    try:
                        text = element.text.strip()
                        aria_label = element.get_attribute('aria-label') or ''
                        print(f"      - Element {i+1}: '{text}' (aria: '{aria_label[:30]}...')")
                    except Exception as e:
                        print(f"      - Element {i+1}: Error reading - {e}")
                        
            except Exception as e:
                print(f"   ❌ {selector}: Failed - {e}")
        
        print("\n🧪 Step 3: Testing variant extractor...")
        
        # Test the variant extractor directly
        from amazon_variant_extractor import AmazonVariantExtractor
        
        extractor = AmazonVariantExtractor(scraper.driver)
        variants = extractor.extract_variants()
        
        print(f"\n📊 RESULTS:")
        print(f"   🔢 Total variants found: {len(variants)}")
        
        for i, variant in enumerate(variants[:5]):  # Show first 5
            print(f"\n   📦 Variant {i+1}:")
            print(f"      🏷️ Name: {variant.get('name', 'NO NAME')}")
            print(f"      💰 Price: ${variant.get('price', 'NO PRICE')}")
            print(f"      📦 Stock: {variant.get('stock', 'NO STOCK')}")
            print(f"      🖼️ Images: {len(variant.get('images', []))} images")
            print(f"      🔧 SKU: {variant.get('sku', 'NO SKU')}")
            print(f"      📋 Attributes: {variant.get('attributes', {})}")
            
        return variants
        
    except Exception as e:
        print(f"❌ DEBUG FAILED: {e}")
        import traceback
        traceback.print_exc()
        return []
    
    finally:
        if hasattr(scraper, 'driver'):
            scraper.driver.quit()

if __name__ == "__main__":
    debug_variant_extraction()
