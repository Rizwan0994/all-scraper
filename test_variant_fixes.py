#!/usr/bin/env python3
"""
🧪 TEST VARIANT FIXES
Test script to verify that our variant extraction fixes work correctly
"""

import json
import re
from scraper.universal_scraper import UniversalScraper

def test_variant_name_cleaning():
    """Test the new variant name cleaning functionality"""
    print("🧪 TESTING VARIANT NAME CLEANING")
    print("=" * 50)
    
    # Create a scraper instance to test the cleaning method
    scraper = UniversalScraper()
    
    # Test cases with problematic variant names
    test_cases = [
        "$9.98\n$15.99",  # Pricing with newlines
        "See available options",  # Placeholder text
        "$9.99\n$15.99",  # Another pricing artifact
        "Black",  # Good variant name
        "Large",  # Good variant name
        "128GB",  # Good variant name
        "Select",  # Placeholder
        "Choose",  # Placeholder
        "Quantity",  # Should be filtered
        "Qty 1+",  # Should be filtered
        "Limited time deal",  # Should be filtered
        "73% off",  # Should be filtered
    ]
    
    print("Testing variant name cleaning:")
    for test_case in test_cases:
        cleaned = scraper._clean_variant_name(test_case)
        status = "✅ CLEANED" if cleaned else "❌ FILTERED"
        print(f"  '{test_case}' → '{cleaned}' {status}")
    
    print()

def test_sku_generation():
    """Test the new unique SKU generation"""
    print("🧪 TESTING SKU GENERATION")
    print("=" * 50)
    
    scraper = UniversalScraper()
    
    # Test SKU generation for different variants
    test_variants = [
        ("PROD1", 1, "color"),
        ("PROD1", 2, "color"),
        ("PROD1", 3, "size"),
        ("PROD1", 4, "storage"),
        ("PROD2", 1, "color"),
        ("PROD2", 2, "size"),
    ]
    
    print("Testing unique SKU generation:")
    skus = []
    for product_id, index, variant_type in test_variants:
        sku = scraper._generate_unique_variant_sku(product_id, index, variant_type)
        skus.append(sku)
        print(f"  Product: {product_id}, Index: {index}, Type: {variant_type} → SKU: {sku}")
    
    # Check for uniqueness
    unique_skus = set(skus)
    if len(unique_skus) == len(skus):
        print("✅ All SKUs are unique!")
    else:
        print("❌ Duplicate SKUs found!")
    
    print()

def test_variant_type_detection():
    """Test the enhanced variant type detection"""
    print("🧪 TESTING VARIANT TYPE DETECTION")
    print("=" * 50)
    
    scraper = UniversalScraper()
    
    # Test cases for variant type detection
    test_cases = [
        ("variation_color_name", ["a-button"], "Black"),
        ("variation_size_name", ["a-button"], "Large"),
        ("variation_storage_name", ["a-button"], "128GB"),
        ("variation_style_name", ["a-button"], "Premium"),
        ("", [], "Red"),
        ("", [], "Small"),
        ("", [], "256GB"),
    ]
    
    print("Testing variant type detection:")
    for container_id, container_class, variant_text in test_cases:
        variant_type = scraper._detect_variant_type(container_id, container_class, variant_text)
        print(f"  Container: {container_id}, Text: '{variant_text}' → Type: {variant_type}")
    
    print()

def analyze_existing_data():
    """Analyze existing data to see the current issues"""
    print("🔍 ANALYZING EXISTING DATA")
    print("=" * 50)
    
    try:
        with open('scraped_data/products.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📊 Loaded {len(data)} products")
        
        # Find products with variants
        products_with_variants = [p for p in data if p.get('variants')]
        print(f"📦 Products with variants: {len(products_with_variants)}")
        
        if products_with_variants:
            # Analyze the first product with variants
            product = products_with_variants[0]
            print(f"\n🎯 ANALYZING FIRST PRODUCT WITH VARIANTS:")
            print(f"   Product: {product['product_name'][:50]}...")
            print(f"   Unit Price: ${product['unit_price']}")
            print(f"   Variants: {len(product['variants'])}")
            
            print(f"\n📦 VARIANT ANALYSIS:")
            for i, variant in enumerate(product['variants'], 1):
                print(f"   Variant {i}:")
                print(f"      Type: {variant.get('type', 'MISSING')}")
                print(f"      Name: {variant.get('name', 'MISSING')}")
                print(f"      Price: {variant.get('price', 'MISSING')}")
                print(f"      Stock: {variant.get('stock', 'MISSING')}")
                print(f"      SKU: {variant.get('sku', 'MISSING')}")
                print(f"      Images: {len(variant.get('images', []))}")
                print(f"      Attributes: {variant.get('attributes', {})}")
                print()
            
            # Check for issues
            print(f"🔍 ISSUE ANALYSIS:")
            
            # Check for pricing artifacts in names
            pricing_artifacts = [v for v in product['variants'] if '$' in v.get('name', '')]
            print(f"   Variants with pricing artifacts: {len(pricing_artifacts)}")
            
            # Check for placeholder text
            placeholders = [v for v in product['variants'] if 'see available options' in v.get('name', '').lower()]
            print(f"   Variants with placeholder text: {len(placeholders)}")
            
            # Check for duplicate SKUs
            skus = [v.get('sku') for v in product['variants']]
            unique_skus = set(skus)
            print(f"   Total SKUs: {len(skus)}, Unique SKUs: {len(unique_skus)}")
            if len(skus) != len(unique_skus):
                print(f"   ❌ DUPLICATE SKUs found!")
            else:
                print(f"   ✅ All SKUs are unique")
            
            # Check for single images
            single_image_variants = [v for v in product['variants'] if len(v.get('images', [])) <= 1]
            print(f"   Variants with single/no images: {len(single_image_variants)}")
            
    except Exception as e:
        print(f"❌ Error analyzing data: {e}")

def main():
    """Run all tests"""
    print("🚀 TESTING VARIANT EXTRACTION FIXES")
    print("=" * 60)
    print()
    
    # Run all tests
    test_variant_name_cleaning()
    test_sku_generation()
    test_variant_type_detection()
    analyze_existing_data()
    
    print("🎉 TESTING COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    main()
