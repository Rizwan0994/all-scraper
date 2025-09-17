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

# Initialize scraper and database manager
scraper = UniversalScraper(socketio=socketio)
db_manager = DatabaseManager()

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
    """Get all scraped products from persistent files"""
    try:
        # Try to load from persistent JSON file first
        json_file = "scraped_data/products.json"
        if os.path.exists(json_file):
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                products = []
                for item in data:
                    products.append({
                        'title': item.get('product_name', ''),
                        'price': item.get('unit_price', 0.0),
                        'category': item.get('category', ''),
                        'sub_category': item.get('sub_category', ''),
                        'source_site': item.get('source_site', ''),
                        'rating': item.get('rating', 0.0),
                        'image': item.get('product_images', [None])[0] if item.get('product_images') else None
                    })
                logger.info(f"Loaded {len(products)} products from persistent file")
                return jsonify(products)
        
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
        
        # Insert all products with connection parameters
        result = db_manager.insert_products(products, test_mode=False, connection_params=connection_params)
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
        
        # Insert only first product for testing with connection parameters
        result = db_manager.insert_products(products, test_mode=True, connection_params=connection_params)
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
