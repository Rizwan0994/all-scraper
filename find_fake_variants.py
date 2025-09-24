#!/usr/bin/env python3
"""
🚨 FIND AND FIX FAKE PRICE VARIANTS
This script will locate and disable fake price variant creation
"""

import os
import sys

def find_fake_price_variants():
    """Find where fake price variants are being created"""
    print("🚨 HUNTING FOR FAKE PRICE VARIANT CREATION")
    print("=" * 60)
    
    # Look through all python files for variant creation
    base_dir = "."
    python_files = []
    
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    print(f"📁 Scanning {len(python_files)} Python files...")
    
    # Search patterns that might create price variants
    search_patterns = [
        '"type": "price"',
        "'type': 'price'",
        "type.*price",
        "price.*type",
        "variant.*price",
        "name.*$.*price"
    ]
    
    found_files = []
    
    for python_file in python_files:
        try:
            if '__pycache__' in python_file:
                continue
                
            with open(python_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for pattern in search_patterns:
                import re
                if re.search(pattern, content, re.IGNORECASE):
                    found_files.append(python_file)
                    print(f"🎯 FOUND POTENTIAL MATCH: {python_file}")
                    # Show lines containing the pattern
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if re.search(pattern, line, re.IGNORECASE):
                            print(f"   Line {i}: {line.strip()}")
                    print()
                    break
                    
        except Exception as e:
            continue
    
    print(f"\n📊 SUMMARY:")
    print(f"   Files potentially creating price variants: {len(found_files)}")
    
    for file in found_files:
        print(f"   - {file}")
        
    return found_files

if __name__ == "__main__":
    find_fake_price_variants()
