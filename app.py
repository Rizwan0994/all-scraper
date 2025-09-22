#!/usr/bin/env python3
"""
Universal Product Scraper - Main Application
A comprehensive web scraping solution for e-commerce sites
"""

import sys
import os
import logging
import webbrowser
from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from flask_socketio import SocketIO
from datetime import datetime
import json
import csv
import io

# Import our scraper modules
from scraper.universal_scraper import UniversalScraper, Product
from db_manager import DatabaseManager
from chunk_manager import ChunkManager

# Configure logging with UTF-8 encoding for Windows compatibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize scraper, database manager, and chunk manager
scraper = UniversalScraper(socketio=socketio)
db_manager = DatabaseManager()
chunk_manager = ChunkManager()

# Authentication configuration
ADMIN_PASSWORD = "scraper@123"  # Change this to your desired password

def check_auth():
    """Check if user is authenticated"""
    return session.get('authenticated', False)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['authenticated'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout user"""
    session.pop('authenticated', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    """Main dashboard page"""
    if not check_auth():
        return redirect(url_for('login'))
    try:
        # Try to load from persistent files for accurate stats
        json_file = "scraped_data/products.json"
        if os.path.exists(json_file):
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Convert to Product objects for stats calculation
                products = []
                for item in data:
                    product = Product(**item)
                    products.append(product)
                stats = scraper.get_statistics(products)
        else:
            stats = scraper.get_statistics(scraper.scraped_products)
        
        return render_template('index.html', stats=stats)
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        stats = scraper.get_statistics(scraper.scraped_products)
        return render_template('index.html', stats=stats)

@app.route('/scrape', methods=['POST'])
def start_scraping():
    """Start scraping process"""
    if not check_auth():
        return jsonify({'status': 'error', 'error': 'Authentication required'}), 401
    try:
        data = request.get_json()
        keywords = data.get('keywords', '').split(',')
        max_products = data.get('max_products', 200)
        selected_sites = data.get('selected_sites', [])
        
        logger.info(f"Starting scraping with keywords: {keywords}")
        logger.info(f"Max products per site: {max_products}")
        logger.info(f"Selected sites: {selected_sites}")
        
        # Reset stop flag before starting new scraping session
        scraper.reset_stop_flag()
        
        # Start scraping in background
        products = scraper.scrape_selected_sites(keywords, max_products, selected_sites)
        
        return jsonify({
            'status': 'started',
            'message': f'Scraping started for {len(selected_sites)} sites',
            'total_products': len(products)
        })
        
    except Exception as e:
        logger.error(f"Scraping error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/scraping/stop', methods=['POST'])
def stop_scraping():
    """Stop the current scraping process"""
    if not check_auth():
        return jsonify({'status': 'error', 'error': 'Authentication required'}), 401
    try:
        # Stop the scraping process
        scraper.stop_scraping_process()
        
        logger.info("Scraping stop requested by user")
        
        return jsonify({
            'status': 'success',
            'message': 'Scraping stop requested. The process will stop gracefully.'
        })
        
    except Exception as e:
        logger.error(f"Stop scraping error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/status')
def get_status():
    """Get current scraping status from persistent files"""
    try:
        # Try to load from persistent files for accurate stats
        json_file = "scraped_data/products.json"
        if os.path.exists(json_file):
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Convert to Product objects for stats calculation
                products = []
                for item in data:
                    product = Product(**item)
                    products.append(product)
                stats = scraper.get_statistics(products)
        else:
            stats = scraper.get_statistics(scraper.scraped_products)
        
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error loading status: {e}")
        stats = scraper.get_statistics(scraper.scraped_products)
        return jsonify(stats)

@app.route('/products')
def get_products():
    """Get paginated products - DEPRECATED, use /api/products/page/<page> instead"""
    try:
        # For backwards compatibility, return first page only
        return get_products_page(1)
    except Exception as e:
        logger.error(f"Error in get_products: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/page/<int:page>')
def get_products_page(page):
    """Get products with pagination using chunks"""
    if not check_auth():
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        per_page = request.args.get('per_page', 50, type=int)
        per_page = min(max(per_page, 10), 200)  # Between 10-200 per page
        
        # Check if chunks are available
        chunks_index_file = "scraped_data/chunks/index.json"
        if os.path.exists(chunks_index_file):
            logger.info(f"Loading page {page} from chunks ({per_page} per page)")
            
            # Load index
            with open(chunks_index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
            
            total_products = index.get('total_products', 0)
            total_pages = (total_products + per_page - 1) // per_page
            
            # Calculate which chunk(s) we need
            start_product = (page - 1) * per_page
            end_product = start_product + per_page
            
            if start_product >= total_products:
                return jsonify({
                    'products': [],
                    'page': page,
                    'per_page': per_page,
                    'total_products': total_products,
                    'total_pages': total_pages,
                    'has_more': False
                })
            
            # Find relevant chunks
            needed_chunks = []
            for chunk_info in index["chunks"]:
                chunk_start, chunk_end = chunk_info["product_range"]
                # Convert to 0-based indexing
                chunk_start_idx = chunk_start - 1
                chunk_end_idx = chunk_end - 1
                
                if not (end_product <= chunk_start_idx or start_product > chunk_end_idx):
                    needed_chunks.append(chunk_info)
            
            # Load and combine products from needed chunks
            all_products = []
            chunks_dir = "scraped_data/chunks"
            
            for chunk_info in needed_chunks:
                chunk_path = os.path.join(chunks_dir, chunk_info["file"])
                with open(chunk_path, 'r', encoding='utf-8') as f:
                    chunk_data = json.load(f)
                all_products.extend(chunk_data["products"])
            
            # Extract the exact page range
            page_products = all_products[start_product:end_product]
            
            # Format products for frontend
            formatted_products = []
            for item in page_products:
                formatted_products.append({
                    'title': item.get('product_name', ''),
                    'price': item.get('unit_price', 0.0),
                    'category': item.get('category', ''),
                    'sub_category': item.get('sub_category', ''),
                    'source_site': item.get('source_site', ''),
                    'rating': item.get('rating', 0.0),
                    'image': item.get('product_images', [None])[0] if item.get('product_images') else None,
                    'sku': item.get('sku', ''),
                    'stock': item.get('current_stock', 0),
                    'description': item.get('product_description', '')[:200] + '...' if len(item.get('product_description', '')) > 200 else item.get('product_description', '')
                })
            
            return jsonify({
                'products': formatted_products,
                'page': page,
                'per_page': per_page,
                'total_products': total_products,
                'total_pages': total_pages,
                'has_more': page < total_pages
            })
        
        else:
            # Fallback to traditional loading for first 1000 products only
            logger.info("Chunks not available, using fallback mode")
            json_file = "scraped_data/products.json"
            if os.path.exists(json_file):
                logger.warning("Loading large JSON file - this may be slow!")
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                    # Limit to reasonable amount for performance
                    if len(data) > 10000:
                        logger.warning(f"Large dataset ({len(data)} products) - limiting to first 10,000")
                        data = data[:10000]
                
                    total_products = len(data)
                    total_pages = (total_products + per_page - 1) // per_page
                
                    start_idx = (page - 1) * per_page
                    end_idx = start_idx + per_page
                
                    page_data = data[start_idx:end_idx]
                
                    products = []
                    for item in page_data:
                        products.append({
                            'title': item.get('product_name', ''),
                            'price': item.get('unit_price', 0.0),
                            'category': item.get('category', ''),
                            'sub_category': item.get('sub_category', ''),
                            'source_site': item.get('source_site', ''),
                            'rating': item.get('rating', 0.0),
                            'image': item.get('product_images', [None])[0] if item.get('product_images') else None
                        })
                
                    return jsonify({
                        'products': products,
                        'page': page,
                        'per_page': per_page,
                        'total_products': total_products,
                        'total_pages': total_pages,
                        'has_more': page < total_pages
                    })
                
        # No data available
        return jsonify({
            'products': [],
            'page': page,
            'per_page': per_page,
            'total_products': 0,
            'total_pages': 0,
            'has_more': False
        })
        
    except Exception as e:
        logger.error(f"Error loading products page {page}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/stats')
def get_products_stats():
    """Get pre-computed statistics from cache"""
    if not check_auth():
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        # Try to load from cache first
        cache_file = "scraped_data/cache/stats.json"
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)
            logger.info("Loaded stats from cache")
            return jsonify(stats)
        
        # Try to load from chunks index
        chunks_index_file = "scraped_data/chunks/index.json"
        if os.path.exists(chunks_index_file):
            with open(chunks_index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
            
            stats = {
                'total_products': index.get('total_products', 0),
                'total_chunks': index.get('total_chunks', 0),
                'global_stats': index.get('global_stats', {}),
                'source': 'chunks_index'
            }
            return jsonify(stats)
        
        # Fallback to traditional stats
        return get_status()
        
    except Exception as e:
        logger.error(f"Error loading stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/search')
def search_products():
    """Search products across chunks"""
    if not check_auth():
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        query = request.args.get('q', '').strip()
        category = request.args.get('category', '').strip()
        site = request.args.get('site', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        per_page = min(max(per_page, 10), 200)
        
        if not query and not category and not site:
            return jsonify({'error': 'At least one search parameter required'}), 400
        
        # Check if chunks are available
        chunks_index_file = "scraped_data/chunks/index.json"
        if os.path.exists(chunks_index_file):
            with open(chunks_index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
            
            # Find relevant chunks based on metadata
            relevant_chunks = []
            for chunk_info in index["chunks"]:
                should_search = False
                
                if category and category.lower() in [c.lower() for c in chunk_info.get("categories", [])]:
                    should_search = True
                elif site and site.lower() in [s.lower() for s in chunk_info.get("sites", [])]:
                    should_search = True
                elif not category and not site:  # Text search - check all chunks
                    should_search = True
                
                if should_search:
                    relevant_chunks.append(chunk_info)
            
            # Search within relevant chunks
            results = []
            chunks_dir = "scraped_data/chunks"
            
            for chunk_info in relevant_chunks:
                chunk_path = os.path.join(chunks_dir, chunk_info["file"])
                with open(chunk_path, 'r', encoding='utf-8') as f:
                    chunk_data = json.load(f)
                
                for product in chunk_data["products"]:
                    matches = True
                    
                    # Text search
                    if query:
                        product_text = (
                            product.get('product_name', '') + ' ' +
                            product.get('product_description', '') + ' ' +
                            product.get('category', '') + ' ' +
                            product.get('source_site', '')
                        ).lower()
                        if query.lower() not in product_text:
                            matches = False
                    
                    # Category filter
                    if category and category.lower() != product.get('category', '').lower():
                        matches = False
                    
                    # Site filter
                    if site and site.lower() != product.get('source_site', '').lower():
                        matches = False
                    
                    if matches:
                        results.append({
                            'title': product.get('product_name', ''),
                            'price': product.get('unit_price', 0.0),
                            'category': product.get('category', ''),
                            'sub_category': product.get('sub_category', ''),
                            'source_site': product.get('source_site', ''),
                            'rating': product.get('rating', 0.0),
                            'image': product.get('product_images', [None])[0] if product.get('product_images') else None,
                            'sku': product.get('sku', ''),
                            'stock': product.get('current_stock', 0)
                        })
            
            # Paginate results
            total_results = len(results)
            total_pages = (total_results + per_page - 1) // per_page
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            page_results = results[start_idx:end_idx]
            
            return jsonify({
                'products': page_results,
                'page': page,
                'per_page': per_page,
                'total_results': total_results,
                'total_pages': total_pages,
                'has_more': page < total_pages,
                'query': query,
                'category': category,
                'site': site,
                'chunks_searched': len(relevant_chunks)
            })
        
        else:
            return jsonify({'error': 'Search requires chunks to be initialized'}), 503
            
    except Exception as e:
        logger.error(f"Error searching products: {e}")
        return jsonify({'error': str(e)}), 500
        
        # If no JSON file, try CSV file
        csv_file = "scraped_data/products.csv"
        if os.path.exists(csv_file):
            products = []
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    products.append({
                        'title': row.get('product_name', ''),
                        'price': float(row.get('unit_price', 0.0)) if row.get('unit_price') else 0.0,
                        'category': row.get('category', ''),
                        'sub_category': row.get('sub_category', ''),
                        'source_site': row.get('source_site', ''),
                        'rating': float(row.get('rating', 0.0)) if row.get('rating') else 0.0,
                        'image': None  # CSV doesn't store images
                    })
                logger.info(f"Loaded {len(products)} products from CSV file")
                return jsonify(products)
        
        # If no persistent files, return current scraper data
        products = []
        for product in scraper.scraped_products:
            products.append({
                'title': product.product_name,
                'price': product.unit_price,
                'category': product.category,
                'sub_category': product.sub_category,
                'source_site': product.source_site,
                'rating': product.rating,
                'image': product.product_images[0] if product.product_images else None
            })
        return jsonify(products)
        
    except Exception as e:
        logger.error(f"Error loading products: {e}")
        return jsonify([])

@app.route('/download/<format>')
def download_data(format):
    """Download scraped data from persistent files"""
    try:
        if format == 'json':
            # Try to serve the persistent JSON file
            json_file = "scraped_data/products.json"
            if os.path.exists(json_file):
                return send_file(
                    json_file,
                    mimetype='application/json',
                    as_attachment=True,
                    download_name='products.json'
                )
            else:
                # Fallback to current data
                data = []
                for product in scraper.scraped_products:
                    data.append({
                        'product_name': product.product_name,
                        'unit_price': product.unit_price,
                        'category': product.category,
                        'source_site': product.source_site,
                        'source_url': product.source_url,
                        'rating': product.rating,
                        'scraped_at': product.scraped_at
                    })
                
                output = io.StringIO()
                json.dump(data, output, indent=2, default=str)
                output.seek(0)
                
                return send_file(
                    io.BytesIO(output.getvalue().encode()),
                    mimetype='application/json',
                    as_attachment=True,
                    download_name='products.json'
                )
        
        elif format == 'csv':
            # Try to serve the persistent CSV file
            csv_file = "scraped_data/products.csv"
            if os.path.exists(csv_file):
                return send_file(
                    csv_file,
                    mimetype='text/csv',
                    as_attachment=True,
                    download_name='products.csv'
                )
            else:
                # Fallback to current data
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(['Product Name', 'Price', 'Category', 'Site', 'URL', 'Rating', 'Scraped At'])
                
                for product in scraper.scraped_products:
                    writer.writerow([
                        product.product_name,
                        product.unit_price,
                        product.category,
                        product.source_site,
                        product.source_url,
                        product.rating,
                        product.scraped_at
                    ])
                
                output.seek(0)
                return send_file(
                    io.BytesIO(output.getvalue().encode()),
                    mimetype='text/csv',
                    as_attachment=True,
                    download_name='products.csv'
                )
        
        else:
            return jsonify({'error': 'Invalid format. Use json or csv'}), 400
            
    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/delete-all', methods=['POST'])
def delete_all_products():
    """Delete all scraped products (JSON and CSV files)"""
    if not check_auth():
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        json_file = "scraped_data/products.json"
        csv_file = "scraped_data/products.csv"
        
        deleted_files = []
        
        # Delete JSON file if it exists
        if os.path.exists(json_file):
            os.remove(json_file)
            deleted_files.append('products.json')
            logger.info(f"Deleted {json_file}")
        
        # Delete CSV file if it exists
        if os.path.exists(csv_file):
            os.remove(csv_file)
            deleted_files.append('products.csv')
            logger.info(f"Deleted {csv_file}")
        
        # Also clear the scraper's in-memory data
        scraper.scraped_products = []
        scraper.total_scraped = 0
        scraper.current_stats = {
            'total_products': 0,
            'site_breakdown': {},
            'current_site': '',
            'current_status': 'Ready'
        }
        
        if deleted_files:
            return jsonify({
                'success': True,
                'message': f'Successfully deleted: {", ".join(deleted_files)}',
                'deleted_files': deleted_files
            })
        else:
            return jsonify({
                'success': True,
                'message': 'No product files found to delete',
                'deleted_files': []
            })
            
    except Exception as e:
        logger.error(f"Error deleting products: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to delete products: {str(e)}'
        }), 500

@app.route('/api/db/connect', methods=['POST'])
def test_database_connection():
    """Test database connection"""
    try:
        data = request.get_json()
        result = scraper.test_database_connection(**data)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/db/insert', methods=['POST'])
def insert_products():
    """Insert products into database"""
    try:
        data = request.get_json()
        table_name = data.get('table_name', 'products')
        mapping = data.get('mapping', {})
        
        result = scraper.insert_products_to_database(table_name, mapping)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Database insertion error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/save', methods=['POST'])
def save_data():
    """Manually save current data to persistent files"""
    try:
        success = scraper.force_save()
        if success:
            return jsonify({
                'success': True,
                'message': f'Data saved successfully. {len(scraper.scraped_products)} products saved.'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No data to save'
            })
    except Exception as e:
        logger.error(f"Save error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/db/insert-all', methods=['POST'])
def insert_all_products():
    """Insert all products from JSON file to database"""
    try:
        # Get connection parameters from request
        data = request.get_json() or {}
        connection_params = {
            'host': data.get('host'),
            'user': data.get('user'),
            'password': data.get('password'),
            'database': data.get('database'),
            'port': data.get('port')
        }
        
        # Load products from JSON file
        json_file = "scraped_data/products.json"
        if not os.path.exists(json_file):
            return jsonify({
                'success': False,
                'message': 'No products.json file found. Please scrape some products first.'
            }), 400
        
        with open(json_file, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        if not products:
            return jsonify({
                'success': False,
                'message': 'No products found in JSON file.'
            }), 400
        
        # Use chunked insertion method for better performance
        result = db_manager.insert_products_chunked(test_mode=False, connection_params=connection_params)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Insert all products error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/db/insert-test', methods=['POST'])
def insert_test_product():
    """Insert single product for testing"""
    try:
        # Get connection parameters from request
        data = request.get_json() or {}
        connection_params = {
            'host': data.get('host'),
            'user': data.get('user'),
            'password': data.get('password'),
            'database': data.get('database'),
            'port': data.get('port')
        }
        
        # Load products from JSON file
        json_file = "scraped_data/products.json"
        if not os.path.exists(json_file):
            return jsonify({
                'success': False,
                'message': 'No products.json file found. Please scrape some products first.'
            }), 400
        
        with open(json_file, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        if not products:
            return jsonify({
                'success': False,
                'message': 'No products found in JSON file.'
            }), 400
        
        # Use chunked insertion method for testing (only first chunk)
        result = db_manager.insert_products_chunked(test_mode=True, connection_params=connection_params)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Insert test product error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/db/product-count')
def get_product_count():
    """Get total number of products available for insertion"""
    try:
        count = db_manager.get_product_count()
        return jsonify({
            'success': True,
            'count': count
        })
    except Exception as e:
        logger.error(f"Get product count error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def main():
    """Main entry point"""
    print("🕷️  UNIVERSAL PRODUCT SCRAPER")
    print("="*50)
    print("Complete solution for scraping Amazon, eBay, AliExpress, Etsy, Daraz, and ValueBox")
    print()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'web':
            print("🌐 Starting web interface...")
            print("Open your browser to: http://localhost:5000")
            
            try:
                webbrowser.open('http://localhost:5000')
            except:
                pass
            
            socketio.run(app, host='0.0.0.0', port=5000, debug=False)
            
        elif command == 'scrape':
            print("🔍 Starting command line scraping...")
            # Command line scraping logic here
            pass
        else:
            print("Usage: python app.py [web|scrape]")
    else:
        print("🌐 Starting web interface...")
        print("Open your browser to: http://localhost:5000")
        
        try:
            webbrowser.open('http://localhost:5000')
        except:
            pass
        
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)

if __name__ == "__main__":
    main()
