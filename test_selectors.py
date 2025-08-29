#!/usr/bin/env python3
"""
Comprehensive test script to verify all website selectors
"""

import cloudscraper
from bs4 import BeautifulSoup
import time
import re

def test_amazon_selectors():
    """Test Amazon selectors"""
    print("Testing Amazon selectors...")
    scraper = cloudscraper.create_scraper()
    
    try:
        response = scraper.get('https://www.amazon.com/s?k=phone')
        soup = BeautifulSoup(response.content, 'html.parser')
        
        selectors = [
            '[data-asin]',
            '[data-component-type="s-search-result"]',
            '.s-result-item',
            '[data-testid="product-card"]',
            '.s-card-container',
            '.s-include-content-margin',
            '.a-section'
        ]
        
        for selector in selectors:
            items = soup.select(selector)
            print(f"  {selector}: {len(items)} items")
            
            if items:
                # Test title extraction
                for i, item in enumerate(items[:3]):
                    title_elem = (item.find('h2', class_='a-color-base') or 
                                 item.find('span', class_='a-size-base-plus') or
                                 item.find('span', class_='a-text-normal'))
                    title = title_elem.get_text(strip=True) if title_elem else "No title"
                    print(f"    Item {i+1}: {title[:50]}...")
                break
                
    except Exception as e:
        print(f"  Error: {e}")

def test_ebay_selectors():
    """Test eBay selectors"""
    print("Testing eBay selectors...")
    scraper = cloudscraper.create_scraper()
    
    try:
        response = scraper.get('https://www.ebay.com/sch/i.html?_nkw=phone')
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Print page title to see if we're getting the right page
        title = soup.find('title')
        print(f"  Page title: {title.get_text() if title else 'No title'}")
        
        selectors = [
            '.s-item',
            '[data-testid="item-card"]',
            '.s-item__info',
            '[data-testid="s-item"]',
            '[data-testid="srp-results"] .s-item',
            '.srp-results .s-item',
            '.srp-grid .s-item',
            '[data-testid="srp-results"] [data-testid*="item"]'
        ]
        
        for selector in selectors:
            items = soup.select(selector)
            print(f"  {selector}: {len(items)} items")
            
            if items:
                # Test title extraction
                for i, item in enumerate(items[:3]):
                    title_elem = item.select_one('.s-item__title') or item.select_one('h3')
                    title = title_elem.get_text(strip=True) if title_elem else "No title"
                    print(f"    Item {i+1}: {title[:50]}...")
                break
                
    except Exception as e:
        print(f"  Error: {e}")

def test_daraz_selectors():
    """Test Daraz selectors"""
    print("Testing Daraz selectors...")
    scraper = cloudscraper.create_scraper()
    
    try:
        response = scraper.get('https://www.daraz.pk/catalog/?q=phone')
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check if we're being blocked
        title = soup.find('title')
        print(f"  Page title: {title.get_text() if title else 'No title'}")
        
        # Check for CAPTCHA or blocking
        if 'captcha' in str(soup).lower() or 'punish' in str(soup).lower():
            print("  Blocked by anti-bot protection")
            return
        
        selectors = [
            '[data-qa-locator="product-item"]',
            '.gridItem--Yd0sa',
            '.c2prKC',
            '.cRjKsc',
            '[data-testid="product-card"]',
            '.product-item',
            '[class*="product"]',
            '[class*="item"]'
        ]
        
        for selector in selectors:
            items = soup.select(selector)
            print(f"  {selector}: {len(items)} items")
            
            if items:
                # Test title extraction
                for i, item in enumerate(items[:3]):
                    title_elem = (item.find('div', class_='title--wFj93') or
                                 item.find('a', class_='c16H9d') or
                                 item.find('h3') or
                                 item.find('div', class_='RfADt'))
                    title = title_elem.get_text(strip=True) if title_elem else "No title"
                    print(f"    Item {i+1}: {title[:50]}...")
                break
                
    except Exception as e:
        print(f"  Error: {e}")

