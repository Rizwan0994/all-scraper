#!/usr/bin/env python3
"""
Variant Data Cleaning Report
============================

Compare before/after cleaning results and show improvements made.
"""

import json
from collections import Counter
import re

def analyze_file(filename, label):
    """Analyze variant data in a JSON file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        stats = {
            'total_products': len(products),
            'products_with_variants': 0,
            'total_variants': 0,
            'variant_names': [],
            'variant_skus': [],
            'variant_types': Counter(),
            'attribute_keys': Counter(),
            'issues': {
                'price_hidden': 0,
                'options_from': 0,
                'generic_skus': 0,
                'missing_attributes': 0
            }
        }
        
        for product in products:
            if 'variants' in product and product['variants']:
                stats['products_with_variants'] += 1
                
                for variant in product['variants']:
                    stats['total_variants'] += 1
                    
                    # Collect variant names
                    name = variant.get('name', '')
                    stats['variant_names'].append(name)
                    
                    # Collect SKUs
                    sku = variant.get('sku', '')
                    stats['variant_skus'].append(sku)
                    
                    # Count variant types
                    v_type = variant.get('type', 'unknown')
                    stats['variant_types'][v_type] += 1
                    
                    # Count attribute keys
                    attributes = variant.get('attributes', {})
                    for key in attributes.keys():
                        stats['attribute_keys'][key] += 1
                    
                    # Check for issues
                    if name == 'Price Hidden':
                        stats['issues']['price_hidden'] += 1
                    
                    if 'options from' in name:
                        stats['issues']['options_from'] += 1
                    
                    if re.match(r'^VAR-\d+$', sku):
                        stats['issues']['generic_skus'] += 1
                    
                    if not attributes or len(attributes) == 0:
                        stats['issues']['missing_attributes'] += 1
        
        print(f"\n{label.upper()} ANALYSIS")
        print("=" * 50)
        print(f"📊 Total products: {stats['total_products']}")
        print(f"📦 Products with variants: {stats['products_with_variants']}")
        print(f"🔧 Total variants: {stats['total_variants']}")
        
        print(f"\n🏷️ Variant Types:")
        for v_type, count in stats['variant_types'].most_common():
            print(f"  • {v_type}: {count}")
        
        print(f"\n📋 Attribute Keys:")
        for key, count in stats['attribute_keys'].most_common():
            print(f"  • {key}: {count}")
        
        print(f"\n⚠️ Issues Found:")
        for issue, count in stats['issues'].items():
            print(f"  • {issue.replace('_', ' ').title()}: {count}")
        
        # Show sample variant names
        unique_names = list(set(stats['variant_names']))
        print(f"\n📝 Sample Variant Names ({len(unique_names)} unique):")
        for i, name in enumerate(unique_names[:10]):
            print(f"  {i+1}. '{name}'")
        if len(unique_names) > 10:
            print(f"  ... and {len(unique_names) - 10} more")
        
        return stats
        
    except Exception as e:
        print(f"❌ Error analyzing {filename}: {e}")
        return None

def main():
    print("📊 VARIANT DATA CLEANING COMPARISON REPORT")
    print("=" * 60)
    
    # Analyze original data
    original_stats = analyze_file('scraped_data/products.json', 'BEFORE CLEANING')
    
    # Analyze cleaned data  
    cleaned_stats = analyze_file('scraped_data/products_cleaned.json', 'AFTER CLEANING')
    
    if original_stats and cleaned_stats:
        print(f"\n🎯 IMPROVEMENT SUMMARY")
        print("=" * 40)
        
        # Calculate improvements
        improvements = {}
        for issue in original_stats['issues']:
            before = original_stats['issues'][issue]
            after = cleaned_stats['issues'][issue] 
            fixed = before - after
            improvements[issue] = (before, after, fixed)
        
        for issue, (before, after, fixed) in improvements.items():
            improvement_pct = (fixed / before * 100) if before > 0 else 0
            print(f"🔧 {issue.replace('_', ' ').title()}:")
            print(f"   Before: {before} → After: {after} (Fixed: {fixed}, {improvement_pct:.1f}%)")
        
        # SKU improvements
        original_unique_skus = len(set(original_stats['variant_skus']))
        cleaned_unique_skus = len(set(cleaned_stats['variant_skus']))
        print(f"\n🆔 SKU Uniqueness:")
        print(f"   Before: {original_unique_skus}/{original_stats['total_variants']} unique")
        print(f"   After: {cleaned_unique_skus}/{cleaned_stats['total_variants']} unique")
        
        # Attribute improvements
        print(f"\n🏷️ Attribute Diversity:")
        print(f"   Before: {len(original_stats['attribute_keys'])} different attribute types")
        print(f"   After: {len(cleaned_stats['attribute_keys'])} different attribute types")

if __name__ == "__main__":
    main()