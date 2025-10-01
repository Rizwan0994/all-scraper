#!/usr/bin/env python3
"""
Variant Data Cleaning Script
============================

This script fixes problematic variant data in products.json:
1. Creates backup copy (products_backup.json)
2. Cleans generic variant names like "Price Hidden"
3. Generates unique SKUs for each variant
4. Extracts structured attributes from variant names
5. Preserves good data while fixing bad data
6. Saves cleaned version as products_cleaned.json

Author: AI Assistant
Date: September 24, 2025
"""

import json
import re
import shutil
from datetime import datetime
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VariantDataCleaner:
    def __init__(self, input_file="scraped_data/products.json"):
        self.input_file = input_file
        self.backup_file = "scraped_data/products_backup.json"
        self.output_file = "scraped_data/products_cleaned.json"
        self.stats = {
            'total_products': 0,
            'products_with_variants': 0,
            'total_variants_before': 0,
            'total_variants_after': 0,
            'cleaned_names': 0,
            'generated_skus': 0,
            'extracted_attributes': 0,
            'issues_fixed': []
        }
        
    def create_backup(self):
        """Create backup of original products.json"""
        try:
            shutil.copy2(self.input_file, self.backup_file)
            logger.info(f"✅ Created backup: {self.backup_file}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create backup: {e}")
            return False
    
    def load_products(self):
        """Load products from JSON file"""
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                products = json.load(f)
            logger.info(f"✅ Loaded {len(products)} products from {self.input_file}")
            return products
        except Exception as e:
            logger.error(f"❌ Failed to load products: {e}")
            return []
    
    def clean_variant_name(self, variant_name, product_name="", variant_index=0):
        """Clean problematic variant names"""
        original_name = variant_name
        
        # Handle generic names
        if variant_name in ["Price Hidden", "price hidden", "Price hidden"]:
            # Try to generate meaningful name from product
            if "headphones" in product_name.lower():
                cleaned_name = "Default"
            elif "jeans" in product_name.lower():
                cleaned_name = "Standard Fit"
            else:
                cleaned_name = f"Option {variant_index + 1}"
            self.stats['issues_fixed'].append(f"Generic name: '{original_name}' → '{cleaned_name}'")
            return cleaned_name
        
        # Handle aggregated option text like "9 options from $101.12"
        options_pattern = r'^(\d+)\s+options?\s+from\s+\$[\d,]+\.?\d*$'
        if re.match(options_pattern, variant_name):
            match = re.match(options_pattern, variant_name)
            option_count = match.group(1)
            cleaned_name = f"Variant {variant_index + 1}"
            self.stats['issues_fixed'].append(f"Aggregated text: '{original_name}' → '{cleaned_name}'")
            return cleaned_name
        
        # Remove prices from variant names
        price_pattern = r'\$[\d,]+\.?\d*'
        if re.search(price_pattern, variant_name):
            cleaned_name = re.sub(price_pattern, '', variant_name).strip()
            cleaned_name = re.sub(r'\s+', ' ', cleaned_name)  # Remove extra spaces
            cleaned_name = cleaned_name.strip('| -')  # Remove separators
            if cleaned_name and cleaned_name != variant_name:
                self.stats['issues_fixed'].append(f"Price removal: '{original_name}' → '{cleaned_name}'")
                return cleaned_name
        
        # Return original if no cleaning needed
        return variant_name
    
    def generate_unique_sku(self, product_id, variant_index, variant_name, variant_type="variant"):
        """Generate unique SKU for variant"""
        # Extract base product ID (remove prefix if exists)
        base_id = product_id.replace('amazon_', '').replace('ebay_', '').replace('etsy_', '')
        
        # Create variant suffix based on type and name
        if variant_type == "size":
            suffix = variant_name.replace(' ', '').upper()[:6]
        elif variant_type == "color":
            suffix = variant_name.replace(' ', '').upper()[:6]
        else:
            suffix = f"VAR{variant_index:03d}"
        
        # Generate unique SKU
        unique_sku = f"{base_id}-{suffix}"
        return unique_sku
    
    def extract_structured_attributes(self, variant_name, variant_type="variant"):
        """Extract structured attributes from variant name"""
        attributes = {}
        
        if not variant_name or variant_name.strip() == "":
            return attributes
        
        # Size patterns
        size_patterns = [
            (r'\b(XS|S|M|L|XL|XXL|XXXL)\b', 'Size'),
            (r'\b(\d+)\s*(?:Short|Long)\b', 'Size'),
            (r'\b(Small|Medium|Large|Extra Large)\b', 'Size'),
        ]
        
        # Color patterns  
        color_patterns = [
            (r'\b(Red|Blue|Black|White|Green|Yellow|Pink|Purple|Orange|Brown|Gray|Grey|Silver|Gold|Navy|Maroon)\b', 'Color'),
        ]
        
        # Storage/Memory patterns
        tech_patterns = [
            (r'\b(\d+)\s*GB\b(?!\s+Storage)', 'RAM'),
            (r'\b(\d+)\s*GB\s+(?:Storage|SSD|storage)\b', 'Storage'),
        ]
        
        # Apply patterns
        all_patterns = [
            (size_patterns, 'Size'),
            (color_patterns, 'Color'), 
            (tech_patterns, 'Tech')
        ]
        
        for pattern_group, group_type in all_patterns:
            for pattern, attr_name in pattern_group:
                matches = re.findall(pattern, variant_name, re.IGNORECASE)
                if matches:
                    attributes[attr_name] = matches[0]
        
        # If variant_type is specific, use it
        if variant_type in ['size', 'color', 'storage'] and not attributes:
            attr_name = variant_type.title()
            attributes[attr_name] = variant_name
        
        # If no structured attributes found, keep as generic
        if not attributes and variant_name not in ["Price Hidden", "Default"]:
            # Only add as variant if it's meaningful
            if len(variant_name) < 50 and not re.search(r'options? from', variant_name):
                attributes['Option'] = variant_name
        
        return attributes
    
    def clean_variant(self, variant, product_id, product_name, variant_index):
        """Clean a single variant"""
        cleaned = variant.copy()
        changes_made = False
        
        # Clean variant name
        original_name = variant.get('name', '')
        cleaned_name = self.clean_variant_name(original_name, product_name, variant_index)
        if cleaned_name != original_name:
            cleaned['name'] = cleaned_name
            changes_made = True
            self.stats['cleaned_names'] += 1
        
        # Generate unique SKU
        variant_type = variant.get('type', 'variant')
        new_sku = self.generate_unique_sku(product_id, variant_index, cleaned_name, variant_type)
        if new_sku != variant.get('sku', ''):
            cleaned['sku'] = new_sku
            changes_made = True
            self.stats['generated_skus'] += 1
        
        # Extract structured attributes
        new_attributes = self.extract_structured_attributes(cleaned_name, variant_type)
        if new_attributes:
            # Replace generic attributes with structured ones
            old_attributes = variant.get('attributes', {})
            
            # Keep existing good attributes, add new structured ones
            final_attributes = {}
            
            # Add structured attributes
            final_attributes.update(new_attributes)
            
            # Keep existing non-generic attributes
            for key, value in old_attributes.items():
                if key not in ['variant'] and key not in final_attributes:
                    # Only keep if it's not generic text
                    if not re.search(r'options? from|\$\d+|Price Hidden', str(value)):
                        final_attributes[key] = value
            
            if final_attributes != old_attributes:
                cleaned['attributes'] = final_attributes
                changes_made = True
                self.stats['extracted_attributes'] += 1
        
        return cleaned, changes_made
    
    def clean_product_variants(self, product):
        """Clean all variants for a single product"""
        if 'variants' not in product or not product['variants']:
            return product, False
        
        product_id = product.get('product_id', 'unknown')
        product_name = product.get('product_name', '')
        variants = product['variants']
        
        cleaned_product = product.copy()
        cleaned_variants = []
        product_changed = False
        
        for i, variant in enumerate(variants):
            cleaned_variant, changed = self.clean_variant(
                variant, product_id, product_name, i
            )
            cleaned_variants.append(cleaned_variant)
            if changed:
                product_changed = True
        
        cleaned_product['variants'] = cleaned_variants
        return cleaned_product, product_changed
    
    def process_all_products(self, products):
        """Process all products and clean their variants"""
        cleaned_products = []
        
        self.stats['total_products'] = len(products)
        
        for product in products:
            if 'variants' in product and product['variants']:
                self.stats['products_with_variants'] += 1
                self.stats['total_variants_before'] += len(product['variants'])
                
                cleaned_product, changed = self.clean_product_variants(product)
                cleaned_products.append(cleaned_product)
                
                self.stats['total_variants_after'] += len(cleaned_product['variants'])
                
                if changed:
                    logger.info(f"✅ Cleaned variants for: {product.get('product_name', 'Unknown')[:50]}...")
            else:
                # No variants, keep as-is
                cleaned_products.append(product)
        
        return cleaned_products
    
    def save_cleaned_products(self, products):
        """Save cleaned products to output file"""
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(products, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Saved cleaned data to: {self.output_file}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save cleaned data: {e}")
            return False
    
    def print_statistics(self):
        """Print cleaning statistics"""
        print("\n" + "="*60)
        print("🧹 VARIANT DATA CLEANING RESULTS")
        print("="*60)
        print(f"📊 Total products processed: {self.stats['total_products']}")
        print(f"📦 Products with variants: {self.stats['products_with_variants']}")
        print(f"🔧 Variants before cleaning: {self.stats['total_variants_before']}")
        print(f"✨ Variants after cleaning: {self.stats['total_variants_after']}")
        print(f"📝 Variant names cleaned: {self.stats['cleaned_names']}")
        print(f"🆔 Unique SKUs generated: {self.stats['generated_skus']}")  
        print(f"🏷️ Attributes extracted: {self.stats['extracted_attributes']}")
        
        if self.stats['issues_fixed']:
            print(f"\n🔧 Issues Fixed ({len(self.stats['issues_fixed'])} total):")
            for i, issue in enumerate(self.stats['issues_fixed'][:10]):  # Show first 10
                print(f"  {i+1}. {issue}")
            if len(self.stats['issues_fixed']) > 10:
                print(f"  ... and {len(self.stats['issues_fixed']) - 10} more")
        
        print("\n📁 Files created:")
        print(f"  • Backup: {self.backup_file}")
        print(f"  • Cleaned: {self.output_file}")
        print("="*60)
    
    def run(self):
        """Run the complete cleaning process"""
        logger.info("🧹 Starting variant data cleaning process...")
        
        # Step 1: Create backup
        if not self.create_backup():
            return False
        
        # Step 2: Load products
        products = self.load_products()
        if not products:
            return False
        
        # Step 3: Process and clean
        logger.info("🔧 Processing and cleaning variant data...")
        cleaned_products = self.process_all_products(products)
        
        # Step 4: Save results
        if not self.save_cleaned_products(cleaned_products):
            return False
        
        # Step 5: Show statistics
        self.print_statistics()
        
        logger.info("✅ Variant data cleaning completed successfully!")
        return True

def main():
    """Main execution function"""
    print("🧹 VARIANT DATA CLEANING SCRIPT")
    print("="*50)
    
    # Initialize cleaner
    cleaner = VariantDataCleaner()
    
    # Run cleaning process
    success = cleaner.run()
    
    if success:
        print("\n🎉 All done! Your variant data has been cleaned.")
        print("📋 Next steps:")
        print("  1. Review products_cleaned.json")
        print("  2. If satisfied, replace products.json")  
        print("  3. Run database insertion with clean data")
    else:
        print("\n❌ Cleaning process failed. Check logs for details.")

if __name__ == "__main__":
    main()