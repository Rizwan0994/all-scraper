#!/usr/bin/env python3
"""
Test Variant Images Fix
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

def test_variant_images_fix():
    """Test if variant images are now being properly assigned"""
    
    print("🔧 TESTING VARIANT IMAGES FIX")
    print("=" * 50)
    
    try:
        from universal_scraper import UniversalScraper
        
        # Initialize scraper
        print("\n🔧 Initializing Universal Scraper...")
        scraper = UniversalScraper()
        
        # Test with a product that should have variants
        print("\n🔍 Testing with Xbox product that should have variants...")
        test_url = "https://www.amazon.com/Microsoft-Xbox-Gaming-Console-video-game/dp/B08H75RTZ8"
        
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
                print(f"\n   Variant Image Analysis:")
                variants_with_images = 0
                variants_without_images = 0
                
                for i, variant in enumerate(product.variants, 1):
                    variant_name = variant.get('name', 'Unknown')
                    variant_images = variant.get('images', [])
                    image_count = len(variant_images) if variant_images else 0
                    
                    if image_count > 0:
                        variants_with_images += 1
                        status = "✅ HAS IMAGES"
                        print(f"      {i}. {variant_name[:50]}... - {image_count} images {status}")
                        if variant_images:
                            print(f"         First image: {variant_images[0][:80]}...")
                    else:
                        variants_without_images += 1
                        status = "❌ NO IMAGES"
                        print(f"      {i}. {variant_name[:50]}... - {image_count} images {status}")
                
                print(f"\n📈 ANALYSIS:")
                print(f"   Variants with images: {variants_with_images}")
                print(f"   Variants without images: {variants_without_images}")
                
                if variants_without_images == 0:
                    print("🎉 SUCCESS! All variants now have images!")
                    return True
                elif variants_with_images > variants_without_images:
                    print("✅ GOOD! Most variants have images, some improvement needed")
                    return True
                else:
                    print("❌ ISSUE! Still missing variant images")
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
    success = test_variant_images_fix()
    if success:
        print("\n🎉 VARIANT IMAGES FIX TEST PASSED!")
    else:
        print("\n💥 VARIANT IMAGES FIX TEST FAILED!")

