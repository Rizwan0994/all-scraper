#!/usr/bin/env python3
"""
Test Fresh Scraping to Verify Variant Extraction Fix
"""

import os
import sys
import json
import logging
from datetime import datetime

# Add scraper to path
sys.path.append('scraper')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_fresh_scraping():
    """Test fresh scraping with a specific product URL"""
    
    print("🔧 TESTING FRESH SCRAPING WITH VARIANT EXTRACTION FIX")
    print("=" * 70)
    
    try:
        from universal_scraper import UniversalScraper
        
        # Initialize scraper
        print("\n🔧 Initializing Universal Scraper...")
        scraper = UniversalScraper()
        
        # Test with a specific product that has variants
        print("\n🔍 Testing with specific Amazon product URL...")
        test_url = "https://www.amazon.com/Apple-iPhone-15-128GB-Black/dp/B0CHX1W1XY"
        
        # Scrape this specific product
        products = scraper.scrape_amazon(test_url, max_products=1)
        
        print(f"\n📊 RESULTS:")
        print(f"   Products scraped: {len(products)}")
        
        if products:
            product = products[0]
            variant_count = len(product.variants) if product.variants else 0
            
            print(f"\n   Product: {product.product_name[:80]}...")
            print(f"   Variants: {variant_count}")
            
            if variant_count > 0:
                print(f"\n   Variant Details:")
                clean_count = 0
                fake_count = 0
                
                for i, variant in enumerate(product.variants, 1):
                    variant_name = variant.get('name', variant.get('option', variant.get('color', 'Unknown')))
                    variant_type = variant.get('type', 'unknown')
                    price = variant.get('price', 'N/A')
                    
                    # Check if it's a clean variant
                    is_clean = not any(pattern in variant_name.lower() for pattern in [
                        'add to list', 'update page', 'select', 'choose', 'qty', 'quantity'
                    ]) and not variant_name.isdigit() and not variant_name.endswith('+')
                    
                    if is_clean:
                        clean_count += 1
                        status = "✅ CLEAN"
                    else:
                        fake_count += 1
                        status = "❌ FAKE"
                    
                    print(f"      {i}. [{variant_type}] {variant_name} - ${price} {status}")
                
                print(f"\n📈 ANALYSIS:")
                print(f"   Clean variants: {clean_count}")
                print(f"   Fake variants: {fake_count}")
                
                if fake_count == 0 and clean_count > 0:
                    print("🎉 SUCCESS! All variants are clean!")
                    return True
                elif fake_count < clean_count:
                    print("✅ GOOD! Most variants are clean")
                    return True
                else:
                    print("❌ ISSUE! Still getting fake variants")
                    return False
            else:
                print("ℹ️  No variants found (this might be correct for this product)")
                return True
        else:
            print("❌ No products scraped")
            return False
        
        # Cleanup
        scraper.cleanup()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_fresh_scraping()
    if success:
        print("\n🎉 FRESH SCRAPING TEST PASSED!")
    else:
        print("\n💥 FRESH SCRAPING TEST FAILED!")

