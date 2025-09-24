#!/usr/bin/env python3
"""
Quick test script for Amazon variant extraction
Tests one product to see if variants are properly extracted with images and prices
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper.universal_scraper import UniversalScraper

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_amazon_variant_extraction():
    """Test Amazon variant extraction on a single product"""
    
    # Test URL - Amazon T-shirt with multiple color variants (like your screenshot)
    test_url = "https://www.amazon.com/Amazon-Essentials-Short-Sleeve-Crewneck-T-Shirt/dp/B07JPL231L"
    
    print("🧪 TESTING AMAZON VARIANT EXTRACTION")
    print("=" * 50)
    print(f"Test URL: {test_url}")
    print()
    
    try:
        # Initialize scraper
        scraper = UniversalScraper()
        
        print("✅ Scraper initialized")
        print("🔍 Starting variant extraction...")
        print()
        
        # Extract product data
        products = scraper._scrape_amazon_single_product(test_url)
        
        if products:
            product = products[0]
            print(f"📦 PRODUCT: {product.get('name', 'Unknown')[:60]}...")
            print(f"💰 BASE PRICE: ${product.get('price', 'N/A')}")
            print(f"🏪 SITE: {product.get('site', 'Unknown')}")
            print()
            
            # Check variants
            variants = product.get('variants', [])
            print(f"🎨 VARIANTS FOUND: {len(variants)}")
            print()
            
            if variants:
                print("VARIANT DETAILS:")
                print("-" * 40)
                
                for i, variant in enumerate(variants[:10], 1):  # Show first 10 variants
                    name = variant.get('name', 'Unknown')
                    price = variant.get('price', 'N/A')
                    images = variant.get('images', [])
                    stock = variant.get('stock', 'N/A')
                    
                    print(f"{i:2d}. {name}")
                    print(f"    💰 Price: ${price}")
                    print(f"    📦 Stock: {stock}")
                    print(f"    🖼️  Images: {len(images)} found")
                    
                    if images:
                        print(f"    🔗 First image: {images[0][:60]}...")
                    
                    print()
                
                if len(variants) > 10:
                    print(f"... and {len(variants) - 10} more variants")
                    
            else:
                print("❌ No variants found")
                
            # Check images
            main_images = product.get('images', [])
            print(f"🖼️  MAIN PRODUCT IMAGES: {len(main_images)}")
            
            if main_images:
                print("Main images:")
                for i, img in enumerate(main_images[:3], 1):
                    print(f"  {i}. {img[:60]}...")
            
            print()
            print("✅ TEST COMPLETED SUCCESSFULLY!")
            
        else:
            print("❌ No products extracted")
            
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        try:
            scraper.cleanup()
        except:
            pass

if __name__ == "__main__":
    test_amazon_variant_extraction()
