#!/usr/bin/env python3
"""
Chunk Manager for Large Product Data
Handles splitting and managing product chunks for efficient loading
"""

import json
import os
import math
import shutil
from datetime import datetime
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ChunkManager:
    def __init__(self, chunk_size=5000, chunks_dir="scraped_data/chunks"):
        self.chunk_size = chunk_size
        self.chunks_dir = chunks_dir
        self.cache_dir = "scraped_data/cache"
        self.index_file = os.path.join(chunks_dir, "index.json")
        self.temp_products = []  # Buffer for new products
        
        # Create directories
        os.makedirs(self.chunks_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def initialize_from_existing(self):
        """Initialize chunks from existing products.json file"""
        json_file = "scraped_data/products.json"
        
        if not os.path.exists(json_file):
            logger.info("No existing products.json found. Starting with empty chunks.")
            self._create_empty_index()
            return
        
        # Check if already chunked
        if os.path.exists(self.index_file):
            logger.info("Chunks already exist. Checking if update needed...")
            return self._check_and_update_chunks()
        
        logger.info("Converting existing products.json to chunks...")
        self._convert_json_to_chunks()
    
    def add_products(self, new_products: List[Dict[str, Any]]):
        """Add new products to the chunk system (called by scraper) with deduplication"""
        # Filter out duplicates before adding to temp products
        filtered_products = self._filter_duplicates(new_products)
        
        if filtered_products:
            self.temp_products.extend(filtered_products)
            logger.info(f"Added {len(filtered_products)} new products (filtered {len(new_products) - len(filtered_products)} duplicates)")
        
        # If we have enough products, create a new chunk or append to existing
        if len(self.temp_products) >= 100:  # Process in batches of 100
            self._process_temp_products()
    
    def _filter_duplicates(self, new_products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out duplicate products by checking against existing products in chunks"""
        if not new_products:
            return []
        
        # Load existing product URLs for deduplication
        existing_urls = self._get_existing_product_urls()
        
        filtered_products = []
        duplicates_found = 0
        
        for product in new_products:
            source_url = product.get('source_url', '').strip()
            product_name = product.get('product_name', '').strip().lower()
            
            # Skip if URL already exists
            if source_url in existing_urls:
                duplicates_found += 1
                logger.debug(f"Duplicate URL skipped: {product.get('product_name', 'Unknown')[:50]}...")
                continue
            
            # Additional check for similar product names from same site
            is_duplicate = False
            for existing_url, existing_name in existing_urls.items():
                if (product_name == existing_name.lower() and 
                    product.get('source_site') == self._get_site_from_url(existing_url)):
                    is_duplicate = True
                    duplicates_found += 1
                    logger.debug(f"Duplicate product name skipped: {product.get('product_name', 'Unknown')[:50]}...")
                    break
            
            if not is_duplicate:
                filtered_products.append(product)
        
        if duplicates_found > 0:
            logger.info(f"Filtered out {duplicates_found} duplicate products")
        
        return filtered_products
    
    def _get_existing_product_urls(self) -> Dict[str, str]:
        """Get all existing product URLs and names from chunks for deduplication"""
        existing_urls = {}
        
        try:
            index = self._load_or_create_index()
            
            for chunk_info in index.get("chunks", []):
                chunk_path = os.path.join(self.chunks_dir, chunk_info["file"])
                
                if os.path.exists(chunk_path):
                    with open(chunk_path, 'r', encoding='utf-8') as f:
                        chunk_data = json.load(f)
                    
                    for product in chunk_data.get("products", []):
                        source_url = product.get('source_url', '').strip()
                        product_name = product.get('product_name', '').strip()
                        if source_url:
                            existing_urls[source_url] = product_name
                            
        except Exception as e:
            logger.warning(f"Error loading existing URLs for deduplication: {e}")
        
        return existing_urls
    
    def _get_site_from_url(self, url: str) -> str:
        """Extract site name from URL"""
        if 'amazon.com' in url:
            return 'Amazon'
        elif 'ebay.com' in url:
            return 'eBay'
        elif 'daraz.pk' in url:
            return 'Daraz'
        elif 'aliexpress.com' in url:
            return 'AliExpress'
        elif 'etsy.com' in url:
            return 'Etsy'
        elif 'valuebox.pk' in url:
            return 'ValueBox'
        return 'Unknown'

    def _process_temp_products(self):
        """Process temporary products and add to chunks"""
        if not self.temp_products:
            return
        
        try:
            index = self._load_or_create_index()
            
            # Get the current last chunk
            if index["chunks"]:
                last_chunk_info = index["chunks"][-1]
                last_chunk_path = os.path.join(self.chunks_dir, last_chunk_info["file"])
                
                # Load last chunk
                with open(last_chunk_path, 'r', encoding='utf-8') as f:
                    last_chunk_data = json.load(f)
                
                current_count = last_chunk_data["chunk_info"]["product_count"]
                
                # If last chunk has room, add products to it
                if current_count < self.chunk_size:
                    products_to_add = min(
                        len(self.temp_products), 
                        self.chunk_size - current_count
                    )
                    
                    # Add products to existing chunk
                    last_chunk_data["products"].extend(self.temp_products[:products_to_add])
                    last_chunk_data["chunk_info"]["product_count"] += products_to_add
                    last_chunk_data["chunk_info"]["end_index"] += products_to_add
                    
                    # Save updated chunk
                    with open(last_chunk_path, 'w', encoding='utf-8') as f:
                        json.dump(last_chunk_data, f, ensure_ascii=False, indent=2)
                    
                    # Remove processed products
                    self.temp_products = self.temp_products[products_to_add:]
                    
                    # Update index
                    last_chunk_info["product_count"] = last_chunk_data["chunk_info"]["product_count"]
                    last_chunk_info["product_range"][1] = last_chunk_data["chunk_info"]["end_index"]
                    
                    logger.info(f"Added {products_to_add} products to existing chunk {last_chunk_info['chunk_id']}")
            
            # Create new chunks for remaining products
            while len(self.temp_products) >= self.chunk_size:
                self._create_new_chunk()
            
            # Update index file
            self._save_index(index)
            
            # Update stats cache
            self._update_stats_cache()
            
        except Exception as e:
            logger.error(f"Error processing temp products: {e}")
    
    def _create_new_chunk(self):
        """Create a new chunk from temp products"""
        if not self.temp_products:
            return
        
        index = self._load_or_create_index()
        next_chunk_id = len(index["chunks"]) + 1
        
        # Take products for new chunk
        products_for_chunk = self.temp_products[:self.chunk_size]
        self.temp_products = self.temp_products[self.chunk_size:]
        
        # Calculate indices
        start_index = index["total_products"] + 1
        end_index = start_index + len(products_for_chunk) - 1
        
        # Create chunk data
        chunk_filename = f"chunk_{next_chunk_id:04d}.json"
        chunk_data = {
            "chunk_info": {
                "chunk_id": next_chunk_id,
                "start_index": start_index,
                "end_index": end_index,
                "product_count": len(products_for_chunk)
            },
            "products": products_for_chunk
        }
        
        # Save chunk file
        chunk_path = os.path.join(self.chunks_dir, chunk_filename)
        with open(chunk_path, 'w', encoding='utf-8') as f:
            json.dump(chunk_data, f, ensure_ascii=False, indent=2)
        
        # Add to index
        chunk_info = self._analyze_chunk(chunk_data)
        index["chunks"].append(chunk_info)
        index["total_products"] += len(products_for_chunk)
        index["total_chunks"] = len(index["chunks"])
        
        logger.info(f"Created new chunk {next_chunk_id} with {len(products_for_chunk)} products")
    
    def force_save(self):
        """Force save any pending products"""
        if self.temp_products:
            logger.info(f"Force saving {len(self.temp_products)} pending products...")
            
            # If we have pending products, add them to a chunk even if not full
            if self.temp_products:
                # Try to add to existing chunk first
                self._process_temp_products()
                
                # If still have products, create partial chunk
                if self.temp_products:
                    self._create_partial_chunk()
    
    def _create_partial_chunk(self):
        """Create a chunk with remaining products (less than chunk_size)"""
        if not self.temp_products:
            return
        
        index = self._load_or_create_index()
        next_chunk_id = len(index["chunks"]) + 1
        
        # Calculate indices
        start_index = index["total_products"] + 1
        end_index = start_index + len(self.temp_products) - 1
        
        # Create chunk data
        chunk_filename = f"chunk_{next_chunk_id:04d}.json"
        chunk_data = {
            "chunk_info": {
                "chunk_id": next_chunk_id,
                "start_index": start_index,
                "end_index": end_index,
                "product_count": len(self.temp_products)
            },
            "products": self.temp_products.copy()
        }
        
        # Save chunk file
        chunk_path = os.path.join(self.chunks_dir, chunk_filename)
        with open(chunk_path, 'w', encoding='utf-8') as f:
            json.dump(chunk_data, f, ensure_ascii=False, indent=2)
        
        # Add to index
        chunk_info = self._analyze_chunk(chunk_data)
        index["chunks"].append(chunk_info)
        index["total_products"] += len(self.temp_products)
        index["total_chunks"] = len(index["chunks"])
        
        # Clear temp products
        logger.info(f"Created partial chunk {next_chunk_id} with {len(self.temp_products)} products")
        self.temp_products = []
        
        # Save index
        self._save_index(index)
    
    def _convert_json_to_chunks(self):
        """Convert existing products.json to chunk format"""
        json_file = "scraped_data/products.json"
        
        logger.info("Loading existing products.json...")
        with open(json_file, 'r', encoding='utf-8') as f:
            all_products = json.load(f)
        
        total_products = len(all_products)
        total_chunks = math.ceil(total_products / self.chunk_size)
        
        logger.info(f"Converting {total_products:,} products into {total_chunks} chunks...")
        
        # Create backup
        backup_file = f"scraped_data/products_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        shutil.copy2(json_file, backup_file)
        logger.info(f"Backup created: {backup_file}")
        
        chunks_info = []
        
        # Create chunks
        for chunk_num in range(total_chunks):
            start_idx = chunk_num * self.chunk_size
            end_idx = min(start_idx + self.chunk_size, total_products)
            
            chunk_products = all_products[start_idx:end_idx]
            
            # Create chunk file
            chunk_filename = f"chunk_{chunk_num+1:04d}.json"
            chunk_path = os.path.join(self.chunks_dir, chunk_filename)
            
            chunk_data = {
                "chunk_info": {
                    "chunk_id": chunk_num + 1,
                    "start_index": start_idx + 1,
                    "end_index": end_idx,
                    "product_count": len(chunk_products)
                },
                "products": chunk_products
            }
            
            with open(chunk_path, 'w', encoding='utf-8') as f:
                json.dump(chunk_data, f, ensure_ascii=False, indent=2)
            
            # Collect metadata for index
            chunk_info = self._analyze_chunk(chunk_data)
            chunks_info.append(chunk_info)
            
            logger.info(f"Created {chunk_filename} ({len(chunk_products):,} products)")
        
        # Create index file
        self._create_index_file(total_products, total_chunks, chunks_info)
        
        # Create stats cache
        self._create_stats_cache(all_products)
        
        logger.info("✅ Conversion to chunks completed successfully!")
    
    def _load_or_create_index(self):
        """Load existing index or create empty one"""
        if os.path.exists(self.index_file):
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return self._create_empty_index()
    
    def _create_empty_index(self):
        """Create empty index structure"""
        index = {
            "total_products": 0,
            "total_chunks": 0,
            "products_per_chunk": self.chunk_size,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "chunks": [],
            "global_stats": {}
        }
        self._save_index(index)
        return index
    
    def _save_index(self, index):
        """Save index to file"""
        index["updated_at"] = datetime.now().isoformat()
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    
    def _analyze_chunk(self, chunk_data):
        """Analyze chunk to create metadata"""
        products = chunk_data["products"]
        
        categories = set()
        sites = set()
        prices = []
        
        for product in products:
            if product.get('category'):
                categories.add(product['category'])
            if product.get('source_site'):
                sites.add(product['source_site'])
            if product.get('unit_price'):
                try:
                    prices.append(float(product['unit_price']))
                except (ValueError, TypeError):
                    pass
        
        return {
            "chunk_id": chunk_data["chunk_info"]["chunk_id"],
            "file": f"chunk_{chunk_data['chunk_info']['chunk_id']:04d}.json",
            "product_range": [
                chunk_data["chunk_info"]["start_index"],
                chunk_data["chunk_info"]["end_index"]
            ],
            "product_count": chunk_data["chunk_info"]["product_count"],
            "categories": list(categories),
            "price_range": [min(prices) if prices else 0, max(prices) if prices else 0],
            "sites": list(sites)
        }
    
    def _create_index_file(self, total_products, total_chunks, chunks_info):
        """Create the main index file"""
        index = {
            "total_products": total_products,
            "total_chunks": total_chunks,
            "products_per_chunk": self.chunk_size,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "chunks": chunks_info,
            "global_stats": self._calculate_global_stats(chunks_info)
        }
        
        self._save_index(index)
        logger.info(f"Created index file with {total_chunks} chunks")
    
    def _calculate_global_stats(self, chunks_info):
        """Calculate global statistics from chunks"""
        all_categories = set()
        all_sites = set()
        min_price = float('inf')
        max_price = 0
        
        for chunk in chunks_info:
            all_categories.update(chunk["categories"])
            all_sites.update(chunk["sites"])
            if chunk["price_range"][0] > 0:
                min_price = min(min_price, chunk["price_range"][0])
            max_price = max(max_price, chunk["price_range"][1])
        
        return {
            "total_categories": len(all_categories),
            "total_sites": len(all_sites),
            "price_range": [min_price if min_price != float('inf') else 0, max_price],
            "categories": list(all_categories),
            "sites": list(all_sites)
        }
    
    def _create_stats_cache(self, all_products):
        """Create cached statistics"""
        stats = {
            "total_products": len(all_products),
            "categories": {},
            "sites": {},
            "avg_price": 0,
            "price_range": [0, 0],
            "created_at": datetime.now().isoformat()
        }
        
        prices = []
        for product in all_products:
            # Count categories
            category = product.get('category', 'Unknown')
            stats["categories"][category] = stats["categories"].get(category, 0) + 1
            
            # Count sites
            site = product.get('source_site', 'Unknown')
            stats["sites"][site] = stats["sites"].get(site, 0) + 1
            
            # Collect prices
            try:
                price = float(product.get('unit_price', 0))
                if price > 0:
                    prices.append(price)
            except (ValueError, TypeError):
                pass
        
        if prices:
            stats["avg_price"] = sum(prices) / len(prices)
            stats["price_range"] = [min(prices), max(prices)]
        
        # Save stats cache
        cache_file = os.path.join(self.cache_dir, "stats.json")
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        logger.info("Created statistics cache")
    
    def _update_stats_cache(self):
        """Update cached statistics"""
        # For now, we'll recalculate from index
        # In production, this could be more incremental
        try:
            index = self._load_or_create_index()
            
            # Quick stats from index
            stats = {
                "total_products": index["total_products"],
                "total_chunks": index["total_chunks"],
                "global_stats": index.get("global_stats", {}),
                "updated_at": datetime.now().isoformat()
            }
            
            cache_file = os.path.join(self.cache_dir, "stats.json")
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Error updating stats cache: {e}")
    
    def get_all_products_for_db(self):
        """Get all products in chunks for database insertion"""
        index = self._load_or_create_index()
        
        for chunk_info in index["chunks"]:
            chunk_path = os.path.join(self.chunks_dir, chunk_info["file"])
            with open(chunk_path, 'r', encoding='utf-8') as f:
                chunk_data = json.load(f)
            
            yield chunk_data["products"]  # Yield products in chunks
    
    def _check_and_update_chunks(self):
        """Check if chunks need updating based on original file"""
        json_file = "scraped_data/products.json"
        
        if not os.path.exists(json_file):
            return
        
        # Get modification times
        json_mtime = os.path.getmtime(json_file)
        index_mtime = os.path.getmtime(self.index_file)
        
        # If JSON is newer, we need to update chunks
        if json_mtime > index_mtime:
            logger.info("products.json is newer than chunks. Updating...")
            self._convert_json_to_chunks()



    def _load_products_from_csv(self):
        """Fallback method to load products from CSV file"""
        csv_file = "scraped_data/products.csv"
        if not os.path.exists(csv_file):
            return []
        
        try:
            import csv
            products = []
            
            logger.info("Loading products from CSV fallback...")
            with open(csv_file, 'r', encoding='utf-8') as f:
                csv_reader = csv.DictReader(f)
                
                for i, row in enumerate(csv_reader):
                    product = {}
                    
                    # Convert CSV row to product format
                    for key, value in row.items():
                        if value and value != '':
                            # Handle numeric fields
                            if key in ['unit_price', 'purchase_price', 'rating', 'current_stock', 'discount']:
                                try:
                                    product[key] = float(value) if '.' in str(value) else int(value)
                                except:
                                    product[key] = 0
                            # Handle list fields
                            elif key in ['product_images', 'additional_images', 'variants']:
                                if value.startswith('[') and value.endswith(']'):
                                    try:
                                        product[key] = json.loads(value)
                                    except:
                                        product[key] = []
                                else:
                                    product[key] = [value] if key != 'variants' else []
                            else:
                                product[key] = value
                    
                    # Ensure required fields
                    for field in ['product_images', 'additional_images', 'variants']:
                        if field not in product:
                            product[field] = []
                    
                    products.append(product)
                    
                    # Progress for large files
                    if (i + 1) % 10000 == 0:
                        logger.info(f"Loaded {i + 1:,} products from CSV...")
            
            logger.info(f"Successfully loaded {len(products):,} products from CSV fallback")
            return products
            
        except Exception as e:
            logger.error(f"Error loading from CSV: {e}")
            return []
    