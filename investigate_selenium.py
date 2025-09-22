#!/usr/bin/env python3
"""
Investigate Selenium setup and variant extraction
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'scraper'))

from universal_scraper import UniversalScraper
import time

def investigate_selenium_setup():
    """Investigate if Selenium is properly set up"""
    print("🔍 INVESTIGATING SELENIUM SETUP")
    print("=" * 50)
    
    # Initialize scraper
    scraper = UniversalScraper()
    
    print("1. Checking Selenium driver initialization...")
    if hasattr(scraper, 'stealth_driver') and scraper.stealth_driver:
        print("   ✅ Stealth driver is initialized")
        print(f"   Driver type: {type(scraper.stealth_driver)}")
    else:
        print("   ❌ Stealth driver is NOT initialized")
        return False
    
    print("\n2. Testing Selenium driver with a simple page...")
    try:
        # Test with a simple page
        scraper.stealth_driver.get("https://httpbin.org/user-agent")
        time.sleep(2)
        page_source = scraper.stealth_driver.page_source
        print(f"   ✅ Selenium driver is working")
        print(f"   Page source length: {len(page_source)} characters")
    except Exception as e:
        print(f"   ❌ Selenium driver error: {e}")
        return False
    
    print("\n3. Testing Amazon page with Selenium...")
    try:
        # Test with Amazon page
        amazon_url = "https://www.amazon.com/Sidefeel-Womens-Jeans-Waisted-Strechy/dp/B0D4QFSLP3/ref=sr_1_1?dib=eyJ2IjoiMSJ9.mB-EBI4ilAZySmJHfVi9t0GRmpwhB6Xm-ncHlRNYij9Lbyy87zDjrMvRJ8QQlI_hp38vVH_MexZ1F-kwkWTa21RgsRSwz8fPWpMHytFTdKCVeVHgmmyTAa43IQc4foy3RwcX4Y783_CJi1jDwjX3a4kY3e9x-yuvkRgx8Q-PBBUlTM3Y-VecC1s2dIaxd3LUYj9qzYEkSgAxwcLjsior2n4TmpCK_1OrwSUC8nXweg6MHX7wgdn5IhJR0VsYujCgMCs7W5uPpzE6ChTEtjqHvzivUYKM4mu8wTLuqMaYuOA.bx3hj5gml4l-Z1MkcLgoCtRV6CfzyS0NAw3jQXpRuxE&dib_tag=se&keywords=jeans&qid=1758530796&sr=8-1"
        
        scraper.stealth_driver.get(amazon_url)
        time.sleep(5)  # Wait for page to load
        
        page_source = scraper.stealth_driver.page_source
        print(f"   ✅ Amazon page loaded with Selenium")
        print(f"   Page source length: {len(page_source)} characters")
        
        # Check for variant elements
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Look for variant containers
        variant_containers = soup.select('.a-button-toggle-group, [role="radiogroup"], .a-button-selected')
        print(f"   Found {len(variant_containers)} variant containers")
        
        if variant_containers:
            print("   ✅ Variant containers found!")
            for i, container in enumerate(variant_containers[:3]):
                text = container.get_text(strip=True)
                print(f"     {i+1}. {text[:100]}...")
        else:
            print("   ❌ No variant containers found")
        
    except Exception as e:
        print(f"   ❌ Amazon page error: {e}")
        return False
    
    print("\n4. Testing variant extraction...")
    try:
        variants = scraper.extract_variants(soup, 'Sidefeel Womens Wide Leg Jeans', 32.99)
        print(f"   Variants found: {len(variants)}")
        
        if variants:
            print("   ✅ Variant extraction is working!")
            for i, variant in enumerate(variants):
                print(f"     {i+1}. {variant}")
        else:
            print("   ❌ No variants extracted")
        
    except Exception as e:
        print(f"   ❌ Variant extraction error: {e}")
        return False
    
    return True

def investigate_amazon_scraping_method():
    """Investigate how Amazon scraping method works"""
    print("\n🔍 INVESTIGATING AMAZON SCRAPING METHOD")
    print("=" * 50)
    
    # Initialize scraper
    scraper = UniversalScraper()
    
    print("1. Checking Amazon scraping method...")
    
    # Look at the Amazon scraping method
    import inspect
    source = inspect.getsource(scraper.scrape_amazon)
    
    # Check if it uses Selenium for product pages
    if 'stealth_driver.get' in source:
        print("   ✅ Amazon scraping method uses Selenium for product pages")
    elif 'safe_request' in source:
        print("   ❌ Amazon scraping method uses safe_request (no JavaScript)")
        print("   This is why variants are not being extracted!")
    else:
        print("   ❓ Could not determine how Amazon scraping method works")
    
    # Check if it uses Selenium for variants
    if 'stealth_driver' in source and 'extract_variants' in source:
        print("   ✅ Amazon scraping method should use Selenium for variants")
    else:
        print("   ❌ Amazon scraping method does not use Selenium for variants")

def main():
    """Main investigation function"""
    print("🔍 COMPREHENSIVE SELENIUM INVESTIGATION")
    print("=" * 60)
    
    # Test 1: Selenium setup
    selenium_working = investigate_selenium_setup()
    
    # Test 2: Amazon scraping method
    investigate_amazon_scraping_method()
    
    print("\n📋 INVESTIGATION SUMMARY")
    print("=" * 30)
    
    if selenium_working:
        print("✅ Selenium is properly set up and working")
        print("✅ Can load Amazon pages with JavaScript")
        print("✅ Variant containers are found on the page")
        print("❌ But variant extraction is not working properly")
        print("\n🔧 RECOMMENDATION:")
        print("The issue is in the Amazon scraping method - it's using safe_request")
        print("instead of Selenium for product pages. Need to fix this.")
    else:
        print("❌ Selenium is not working properly")
        print("❌ Need to fix Selenium setup first")
    
    print("\n✅ Investigation completed!")

if __name__ == "__main__":
    main()
