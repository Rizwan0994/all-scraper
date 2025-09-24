#!/usr/bin/env python3
"""
🧪 TEST FIXED VARIANT EXTRACTION
Test the variant extraction after fixing fake price variants
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))
sys.path.append('scraper')

def test_fixed_extraction():
    """Test the fixed variant extraction"""
    print("🧪 TESTING FIXED VARIANT EXTRACTION")
    print("=" * 60)
    
    try:
        from universal_scraper import UniversalScraper
        
        # Initialize scraper
        print("🚀 Initializing scraper...")
        scraper = UniversalScraper()
        
        # Test with a simple search that should have variants
        print("\n🔍 Testing with headphones search...")
        products = scraper.scrape_amazon("headphones", max_products=1)
        
        print(f"\n📊 RESULTS:")
        print(f"   Products scraped: {len(products)}")
        
        if products:
            product = products[0]
            print(f"\n   Product: {product.product_name[:80]}...")
            print(f"   Unit Price: ${product.unit_price}")
            print(f"   Variants: {len(product.variants) if product.variants else 0}")
            
            if product.variants:
                print(f"\n🎯 VARIANT ANALYSIS:")
                for i, variant in enumerate(product.variants[:5], 1):
                    print(f"   {i}. Type: {variant.get('type', 'MISSING')}")
                    print(f"      Name: {variant.get('name', 'MISSING')}")
                    print(f"      Price: ${variant.get('price', 'MISSING')}")
                    print(f"      Stock: {variant.get('stock', 'MISSING')}")
                    print(f"      SKU: {variant.get('sku', 'MISSING')}")
                    print(f"      Images: {len(variant.get('images', []))}")
                    print(f"      Attributes: {variant.get('attributes', {})}")
                    print()
                
                # Check for fake price variants
                price_variants = [v for v in product.variants if v.get('type') == 'price']
                print(f"🚨 FAKE PRICE VARIANTS: {len(price_variants)}")
                
                if len(price_variants) == 0:
                    print("✅ SUCCESS! No fake price variants found!")
                else:
                    print("❌ STILL HAVE FAKE PRICE VARIANTS!")
                
                return len(price_variants) == 0
            else:
                print("📝 No variants found (this is okay for some products)")
                return True
        else:
            print("❌ No products scraped")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if 'scraper' in locals():
            scraper.cleanup()

if __name__ == "__main__":
    success = test_fixed_extraction()
    if success:
        print("\n🎉 VARIANT FIX TEST PASSED!")
    else:
        print("\n💥 VARIANT FIX TEST FAILED!")
