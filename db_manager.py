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

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.credentials = self.load_credentials()
    
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
                name, source_url, slug, unit, min_purchase_qty, max_purchase_qty,
                meta_title, price, sku, current_stock, discount, delivery_time,
                weight, height, length, width, product_description, meta_description,
                order_count, product_reviews, disocunt_type, child_category, stock,
                status, brand, created_by, updated_by, created_at, updated_at,
                product_reviews_avg, store_id, product_reviews_sum, is_featured,
                views_count, variation_type, h1
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s
            )
            """
            
            # Generate slug from product name
            slug = product.get('product_name', '').lower().replace(' ', '-').replace(',', '').replace('.', '')[:100]
            
            # Extract delivery time (convert "24 hr(s)" to "24")
            delivery_time = product.get('standard_delivery_time', '72')
            if 'hr' in delivery_time:
                delivery_time = delivery_time.split()[0]
            
            values = (
                product.get('product_name', '')[:255],  # name
                product.get('source_url', ''),  # source_url
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
                '12',  # disocunt_type (default to 12 for percentage)
                '26',  # child_category (default)
                product.get('current_stock', 0),  # stock
                '7',  # status (active)
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
                'SINGLE',  # variation_type
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
    
    def _insert_product_attributes(self, cursor, product_id, product):
        """Insert product attributes"""
        try:
            # Map category to attributes (simplified mapping)
            category = product.get('category', '').lower()
            
            # Define category to attribute mapping
            category_attributes = {
                'electronics': [1, 12, 27],  # Color, Size, Brand
                'toys': [1, 12, 27],  # Color, Size, Brand
                'clothing': [1, 12, 18, 27],  # Color, Size, Material, Brand
            }
            
            # Get attributes for this category
            attributes = category_attributes.get(category, [1, 12])  # Default: Color, Size
            
            for attr_id in attributes:
                insert_query = """
                INSERT INTO product_attributes (product_id, attribute_id, type, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                """
                values = (
                    product_id,
                    attr_id,
                    'parent',
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
                cursor.execute(insert_query, values)
                
        except Exception as e:
            logger.error(f"Error inserting product attributes: {e}")
    
    def _insert_product_variations(self, cursor, product_id, product):
        """Insert product variations"""
        try:
            variants = product.get('variants', [])
            
            if not variants:
                # Insert single variation for products without variants
                insert_query = """
                INSERT INTO product_variations (
                    product_id, sku, purchase_price, unit_price, current_stock,
                    created_by, updated_by, created_at, updated_at, discount,
                    discount_type, combination, stock_status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                values = (
                    product_id,
                    product.get('sku', ''),
                    product.get('purchase_price', 0),
                    product.get('unit_price', 0),
                    product.get('current_stock', 0),
                    '1',  # created_by
                    '1',  # updated_by
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    product.get('discount', 0),
                    '12',  # discount_type
                    'single_combination',
                    '1'  # stock_status
                )
                cursor.execute(insert_query, values)
            else:
                # Insert each variant
                for variant in variants:
                    insert_query = """
                    INSERT INTO product_variations (
                        product_id, sku, purchase_price, unit_price, current_stock,
                        created_by, updated_by, created_at, updated_at, discount,
                        discount_type, combination, stock_status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    values = (
                        product_id,
                        variant.get('sku', ''),
                        product.get('purchase_price', 0),  # Use main product purchase price
                        variant.get('price', 0),
                        variant.get('stock', 0),
                        '1',  # created_by
                        '1',  # updated_by
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        product.get('discount', 0),
                        '12',  # discount_type
                        'single_combination',
                        '1'  # stock_status
                    )
                    cursor.execute(insert_query, values)
                    
        except Exception as e:
            logger.error(f"Error inserting product variations: {e}")
    
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
            
            # Insert each image
            for i, image_url in enumerate(all_images):
                if image_url and image_url.strip():  # Check if URL is not empty
                    insert_query = """
                    INSERT INTO images (
                        url, imageable_id, imageable_type, type, created_by, updated_by,
                        created_at, updated_at, alt
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    # Determine image type: first image = thumbnail, others = product
                    if i == 0:
                        image_type = "thumbnail"  # First image is thumbnail
                    else:
                        image_type = "product"   # Additional images are product type
                    
                    # Generate alt text from product name
                    alt_text = f"{product.get('product_name', 'Product')} - {image_type.title()} Image {i+1}"
                    
                    values = (
                        image_url.strip(),  # url
                        product_id,  # imageable_id
                        'App\\Models\\Product',  # imageable_type
                        image_type,  # type
                        None,  # created_by
                        None,  # updated_by
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # created_at
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # updated_at
                        alt_text  # alt
                    )
                    
                    logger.info(f"Executing image insert query with values: {values[:3]}...")
                    cursor.execute(insert_query, values)
                    image_id = cursor.lastrowid
                    logger.info(f"Inserted {image_type} image {i+1} with ID {image_id}: {image_url[:50]}...")
                else:
                    logger.warning(f"Skipping empty image URL at index {i}")
            
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
        """Check if product already exists based on source URL"""
        try:
            source_url = product.get('source_url', '')
            if not source_url:
                logger.warning("Product has no source URL, cannot check for duplicates")
                return None
            
            check_query = "SELECT id FROM products WHERE source_url = %s"
            cursor.execute(check_query, (source_url,))
            result = cursor.fetchone()
            
            if result:
                logger.info(f"Product with source URL already exists: {source_url[:50]}...")
                return result[0]
            else:
                logger.info(f"Product with source URL is new: {source_url[:50]}...")
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
                '12',  # disocunt_type (default to 12 for percentage)
                '26',  # child_category (default)
                product.get('current_stock', 0),  # stock
                '7',  # status (active)
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
        """Get total number of products in JSON file"""
        try:
            json_file = "scraped_data/products.json"
            if os.path.exists(json_file):
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return len(data)
            return 0
        except Exception as e:
            logger.error(f"Error getting product count: {e}")
            return 0
