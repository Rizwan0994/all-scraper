#!/usr/bin/env python3
"""
Universal Product Scraper - Main Application
A comprehensive web scraping solution for e-commerce sites
"""

import sys
import os
import logging
import webbrowser
from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO
from datetime import datetime
import json
import csv
import io

# Import our scraper modules
from scraper.universal_scraper import UniversalScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize scraper
scraper = UniversalScraper(socketio=socketio)

@app.route('/')
def index():
    """Main dashboard page"""
    stats = scraper.get_statistics(scraper.scraped_products)
    return render_template('index.html', stats=stats)

@app.route('/scrape', methods=['POST'])
def start_scraping():
    """Start scraping process"""
    try:
        data = request.get_json()
        keywords = data.get('keywords', '').split(',')
        max_products = data.get('max_products', 200)
        selected_sites = data.get('selected_sites', [])
        
        logger.info(f"Starting scraping with keywords: {keywords}")
        logger.info(f"Max products per site: {max_products}")
        logger.info(f"Selected sites: {selected_sites}")
        
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

@app.route('/status')
def get_status():
    """Get current scraping status"""
    stats = scraper.get_statistics(scraper.scraped_products)
    return jsonify(stats)

@app.route('/products')
def get_products():
    """Get all scraped products"""
    products = []
    for product in scraper.scraped_products:
        products.append({
            'title': product.product_name,
            'price': product.unit_price,
            'category': product.category,
            'sub_category': product.sub_category,
            'source_site': product.source_site,
            'rating': product.rating
        })
    return jsonify(products)

@app.route('/download/<format>')
def download_data(format):
    """Download scraped data"""
    if format == 'json':
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
            download_name=f'products_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
    
    elif format == 'csv':
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
            download_name=f'products_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )

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
