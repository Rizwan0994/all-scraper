#!/usr/bin/env python3
"""
Database Manager for Product Insertion
Handles MySQL database operations for scraped products
"""

import mysql.connector
from mysql.connector import Error
import json
import logging
from datetime import datetime
import os
from chunk_manager import ChunkManager

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.credentials = self.load_credentials()
        # Caches to reduce DB lookups per run
        self._attribute_parent_cache = {}
        # maps parent_id -> { normalized_child_name: child_id }
        self._attribute_children_cache = {}
        # Chunk manager for efficient data loading
        self.chunk_manager = ChunkManager()
    
    def load_credentials(self):
        """Load database credentials from db-credential.tx file"""
        try:
            cred_file = "db-structure-guide/db-credential.tx"
            if os.path.exists(cred_file):
                with open(cred_file, 'r') as f:
                    lines = f.readlines()
                    credentials = {}
                    for line in lines:
                        if ':' in line:
                            key, value = line.strip().split(':', 1)
                            credentials[key.strip()] = value.strip()
                    return credentials
            return {}
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            return {}
    
    def connect(self, host=None, user=None, password=None, database=None, port=None):
        """Connect to MySQL database"""
        try:
            # Use provided credentials or fallback to file credentials
            host = host or self.credentials.get('host', 'localhost')
            user = user or self.credentials.get('user', 'scrapping')
            password = password or self.credentials.get('password', 'el6xBRHruZ5BWqGhgvGA')
            database = database or self.credentials.get('dbname', 'scrapping')
            port = port or int(self.credentials.get('port', '3306'))
            
            self.connection = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                port=port,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
            
            if self.connection.is_connected():
                logger.info(f"Connected to MySQL database: {database}")
                return True
                
        except Error as e:
            logger.error(f"Database connection error: {e}")
            if e.errno == 2003:
                logger.error("Connection refused. The server might not allow external connections or the host/port is incorrect.")
            elif e.errno == 1045:
                logger.error("Access denied. Check username and password.")
            elif e.errno == 2002:
                logger.error("Can't connect to server. Check if the server is running and accessible.")
            return False
    
    def test_connection(self, host=None, user=None, password=None, database=None, port=None):
        """Test database connection"""
        try:
            if self.connect(host, user, password, database, port):
                self.disconnect()
                return {'success': True, 'message': 'Connection successful'}
            else:
                return {'success': False, 'message': 'Connection failed'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def disconnect(self):
        """Disconnect from database"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Database connection closed")
    
    def insert_products(self, products_data, test_mode=False, connection_params=None):
        """Insert products into database"""
        try:
            logger.info(f"Starting product insertion. Total products: {len(products_data)}, Test mode: {test_mode}")
            
            # Use provided connection parameters or default to file credentials
            if connection_params:
                logger.info(f"Using provided connection parameters: {connection_params}")
                if not self.connect(**connection_params):
                    return {'success': False, 'message': 'Database connection failed with provided parameters'}
            else:
                if not self.connection or not self.connection.is_connected():
                    if not self.connect():
                        return {'success': False, 'message': 'Database connection failed'}
            
            cursor = self.connection.cursor()
            inserted_count = 0
            
            # Limit to 1 product for test mode
            if test_mode:
                products_data = products_data[:1]
                logger.info(f"Test mode: Processing only 1 product")
            
            logger.info(f"Processing {len(products_data)} products for insertion")
            
            inserted_count = 0
            updated_count = 0
            skipped_count = 0
            
            for i, product in enumerate(products_data):
                try:
                    logger.info(f"Processing product {i+1}: {product.get('product_name', 'Unknown')[:50]}...")
                    
                    # Check if product already exists
                    existing_product_id = self._check_product_exists(cursor, product)
                    
                    if existing_product_id:
                        logger.info(f"Product already exists with ID: {existing_product_id}. Updating...")
                        
                        # Update existing product
                        if self._update_existing_product(cursor, existing_product_id, product):
                            updated_count += 1
                            logger.info(f"Product {i+1} updated successfully. Total updated: {updated_count}")
                        else:
                            logger.error(f"Failed to update product: {product.get('product_name', 'Unknown')}")
                    else:
                        # Insert new product
                        product_id = self._insert_main_product(cursor, product)
                        if product_id:
                            logger.info(f"Successfully inserted new product with ID: {product_id}")
                            
                            # Insert product images
                            self._insert_product_images(cursor, product_id, product)
                            
                            # Insert product attributes
                            self._insert_product_attributes(cursor, product_id, product)
                            
                            # Insert product variations
                            self._insert_product_variations(cursor, product_id, product)
                            
                            inserted_count += 1
                            logger.info(f"Product {i+1} fully inserted. Total inserted: {inserted_count}")
                        else:
                            logger.error(f"Failed to insert main product for: {product.get('product_name', 'Unknown')}")
                        
                except Exception as e:
                    logger.error(f"Error processing product {product.get('product_name', 'Unknown')}: {e}")
                    continue
            
            self.connection.commit()
            cursor.close()
            
            return {
                'success': True, 
                'message': f'Successfully processed {len(products_data)} products: {inserted_count} inserted, {updated_count} updated',
                'count': inserted_count,
                'inserted': inserted_count,
                'updated': updated_count,
                'skipped': skipped_count
            }
            
        except Exception as e:
            logger.error(f"Error in insert_products: {e}")
            if self.connection:
                self.connection.rollback()
            return {'success': False, 'message': str(e)}
    
    def _insert_main_product(self, cursor, product):
        """Insert main product into products table"""
        try:
            logger.info(f"Inserting main product: {product.get('product_name', 'Unknown')}")
            
            # Map scraped data to database fields
            insert_query = """
            INSERT INTO products (
                name, slug, unit, min_purchase_qty, max_purchase_qty,
                meta_title, price, sku, current_stock, discount, delivery_time,
                weight, height, length, width, product_description, meta_description,
                order_count, product_reviews, disocunt_type, child_category, stock,
                status, brand, created_by, updated_by, created_at, updated_at,
                product_reviews_avg, store_id, product_reviews_sum, is_featured,
                views_count, variation_type, h1
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s
            )
            """
            
            # Generate slug from product name
            slug = product.get('product_name', '').lower().replace(' ', '-').replace(',', '').replace('.', '')[:100]
            
            # Extract delivery time (convert "24 hr(s)" to "24")
            delivery_time = product.get('standard_delivery_time', '72')
            if 'hr' in delivery_time:
                delivery_time = delivery_time.split()[0]
            
            # CRITICAL FIX: Detect variation_type from scraped data
            variation_type = self._detect_variation_type(product)
            
            values = (
                product.get('product_name', '')[:255],  # name
                slug,  # slug
                '1',  # unit
                '1',  # min_purchase_qty
                '10',  # max_purchase_qty
                product.get('product_name', '')[:255],  # meta_title
                product.get('unit_price', 0),  # price
                product.get('sku', ''),  # sku
                product.get('current_stock', 0),  # current_stock
                product.get('discount', 0),  # discount
                delivery_time,  # delivery_time
                product.get('weight', 0),  # weight
                product.get('height', 0),  # height
                product.get('length', 0),  # length
                product.get('width', 0),  # width
                product.get('product_description', ''),  # product_description
                product.get('meta_tags_description', ''),  # meta_description
                0,  # order_count
                product.get('review_count', 0),  # product_reviews
                '14',  # disocunt_type (ID 14 = Percentage)
                '26',  # child_category (default)
                '11',  # stock (ID 11 = Stock In)
                '8',  # status (ID 8 = Published)
                '16',  # brand (default)
                '1',  # created_by
                '1',  # updated_by
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # created_at
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # updated_at
                product.get('rating', 0),  # product_reviews_avg
                '1',  # store_id
                product.get('rating', 0),  # product_reviews_sum
                '0',  # is_featured
                0,  # views_count
                variation_type,  # variation_type - FIXED!
                None  # h1
            )
            
            logger.info(f"Executing insert query with values: {values[:5]}...")  # Log first 5 values
            cursor.execute(insert_query, values)
            product_id = cursor.lastrowid
            logger.info(f"Insert successful. Product ID: {product_id}")
            return product_id
            
        except Exception as e:
            logger.error(f"Error inserting main product: {e}")
            logger.error(f"Product data: {product}")
            return None
    
    def _detect_variation_type(self, product):
        """Detect variation type from scraped product data.
        
        ENHANCED LOGIC:
        - 'SINGLE': Products with no variants OR variants of only one type (e.g., only colors)
        - 'MULTIPLE': Products with variants of multiple types (e.g., colors AND sizes)
        
        Args:
            product: Product data dictionary from scraper
            
        Returns:
            'SINGLE' or 'MULTIPLE' based on actual variant analysis
        """
        try:
            variants = product.get('variants', [])
            
            if not variants:
                logger.debug("No variants found, setting to SINGLE")
                return 'SINGLE'
            
            # Group variants by type to detect multi-attribute products
            variant_types = set()
            for variant in variants:
                variant_type = variant.get('type', 'unknown')
                variant_types.add(variant_type)
            
            # If more than one variant type, it's multi-attribute
            if len(variant_types) > 1:
                logger.debug(f"Multi-attribute product detected with {len(variant_types)} types: {list(variant_types)}")
                return 'MULTIPLE'
            else:
                logger.debug(f"Single-attribute product detected with type: {list(variant_types)}")
                return 'SINGLE'
                    
        except Exception as e:
            logger.error(f"Error detecting variation type: {e}")
            return 'SINGLE'  # Default fallback
    
    def _validate_combination_format(self, combination):
        """Validate that combination matches expected database format.
        
        Expected formats:
        - Text format: "Green / Medium", "Red / 8GB"
        - Simple format: "single_combination", "default_combination"
        
        Args:
            combination: Generated combination string
            
        Returns:
            bool: True if format is valid
        """
        try:
            if not combination or not isinstance(combination, str):
                return False
            
            # Allow simple formats
            simple_formats = ['single_combination', 'default_combination']
            if combination in simple_formats:
                return True
            
            # Check text format: should contain " / " separator and no IDs
            if ' / ' in combination:
                parts = combination.split(' / ')
                # Each part should be text, not numbers or ID format
                for part in parts:
                    part = part.strip()
                    if not part:
                        return False
                    # Reject ID-based formats like "1:4"
                    if ':' in part or part.isdigit():
                        return False
                return True
            
            # Single word attributes (like colors) are also valid
            if len(combination.split()) <= 3 and ':' not in combination and '|' not in combination:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error validating combination format: {e}")
            return False
    
    def _insert_product_attributes(self, cursor, product_id, product):
        """Insert product attributes derived from product-level fields and variants.

        - Ensures attribute parents/values exist in `attributes` table
        - Inserts rows into `product_attributes` for parents (type='parent') and used values (type='child')
        """
        try:
            logger.info(f"Starting attribute insertion for product ID: {product_id}")
            # 1) Collect attribute -> set(values) from product
            attribute_to_values = self._collect_product_attribute_values(product)
            
            if not attribute_to_values:
                logger.info(f"No attributes found for product ID: {product_id}")
                return
            
            logger.info(f"Found {len(attribute_to_values)} attribute types: {list(attribute_to_values.keys())}")

            # 2) Ensure parents/values exist and insert product_attributes rows
            total_links = 0
            for attr_name, values in attribute_to_values.items():
                logger.info(f"Processing attribute '{attr_name}' with {len(values)} values: {list(values)}")
                parent_id = self._get_or_create_attribute_parent(cursor, attr_name)
                # Insert parent link (if not exists)
                self._ensure_product_attribute_link(cursor, product_id, parent_id, 'parent')
                total_links += 1

                # Insert value links
                for value_name in values:
                    child_id = self._get_or_create_attribute_value(cursor, parent_id, value_name)
                    self._ensure_product_attribute_link(cursor, product_id, child_id, 'child')
                    total_links += 1
            
            logger.info(f"Successfully created {total_links} attribute links for product ID: {product_id}")

        except Exception as e:
            logger.error(f"Error inserting product attributes: {e}")
    
    def _insert_product_variations(self, cursor, product_id, product):
        """Insert product variations - EVERY product MUST have at least one variant"""
        try:
            variants = product.get('variants', [])
            
            # REAL-WORLD E-COMMERCE RULE: Every product must have at least one variant
            if not variants:
                # Create default variant with main product details
                logger.info(f"Product has no variants, creating default variant for product_id: {product_id}")
                
                # Generate default SKU if none exists
                default_sku = product.get('sku', f"DEFAULT-{product_id}")
                if not default_sku:
                    default_sku = f"DEFAULT-{product_id}"
                
                insert_query = """
                INSERT INTO product_variations (
                    product_id, sku, purchase_price, unit_price, current_stock,
                    created_by, updated_by, created_at, updated_at, discount,
                    discount_type, combination, stock_status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                # CRITICAL FIX: Force integer conversion for stock
                default_stock = product.get('current_stock', 0)
                try:
                    default_stock = int(default_stock) if default_stock else 0
                except (ValueError, TypeError):
                    logger.warning(f"Invalid stock value '{default_stock}' for default variant, defaulting to 0")
                    default_stock = 0
                
                # CRITICAL FIX: Force float conversion for prices
                default_purchase_price = product.get('purchase_price', 0)
                default_unit_price = product.get('unit_price', 0)
                try:
                    default_purchase_price = float(default_purchase_price) if default_purchase_price else 0.0
                    default_unit_price = float(default_unit_price) if default_unit_price else 0.0
                except (ValueError, TypeError):
                    default_purchase_price = 0.0
                    default_unit_price = 0.0
                
                values = (
                    product_id,
                    default_sku,
                    default_purchase_price,
                    default_unit_price,
                    default_stock,
                    '1',  # created_by
                    '1',  # updated_by
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    product.get('discount', 0),
                    '14',  # discount_type (ID 14 = Percentage)
                    'default_combination',
                    '11'  # stock_status (ID 11 = Stock In)
                )
                cursor.execute(insert_query, values)
                variation_id = cursor.lastrowid
                logger.info(f"Created DEFAULT variant with ID: {variation_id} for product_id: {product_id}")
                
                # Insert ALL additional images to the default variant (since it's the only variant)
                additional_images = product.get('additional_images', [])
                main_images = product.get('product_images', [])
                
                # Collect all images for default variant
                all_default_images = []
                
                # Add main images (except first which is thumbnail)
                if len(main_images) > 1:
                    all_default_images.extend(main_images[1:])
                
                # Add all additional images
                if additional_images:
                    all_default_images.extend(additional_images)
                
                # Insert all collected images
                if all_default_images:
                    logger.info(f"Adding {len(all_default_images)} images to default variant")
                    self._insert_variant_images(cursor, variation_id, all_default_images, product)
                else:
                    # If no additional images, use main image as fallback
                    if main_images and main_images[0]:
                        self._insert_variant_image(cursor, variation_id, main_images[0], product)
                
            else:
                # NEW: Enhanced logic for single vs multi-attribute products
                variants = product.get('variants', [])
                variation_type = self._detect_variation_type(product)
                
                # Group variants by type to detect multi-attribute products
                variant_groups = {}
                for variant in variants:
                    variant_type = variant.get('type', 'unknown')
                    if variant_type not in variant_groups:
                        variant_groups[variant_type] = []
                    variant_groups[variant_type].append(variant)
                
                logger.info(f"Product has {len(variant_groups)} variant types: {list(variant_groups.keys())}")
                
                # Check if this is truly a multi-attribute product
                is_multi_attribute = len(variant_groups) > 1
                
                if is_multi_attribute:
                    logger.info(f"Processing multi-attribute product with {len(variant_groups)} attribute types")
                    self._insert_multi_attribute_variations(cursor, product_id, product, variant_groups)
                else:
                    logger.info(f"Processing single-attribute product")
                    self._insert_single_attribute_variations(cursor, product_id, product, variants)

                    
        except Exception as e:
            logger.error(f"Error inserting product variations: {e}")
    
    def _insert_single_attribute_variations(self, cursor, product_id, product, variants):
        """Insert variations for single-attribute products (e.g., only colors OR only sizes)"""
        try:
            additional_images = product.get('additional_images', [])
            
            for i, variant in enumerate(variants):
                # Clean variant name - remove prices and newlines
                clean_variant_name = self._clean_variant_name(variant.get('name', ''))
                
                # Build combination string using text format
                combination = self._build_single_variant_combination(cursor, variant, product, product_id, clean_variant_name)

                insert_query = """
                INSERT INTO product_variations (
                    product_id, sku, purchase_price, unit_price, current_stock,
                    created_by, updated_by, created_at, updated_at, discount,
                    discount_type, combination, stock_status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                # CRITICAL FIX: Force integer conversion for stock values
                variant_stock = variant.get('stock', 0)
                try:
                    variant_stock = int(variant_stock) if variant_stock else 0
                except (ValueError, TypeError):
                    logger.warning(f"Invalid stock value '{variant_stock}' for variant, defaulting to 0")
                    variant_stock = 0
                
                # CRITICAL FIX: Force float conversion for prices
                variant_price = variant.get('price', 0)
                try:
                    variant_price = float(variant_price) if variant_price else 0.0
                except (ValueError, TypeError):
                    logger.warning(f"Invalid price value '{variant_price}' for variant, defaulting to 0.0")
                    variant_price = 0.0
                
                purchase_price = product.get('purchase_price', 0)
                try:
                    purchase_price = float(purchase_price) if purchase_price else 0.0
                except (ValueError, TypeError):
                    purchase_price = 0.0
                
                values = (
                    product_id,
                    variant.get('sku', ''),
                    purchase_price,  # Use main product purchase price
                    variant_price,
                    variant_stock,
                    '1',  # created_by
                    '1',  # updated_by
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    product.get('discount', 0),
                    '14',  # discount_type (ID 14 = Percentage)
                    combination or 'default_combination',
                    '11'  # stock_status (ID 11 = Stock In)
                )
                cursor.execute(insert_query, values)
                variation_id = cursor.lastrowid
                logger.info(f"Inserted single-attribute variation with ID: {variation_id}, combination: {combination}")
                
                # Insert variant-specific images
                variant_images = variant.get('images', [])
                all_variant_images = []
                
                # Add variant-specific images
                if variant_images:
                    all_variant_images.extend(variant_images)
                
                # Add additional_images to FIRST variant only
                if i == 0 and additional_images:
                    logger.info(f"Adding {len(additional_images)} additional_images to first variant")
                    all_variant_images.extend(additional_images)
                
                # Insert all collected images for this variant
                if all_variant_images:
                    self._insert_variant_images(cursor, variation_id, all_variant_images, product)
                    logger.info(f"Inserted {len(all_variant_images)} images for variant ID: {variation_id}")
                else:
                    # If variant has no images, use main product image as fallback
                    main_images = product.get('product_images', [])
                    if main_images and main_images[0]:
                        logger.info(f"Variant has no images, using main product image as fallback")
                        self._insert_variant_image(cursor, variation_id, main_images[0], product)
        
        except Exception as e:
            logger.error(f"Error inserting single-attribute variations: {e}")
    
    def _insert_multi_attribute_variations(self, cursor, product_id, product, variant_groups):
        """Insert variations for multi-attribute products (e.g., colors AND sizes)"""
        try:
            from itertools import product as itertools_product
            
            # Get all combinations across different attribute types
            attribute_combinations = list(itertools_product(*variant_groups.values()))
            logger.info(f"Generated {len(attribute_combinations)} combinations for multi-attribute product")
            
            additional_images = product.get('additional_images', [])
            
            for i, combination in enumerate(attribute_combinations):
                # Build combination string from multiple variants
                combination_parts = []
                combined_price = 0.0
                combined_stock = 0
                combined_sku_parts = []
                variant_images = []
                
                for variant in combination:
                    clean_name = self._clean_variant_name(variant.get('name', ''))
                    combination_parts.append(clean_name)
                    
                    # Combine prices (use highest price for the combination)
                    variant_price = variant.get('price', 0)
                    try:
                        variant_price = float(variant_price) if variant_price else 0.0
                        combined_price = max(combined_price, variant_price)
                    except (ValueError, TypeError):
                        pass
                    
                    # Combine stock (use minimum stock for the combination - bottleneck approach)
                    variant_stock = variant.get('stock', 0)
                    try:
                        variant_stock = int(variant_stock) if variant_stock else 0
                        combined_stock = min(combined_stock, variant_stock) if combined_stock > 0 else variant_stock
                    except (ValueError, TypeError):
                        pass
                    
                    # Collect SKU parts
                    if variant.get('sku'):
                        combined_sku_parts.append(variant.get('sku'))
                    
                    # Collect images from all variants in combination
                    if variant.get('images'):
                        variant_images.extend(variant.get('images'))
                
                # Create text-based combination string
                combination_text = ' / '.join(combination_parts)
                combined_sku = '-'.join(combined_sku_parts) if combined_sku_parts else ''
                
                insert_query = """
                INSERT INTO product_variations (
                    product_id, sku, purchase_price, unit_price, current_stock,
                    created_by, updated_by, created_at, updated_at, discount,
                    discount_type, combination, stock_status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                purchase_price = product.get('purchase_price', 0)
                try:
                    purchase_price = float(purchase_price) if purchase_price else 0.0
                except (ValueError, TypeError):
                    purchase_price = 0.0
                
                values = (
                    product_id,
                    combined_sku,
                    purchase_price,
                    combined_price,
                    combined_stock,
                    '1',  # created_by
                    '1',  # updated_by
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    product.get('discount', 0),
                    '14',  # discount_type (ID 14 = Percentage)
                    combination_text,
                    '11'  # stock_status (ID 11 = Stock In)
                )
                cursor.execute(insert_query, values)
                variation_id = cursor.lastrowid
                logger.info(f"Inserted multi-attribute variation with ID: {variation_id}, combination: {combination_text}")
                
                # Insert variant-specific images
                all_variant_images = []
                
                # Add images from all variants in this combination
                if variant_images:
                    all_variant_images.extend(variant_images)
                
                # Add additional_images to FIRST combination only
                if i == 0 and additional_images:
                    logger.info(f"Adding {len(additional_images)} additional_images to first combination")
                    all_variant_images.extend(additional_images)
                
                # Insert all collected images for this combination
                if all_variant_images:
                    self._insert_variant_images(cursor, variation_id, all_variant_images, product)
                    logger.info(f"Inserted {len(all_variant_images)} images for combination ID: {variation_id}")
                else:
                    # If combination has no images, use main product image as fallback
                    main_images = product.get('product_images', [])
                    if main_images and main_images[0]:
                        logger.info(f"Combination has no images, using main product image as fallback")
                        self._insert_variant_image(cursor, variation_id, main_images[0], product)
        
        except Exception as e:
            logger.error(f"Error inserting multi-attribute variations: {e}")

    def _build_single_variant_combination(self, cursor, variant, product, product_id, clean_name=None):
        """Build combination string for single-attribute products"""
        try:
            variant_name = variant.get('name') or clean_name
            if variant_name:
                # For single-attribute products, just clean and return the variant name
                return self._clean_variant_name(variant_name)
            else:
                return 'default_combination'
        except Exception as e:
            logger.error(f"Error building single variant combination: {e}")
            return 'default_combination'
                    
        except Exception as e:
            logger.error(f"Error inserting product variations: {e}")
    
    def _clean_variant_name(self, variant_name):
        """Clean variant name by removing prices, newlines, and extra text"""
        try:
            if not variant_name:
                return ""
            
            # Remove prices ($xx.xx format)
            import re
            clean_name = re.sub(r'\$[\d,]+\.?\d*', '', variant_name)
            
            # Remove newlines and excessive whitespace
            clean_name = re.sub(r'\n+', ' ', clean_name)
            clean_name = re.sub(r'\s+', ' ', clean_name)
            
            # Remove common separators and clean up
            clean_name = clean_name.replace('|', ',').strip()
            
            # Fix multiple spaces and clean up spacing around commas
            clean_name = re.sub(r'\s*,\s*', ', ', clean_name)
            clean_name = re.sub(r'\s+', ' ', clean_name)
            
            # Remove leading/trailing commas or pipes
            clean_name = clean_name.strip('|, ').strip()
            
            logger.info(f"Cleaned variant name: '{variant_name}' -> '{clean_name}'")
            return clean_name
            
        except Exception as e:
            logger.error(f"Error cleaning variant name: {e}")
            return variant_name or ""

    def _build_variant_combination(self, cursor, variant, product, product_id, clean_name=None):
        """Create ID-based combination string for a variant and ensure product_attributes links.
        
        ENHANCED FOR E-COMMERCE:
        - Uses variant['type'] field (color, size, etc.) from scraper
        - Uses variant['name'] field as the attribute value
        - Maps to existing database attributes (Color, Size, Material)
        - Supports multiple attribute combinations
        """
        try:
            option_pairs = []  # list of (parent_id, child_id)
            found_map = {}

            # PRIORITY 1: Use variant type and name from scraper (most common case)
            variant_type = variant.get('type')
            variant_name = variant.get('name') or clean_name
            
            if variant_type and variant_name:
                # This is the standard format from our scraper
                found_map[variant_type] = variant_name
                logger.debug(f"Using variant type '{variant_type}' with value '{variant_name}'")
            
            # PRIORITY 2: Extract options from standard fields (backward compatibility)
            possible_keys = ['options', 'attributes']
            for key in possible_keys:
                raw = variant.get(key)
                if isinstance(raw, dict):
                    # Skip generic 'variant' key with full text value
                    for k, v in raw.items():
                        if k.lower() != 'variant':  # Skip generic variant field
                            found_map[k] = v
                elif isinstance(raw, list):
                    for item in raw:
                        name = (item or {}).get('name')
                        value = (item or {}).get('value')
                        if name is not None and value is not None:
                            found_map[name] = value

            # PRIORITY 3: If no proper options found, try to parse from clean_name
            if not found_map and clean_name:
                parsed_attributes = self._parse_variant_attributes_from_name(clean_name)
                found_map.update(parsed_attributes)
                logger.info(f"Parsed attributes from name '{clean_name}': {parsed_attributes}")

            # PRIORITY 4: If still no options, try product-level attributes
            if not found_map and isinstance(product.get('attributes'), dict):
                product_attrs = product.get('attributes')
                for k, v in product_attrs.items():
                    if k.lower() != 'variant':  # Skip generic variant field
                        found_map[k] = v

            # Create attribute pairs with proper mapping
            for name, value in found_map.items():
                if value is None or str(value).strip() == '':
                    continue
                    
                # Clean attribute name and value
                clean_attr_name = str(name).strip()
                clean_attr_value = str(value).strip()
                
                # Get or create parent attribute (maps to existing DB attributes)
                parent_id = self._get_or_create_attribute_parent(cursor, clean_attr_name)
                child_id = self._get_or_create_attribute_value(cursor, parent_id, clean_attr_value)
                option_pairs.append((parent_id, child_id))

                # Ensure product_attributes rows exist (links product to parent attribute)
                self._ensure_product_attribute_link(cursor, product_id, parent_id, 'parent')

            if not option_pairs:
                logger.warning(f"No valid attributes found for variant: {variant.get('name', 'Unknown')}")
                return 'single_combination'

            # CRITICAL FIX: Generate text-based combination using database values
            text_combination = self._convert_ids_to_text_combination(cursor, option_pairs)
            
            # Validate combination format
            if not self._validate_combination_format(text_combination):
                logger.warning(f"Invalid combination format generated: '{text_combination}', using fallback")
                text_combination = 'default_combination'
            
            # CRITICAL FIX: Ensure product_attributes links exist for THIS specific variant
            for parent_id, child_id in option_pairs:
                # Create parent link (shared across all variants)
                self._ensure_product_attribute_link(cursor, product_id, parent_id, 'parent')
                # Create child link (specific to this variant)
                self._ensure_product_attribute_link(cursor, product_id, child_id, 'child')
            
            logger.info(f"Generated text combination: '{text_combination}' from {len(option_pairs)} attributes")
            return text_combination
            
        except Exception as e:
            logger.error(f"Error building variant combination: {e}")
            return 'default_combination'
    
    def _parse_variant_attributes_from_name(self, variant_name):
        """Parse attributes from variant name like '8GB RAM, 288GB Storage' or '16GB | 288GB Storage'"""
        try:
            import re
            attributes = {}
            
            if not variant_name or variant_name.strip() == '':
                return attributes
            
            # Common patterns to extract attributes (order matters - most specific first)
            patterns = [
                # Complex Size patterns: 88x104-25 lbs, 48x72-20 lbs, etc. (COMPLETE size descriptions)
                (r'(\d+x\d+(?:-\d+)?\s*lbs?)', 'Size'),
                (r'(\d+\s*Inch\s*x\s*\d+\s*Inch\s*[^\d]*\d+\s*LBS?)', 'Size'),  # "50 Inch x 60 Inch ï½œ10LBS"
                # Color with "/": Gray/Blue, Black/Silver (before simple colors) - MISSING PATTERN!
                (r'\b([A-Za-z]+/[A-Za-z]+)\b', 'Color'),
                # Color with "&": Black & Orange, Navy & Blue (before simple colors)
                (r'\b([A-Za-z]+\s*&\s*[A-Za-z]+)\b', 'Color'),
                # Color with "and": Black and Blue, Grey and Black (before simple colors)  
                (r'\b([A-Za-z]+\s+and\s+[A-Za-z]+)\b', 'Color'),
                # Color patterns: Red, Blue, Black, etc. (include modifiers like Dark, Light)
                (r'\b((?:Dark|Light|Bright|Deep|Pale)?\s*(?:Red|Blue|Black|White|Green|Yellow|Pink|Purple|Orange|Brown|Gray|Grey|Silver|Gold))\b', 'Color'),
                # RAM patterns: 8GB, 16GB, etc.
                (r'(\d+)\s*GB(?:\s+RAM)?', 'Capacity'),
                # Storage patterns: 288GB Storage, 512GB SSD, etc.
                (r'(\d+)\s*GB\s+(?:Storage|SSD|storage)', 'Capacity'),  
                # Simple Size patterns: 60x80, 48x72, etc. (only if no complex size found)
                (r'(\d+x\d+)', 'Size'),
                # Standard Size patterns: Small, Medium, Large, XL, etc.
                (r'\b(XS|S|M|L|XL|XXL|XXXL|Small|Medium|Large|Extra Large)\b', 'Size'),
                # Material patterns
                (r'\b(Cotton|Leather|Polyester|Silk|Wool|Linen|Denim)\b', 'Material'),
                # Weight patterns: 25 lbs, 20 lbs, etc. (LAST - only if no size with weight found)
                (r'(\d+\s*lbs?)', 'Weight'),
            ]
            
            # Try to extract using patterns (most specific first, avoid conflicts)
            found_attributes = set()  # Track which attribute types we've found
            
            for pattern, attr_name in patterns:
                # Skip if we already found this attribute type
                if attr_name in found_attributes:
                    continue
                    
                matches = re.findall(pattern, variant_name, re.IGNORECASE)
                if matches:
                    if attr_name in ['Capacity'] and any('GB' in str(m) for m in matches):
                        # For Capacity (RAM/Storage), add GB unit if not present
                        for match in matches:
                            if 'GB' not in str(match):
                                attributes[attr_name] = f"{match}GB"
                            else:
                                attributes[attr_name] = str(match)
                            found_attributes.add(attr_name)
                            break  # Take first match
                    else:
                        # For other attributes, use as-is
                        # If multiple matches, take the first one
                        match_value = str(matches[0]).strip()
                        
                        # Special handling for multi-word colors
                        if attr_name == 'Color' and ('&' in match_value or 'and' in match_value.lower()):
                            # Clean up formatting for colors like "Black & Orange"
                            match_value = re.sub(r'\s*&\s*', ' & ', match_value)
                            match_value = re.sub(r'\s+and\s+', ' & ', match_value, flags=re.IGNORECASE)
                        
                        attributes[attr_name] = match_value
                        found_attributes.add(attr_name)
            
            # If no patterns matched, try simple comma/pipe separation
            if not attributes:
                # Split by common separators
                parts = re.split(r'[|,]', variant_name)
                for i, part in enumerate(parts):
                    part = part.strip()
                    if part and len(part) < 50:  # Avoid very long strings
                        # Use generic attribute names
                        attr_name = f"Option_{i+1}" if len(parts) > 1 else "Option"
                        attributes[attr_name] = part
            
            logger.info(f"Parsed attributes from '{variant_name}': {attributes}")
            return attributes
            
        except Exception as e:
            logger.error(f"Error parsing variant attributes from name: {e}")
            return {}

    def _collect_product_attribute_values(self, product):
        """Return mapping attr_name -> set(values) from product-level fields and variants."""
        attribute_to_values = {}

        def add(attr_name, value):
            if value is None:
                return
            name_n = self._normalize_text(str(attr_name))
            value_n = self._normalize_text(str(value))
            if not name_n or not value_n:
                return
            attribute_to_values.setdefault(name_n, set()).add(value_n)

        # Common product-level keys
        for key in ['color', 'size', 'material', 'brand', 'weight', 'dimensions', 'capacity', 'flavor', 'pack size', 'pack_size']:
            value = product.get(key)
            if key in product and value not in (None, ''):
                # Skip meaningless default values
                if key == 'weight' and (value == 0 or value == 0.0 or str(value) == '0.0'):
                    continue
                if key in ['height', 'length', 'width'] and (value == 0 or value == 0.0 or str(value) == '0.0'):
                    continue
                add(key, value)

        # attributes could be dict or list
        attrs = product.get('attributes')
        if isinstance(attrs, dict):
            for k, v in attrs.items():
                add(k, v)
        elif isinstance(attrs, list):
            for item in attrs:
                if isinstance(item, dict) and 'name' in item and 'value' in item:
                    add(item.get('name'), item.get('value'))

        # From variants
        for variant in product.get('variants', []) or []:
            for key in ['options', 'attributes']:
                v = variant.get(key)
                if isinstance(v, dict):
                    for k, val in v.items():
                        add(k, val)
                elif isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict) and 'name' in item and 'value' in item:
                            add(item.get('name'), item.get('value'))

        return attribute_to_values

    def _normalize_text(self, text):
        try:
            return ' '.join(text.strip().split()).lower()
        except Exception:
            return ''

    def _map_variant_type_to_attribute(self, variant_type):
        """Map scraped variant type to standard e-commerce attribute names.
        
        This ensures we use existing database attributes (Color, Size, Material)
        instead of creating new ones.
        """
        type_mapping = {
            # Color variants
            'color': 'Color',
            'colour': 'Color',
            'colors': 'Color',
            'colours': 'Color',
            
            # Size variants
            'size': 'Size',
            'sizes': 'Size',
            
            # Material variants
            'material': 'Material',
            'materials': 'Material',
            'fabric': 'Material',
            
            # Storage/Memory variants - CRITICAL FIX: Map to existing 'Capacity' attribute
            'storage': 'Capacity',
            'memory': 'Capacity', 
            'capacity': 'Capacity',
            'ram': 'Capacity',
            
            # Pack Size variants
            'pack_size': 'Pack Size',
            'pack size': 'Pack Size',
            'packsize': 'Pack Size',
            
            # Other existing attributes
            'flavor': 'Flavor',
            'flavour': 'Flavor',
            'warranty': 'Warranty',
            'power': 'Power',
            'weight': 'Weight',
            'dimensions': 'Dimensions',
            'dimension': 'Dimensions',
            'brand': 'Brand',
            
            # Generic variant type - will be handled specially
            'variant': 'Variant',
        }
        
        normalized_type = variant_type.lower().strip()
        mapped = type_mapping.get(normalized_type, variant_type.title())
        
        logger.debug(f"Mapped variant type '{variant_type}' -> '{mapped}'")
        return mapped

    def _get_or_create_attribute_parent(self, cursor, name):
        """Return id for parent attribute (parent_id IS NULL), creating if needed.
        
        IMPORTANT: Maps common scraped variant types to existing database attributes.
        """
        # CRITICAL: Map variant type to standard attribute name
        mapped_name = self._map_variant_type_to_attribute(name)
        
        normalized = self._normalize_text(mapped_name)
        if normalized in self._attribute_parent_cache:
            logger.debug(f"Using cached parent attribute '{mapped_name}' (ID: {self._attribute_parent_cache[normalized]})")
            return self._attribute_parent_cache[normalized]

        select_sql = "SELECT id FROM attributes WHERE LOWER(name) = %s AND parent_id IS NULL LIMIT 1"
        cursor.execute(select_sql, (normalized,))
        row = cursor.fetchone()
        if row:
            parent_id = int(row[0])
            self._attribute_parent_cache[normalized] = parent_id
            logger.debug(f"Found existing parent attribute '{mapped_name}' (ID: {parent_id})")
            return parent_id

        # ONLY create if doesn't exist (should rarely happen with seeded data)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        insert_sql = """
            INSERT INTO attributes (name, status, `order`, parent_id, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_sql, (mapped_name.strip(), 'active', 0, None, now, now))
        parent_id = cursor.lastrowid
        self._attribute_parent_cache[normalized] = parent_id
        # init children cache bucket
        self._attribute_children_cache.setdefault(parent_id, {})
        logger.info(f"Created new parent attribute '{mapped_name}' (ID: {parent_id}) - this should rarely happen!")
        return parent_id

    def _get_or_create_attribute_value(self, cursor, parent_id, value_name):
        """Return id for child attribute value under given parent, creating if needed."""
        normalized_value = self._normalize_text(value_name)
        children_cache = self._attribute_children_cache.setdefault(parent_id, {})
        if normalized_value in children_cache:
            logger.debug(f"Using cached attribute value '{value_name}' (ID: {children_cache[normalized_value]})")
            return children_cache[normalized_value]

        select_sql = "SELECT id FROM attributes WHERE LOWER(name) = %s AND parent_id = %s LIMIT 1"
        cursor.execute(select_sql, (normalized_value, parent_id))
        row = cursor.fetchone()
        if row:
            child_id = int(row[0])
            children_cache[normalized_value] = child_id
            logger.debug(f"Found existing attribute value '{value_name}' (ID: {child_id})")
            return child_id

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        insert_sql = """
            INSERT INTO attributes (name, status, `order`, parent_id, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_sql, (value_name.strip(), 'active', 0, parent_id, now, now))
        child_id = cursor.lastrowid
        children_cache[normalized_value] = child_id
        logger.info(f"Created new attribute value '{value_name}' (ID: {child_id}, parent: {parent_id})")
        return child_id

    def _ensure_product_attribute_link(self, cursor, product_id, attribute_id, link_type):
        """Insert into product_attributes if not exists for given product and attribute."""
        try:
            check_sql = "SELECT id FROM product_attributes WHERE product_id = %s AND attribute_id = %s AND type = %s LIMIT 1"
            cursor.execute(check_sql, (product_id, attribute_id, link_type))
            if cursor.fetchone():
                return

            insert_sql = """
                INSERT INTO product_attributes (product_id, attribute_id, type, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
            """
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(insert_sql, (product_id, attribute_id, link_type, now, now))
        except Exception as e:
            logger.error(f"Error ensuring product attribute link: {e}")
    
    def _convert_ids_to_text_combination(self, cursor, option_pairs):
        """Convert (parent_id, child_id) pairs to 'Value1 / Value2' format.
        
        Args:
            cursor: Database cursor
            option_pairs: List of (parent_id, child_id) tuples
            
        Returns:
            String like "Green / Medium" or "Red / 8GB"
        """
        try:
            text_parts = []
            
            # Sort by parent_id for consistent ordering
            sorted_pairs = sorted(option_pairs, key=lambda x: x[0])
            
            for parent_id, child_id in sorted_pairs:
                # Get child attribute name from database
                select_sql = "SELECT name FROM attributes WHERE id = %s AND parent_id = %s LIMIT 1"
                cursor.execute(select_sql, (child_id, parent_id))
                result = cursor.fetchone()
                
                if result:
                    text_parts.append(result[0])
                    logger.debug(f"Found attribute value: {result[0]} (id: {child_id})")
                else:
                    logger.warning(f"Could not find attribute name for child_id: {child_id}, parent_id: {parent_id}")
                    # Fallback to ID-based format for this part
                    text_parts.append(f"attr_{child_id}")
            
            if text_parts:
                combination_text = ' / '.join(text_parts)
                logger.info(f"Generated text combination: '{combination_text}' from {len(option_pairs)} attributes")
                return combination_text
            else:
                logger.warning("No valid text parts found, using default combination")
                return 'default_combination'
                
        except Exception as e:
            logger.error(f"Error converting IDs to text combination: {e}")
            return 'default_combination'
    
    def _insert_variant_images(self, cursor, variation_id, variant_images, product):
        """Insert variant-specific images into images table"""
        try:
            logger.info(f"Inserting {len(variant_images)} images for variation ID: {variation_id}")
            
            for i, image_url in enumerate(variant_images):
                if image_url and image_url.strip():
                    self._insert_variant_image(cursor, variation_id, image_url, product, i+1)
                    
        except Exception as e:
            logger.error(f"Error inserting variant images: {e}")
    
    def _insert_variant_image(self, cursor, variation_id, image_url, product, image_index=1):
        """Insert single variant image"""
        try:
            insert_query = """
            INSERT INTO images (
                url, imageable_id, imageable_type, type, created_by, updated_by,
                created_at, updated_at, alt
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            # Generate alt text from product name and variant info
            alt_text = f"{product.get('product_name', 'Product')} - Variant Image {image_index}"
            
            values = (
                image_url.strip(),  # url
                variation_id,  # imageable_id (variation ID)
                'App\\Models\\ProductVariation',  # imageable_type
                'product_variation',  # type
                None,  # created_by
                None,  # updated_by
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # created_at
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # updated_at
                alt_text  # alt
            )
            
            cursor.execute(insert_query, values)
            image_id = cursor.lastrowid
            logger.info(f"Inserted variant image {image_index} with ID {image_id}: {image_url[:50]}...")
            
        except Exception as e:
            logger.error(f"Error inserting variant image: {e}")
    
    def _insert_product_images(self, cursor, product_id, product):
        """Insert product images into images table"""
        try:
            logger.info(f"Inserting images for product ID: {product_id}")
            logger.info(f"Product data keys: {list(product.keys())}")
            
            # Get main product images
            main_images = product.get('product_images', [])
            # Get additional images
            additional_images = product.get('additional_images', [])
            
            logger.info(f"Main images: {main_images}")
            logger.info(f"Additional images: {additional_images}")
            
            # Combine all images
            all_images = main_images + additional_images
            
            if not all_images:
                logger.warning(f"No images found for product ID: {product_id}")
                logger.warning(f"Product name: {product.get('product_name', 'Unknown')}")
                return
            
            logger.info(f"Found {len(all_images)} images for product ID: {product_id}")
            
            # Insert only the first image as thumbnail
            if all_images and all_images[0]:
                image_url = all_images[0].strip()
                if image_url:
                    insert_query = """
                    INSERT INTO images (
                        url, imageable_id, imageable_type, type, created_by, updated_by,
                        created_at, updated_at, alt
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    # Only insert thumbnail (first image)
                    alt_text = f"{product.get('product_name', 'Product')} - Thumbnail"
                    
                    values = (
                        image_url,  # url
                        product_id,  # imageable_id
                        'App\\Models\\Product',  # imageable_type
                        'thumbnail',  # type
                        None,  # created_by
                        None,  # updated_by
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # created_at
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # updated_at
                        alt_text  # alt
                    )
                    
                    logger.info(f"Inserting thumbnail image for product ID: {product_id}")
                    cursor.execute(insert_query, values)
                    image_id = cursor.lastrowid
                    logger.info(f"Inserted thumbnail image with ID {image_id}: {image_url[:50]}...")
                    
                    logger.info(f"Additional images ({len(all_images)-1}) will be handled by variants")
            
            logger.info(f"Successfully inserted {len(all_images)} images for product ID: {product_id}")
            
            # Verify images were inserted
            verify_query = "SELECT COUNT(*) FROM images WHERE imageable_id = %s AND imageable_type = 'App\\\\Models\\\\Product'"
            cursor.execute(verify_query, (product_id,))
            count = cursor.fetchone()[0]
            logger.info(f"Verification: {count} images found in database for product ID: {product_id}")
            
        except Exception as e:
            logger.error(f"Error inserting product images: {e}")
            logger.error(f"Product ID: {product_id}, Product: {product.get('product_name', 'Unknown')}")
    
    def _check_product_exists(self, cursor, product):
        """Check if product already exists based on product name and SKU"""
        try:
            product_name = product.get('product_name', '')
            sku = product.get('sku', '')
            
            if not product_name and not sku:
                logger.warning("Product has no name or SKU, cannot check for duplicates")
                return None
            
            # Check by SKU first (most reliable), then by name
            if sku:
                check_query = "SELECT id FROM products WHERE sku = %s"
                cursor.execute(check_query, (sku,))
                result = cursor.fetchone()
                if result:
                    logger.info(f"Product with SKU already exists: {sku}")
                    return result[0]
            
            # Check by name if SKU check failed
            if product_name:
                check_query = "SELECT id FROM products WHERE name = %s"
                cursor.execute(check_query, (product_name,))
                result = cursor.fetchone()
                if result:
                    logger.info(f"Product with name already exists: {product_name[:50]}...")
                    return result[0]
            
            logger.info(f"Product is new: {product_name[:50]}...")
            return None
                
        except Exception as e:
            logger.error(f"Error checking if product exists: {e}")
            return None
    
    def _update_existing_product(self, cursor, product_id, product):
        """Update existing product with new data"""
        try:
            logger.info(f"Updating existing product ID: {product_id}")
            
            # Update main product data
            update_query = """
            UPDATE products SET 
                name = %s, slug = %s, unit = %s, min_purchase_qty = %s, max_purchase_qty = %s,
                meta_title = %s, price = %s, sku = %s, current_stock = %s, discount = %s, 
                delivery_time = %s, weight = %s, height = %s, length = %s, width = %s,
                product_description = %s, meta_description = %s, order_count = %s, 
                product_reviews = %s, disocunt_type = %s, child_category = %s, stock = %s,
                status = %s, brand = %s, updated_by = %s, updated_at = %s,
                product_reviews_avg = %s, store_id = %s, product_reviews_sum = %s,
                is_featured = %s, views_count = %s, variation_type = %s, h1 = %s
            WHERE id = %s
            """
            
            # Generate slug from product name
            slug = product.get('product_name', '').lower().replace(' ', '-').replace(',', '').replace('.', '')[:100]
            
            # Extract delivery time (convert "24 hr(s)" to "24")
            delivery_time = product.get('standard_delivery_time', '72')
            if 'hr' in delivery_time:
                delivery_time = delivery_time.split()[0]
            
            values = (
                product.get('product_name', '')[:255],  # name
                slug,  # slug
                '1',  # unit
                '1',  # min_purchase_qty
                '10',  # max_purchase_qty
                product.get('product_name', '')[:255],  # meta_title
                product.get('unit_price', 0),  # price
                product.get('sku', ''),  # sku
                product.get('current_stock', 0),  # current_stock
                product.get('discount', 0),  # discount
                delivery_time,  # delivery_time
                product.get('weight', 0),  # weight
                product.get('height', 0),  # height
                product.get('length', 0),  # length
                product.get('width', 0),  # width
                product.get('product_description', ''),  # product_description
                product.get('meta_tags_description', ''),  # meta_description
                0,  # order_count
                product.get('review_count', 0),  # product_reviews
                '14',  # disocunt_type (ID 14 = Percentage from types table)
                '26',  # child_category (default)
                '11',  # stock (ID 11 = Stock In from stock_status types)
                '8',  # status (ID 8 = Published from status types)
                '16',  # brand (default)
                '1',  # updated_by
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # updated_at
                product.get('rating', 0),  # product_reviews_avg
                '1',  # store_id
                product.get('rating', 0),  # product_reviews_sum
                '0',  # is_featured
                0,  # views_count
                'SINGLE',  # variation_type
                None,  # h1
                product_id  # WHERE id
            )
            
            cursor.execute(update_query, values)
            logger.info(f"Updated main product data for ID: {product_id}")
            
            # Delete old images and insert new ones
            self._delete_product_images(cursor, product_id)
            self._insert_product_images(cursor, product_id, product)
            
            # Update product attributes (delete old, insert new)
            self._delete_product_attributes(cursor, product_id)
            self._insert_product_attributes(cursor, product_id, product)
            
            # Update product variations (delete old, insert new)
            self._delete_product_variations(cursor, product_id)
            self._insert_product_variations(cursor, product_id, product)
            
            logger.info(f"Successfully updated all data for product ID: {product_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating existing product: {e}")
            return False
    
    def _delete_product_images(self, cursor, product_id):
        """Delete existing product images"""
        try:
            delete_query = "DELETE FROM images WHERE imageable_id = %s AND imageable_type = 'App\\\\Models\\\\Product'"
            cursor.execute(delete_query, (product_id,))
            logger.info(f"Deleted existing images for product ID: {product_id}")
        except Exception as e:
            logger.error(f"Error deleting product images: {e}")
    
    def _delete_product_attributes(self, cursor, product_id):
        """Delete existing product attributes"""
        try:
            delete_query = "DELETE FROM product_attributes WHERE product_id = %s"
            cursor.execute(delete_query, (product_id,))
            logger.info(f"Deleted existing attributes for product ID: {product_id}")
        except Exception as e:
            logger.error(f"Error deleting product attributes: {e}")
    
    def _delete_product_variations(self, cursor, product_id):
        """Delete existing product variations"""
        try:
            delete_query = "DELETE FROM product_variations WHERE product_id = %s"
            cursor.execute(delete_query, (product_id,))
            logger.info(f"Deleted existing variations for product ID: {product_id}")
        except Exception as e:
            logger.error(f"Error deleting product variations: {e}")
    
    def get_product_count(self):
        """Get total number of products efficiently"""
        try:
            # Try to get count from chunk index first
            chunks_index_file = "scraped_data/chunks/index.json"
            if os.path.exists(chunks_index_file):
                with open(chunks_index_file, 'r', encoding='utf-8') as f:
                    index = json.load(f)
                    return index.get('total_products', 0)
            
            # Fallback to JSON file
            json_file = "scraped_data/products.json"
            if os.path.exists(json_file):
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return len(data)
            return 0
        except Exception as e:
            logger.error(f"Error getting product count: {e}")
            return 0
    
    def _load_products_efficiently(self):
        """Load products using chunks if available, fallback to JSON"""
        try:
            # Check if chunks are available
            chunks_index_file = "scraped_data/chunks/index.json"
            if os.path.exists(chunks_index_file):
                logger.info("Loading products from chunks...")
                products = []
                for chunk_products in self.chunk_manager.get_all_products_for_db():
                    products.extend(chunk_products)
                logger.info(f"Loaded {len(products):,} products from chunks")
                return products
            
            # Fallback to traditional JSON loading
            logger.info("Chunks not available, loading from JSON file...")
            json_file = "scraped_data/products.json"
            if not os.path.exists(json_file):
                raise Exception('No products.json file found. Please scrape some products first.')
            
            with open(json_file, 'r', encoding='utf-8') as f:
                products = json.load(f)
            
            logger.info(f"Loaded {len(products):,} products from JSON file")
            return products
        
        except Exception as e:
            logger.error(f"Error loading products: {e}")
            raise
    
    def insert_products_chunked(self, test_mode=False, connection_params=None):
        """Insert products using efficient chunk loading"""
        try:
            logger.info(f"Starting chunked product insertion. Test mode: {test_mode}")
            
            # Connect to database
            if connection_params:
                if not self.connect(**connection_params):
                    return {'success': False, 'message': 'Database connection failed'}
            else:
                if not self.connection or not self.connection.is_connected():
                    if not self.connect():
                        return {'success': False, 'message': 'Database connection failed'}
            
            cursor = self.connection.cursor()
            total_inserted = 0
            total_updated = 0
            total_chunks = 0
            
            # Check if chunks are available
            chunks_index_file = "scraped_data/chunks/index.json"
            if os.path.exists(chunks_index_file):
                logger.info("Using chunk-based insertion...")
                
                # Get chunk information
                with open(chunks_index_file, 'r', encoding='utf-8') as f:
                    index = json.load(f)
                
                total_products = index.get('total_products', 0)
                logger.info(f"Total products to process: {total_products:,}")
                
                # Process chunks
                for chunk_products in self.chunk_manager.get_all_products_for_db():
                    total_chunks += 1
                    
                    if test_mode and total_chunks > 1:
                        logger.info("Test mode: Processing only first chunk")
                        break
                    
                    logger.info(f"Processing chunk {total_chunks} with {len(chunk_products):,} products...")
                    
                    # Process products in this chunk
                    chunk_inserted, chunk_updated = self._process_product_chunk(cursor, chunk_products)
                    total_inserted += chunk_inserted
                    total_updated += chunk_updated
                    
                    logger.info(f"Chunk {total_chunks} completed: {chunk_inserted} inserted, {chunk_updated} updated")
                    
                    # Commit after each chunk to avoid long transactions
                    self.connection.commit()
            
            else:
                # Fallback to traditional method
                logger.info("Chunks not available, using traditional insertion...")
                products = self._load_products_efficiently()
                
                if test_mode:
                    products = products[:1]
                
                chunk_inserted, chunk_updated = self._process_product_chunk(cursor, products)
                total_inserted += chunk_inserted
                total_updated += chunk_updated
                self.connection.commit()
            
            cursor.close()
            
            return {
                'success': True,
                'message': f'Successfully processed products: {total_inserted} inserted, {total_updated} updated',
                'inserted': total_inserted,
                'updated': total_updated,
                'chunks_processed': total_chunks
            }
            
        except Exception as e:
            logger.error(f"Error in chunked product insertion: {e}")
            if self.connection:
                self.connection.rollback()
            return {'success': False, 'message': str(e)}
    
    def insert_products_from_json(self, products, connection_params=None):
        """Insert products directly from JSON data - for Insert All Products button"""
        try:
            logger.info(f"🚀 Starting direct JSON insertion of {len(products):,} products")
            
            # Connect to database
            if connection_params:
                if not self.connect(**connection_params):
                    return {'success': False, 'message': 'Database connection failed'}
            else:
                if not self.connection or not self.connection.is_connected():
                    if not self.connect():
                        return {'success': False, 'message': 'Database connection failed'}
            
            cursor = self.connection.cursor()
            
            # Process all products
            total_inserted, total_updated = self._process_product_chunk(cursor, products)
            
            # Commit transaction
            self.connection.commit()
            cursor.close()
            
            logger.info(f"✅ JSON insertion completed: {total_inserted} inserted, {total_updated} updated")
            
            return {
                'success': True,
                'message': f'Successfully processed {len(products):,} products from JSON: {total_inserted} inserted, {total_updated} updated',
                'inserted': total_inserted,
                'updated': total_updated,
                'source': 'json_file'
            }
            
        except Exception as e:
            logger.error(f"Error in JSON product insertion: {e}")
            if self.connection:
                self.connection.rollback()
            return {'success': False, 'message': f'Database error: {str(e)}'}
        
        finally:
            if self.connection and self.connection.is_connected():
                self.connection.close()
    
    def _process_product_chunk(self, cursor, products):
        """Process a chunk of products"""
        inserted_count = 0
        updated_count = 0
        
        for i, product in enumerate(products):
            try:
                logger.info(f"Processing product {i+1}: {product.get('product_name', 'Unknown')[:50]}...")
                
                # Check if product already exists
                existing_product_id = self._check_product_exists(cursor, product)
                
                if existing_product_id:
                    # Update existing product
                    if self._update_existing_product(cursor, existing_product_id, product):
                        updated_count += 1
                else:
                    # Insert new product
                    product_id = self._insert_main_product(cursor, product)
                    if product_id:
                        # Insert related data
                        self._insert_product_images(cursor, product_id, product)
                        self._insert_product_attributes(cursor, product_id, product)
                        self._insert_product_variations(cursor, product_id, product)
                        inserted_count += 1
                        
            except Exception as e:
                logger.error(f"Error processing product {product.get('product_name', 'Unknown')}: {e}")
                continue
        
        return inserted_count, updated_count
