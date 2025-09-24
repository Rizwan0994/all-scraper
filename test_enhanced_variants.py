#!/usr/bin/env python3
"""
🎯 ENHANCED VARIANT EXTRACTION TEST
Testing the new 100% perfect variant data extraction
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper.universal_scraper import UniversalScraper
import json
import time

def test_enhanced_variant_extraction():
    """Test enhanced variant extraction with perfect data"""
    
    print("🎯 TESTING ENHANCED VARIANT EXTRACTION")
    print("=" * 60)
    
    # Initialize scraper
    print("\n🔧 Initializing Universal Scraper...")
    scraper = UniversalScraper()  # No parameters needed
    
    # Test URLs with known variants
    test_urls = [
        # iPhone with storage and carrier variants
        "https://www.amazon.com/s?k=iphone+16&ref=nb_sb_noss",
        # Apple Watch with size variants  
        "https://www.amazon.com/s?k=apple+watch+series+10&ref=nb_sb_noss",
        # AirPods with different models
        "https://www.amazon.com/s?k=airpods+pro&ref=nb_sb_noss"
    ]
    
    for i, search_url in enumerate(test_urls, 1):
        print(f"\n🔍 Test {i}/3: Testing with {search_url.split('k=')[1].split('&')[0]}...")
        
        try:
            # Scrape with enhanced extraction
            search_query = search_url.split('k=')[1].split('&')[0].replace('+', ' ')
            results = scraper.scrape_amazon(
                keywords=search_query,
                max_products=1  # Just test one product per search
            )
            
            if results:
                product = results[0]
                
                # Handle both dict and object formats
                if hasattr(product, '__dict__'):
                    # Convert object to dict for easier access
                    product_dict = product.__dict__ if hasattr(product, '__dict__') else {}
                    product_name = getattr(product, 'product_name', 'Unknown')
                    product_id = getattr(product, 'product_id', 'Unknown')
                    price = getattr(product, 'unit_price', 0)
                    variants = getattr(product, 'variants', [])
                else:
                    # Already a dict
                    product_dict = product
                    product_name = product.get('product_name', 'Unknown')
                    product_id = product.get('product_id', 'Unknown') 
                    price = product.get('unit_price', 0)
                    variants = product.get('variants', [])
                
                print(f"\n📊 RESULTS for {product_name[:50]}...")
                print(f"   Product ID: {product_id}")
                print(f"   Price: ${price}")
                print(f"   Variants found: {len(variants)}")
                
                # Analyze variant quality
                if variants:
                    print(f"\n🎯 VARIANT ANALYSIS:")
                    for j, variant in enumerate(variants[:5], 1):  # Show first 5
                        if hasattr(variant, '__dict__'):
                            v_name = getattr(variant, 'name', 'Unknown')
                            v_type = getattr(variant, 'type', 'N/A')
                            v_price = getattr(variant, 'price', 'N/A')
                            v_stock = getattr(variant, 'stock', 'N/A')
                            v_images = getattr(variant, 'images', [])
                            v_sku = getattr(variant, 'sku', 'N/A')
                        else:
                            v_name = variant.get('name', 'Unknown')
                            v_type = variant.get('type', 'N/A')
                            v_price = variant.get('price', 'N/A')
                            v_stock = variant.get('stock', 'N/A')
                            v_images = variant.get('images', [])
                            v_sku = variant.get('sku', 'N/A')
                        
                        print(f"   {j}. {v_name}")
                        print(f"      Type: {v_type}")
                        print(f"      Price: ${v_price}")
                        print(f"      Stock: {v_stock}")
                        print(f"      Images: {len(v_images) if v_images else 0}")
                        print(f"      SKU: {v_sku}")
                    
                    if len(variants) > 5:
                        print(f"   ... and {len(variants) - 5} more variants")
                    
                    # Check for perfect data indicators
                    perfect_prices = 0
                    perfect_images = 0  
                    perfect_stocks = 0
                    
                    for v in variants:
                        if hasattr(v, '__dict__'):
                            v_price = getattr(v, 'price', None)
                            v_images = getattr(v, 'images', [])
                            v_stock = getattr(v, 'stock', None)
                        else:
                            v_price = v.get('price')
                            v_images = v.get('images', [])
                            v_stock = v.get('stock')
                        
                        if v_price and v_price != price:
                            perfect_prices += 1
                        if v_images and len(v_images) > 0:
                            perfect_images += 1
                        if v_stock and v_stock != 50:
                            perfect_stocks += 1
                    
                    print(f"\n✅ PERFECT DATA METRICS:")
                    print(f"   Unique prices: {perfect_prices}/{len(variants)} ({perfect_prices/len(variants)*100:.1f}%)")
                    print(f"   With images: {perfect_images}/{len(variants)} ({perfect_images/len(variants)*100:.1f}%)")
                    print(f"   Real stock data: {perfect_stocks}/{len(variants)} ({perfect_stocks/len(variants)*100:.1f}%)")
                    
                    # Overall quality score
                    quality_score = (perfect_prices + perfect_images + perfect_stocks) / (len(variants) * 3) * 100
                    print(f"   🏆 QUALITY SCORE: {quality_score:.1f}%")
                    
                    if quality_score >= 80:
                        print("   🎉 EXCELLENT QUALITY!")
                    elif quality_score >= 60:
                        print("   ✅ GOOD QUALITY!")
                    elif quality_score >= 40:
                        print("   ⚠️ NEEDS IMPROVEMENT")
                    else:
                        print("   ❌ POOR QUALITY")
                        
                else:
                    print("   ℹ️ No variants found (might be correct for this product)")
                    
            else:
                print("   ❌ No products scraped")
                
            # Brief pause between tests
            time.sleep(2)
            
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            continue
    
    print("\n🎉 ENHANCED VARIANT EXTRACTION TEST COMPLETED!")
    
    # Cleanup
    try:
        scraper.cleanup()
    except:
        pass

if __name__ == "__main__":
    test_enhanced_variant_extraction()
