#!/usr/bin/env python3
"""
🔧 SIMPLE VARIANT LOGIC TEST
Tests the variant extraction logic without selenium driver issues
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_variant_logic():
    """Test the variant extraction logic directly"""
    print("🔧 TESTING VARIANT EXTRACTION LOGIC")
    print("=" * 60)
    
    # Test the _parse_price method
    from amazon_variant_extractor import AmazonVariantExtractor
    
    # Create a mock extractor (without driver for now)
    class MockExtractor(AmazonVariantExtractor):
        def __init__(self):
            pass  # Skip driver initialization
    
    extractor = MockExtractor()
    
    # Test price parsing
    print("\n💰 Testing price parsing:")
    test_prices = [
        "$12.99",
        "$1,299.99", 
        "£15.50",
        "€20.00",
        "$19.98",
        "Price: $25.99",
        "Sale: $30.00",
        "$invalid",
        "",
        None
    ]
    
    for price_text in test_prices:
        try:
            parsed = extractor._parse_price(price_text)
            print(f"   '{price_text}' -> ${parsed}")
        except Exception as e:
            print(f"   '{price_text}' -> ERROR: {e}")
    
    # Test variant type detection
    print("\n🏷️ Testing variant type detection:")
    test_cases = [
        ("color-black", "button-color", "Black"),
        ("size-large", "size-selector", "Large"), 
        ("storage-128gb", "storage-button", "128GB"),
        ("variant-red", "color-swatch", "Red Color"),
        ("", "", "iPhone 15 Pro Max")
    ]
    
    for element_id, element_class, variant_text in test_cases:
        try:
            variant_type = extractor._detect_variant_type(element_id, element_class, variant_text)
            print(f"   ID:'{element_id}' Class:'{element_class}' Text:'{variant_text}' -> {variant_type}")
        except Exception as e:
            print(f"   ERROR: {e}")
    
    # Test attribute extraction logic that was missing
    print("\n📋 Testing additional info extraction:")
    test_elements = [
        {"class": "color-swatch-button", "data-value": "black", "name": "Space Black"},
        {"class": "size-button-large", "data-value": "L", "name": "Large"},
        {"class": "storage-128gb", "data-value": "128", "name": "128GB"},
        {"class": "variant-button", "data-value": "", "name": "Standard"}
    ]
    
    for element_data in test_elements:
        try:
            # Simulate the additional_info extraction logic
            additional_info = {}
            element_class = element_data.get('class', '')
            data_value = element_data.get('data-value', '')
            variant_name = element_data.get('name', '')
            
            # Extract additional variant attributes (fixed logic)
            if any(color_indicator in element_class.lower() for color_indicator in ['color', 'swatch']):
                additional_info['color'] = variant_name
            elif any(size_indicator in element_class.lower() for size_indicator in ['size']):
                additional_info['size'] = variant_name
            elif any(storage_indicator in variant_name.lower() for storage_indicator in ['gb', 'tb', 'storage']):
                additional_info['storage'] = variant_name
            
            # Add data attributes
            if data_value:
                additional_info['data_value'] = data_value
                
            print(f"   Element: {element_data['name']} -> Attributes: {additional_info}")
            
        except Exception as e:
            print(f"   ERROR with {element_data}: {e}")
    
    print("\n✅ Logic test completed!")
    return True

if __name__ == "__main__":
    test_variant_logic()
