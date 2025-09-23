#!/usr/bin/env python3
"""
Comprehensive Test for Amazon Variant Extraction Fix
Tests both advanced extraction and rule-based filtering
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

def test_comprehensive_fix():
    """Test the comprehensive variant extraction fix"""
    
    print("🔧 TESTING COMPREHENSIVE AMAZON VARIANT EXTRACTION FIX")
    print("=" * 70)
    
    try:
        from universal_scraper import UniversalScraper
        
        # Initialize scraper
        print("\n🔧 Initializing Universal Scraper...")
        scraper = UniversalScraper()
        
        # Check if advanced extractor is available
        if hasattr(scraper, 'ai_verifier'):
            print(f"✅ AI Verifier available: {scraper.ai_verifier.enabled if scraper.ai_verifier else False}")
        
        # Test with a product that has real variants
        print("\n🔍 Testing with Amazon product that has variants...")
        test_url = "https://www.amazon.com/s?k=headphones&ref=sr_pg_1"
        
        # Scrape 2 products to test
        products = scraper.scrape_amazon(test_url, max_products=2)
        
        print(f"\n📊 RESULTS:")
        print(f"   Products scraped: {len(products)}")
        
        # Analyze results
        total_variants = 0
        products_with_variants = 0
        clean_variants_count = 0
        fake_variants_count = 0
        
        for i, product in enumerate(products, 1):
            variant_count = len(product.variants) if product.variants else 0
            total_variants += variant_count
            
            if variant_count > 0:
                products_with_variants += 1
                
                print(f"\n   Product {i}: {product.product_name[:60]}...")
                print(f"   Variants: {variant_count}")
                
                # Analyze each variant
                for j, variant in enumerate(product.variants, 1):
                    variant_name = variant.get('name', variant.get('option', variant.get('color', 'Unknown')))
                    variant_type = variant.get('type', 'unknown')
                    price = variant.get('price', 'N/A')
                    
                    # Check if it's a clean variant
                    is_clean = not any(pattern in variant_name.lower() for pattern in [
                        'add to list', 'update page', 'select', 'choose', 'qty', 'quantity'
                    ]) and not variant_name.isdigit() and not variant_name.endswith('+')
                    
                    if is_clean:
                        clean_variants_count += 1
                        status = "✅ CLEAN"
                    else:
                        fake_variants_count += 1
                        status = "❌ FAKE"
                    
                    print(f"      {j}. [{variant_type}] {variant_name} - ${price} {status}")
        
        print(f"\n📈 ANALYSIS:")
        print(f"   Products with variants: {products_with_variants}/{len(products)}")
        print(f"   Total variants: {total_variants}")
        print(f"   Clean variants: {clean_variants_count}")
        print(f"   Fake variants: {fake_variants_count}")
        
        if fake_variants_count == 0 and clean_variants_count > 0:
            print("🎉 SUCCESS! All variants are clean!")
        elif fake_variants_count < clean_variants_count:
            print("✅ GOOD! Most variants are clean, some improvement needed")
        else:
            print("❌ ISSUE! Still getting fake variants")
        
        # Save test results
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'total_products': len(products),
            'products_with_variants': products_with_variants,
            'total_variants': total_variants,
            'clean_variants': clean_variants_count,
            'fake_variants': fake_variants_count,
            'success_rate': clean_variants_count / total_variants if total_variants > 0 else 0,
            'products': [p.__dict__ for p in products]
        }
        
        with open('comprehensive_test_results.json', 'w') as f:
            json.dump(test_results, f, indent=2)
        
        print(f"\n💾 Test results saved to: comprehensive_test_results.json")
        
        # Cleanup
        scraper.cleanup()
        
        return fake_variants_count == 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_comprehensive_fix()
    if success:
        print("\n🎉 COMPREHENSIVE FIX TEST PASSED!")
    else:
        print("\n💥 COMPREHENSIVE FIX TEST FAILED!")
