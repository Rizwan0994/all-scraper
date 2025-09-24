#!/usr/bin/env python3
"""
🔍 TRACE FAKE VARIANT CREATION
This script will inspect the exact data that's being passed to AI verification
"""

import json

def analyze_existing_data():
    """Analyze the existing data to understand the fake variant pattern"""
    print("🔍 ANALYZING EXISTING FAKE VARIANT DATA")
    print("=" * 60)
    
    # Load the JSON data
    try:
        with open('scraped_data/products.json', 'r') as f:
            data = json.load(f)
        
        print(f"📊 Loaded {len(data)} products")
        
        # Analyze the first product's variants
        if data and data[0]['variants']:
            print(f"\n🎯 ANALYZING FIRST PRODUCT:")
            product = data[0]
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
            
            # Pattern analysis
            print(f"\n🧩 PATTERN ANALYSIS:")
            price_variants = [v for v in product['variants'] if v.get('type') == 'price']
            print(f"   Price-type variants: {len(price_variants)}")
            
            unique_prices = set(v.get('price') for v in product['variants'])
            print(f"   Unique prices: {unique_prices}")
            
            variant_names = [v.get('name') for v in product['variants']]
            print(f"   Variant names: {variant_names}")
            
            # Check if names match prices
            names_are_prices = all(name.startswith('$') for name in variant_names if name)
            print(f"   All names are prices: {names_are_prices}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    analyze_existing_data()
