#!/usr/bin/env python3
"""
Universal Product Scraper - Launcher
Simple launcher for the web interface
"""

import sys
import os
import webbrowser
from app import app, socketio

def main():
    """Main entry point"""
    print("🕷️  UNIVERSAL PRODUCT SCRAPER")
    print("="*50)
    print("Complete solution for scraping Amazon, eBay, AliExpress, Etsy, Daraz, and ValueBox")
    print()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'web':
            print("🌐 Starting web interface...")
            print("Open your browser to: http://localhost:5000")
            
            try:
                webbrowser.open('http://localhost:5000')
            except:
                pass
            
            socketio.run(app, host='0.0.0.0', port=5000, debug=False)
            
        elif command == 'scrape':
            print("🔍 Starting command line scraping...")
            # Import and run command line scraping
            from scraper.universal_scraper import UniversalScraper
            
            scraper = UniversalScraper()
            
            # Enhanced keyword strategy for maximum coverage
            all_keywords = []
            
            # Primary keywords (most popular products)
            primary_keywords = [
                "phone", "laptop", "headphones", "shoes", "shirt", "dress", "watch", "bag",
                "camera", "tablet", "speaker", "jeans", "jacket", "book", "toy", "game"
            ]
            
            # Category-specific keywords
            from scraper.universal_scraper import CATEGORY_MAPPING
            for category, data in CATEGORY_MAPPING.items():
                all_keywords.extend(data["keywords"][:5])  # More keywords per category
            
            # Brand-specific searches for higher volumes
            brand_keywords = [
                "apple", "samsung", "nike", "adidas", "sony", "hp", "dell", "canon",
                "xbox", "playstation", "iphone", "macbook", "airpods", "beats"
            ]
            
            # Combine all keywords and remove duplicates
            keywords = list(set(primary_keywords + all_keywords + brand_keywords))
            
            print(f"📋 Total keywords: {len(keywords)}")
            print(f"🎯 Sample keywords: {', '.join(keywords[:15])}...")
            
            max_products = int(input("Max products per site (default 200): ") or 200)
            
            print(f"\n🚀 Starting enhanced scraping for 10K+ products")
            print(f"Max products per site: {max_products}")
            print(f"Expected total: ~{max_products * 6} products")
            print()
            
            products = scraper.scrape_all_sites(keywords, max_products)
            
            print(f"\n✅ Scraping completed!")
            print(f"Total products: {len(products)}")
            
            stats = scraper.get_statistics(products)
            print(f"Site breakdown: {stats['site_breakdown']}")
            print(f"Data saved to scraped_data/ folder")
            
            if len(products) >= 10000:
                print("🎉 SUCCESS: 10K+ products target achieved!")
            else:
                print(f"📊 Progress: {len(products)}/10000 products ({(len(products)/10000)*100:.1f}%)")
            
        else:
            print("Usage: python run.py [web|scrape]")
            print("  web    - Start web interface")
            print("  scrape - Run command line scraping")
    
    else:
        print("🌐 Starting web interface...")
        print("Open your browser to: http://localhost:5000")
        
        try:
            webbrowser.open('http://localhost:5000')
        except:
            pass
        
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)

if __name__ == "__main__":
    main()
