#!/usr/bin/env python3
"""
Remove duplicate products from products.json based on source URL
"""

import json
import os
from datetime import datetime
from collections import defaultdict

def analyze_duplicates():
    """Analyze duplicate patterns in the products file"""
    
    print("🔍 ANALYZING DUPLICATE PRODUCTS")
    print("=" * 50)
    
    json_file = "scraped_data/products.json"
    if not os.path.exists(json_file):
        print("❌ products.json not found!")
        return None
    
    # Load all products
    print("📖 Loading products...")
    with open(json_file, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    print(f"📊 Total products loaded: {len(products):,}")
    
    # Track products by source URL
    url_to_products = defaultdict(list)
    products_without_url = []
    
    for i, product in enumerate(products):
        source_url = product.get('source_url', '').strip()
        if source_url:
            # Clean URL (remove query parameters for better matching)
            clean_url = source_url.split('?')[0]  # Remove query parameters
            url_to_products[clean_url].append((i, product))
        else:
            products_without_url.append((i, product))
    
    # Analyze duplicates
    duplicate_urls = {url: prods for url, prods in url_to_products.items() if len(prods) > 1}
    unique_urls = {url: prods for url, prods in url_to_products.items() if len(prods) == 1}
    
    print(f"\n📈 DUPLICATE ANALYSIS:")
    print(f"   🔗 Unique URLs: {len(unique_urls):,}")
    print(f"   🔄 URLs with duplicates: {len(duplicate_urls):,}")
    print(f"   ❓ Products without URL: {len(products_without_url):,}")
    
    # Calculate total duplicates
    total_duplicates = sum(len(prods) - 1 for prods in duplicate_urls.values())
    print(f"   🗑️  Total duplicate products: {total_duplicates:,}")
    print(f"   ✅ Products after cleanup: {len(products) - total_duplicates:,}")
    print(f"   📉 Space savings: {total_duplicates / len(products) * 100:.1f}%")
    
    # Show examples of duplicates
    print(f"\n🔍 DUPLICATE EXAMPLES (Top 10):")
    print("-" * 50)
    
    sorted_duplicates = sorted(duplicate_urls.items(), key=lambda x: len(x[1]), reverse=True)
    for i, (url, prods) in enumerate(sorted_duplicates[:10]):
        product_name = prods[0][1].get('product_name', 'Unknown')[:60]
        print(f"   {i+1}. {len(prods)} copies: {product_name}...")
        print(f"      URL: {url[:80]}...")
        
        # Show difference in timestamps if available
        timestamps = []
        for _, prod in prods:
            scraped_at = prod.get('scraped_at', '')
            if scraped_at:
                timestamps.append(scraped_at)
        
        if len(set(timestamps)) > 1:
            print(f"      Scraped at different times: {min(timestamps)} to {max(timestamps)}")
        
        print()
    
    return {
        'total_products': len(products),
        'unique_urls': len(unique_urls),
        'duplicate_urls': len(duplicate_urls),
        'products_without_url': len(products_without_url),
        'total_duplicates': total_duplicates,
        'products_after_cleanup': len(products) - total_duplicates,
        'duplicate_data': duplicate_urls,
        'unique_data': unique_urls,
        'no_url_data': products_without_url
    }

def remove_duplicates(strategy='keep_latest'):
    """Remove duplicate products using specified strategy"""
    
    print(f"\n🗑️  REMOVING DUPLICATES (Strategy: {strategy})")
    print("=" * 50)
    
    json_file = "scraped_data/products.json"
    
    # Load products
    with open(json_file, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    original_count = len(products)
    print(f"📊 Original products: {original_count:,}")
    
    # Group by source URL
    url_to_products = defaultdict(list)
    products_without_url = []
    
    for i, product in enumerate(products):
        source_url = product.get('source_url', '').strip()
        if source_url:
            # Clean URL (remove query parameters and fragments)
            clean_url = source_url.split('?')[0].split('#')[0]
            url_to_products[clean_url].append(product)
        else:
            products_without_url.append(product)
    
    # Apply deduplication strategy
    unique_products = []
    duplicates_removed = 0
    
    for url, prods in url_to_products.items():
        if len(prods) == 1:
            # No duplicates, keep the product
            unique_products.extend(prods)
        else:
            # Multiple products with same URL, apply strategy
            if strategy == 'keep_latest':
                # Keep the product with the latest scraped_at timestamp
                sorted_prods = sorted(prods, key=lambda p: p.get('scraped_at', ''), reverse=True)
                unique_products.append(sorted_prods[0])
                duplicates_removed += len(prods) - 1
                
            elif strategy == 'keep_most_complete':
                # Keep the product with most complete data (most fields filled)
                def completeness_score(product):
                    score = 0
                    for field, value in product.items():
                        if value and value != '' and value != 0 and value != []:
                            if field == 'variants' and isinstance(value, list):
                                score += len(value) * 2  # Variants are valuable
                            elif field in ['product_images', 'additional_images'] and isinstance(value, list):
                                score += len(value)  # Images are valuable
                            elif field in ['product_description', 'product_name']:
                                score += len(str(value)) // 10  # Longer descriptions are better
                            else:
                                score += 1
                    return score
                
                best_product = max(prods, key=completeness_score)
                unique_products.append(best_product)
                duplicates_removed += len(prods) - 1
                
            elif strategy == 'keep_first':
                # Keep the first product (by order in file)
                unique_products.append(prods[0])
                duplicates_removed += len(prods) - 1
    
    # Add products without URLs (keep all since we can't deduplicate them)
    unique_products.extend(products_without_url)
    
    final_count = len(unique_products)
    
    print(f"✅ Products after deduplication: {final_count:,}")
    print(f"🗑️  Duplicates removed: {duplicates_removed:,}")
    print(f"📉 Reduction: {duplicates_removed / original_count * 100:.1f}%")
    
    return unique_products

def backup_and_save_cleaned_data(unique_products):
    """Backup original file and save cleaned data"""
    
    print(f"\n💾 SAVING CLEANED DATA")
    print("=" * 30)
    
    json_file = "scraped_data/products.json"
    
    # Create backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"scraped_data/products_backup_before_dedup_{timestamp}.json"
    
    print(f"📦 Creating backup: {backup_file}")
    os.rename(json_file, backup_file)
    
    # Save cleaned data
    print(f"💾 Saving {len(unique_products):,} unique products...")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(unique_products, f, indent=2, ensure_ascii=False)
    
    # Verify file sizes
    original_size = os.path.getsize(backup_file) / (1024 * 1024)
    new_size = os.path.getsize(json_file) / (1024 * 1024)
    
    print(f"📊 File size comparison:")
    print(f"   Original: {original_size:.2f} MB")
    print(f"   Cleaned:  {new_size:.2f} MB")
    print(f"   Saved:    {original_size - new_size:.2f} MB ({(original_size - new_size) / original_size * 100:.1f}%)")
    
    return backup_file

def update_csv_file(unique_products):
    """Update the CSV file to match the cleaned JSON"""
    
    print(f"\n📊 UPDATING CSV FILE")
    print("=" * 30)
    
    csv_file = "scraped_data/products.csv"
    
    if os.path.exists(csv_file):
        # Backup CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_backup = f"scraped_data/products_backup_before_dedup_{timestamp}.csv"
        os.rename(csv_file, csv_backup)
        print(f"📦 CSV backup created: {csv_backup}")
    
    # Write new CSV
    if unique_products:
        import csv
        
        print(f"💾 Writing {len(unique_products):,} products to CSV...")
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            # Get all possible fieldnames
            fieldnames = set()
            for product in unique_products[:100]:  # Sample first 100 to get fieldnames
                fieldnames.update(product.keys())
            
            fieldnames = sorted(list(fieldnames))
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for i, product in enumerate(unique_products):
                # Convert lists to JSON strings for CSV
                csv_row = {}
                for key, value in product.items():
                    if isinstance(value, (list, dict)):
                        csv_row[key] = json.dumps(value, ensure_ascii=False)
                    else:
                        csv_row[key] = value
                writer.writerow(csv_row)
                
                if (i + 1) % 10000 == 0:
                    print(f"   Written {i + 1:,} products...")
        
        new_csv_size = os.path.getsize(csv_file) / (1024 * 1024)
        print(f"✅ CSV updated: {new_csv_size:.2f} MB")

def main():
    """Main deduplication process"""
    
    print("🧹 PRODUCT DEDUPLICATION TOOL")
    print("=" * 60)
    print("This tool removes duplicate products based on source URL")
    print()
    
    # Step 1: Analyze current duplicates
    analysis = analyze_duplicates()
    if not analysis:
        return False
    
    if analysis['total_duplicates'] == 0:
        print("✅ No duplicates found! Your data is already clean.")
        return True
    
    # Ask user for strategy
    print(f"\n🤔 DEDUPLICATION STRATEGY:")
    print("1. keep_latest - Keep the most recently scraped version")
    print("2. keep_most_complete - Keep the version with most complete data")
    print("3. keep_first - Keep the first occurrence")
    print()
    
    strategy_map = {
        '1': 'keep_latest',
        '2': 'keep_most_complete', 
        '3': 'keep_first'
    }
    
    print("Recommended: Option 2 (keep_most_complete) for best data quality")
    choice = input("Enter your choice (1/2/3) or press Enter for recommended: ").strip()
    
    if choice in strategy_map:
        strategy = strategy_map[choice]
    else:
        strategy = 'keep_most_complete'  # Default
    
    print(f"Selected strategy: {strategy}")
    
    # Confirm before proceeding
    savings = analysis['total_duplicates'] / analysis['total_products'] * 100
    print(f"\n⚠️  This will remove {analysis['total_duplicates']:,} duplicate products ({savings:.1f}% reduction)")
    print("The original file will be backed up before making changes.")
    
    confirm = input("\nProceed with deduplication? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Deduplication cancelled.")
        return False
    
    # Step 2: Remove duplicates
    unique_products = remove_duplicates(strategy)
    
    # Step 3: Backup and save
    backup_file = backup_and_save_cleaned_data(unique_products)
    
    # Step 4: Update CSV
    update_csv_file(unique_products)
    
    print(f"\n🎉 DEDUPLICATION COMPLETE!")
    print("=" * 50)
    print(f"✅ Removed {analysis['total_duplicates']:,} duplicate products")
    print(f"✅ {len(unique_products):,} unique products remain")
    print(f"✅ Original files backed up safely")
    print(f"✅ Both JSON and CSV files updated")
    print(f"\n📂 Backup files created:")
    print(f"   - {backup_file}")
    print(f"\n🚀 Your chunking system will be much more efficient now!")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n💡 TIP: Restart your app to rebuild chunks with the cleaned data")
    else:
        print("\n❌ Deduplication process failed or was cancelled")
