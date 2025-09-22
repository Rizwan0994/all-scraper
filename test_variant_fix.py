#!/usr/bin/env python3
"""
Test the variant extraction fix
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'scraper'))

from universal_scraper import UniversalScraper
import time

def test_variant_fix():
    """Test if the variant extraction fix works"""
    print("🧪 TESTING VARIANT EXTRACTION FIX")
    print("=" * 50)
    
    # Initialize scraper
    scraper = UniversalScraper()
    
    # Test URL - Sidefeel jeans
    url = 'https://www.amazon.com/Sidefeel-Womens-Jeans-Waisted-Strechy/dp/B0D4QFSLP3/ref=sr_1_1?dib=eyJ2IjoiMSJ9.mB-EBI4ilAZySmJHfVi9t0GRmpwhB6Xm-ncHlRNYij9Lbyy87zDjrMvRJ8QQlI_hp38vVH_MexZ1F-kwkWTa21RgsRSwz8fPWpMHytFTdKCVeVHgmmyTAa43IQc4foy3RwcX4Y783_CJi1jDwjX3a4kY3e9x-yuvkRgx8Q-PBBUlTM3Y-VecC1s2dIaxd3LUYj9qzYEkSgAxwcLjsior2n4TmpCK_1OrwSUC8nXweg6MHX7wgdn5IhJR0VsYujCgMCs7W5uPpzE6ChTEtjqHvzivUYKM4mu8wTLuqMaYuOA.bx3hj5gml4l-Z1MkcLgoCtRV6CfzyS0NAw3jQXpRuxE&dib_tag=se&keywords=jeans&qid=1758530796&sr=8-1'
    
    try:
        print("1. Testing Selenium driver...")
        if not hasattr(scraper, 'stealth_driver') or not scraper.stealth_driver:
            print("   ❌ Selenium driver not available")
            return False
        
        print("   ✅ Selenium driver is available")
        
        print("\n2. Testing product page loading with Selenium...")
        scraper.stealth_driver.get(url)
        time.sleep(5)  # Wait for page to load
        
        page_source = scraper.stealth_driver.page_source
        print(f"   ✅ Page loaded: {len(page_source)} characters")
        
        print("\n3. Testing variant extraction...")
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Test the variant extraction method
        variants = scraper.extract_variants(soup, 'Sidefeel Womens Wide Leg Jeans', 32.99)
        
        print(f"   Variants found: {len(variants)}")
        
        if variants:
            print("   ✅ Variant extraction is working!")
            for i, variant in enumerate(variants):
                print(f"     {i+1}. {variant}")
            
            print("\n🎉 SUCCESS! Variant extraction is now working!")
            return True
        else:
            print("   ❌ No variants found")
            
            # Debug: Check what variant containers are on the page
            print("\n4. Debugging variant containers...")
            containers = soup.select('.a-button-toggle-group, [role="radiogroup"], .a-button-selected')
            print(f"   Found {len(containers)} variant containers")
            
            for i, container in enumerate(containers[:3]):
                text = container.get_text(strip=True)
                print(f"     {i+1}. {text[:100]}...")
            
            return False
        
    except Exception as e:
        print(f"   ❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up
        if hasattr(scraper, 'stealth_driver') and scraper.stealth_driver:
            try:
                scraper.stealth_driver.quit()
            except:
                pass

def test_small_scrape():
    """Test with a small scrape to see if variants are extracted"""
    print("\n🧪 TESTING SMALL SCRAPE")
    print("=" * 30)
    
    scraper = UniversalScraper()
    
    try:
        print("Scraping 3 products to test variant extraction...")
        keywords = ["jeans"]
        products = scraper.scrape_amazon(keywords, max_products=3)
        
        print(f"Scraped {len(products)} products")
        
        products_with_variants = 0
        for i, product in enumerate(products):
            variant_count = len(product.variants) if hasattr(product, 'variants') else 0
            print(f"  {i+1}. {product.product_name[:50]}... - {variant_count} variants")
            if variant_count > 0:
                products_with_variants += 1
        
        if products_with_variants > 0:
            print(f"\n✅ SUCCESS! {products_with_variants} products have variants!")
            return True
        else:
            print("\n❌ No products have variants")
            return False
            
    except Exception as e:
        print(f"❌ Error during small scrape: {e}")
        return False
    
    finally:
        # Clean up
        if hasattr(scraper, 'stealth_driver') and scraper.stealth_driver:
            try:
                scraper.stealth_driver.quit()
            except:
                pass

def main():
    """Main test function"""
    print("🔧 TESTING VARIANT EXTRACTION FIX")
    print("=" * 60)
    
    # Test 1: Direct variant extraction
    print("TEST 1: Direct variant extraction")
    test1_success = test_variant_fix()
    
    # Test 2: Small scrape
    print("\nTEST 2: Small scrape test")
    test2_success = test_small_scrape()
    
    print("\n📋 TEST RESULTS")
    print("=" * 30)
    print(f"Direct variant extraction: {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"Small scrape test: {'✅ PASS' if test2_success else '❌ FAIL'}")
    
    if test1_success and test2_success:
        print("\n🎉 ALL TESTS PASSED! Variant extraction is working!")
        print("\n📝 NEXT STEPS:")
        print("1. Run a larger scrape to test with more products")
        print("2. Check the database to see if variants are being stored")
    else:
        print("\n❌ Some tests failed. Need to investigate further.")
    
    print("\n✅ Testing completed!")

if __name__ == "__main__":
    main()
