#!/usr/bin/env python3
"""
Test Xbox Controller Variant Extraction
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

def test_xbox_controller_variants():
    """Test variant extraction specifically for Xbox controller"""
    
    print("🎮 TESTING XBOX CONTROLLER VARIANT EXTRACTION")
    print("=" * 60)
    
    try:
        from universal_scraper import UniversalScraper
        
        # Initialize scraper
        print("\n🔧 Initializing Universal Scraper...")
        scraper = UniversalScraper()
        
        # Test with Xbox Elite Series 2 Core controller
        print("\n🎮 Testing with Xbox Elite Series 2 Core controller...")
        test_url = "https://www.amazon.com/Xbox-Elite-Wireless-Controller-Gaming-Console/dp/B0BTTSYCY7"
        
        # Scrape this specific product using the new single product method
        products = scraper.scrape_single_product(test_url, site='amazon')
        
        print(f"\n📊 RESULTS:")
        print(f"   Products scraped: {len(products)}")
        
        if products:
            product = products[0]
            variant_count = len(product.variants) if product.variants else 0
            
            print(f"\n   Product: {product.product_name[:80]}...")
            print(f"   Variants found: {variant_count}")
            
            if variant_count > 0:
                print(f"\n   Variant Analysis:")
                color_variants = 0
                other_variants = 0
                
                for i, variant in enumerate(product.variants, 1):
                    variant_name = variant.get('name', 'Unknown')
                    variant_type = variant.get('type', 'unknown')
                    variant_images = variant.get('images', [])
                    image_count = len(variant_images) if variant_images else 0
                    
                    if variant_type == 'color':
                        color_variants += 1
                        status = "✅ COLOR VARIANT"
                    else:
                        other_variants += 1
                        status = f"⚠️  {variant_type.upper()}"
                    
                    print(f"      {i}. {variant_name[:50]}... - {variant_type} - {image_count} images {status}")
                    
                    # Check if it's a media element (should be filtered out)
                    if any(media_word in variant_name.lower() for media_word in ['video', 'photo', 'image']):
                        print(f"         ❌ MEDIA ELEMENT DETECTED - Should be filtered out!")
                
                print(f"\n📈 ANALYSIS:")
                print(f"   Color variants: {color_variants}")
                print(f"   Other variants: {other_variants}")
                
                # Expected: Should find Black, Blue, Red, White color variants
                expected_colors = ['black', 'blue', 'red', 'white']
                found_colors = []
                
                for variant in product.variants:
                    if variant.get('type') == 'color':
                        variant_name = variant.get('name', '').lower()
                        for expected_color in expected_colors:
                            if expected_color in variant_name:
                                found_colors.append(expected_color)
                                break
                
                print(f"   Expected colors: {expected_colors}")
                print(f"   Found colors: {found_colors}")
                
                if len(found_colors) >= 2:  # At least 2 color variants
                    print("🎉 SUCCESS! Found multiple color variants!")
                    return True
                elif color_variants > 0:
                    print("✅ PARTIAL SUCCESS! Found some color variants")
                    return True
                else:
                    print("❌ ISSUE! No color variants found")
                    return False
            else:
                print("ℹ️  No variants found")
                return False
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
    success = test_xbox_controller_variants()
    if success:
        print("\n🎉 XBOX CONTROLLER VARIANT TEST PASSED!")
    else:
        print("\n💥 XBOX CONTROLLER VARIANT TEST FAILED!")
