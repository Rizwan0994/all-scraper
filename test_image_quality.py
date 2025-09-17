#!/usr/bin/env python3
"""
Test Image Quality Improvements
"""

def test_image_conversions():
    """Test the new image quality conversion"""
    
    # Test URLs from your products.json
    test_urls = [
        # Low-res thumbnails that should be converted
        "https://m.media-amazon.com/images/I/31uRe+IN88L._AC_US40_.jpg",
        "https://m.media-amazon.com/images/I/51TYKTkfD8L.SS40_PKmb-play-button-overlay-thumb_.jpg", 
        "https://m.media-amazon.com/images/I/41ymWIBCajL._AC_US40_.jpg",
        
        # Already high-res images
        "https://m.media-amazon.com/images/I/415h+DapoEL._AC_SX679_.jpg",
        "https://m.media-amazon.com/images/I/41O7kMijfKL._AC_SX679_.jpg"
    ]
    
    print("🔍 Testing Image Quality Conversion")
    print("=" * 60)
    
    # Import the conversion function
    import sys
    import os
    sys.path.insert(0, os.path.abspath('.'))
    from scraper.universal_scraper import UniversalScraper
    
    scraper = UniversalScraper()
    
    for url in test_urls:
        converted = scraper._convert_to_high_quality_image(url)
        
        print(f"\n📷 Original:  {url}")
        print(f"✨ Enhanced: {converted}")
        
        # Check if conversion was successful
        if '_AC_US40_' in url and '_AC_SX679_' in converted:
            print("✅ SUCCESS: Thumbnail converted to high-res!")
        elif '_SS40_' in url and '_AC_SX679_' in converted:
            print("✅ SUCCESS: Small image converted to high-res!")
        elif '_AC_SX679_' in url and url == converted:
            print("✅ SUCCESS: Already high-res, no change needed!")
        else:
            print("❌ ISSUE: Conversion may not have worked properly")
    
    print("\n🎯 Expected Results:")
    print("- All _AC_US40_ images → _AC_SX679_ (679px width)")
    print("- All _SS40_ images → _AC_SX679_ (679px width)")  
    print("- Already high-res images → unchanged")
    print("- Better variant image distribution")

if __name__ == "__main__":
    test_image_conversions()