def test_aliexpress_selectors():
    """Test AliExpress selectors"""
    print("Testing AliExpress selectors...")
    scraper = cloudscraper.create_scraper()
    
    try:
        response = scraper.get('https://www.aliexpress.com/wholesale?SearchText=phone')
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check if we're being blocked
        title = soup.find('title')
        print(f"  Page title: {title.get_text() if title else 'No title'}")
        
        selectors = [
            '.list-item',
            '[data-product-id]',
            '.product-item',
            '[data-ae_object_value]',
            '.JIIxO',
            '[class*="product"]',
            '[class*="item"]'
        ]
        
        for selector in selectors:
            items = soup.select(selector)
            print(f"  {selector}: {len(items)} items")
            
            if items:
                # Test title extraction
                for i, item in enumerate(items[:3]):
                    title_elem = item.select_one('.item-title') or item.select_one('h3') or item.select_one('.product-title')
                    title = title_elem.get_text(strip=True) if title_elem else "No title"
                    print(f"    Item {i+1}: {title[:50]}...")
                break
                
    except Exception as e:
        print(f"  Error: {e}")

def test_etsy_selectors():
    """Test Etsy selectors"""
    print("Testing Etsy selectors...")
    scraper = cloudscraper.create_scraper()
    
    try:
        response = scraper.get('https://www.etsy.com/search?q=phone')
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check if we're being blocked
        title = soup.find('title')
        print(f"  Page title: {title.get_text() if title else 'No title'}")
        
        selectors = [
            '[data-test-id="listing-card"]',
            '.listing-link',
            '.wt-grid__item-xs-6',
            '[class*="listing"]',
            '[class*="card"]'
        ]
        
        for selector in selectors:
            items = soup.select(selector)
            print(f"  {selector}: {len(items)} items")
            
            if items:
                # Test title extraction
                for i, item in enumerate(items[:3]):
                    title_elem = item.select_one('h3') or item.select_one('.listing-link') or item.select_one('.wt-text-caption')
                    title = title_elem.get_text(strip=True) if title_elem else "No title"
                    print(f"    Item {i+1}: {title[:50]}...")
                break
                
    except Exception as e:
        print(f"  Error: {e}")

def test_valuebox_selectors():
    """Test ValueBox selectors"""
    print("Testing ValueBox selectors...")
    scraper = cloudscraper.create_scraper()
    
    try:
        response = scraper.get('https://www.valuebox.pk/search?q=phone')
        soup = BeautifulSoup(response.content, 'html.parser')
        
        selectors = [
            '.product-item',
            '[data-product-id]',
            '.product-card',
            '[class*="product"]'
        ]
        
        for selector in selectors:
            items = soup.select(selector)
            print(f"  {selector}: {len(items)} items")
            
            if items:
                # Test title extraction with multiple methods
                for i, item in enumerate(items[:3]):
                    # Try multiple title selectors
                    title_elem = (item.select_one('.product-title') or 
                                 item.select_one('h3') or 
                                 item.select_one('.product-name') or
                                 item.select_one('.title') or
                                 item.select_one('a[title]') or
                                 item.select_one('[data-title]'))
                    
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                    else:
                        # Try to get title from link text or alt text
                        link_elem = item.select_one('a')
                        if link_elem:
                            title = link_elem.get('title') or link_elem.get_text(strip=True)
                        else:
                            # Try to find any text that looks like a title
                            title_text = item.get_text()
                            if len(title_text) > 10 and len(title_text) < 200:
                                title = title_text[:50]
                            else:
                                title = "No title"
                    
                    print(f"    Item {i+1}: {title[:50]}...")
                break
                
    except Exception as e:
        print(f"  Error: {e}")

if __name__ == "__main__":
    print("Testing all website selectors...")
    print("=" * 50)
    
    test_amazon_selectors()
    print()
    time.sleep(2)
    
    test_ebay_selectors()
    print()
    time.sleep(2)
    
    test_daraz_selectors()
    print()
    time.sleep(2)
    
    test_aliexpress_selectors()
    print()
    time.sleep(2)
    
    test_etsy_selectors()
    print()
    time.sleep(2)
    
    test_valuebox_selectors()
    print()
    
    print("=" * 50)
    print("Selector testing completed!")
