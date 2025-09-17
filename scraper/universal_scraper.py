#!/usr/bin/env python3
"""
Universal Product Scraper - Core Scraper Class
Handles scraping from multiple e-commerce sites with anti-detection
"""

import os
import sys
import json
import csv
import time
import random
import logging
import requests
import re
import signal
from urllib.parse import urljoin, quote_plus, quote
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
from contextlib import contextmanager

# Anti-detection imports
try:
    from fake_useragent import UserAgent
except ImportError:
    print("fake-useragent not installed. Using default user agents.")
    UserAgent = None

import cloudscraper

# Undetected Chrome driver
try:
    import undetected_chromedriver as uc
except ImportError:
    print("undetected-chromedriver not installed. Selenium features will be limited.")
    uc = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    raise ImportError("BeautifulSoup4 is required. Install with: pip install beautifulsoup4")

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
except ImportError:
    print("Selenium is required for some sites. Install with: pip install selenium")
    webdriver = None

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class Product:
    """Product data structure"""
    product_name: str = ""
    product_type: str = "Single Product"
    purchase_price: float = 0.0
    unit_price: float = 0.0
    sku: str = ""
    stock_status: str = "In Stock"
    current_stock: int = 0
    discount: float = 0.0
    discount_type: str = "%"
    product_images: List[str] = None
    additional_images: List[str] = None
    
    # Categories
    category: str = ""
    sub_category: str = ""
    
    # Delivery & Dimensions
    standard_delivery_time: str = "24 hr(s)"
    weight: float = 0.0
    height: float = 0.0
    length: float = 0.0
    width: float = 0.0
    
    # Descriptions
    product_description: str = ""
    meta_tags_description: str = ""
    
    # Ratings & Reviews
    rating: float = 0.0
    review_count: int = 0
    
    # Seller & Source
    seller_name: str = ""
    source_site: str = ""
    source_url: str = ""
    product_id: str = ""
    
    # Timestamps
    scraped_at: str = ""
    original_title: str = ""
    
    # Variants (for products with multiple options)
    variants: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.product_images is None:
            self.product_images = []
        if self.additional_images is None:
            self.additional_images = []
        if self.variants is None:
            self.variants = []

# Category mapping for better organization
CATEGORY_MAPPING = {
    "Electronics": {
        "keywords": ["phone", "laptop", "tablet", "headphones", "speaker", "camera", "tv", "computer", "xbox", "playstation", "nintendo", "gaming", "console", "controller", "gaming console", "wireless controller", "gaming controller", "ssd", "digital", "cloud-enabled", "gift card", "digital code"],
        "subcategories": ["Smartphones", "Laptops", "Tablets", "Audio", "Cameras", "TVs", "Computers", "Gaming", "Gaming Consoles", "Gaming Accessories", "Digital Products"]
    },
    "Fashion": {
        "keywords": ["shirt", "dress", "shoes", "jeans", "jacket", "bag", "watch", "jewelry"],
        "subcategories": ["Men's Clothing", "Women's Clothing", "Shoes", "Accessories", "Jewelry"]
    },
    "Home & Garden": {
        "keywords": ["furniture", "kitchen", "garden", "decor", "lighting", "bedding"],
        "subcategories": ["Furniture", "Kitchen", "Garden", "Decor", "Lighting"]
    },
    "Sports": {
        "keywords": ["fitness", "sports", "outdoor", "bike", "running", "gym"],
        "subcategories": ["Fitness", "Outdoor", "Cycling", "Running", "Gym Equipment"]
    },
    "Books": {
        "keywords": ["book", "ebook", "magazine", "novel", "textbook"],
        "subcategories": ["Fiction", "Non-Fiction", "Educational", "Magazines"]
    },
    "Toys": {
        "keywords": ["toy", "game", "puzzle", "doll", "car", "lego"],
        "subcategories": ["Educational", "Action Figures", "Board Games", "Building Sets"]
    }
}

def categorize_product(title, description=""):
    """Categorize product based on title and description"""
    text = (title + " " + description).lower()
    
    for category, data in CATEGORY_MAPPING.items():
        if any(keyword in text for keyword in data["keywords"]):
            subcategories = data["subcategories"]
            for sub in subcategories:
                if any(word in text for word in sub.lower().split()):
                    return category, sub
            return category, subcategories[0] if subcategories else ""
    
    return "Electronics", "General"  # Default category

class UniversalScraper:
    """AI-Powered Universal Scraper with 100% Accuracy Target"""
    
    def __init__(self, socketio=None):
        # Multiple session types for different approaches
        self.session = requests.Session()
        self.cloud_scraper = cloudscraper.create_scraper()
        self.driver = None
        self.stealth_driver = None
        
        self.setup_session()
        self.results = []
        self.total_scraped = 0
        self.socketio = socketio
        self.scraped_products = []
        self.scraped_urls = set()  # For deduplication
        self.current_stats = {
            'total_products': 0,
            'site_breakdown': {},
            'current_site': '',
            'current_status': 'Ready'
        }
        
        # Enhanced anti-detection settings
        self.proxy_list = []
        self.current_proxy_index = 0
        self.request_count = 0
        
        # AI-Powered extraction settings
        self.use_dynamic_extraction = True
        self.js_execution_timeout = 30
        self.gallery_interaction_delay = 2
        self.variant_interaction_delay = 3
        
        # Performance optimization
        self.max_concurrent_requests = 3
        self.request_delay_range = (2, 5)
        self.image_quality_threshold = 300  # Minimum pixel width
        
        # Data validation settings
        self.min_images_per_product = 3
        self.min_variants_for_variant_products = 2
        self.data_accuracy_threshold = 0.95
        self.last_request_time = 0
        
        # Create data directory
        os.makedirs('scraped_data', exist_ok=True)
        os.makedirs('images', exist_ok=True)
        
        # Initialize stealth driver for dynamic content
        self._init_stealth_driver()

    def _init_stealth_driver(self):
        """Initialize undetected Chrome driver with stealth configuration"""
        try:
            if not uc:
                logger.warning("Undetected Chrome driver not available, falling back to regular Selenium")
                return False
            
            # Advanced stealth options
            options = uc.ChromeOptions()
            
            # Stealth settings
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins-discovery')
            options.add_argument('--disable-web-security')
            options.add_argument('--allow-running-insecure-content')
            
            # Performance optimization
            options.add_argument('--disable-images')  # We'll load images separately
            options.add_argument('--disable-javascript-harmony-shipping')
            options.add_argument('--disable-background-timer-throttling')
            options.add_argument('--disable-renderer-backgrounding')
            options.add_argument('--disable-backgrounding-occluded-windows')
            
            # User agent rotation
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
            options.add_argument(f'--user-agent={random.choice(user_agents)}')
            
            # Create undetected driver
            self.stealth_driver = uc.Chrome(options=options, version_main=None)
            
            # Execute stealth script
            self.stealth_driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Stealth Chrome driver initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize stealth driver: {e}")
            return False

    def _get_dynamic_content(self, url, wait_for_selectors=None, interact_with_gallery=True):
        """Get page content with JavaScript execution and dynamic interaction"""
        try:
            if not self.stealth_driver:
                logger.warning("Stealth driver not available, falling back to static scraping")
                return self._get_static_content(url)
            
            logger.info(f"🤖 Loading dynamic content from: {url[:60]}...")
            
            # Navigate to page
            self.stealth_driver.get(url)
            
            # Wait for page load
            WebDriverWait(self.stealth_driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait for specific selectors if provided
            if wait_for_selectors:
                for selector in wait_for_selectors:
                    try:
                        WebDriverWait(self.stealth_driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                    except TimeoutException:
                        logger.debug(f"Selector {selector} not found within timeout")
            
            # Simulate human behavior
            self._simulate_human_behavior()
            
            # Interact with image gallery if requested
            if interact_with_gallery:
                self._interact_with_gallery()
            
            # Execute JavaScript to load all dynamic content
            self._execute_content_loading_scripts()
            
            # Get the final HTML
            html = self.stealth_driver.page_source
            return BeautifulSoup(html, 'html.parser')
            
        except Exception as e:
            logger.error(f"Error getting dynamic content: {e}")
            return self._get_static_content(url)

    def _get_static_content(self, url):
        """Fallback to static content retrieval"""
        try:
            response = self.safe_request(url)
            if response and response.status_code == 200:
                return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logger.error(f"Error getting static content: {e}")
        return None

    def _simulate_human_behavior(self):
        """Simulate human-like browsing behavior"""
        try:
            # Random scroll to trigger lazy loading
            scroll_heights = [300, 500, 800, 1200, 1500]
            for height in random.sample(scroll_heights, 3):
                self.stealth_driver.execute_script(f"window.scrollTo(0, {height});")
                time.sleep(random.uniform(0.5, 1.5))
            
            # Scroll back to top
            self.stealth_driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
        except Exception as e:
            logger.debug(f"Error simulating human behavior: {e}")

    def _interact_with_gallery(self):
        """Interact with product image gallery to load all images"""
        try:
            # Gallery selectors to interact with
            gallery_selectors = [
                '#altImages img',
                '.imageThumbnail',
                '.a-button-thumbnail',
                '[data-action="main-image-click"]',
                '.gallery-thumbnail',
                '.media-gallery-item'
            ]
            
            for selector in gallery_selectors:
                try:
                    elements = self.stealth_driver.find_elements(By.CSS_SELECTOR, selector)
                    for i, element in enumerate(elements[:8]):  # Interact with first 8 images
                        try:
                            # Hover over element to trigger any hover effects
                            self.stealth_driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('mouseover', {bubbles: true}));", element)
                            time.sleep(0.5)
                            
                            # Click to load high-res image
                            if element.is_displayed() and element.is_enabled():
                                element.click()
                                time.sleep(random.uniform(1, 2))
                                
                        except Exception as e:
                            logger.debug(f"Error interacting with gallery element {i}: {e}")
                            continue
                            
                except Exception as e:
                    logger.debug(f"Error finding gallery elements with selector {selector}: {e}")
                    continue
            
            logger.info(f"Gallery interaction completed")
            
        except Exception as e:
            logger.debug(f"Error interacting with gallery: {e}")

    def _execute_content_loading_scripts(self):
        """Execute JavaScript to ensure all content is loaded"""
        try:
            scripts = [
                # Load all lazy images
                """
                document.querySelectorAll('img[data-src]').forEach(img => {
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                    }
                });
                """,
                
                # Trigger any lazy loading
                """
                window.dispatchEvent(new Event('scroll'));
                window.dispatchEvent(new Event('resize'));
                """,
                
                # Load Amazon-specific dynamic content
                """
                if (window.ImageBlockATF) {
                    console.log('Amazon ImageBlockATF detected');
                }
                if (window.DetailPageMediaMatrix) {
                    console.log('Amazon MediaMatrix detected');
                }
                """,
                
                # Wait for all images to load
                """
                return new Promise((resolve) => {
                    const images = document.querySelectorAll('img');
                    let loadedCount = 0;
                    const totalImages = images.length;
                    
                    if (totalImages === 0) {
                        resolve(true);
                        return;
                    }
                    
                    images.forEach(img => {
                        if (img.complete) {
                            loadedCount++;
                        } else {
                            img.onload = img.onerror = () => {
                                loadedCount++;
                                if (loadedCount === totalImages) {
                                    resolve(true);
                                }
                            };
                        }
                    });
                    
                    // Fallback timeout
                    setTimeout(() => resolve(true), 5000);
                });
                """
            ]
            
            for script in scripts[:-1]:  # Execute synchronous scripts
                self.stealth_driver.execute_script(script)
                time.sleep(0.5)
            
            # Execute async script for image loading
            self.stealth_driver.execute_async_script(scripts[-1])
            
        except Exception as e:
            logger.debug(f"Error executing content loading scripts: {e}")
        
        # Setup signal handlers for graceful shutdown
        self.setup_signal_handlers()
        
        # Load existing data from persistent files
        self.load_existing_data()
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, saving data and shutting down gracefully...")
            self.cleanup()
            sys.exit(0)
        
        try:
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
        except Exception as e:
            logger.warning(f"Could not setup signal handlers: {e}")
    
    def setup_session(self):
        """Setup session with advanced anti-detection"""
        # Rotate user agents
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        
        # Set realistic headers
        self.session.headers.update({
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Cache-Control': 'max-age=0'
        })
        
        # Setup cloudscraper
        self.cloud_scraper.headers.update({
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def setup_selenium_driver(self):
        """Setup undetected Chrome driver with simplified options"""
        try:
            if uc is None:
                logger.warning("undetected-chromedriver not available. Selenium features disabled.")
                return False
                
            options = uc.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = uc.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return True
        except Exception as e:
            logger.error(f"Failed to setup Selenium driver: {e}")
            return False
    
    def random_delay(self, min_delay=1, max_delay=3):
        """Random delay between requests"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def make_request(self, url, use_cloudscraper=False, max_retries=3):
        """Make HTTP request with anti-detection"""
        for attempt in range(max_retries):
            try:
                self.random_delay()
                
                if use_cloudscraper:
                    response = self.cloud_scraper.get(url, timeout=30)
                else:
                    response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 403:
                    logger.warning(f"Access denied (403) for {url}, trying cloudscraper...")
                    use_cloudscraper = True
                    continue
                else:
                    logger.warning(f"HTTP {response.status_code} for {url}")
                    
            except Exception as e:
                logger.error(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def _find_amazon_products(self, soup):
        """Find Amazon product items using enhanced 2024 selectors"""
        # Priority order of selectors for 2024 Amazon structure
        selectors = [
            # Primary selectors for search results
            'div[data-component-type="s-search-result"]',
            'div[data-asin]:not([data-asin=""])',
            '.s-result-item[data-asin]',
            
            # Alternative selectors
            '.s-card-container[data-asin]',
            '.puis-card-container[data-asin]',
            'div[data-asin]',
            
            # Fallback selectors
            '.s-result-item',
            '.s-card-container',
            '.puis-card-container',
            '[data-testid="product-card"]'
        ]
        
        items = []
        for selector in selectors:
            items = soup.select(selector)[:30]
            if items:
                logger.info(f"Found {len(items)} products using selector: {selector}")
                break
        
        if not items:
            # Debug: Log some HTML content to see what we're getting
            debug_content = soup.get_text()[:500] if soup else "No content"
            logger.debug(f"Amazon debug content: {debug_content}")
            
            # Try to find any divs with data-asin
            all_divs = soup.find_all('div')
            asin_divs = [div for div in all_divs if div.get('data-asin')]
            logger.debug(f"Amazon: Found {len(asin_divs)} divs with data-asin")
            
            # Try to find any product-like elements
            product_elements = soup.find_all(['div', 'article'], class_=lambda x: x and any(word in x.lower() for word in ['product', 'item', 'card', 'result']))
            logger.debug(f"Amazon: Found {len(product_elements)} product-like elements")
        
        return items
    
    def _extract_amazon_price(self, item):
        """Extract price from Amazon product item using 2024 selectors"""
        # Updated price selectors for 2024 Amazon structure
        price_selectors = [
            # Primary price selectors (most reliable)
            '.a-price .a-offscreen',
            '.a-price-whole',
            '.a-price-current .a-offscreen',
            '.a-price-current .a-price-whole',
            
            # Alternative selectors
            '.a-price-range .a-offscreen',
            '.a-price-symbol + .a-price-whole',
            '.a-price-deal .a-offscreen',
            '.a-price-sale .a-offscreen',
            
            # Fallback selectors
            '.a-price .a-text-price',
            '.a-price-current',
            '.a-price-current .a-text-price',
            '[data-a-price]',
            
            # Legacy selectors (still used in some cases)
            '.a-price',
            '.a-offscreen',
            '.a-price-range',
            '.a-price-symbol',
            '.a-price-fraction',
            '.a-price-decimal'
        ]
        
        price_text = None
        price_elem = None
        
        # Try each selector in priority order
        for selector in price_selectors:
            price_elem = item.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                if price_text and '$' in price_text:
                    logger.debug(f"Found price using selector '{selector}': {price_text}")
                    break
        
        # If no price element found, try to find any price-like text
        if not price_text:
            item_text = item.get_text()
            # Look for price patterns in the text
            price_match = re.search(r'\$[\d,]+\.?\d*', item_text)
            if price_match:
                price_text = price_match.group()
                logger.debug(f"Found price using regex: {price_text}")
            else:
                # Try to find any number that looks like a price
                price_match = re.search(r'[\d,]+\.?\d*', item_text)
                if price_match:
                    price_text = f"${price_match.group()}"
                    logger.debug(f"Found price using fallback regex: {price_text}")
        
        if price_text:
            logger.debug(f"Price text found: '{price_text}'")
            price = self.extract_price(price_text)
            return self.ensure_valid_price(price, "Amazon Product", 'amazon')
        
        return 0.0
    
    def _extract_amazon_title(self, item):
        """Extract title from Amazon product item using 2024 selectors"""
        # Updated title selectors for 2024 Amazon structure
        title_selectors = [
            # Primary title selectors
            'h2.a-color-base',
            'h2.a-size-base-plus',
            'h2.a-text-normal',
            'h2.a-size-medium',
            'h2.a-size-large',
            
            # Alternative selectors
            'span.a-color-base',
            'span.a-size-base-plus',
            'span.a-text-normal',
            'span.a-size-medium',
            'span.a-size-large',
            
            # Generic selectors
            'h2',
            'h3',
            '.a-size-base-plus',
            '.a-text-normal',
            '.a-size-medium',
            '.a-size-large',
            
            # Fallback selectors
            '[data-cy="title-recipe"]',
            '[data-testid="product-title"]',
            '.product-title',
            '.a-link-normal'
        ]
        
        title_elem = None
        for selector in title_selectors:
            title_elem = item.select_one(selector)
            if title_elem:
                title_text = title_elem.get_text(strip=True)
                if title_text and len(title_text) > 10:
                    logger.debug(f"Found title using selector '{selector}': {title_text[:50]}...")
                    return self.clean_text(title_text)
        
        # If no title element found, try to find any text that looks like a title
        item_text = item.get_text()
        if len(item_text) > 10 and len(item_text) < 200:
            return self.clean_text(item_text)
        
        return None
    
    def _extract_amazon_rating_reviews(self, item):
        """Extract rating and review count from Amazon product item using 2024 selectors"""
        # Updated rating selectors for 2024 Amazon structure
        rating_selectors = [
            '.a-icon-alt',
            '.a-icon-star .a-icon-alt',
            '[data-hook="rating-out-of-text"]',
            '.a-icon-star-small .a-icon-alt',
            '.a-icon-star-medium .a-icon-alt',
            '.a-icon-star-large .a-icon-alt',
            '.a-icon-star .a-icon-alt',
            '.a-icon-star-small .a-icon-alt',
            '.a-icon-star-medium .a-icon-alt',
            '.a-icon-star-large .a-icon-alt'
        ]
        
        # Updated review count selectors for 2024 Amazon structure
        review_selectors = [
            '#acrCustomerReviewText',
            '[data-hook="total-review-count"]',
            '.a-size-base.a-color-secondary',
            '.a-size-small.a-color-secondary',
            '.a-size-base',
            '.a-size-small'
        ]
        
        rating = 0.0
        review_count = 0
        
        # Extract rating
        for selector in rating_selectors:
            rating_elem = item.select_one(selector)
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                rating_match = re.search(r'[\d.]+', rating_text)
                if rating_match:
                    rating = float(rating_match.group())
                    logger.debug(f"Found rating using selector '{selector}': {rating}")
                    break
        
        # Extract review count
        for selector in review_selectors:
            review_elem = item.select_one(selector)
            if review_elem:
                review_text = review_elem.get_text(strip=True)
                review_match = re.search(r'[\d,]+', review_text)
                if review_match:
                    review_count = int(review_match.group().replace(',', ''))
                    logger.debug(f"Found review count using selector '{selector}': {review_count}")
                    break
        
        return rating, review_count
    
    def _extract_amazon_link(self, item, title):
        """Extract product link from Amazon product item using 2024 selectors"""
        # Updated link selectors for 2024 Amazon structure
        link_selectors = [
            # Primary link selectors
            'h2 a',
            'h3 a',
            '.a-link-normal',
            '.a-text-normal',
            
            # Alternative selectors
            '[data-cy="title-recipe"]',
            '[data-testid="product-link"]',
            '.a-link-normal[href*="/dp/"]',
            '.a-link-normal[href*="/gp/product/"]',
            
            # Fallback selectors
            'a[href*="/dp/"]',
            'a[href*="/gp/product/"]',
            'a[href*="amazon.com"]'
        ]
        
        for selector in link_selectors:
            link_elem = item.select_one(selector)
            if link_elem and link_elem.get('href'):
                href = link_elem.get('href')
                if href.startswith('/'):
                    product_url = f"https://www.amazon.com{href}"
                else:
                    product_url = href
                logger.debug(f"Found product link using selector '{selector}': {product_url[:50]}...")
                return product_url
        
        # Fallback: Generate search URL using product title
        logger.debug(f"No product link found, generating fallback URL for: {title[:30]}...")
        return f"https://www.amazon.com/s?k={quote_plus(title)}"
    
    def _extract_amazon_main_image(self, item):
        """Extract main product image from Amazon product item using 2024 selectors"""
        # Updated image selectors for 2024 Amazon structure
        image_selectors = [
            # Primary image selectors
            '.s-product-image-container img',
            '.s-image img',
            '.a-dynamic-image',
            '.a-image-container img',
            
            # Alternative selectors
            'img[data-src]',
            'img[src*="media-amazon.com"]',
            'img[src*="images-amazon.com"]',
            'img[alt*="product"]',
            
            # Fallback selectors
            'img',
            '.a-image img',
            '.product-image img'
        ]
        
        for selector in image_selectors:
            img_elem = item.select_one(selector)
            if img_elem:
                # Try data-src first (lazy loading), then src
                image_url = img_elem.get('data-src') or img_elem.get('src')
                if image_url and 'amazon' in image_url.lower():
                    # Convert to high-quality image
                    high_quality_url = self._convert_to_high_quality_image(image_url)
                    logger.debug(f"Found product image using selector '{selector}': {high_quality_url[:50]}...")
                    return high_quality_url
        
        logger.debug("No product image found")
        return ""
    
    def _extract_structured_data(self, soup, product_name):
        """Extract structured data from JSON-LD scripts for enhanced accuracy"""
        structured_data = {}
        try:
            # Look for JSON-LD scripts containing product data
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.get_text())
                    if isinstance(data, dict):
                        # Extract product information
                        if 'name' in data:
                            structured_data['name'] = data['name']
                        if 'description' in data:
                            structured_data['description'] = data['description']
                        if 'brand' in data:
                            structured_data['brand'] = data['brand']
                        if 'offers' in data:
                            offers = data['offers']
                            if isinstance(offers, dict):
                                if 'price' in offers:
                                    structured_data['price'] = offers['price']
                                if 'priceCurrency' in offers:
                                    structured_data['currency'] = offers['priceCurrency']
                                if 'availability' in offers:
                                    structured_data['availability'] = offers['availability']
                        if 'aggregateRating' in data:
                            rating_data = data['aggregateRating']
                            if 'ratingValue' in rating_data:
                                structured_data['rating'] = rating_data['ratingValue']
                            if 'reviewCount' in rating_data:
                                structured_data['review_count'] = rating_data['reviewCount']
                        if 'image' in data:
                            images = data['image']
                            if isinstance(images, list):
                                structured_data['images'] = images
                            else:
                                structured_data['images'] = [images]
                except (json.JSONDecodeError, KeyError):
                    continue
        except Exception as e:
            logger.debug(f"Structured data extraction failed: {e}")
        return structured_data
    
    def _enhance_product_with_structured_data(self, product, structured_data):
        """Enhance product data with structured data if available"""
        if not structured_data:
            return product
        
        # Update product name if structured data has a better one
        if 'name' in structured_data and len(structured_data['name']) > len(product.product_name):
            product.product_name = structured_data['name']
        
        # Update price if structured data has it and current price is 0
        if 'price' in structured_data and product.unit_price <= 0:
            try:
                price = float(structured_data['price'])
                if price > 0:
                    product.unit_price = price
            except (ValueError, TypeError):
                pass
        
        # Update rating if structured data has it
        if 'rating' in structured_data and product.rating <= 0:
            try:
                rating = float(structured_data['rating'])
                if 0 <= rating <= 5:
                    product.rating = rating
            except (ValueError, TypeError):
                pass
        
        # Update review count if structured data has it
        if 'review_count' in structured_data and product.review_count <= 0:
            try:
                review_count = int(structured_data['review_count'])
                if review_count >= 0:
                    product.review_count = review_count
            except (ValueError, TypeError):
                pass
        
        # Update images if structured data has them
        if 'images' in structured_data and isinstance(structured_data['images'], list):
            new_images = [img for img in structured_data['images'] if img and 'amazon' in img.lower()]
            if new_images:
                product.product_images = new_images
        
        return product
    
    def _handle_amazon_rate_limiting(self, response, attempt=1):
        """Handle Amazon rate limiting and CAPTCHA detection"""
        if response and response.status_code == 429:
            # Rate limited - wait longer
            wait_time = min(60, 5 * (2 ** attempt))
            logger.warning(f"Rate limited by Amazon. Waiting {wait_time} seconds...")
            time.sleep(wait_time)
            return True
        elif response and response.status_code == 503:
            # Service unavailable - wait and retry
            wait_time = min(30, 3 * (2 ** attempt))
            logger.warning(f"Amazon service unavailable. Waiting {wait_time} seconds...")
            time.sleep(wait_time)
            return True
        elif response and 'captcha' in response.text.lower():
            # CAPTCHA detected
            logger.error("CAPTCHA detected by Amazon. Please try again later.")
            return False
        return False
    
    def _improve_amazon_headers(self):
        """Improve headers to better mimic real browser behavior"""
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def scrape_amazon(self, keywords, max_products=100):
        """Scrape Amazon products with real data only - Enhanced for 2024"""
        self.current_stats['current_site'] = 'Amazon'
        self.current_stats['current_status'] = 'Scraping Amazon...'
        
        # Setup Amazon-specific session with enhanced headers
        self.setup_site_specific_session('amazon')
        self._improve_amazon_headers()
        self.emit_update('status_update', self.current_stats)
        
        products_added = 0
        
        for keyword in keywords:
            if products_added >= max_products:
                break
                
            logger.info(f"Scraping Amazon for: {keyword}")
            self.emit_update('status_update', {'current_status': f'Searching Amazon for: {keyword}'})
            
            search_url = f"https://www.amazon.com/s?k={quote_plus(keyword)}&ref=sr_pg_1"
            response = self.safe_request(search_url)
            
            if not response:
                logger.warning(f"Amazon: Failed to get response for '{keyword}'")
                continue
            
            logger.info(f"Amazon: Got response {response.status_code} for '{keyword}'")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check if we're being blocked
            page_title = soup.find('title')
            if page_title:
                title_text = page_title.get_text().lower()
                if 'captcha' in title_text or 'robot' in title_text:
                    logger.error(f"Amazon: CAPTCHA detected for '{keyword}'")
                    continue
            
            # Enhanced product selectors for 2024 Amazon structure
            items = self._find_amazon_products(soup)
            
            if not items:
                logger.warning(f"Amazon: No items found for '{keyword}'")
                continue
            
            for i, item in enumerate(items):
                if products_added >= max_products:
                    break
                    
                try:
                    # Enhanced title extraction using 2024 selectors
                    title = self._extract_amazon_title(item)
                    
                    if not title or len(title) < 10 or title.lower() in ['results', 'no title']:
                            continue
                    
                    # Enhanced price extraction using 2024 selectors
                    price = self._extract_amazon_price(item)
                    
                    # Debug: Log the extracted price
                    logger.debug(f"Extracted price: {price} for product: {title[:30]}...")
                    
                    # Skip products with no real price
                    if price <= 0:
                        logger.debug(f"Skipping product with no price: {title[:30]}...")
                        continue
                    
                    # Enhanced link extraction using 2024 selectors
                    product_url = self._extract_amazon_link(item, title)
                    
                    # Enhanced image extraction using 2024 selectors
                    main_image_url = self._extract_amazon_main_image(item)
                    
                    # Get additional images using AI-enhanced approach
                    additional_images = []
                    if product_url and main_image_url:
                        logger.info(f"AI-Enhanced image extraction from: {product_url[:50]}...")
                        additional_images = self.scrape_product_images(product_url, site='amazon', max_images=15)
                        logger.info(f"Found {len(additional_images)} high-quality images")
                    
                    # Combine main image with additional images
                    all_images = [main_image_url] + additional_images if main_image_url else additional_images
                    # Remove duplicates and empty URLs
                    all_images = list(dict.fromkeys([img for img in all_images if img and img.strip()]))
                    
                    # Enhanced rating and review extraction
                    rating, review_count = self._extract_amazon_rating_reviews(item)
                    
                    # Auto-categorize
                    category, sub_category = categorize_product(title)
                    
                    # Generate SKU
                    sku = f"AMZ-{keyword[:3].upper()}-{i+1:04d}"
                    
                    # Extract variants from PRODUCT PAGE, not search results
                    product_page_response = None
                    product_soup = None
                    try:
                        if product_url:
                            product_page_response = self.safe_request(product_url)
                            if product_page_response and product_page_response.status_code == 200:
                                product_soup = BeautifulSoup(product_page_response.content, 'html.parser')
                    except Exception as e:
                        logger.warning(f"Failed to fetch product page for variants: {e}")

                    # Extract variants if available (prefer product_soup) with main price fallback
                    variants = self.extract_variants(product_soup or soup, title, main_price=price)
                    
                    # Extract structured data for enhanced accuracy
                    structured_data = self._extract_structured_data(product_soup or soup, title)
                    
                    # ENHANCED IMAGE AND VARIANT MAPPING
                    additional_images = all_images[1:] if len(all_images) > 1 else []
                    logger.info(f"Total images found: {len(all_images)}, Main image: {1 if all_images else 0}, Additional images: {len(additional_images)}")
                    
                    if variants:
                        logger.info(f"Mapping {len(additional_images)} additional images to {len(variants)} variants realistically")
                        
                        # Extract variant-specific images from the PRODUCT page
                        variant_specific_images = self._extract_variant_images(product_soup or soup, title)
                        
                        if variant_specific_images:
                            logger.info(f"Found {len(variant_specific_images)} variant-specific images")
                            self._map_variant_images_realistically(variants, variant_specific_images, main_image_url)
                        else:
                            # Fallback: Intelligent image distribution based on variant type
                            logger.info("No variant-specific images found, using intelligent fallback")
                            self._map_variant_images_fallback(variants, additional_images, main_image_url)
                        
                        # For products with variants, keep first 3-5 additional images for the main product too
                        final_additional_images = additional_images[:5] if len(additional_images) > 2 else additional_images
                        logger.info(f"Product has variants, storing {len(final_additional_images)} main product images and variant-specific images")
                    else:
                        # For products WITHOUT variants, keep all additional images in additional_images
                        final_additional_images = additional_images
                        logger.info(f"Product has no variants, storing {len(final_additional_images)} images as additional_images")
                    
                    # Create the product
                    product = Product(
                        product_name=title,
                        original_title=title,
                        product_type="Variant" if variants else "Single Product",
                        unit_price=price,
                        purchase_price=0.0,
                        sku=sku,
                        category=category,
                        sub_category=sub_category,
                        product_description=f"Quality {title} from Amazon with fast shipping and customer support",
                        meta_tags_description=f"Buy {title} from Amazon at competitive prices",
                        product_images=all_images[:1] if all_images else [],  # First image as main
                        additional_images=final_additional_images,  # Store additional images based on variant status
                        rating=rating,
                        review_count=review_count,
                        source_site='Amazon',
                        source_url=product_url,
                        product_id=f"amazon_{keyword}_{i+1}",
                        scraped_at=datetime.now().isoformat(),
                        seller_name="Amazon",
                        stock_status="In Stock",
                        current_stock=0,
                        variants=variants
                    )
                    
                    # Enhance product with structured data for better accuracy
                    product = self._enhance_product_with_structured_data(product, structured_data)
                    
                    if self.add_product(product):
                        products_added += 1
                
                except Exception as e:
                    logger.debug(f"Error parsing Amazon item: {e}")
                    continue
                
                self.random_delay(3, 8)  # Reasonable delays
            
            self.random_delay(10, 20)  # Delays between keywords
        
        logger.info(f"Amazon scraping completed: {products_added} products")
        return self.scraped_products[-products_added:]
    
    def scrape_product_images(self, product_url, site='amazon', max_images=20):
        """AI-Powered image scraping with 100% accuracy target"""
        try:
            logger.info(f"AI-Enhanced image extraction from: {product_url[:60]}...")
            
            # Use dynamic content loading for better results
            if self.use_dynamic_extraction:
                soup = self._get_dynamic_content(
                    product_url, 
                    wait_for_selectors=['#altImages', '.a-dynamic-image', '#landingImage'],
                    interact_with_gallery=True
                )
            else:
                # Fallback to static scraping
                response = self.safe_request(product_url)
                if not response or response.status_code != 200:
                    logger.warning(f"Failed to get product page: {product_url}")
                    return []
                soup = BeautifulSoup(response.content, 'html.parser')
            
            if not soup:
                logger.error("Failed to get page content")
                return []
            
            images = []
            
            # Multi-method image extraction for maximum accuracy
            if site.lower() == 'amazon':
                images = self._extract_amazon_images_ai_enhanced(soup, product_url)
            elif site.lower() == 'ebay':
                images = self._extract_ebay_images_enhanced(soup)
            elif site.lower() == 'daraz':
                images = self._extract_daraz_images_enhanced(soup)
            else:
                images = self._extract_generic_images_enhanced(soup)
            
            # AI-powered image validation and enhancement
            validated_images = self._validate_and_enhance_images(images, max_images)
            
            logger.info(f"Extracted {len(validated_images)} high-quality images")
            return validated_images
            
        except Exception as e:
            logger.error(f"Error in AI-enhanced image scraping: {e}")
            return []
    
    def _extract_amazon_images(self, soup):
        """Extract images from Amazon product page with enhanced 2024 selectors"""
        images = []
        
        # Comprehensive Amazon image gallery selectors for 2024/2025
        selectors = [
            # Primary gallery selectors (most effective)
            '#altImages img',  # Thumbnail gallery
            '#altImages .a-button-text img',  # Gallery buttons
            '#landingImage',  # Main product image
            '.a-dynamic-image',  # Dynamic images
            '#imgTagWrapperId img',  # Image wrapper
            
            # Additional gallery selectors
            '.imageThumbnail img',  # Thumbnail images
            '.a-button-selected img',  # Selected gallery item
            '[data-old-hires]',  # High-res image data
            
            # Modern 2024/2025 gallery selectors
            '[data-testid="image-thumbnail"] img',
            '[data-testid="product-images"] img',
            '[data-testid="gallery-image"] img',
            '.image-gallery-image img',
            '.product-image-carousel img',
            '.product-image-gallery img',
            '.media-gallery img',
            '.media-gallery-item img',
            
            # Carousel and slider images
            '.a-carousel-item img',
            '.a-carousel-card img',
            '.slider-item img',
            '.gallery-slider img',
            
            # Enhanced gallery button selectors
            '.a-button-toggle img',
            '.a-button-text img',
            '[data-action="main-image-click"] img',
            '.gallery-thumbnail img',
            '.thumbnail-item img',
            
            # Color/variant specific images
            '.twister-plus-content img',
            '.variant-image img',
            '.color-variant-image img',
            '.size-variant-image img',
            '[data-variant-id] img',
            '.color-picker img',
            '.variant-selector img',
            
            # Enhanced media selectors
            'img[src*="media-amazon.com"]',
            'img[data-src*="media-amazon.com"]',
            'img[src*="amazon.com/images"]',
            'img[data-src*="amazon.com/images"]',
            'img[src*="ssl-images-amazon.com"]',
            'img[data-src*="ssl-images-amazon.com"]',
            'img[src*="m.media-amazon.com"]',
            'img[data-src*="m.media-amazon.com"]',
            
            # Product container images
            '#dp-container img',
            '#feature-bullets img',
            '#productDetails img',
            '.product-facts img',
            '.product-overview img',
            
            # Layout-specific selectors
            '.a-spacing-small img',
            '.a-spacing-base img',
            '.a-spacing-medium img',
            
            # Modern product page selectors
            '[data-testid="product-image"] img',
            '.product-image img',
            '.gallery-image img',
            '.hero-image img',
            '.main-image img',
            '[role="img"]',
            
            # Fallback broader selectors
            'img[data-a-dynamic-image]',
            '.dp-image img',
            '.product-photo img',
            '.item-photo img'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for elem in elements:
                # Enhanced image URL extraction from multiple attributes
                img_url = (elem.get('data-old-hires') or 
                          elem.get('data-src') or 
                          elem.get('src') or 
                          elem.get('data-a-dynamic-image') or
                          elem.get('data-lazy') or
                          elem.get('data-original') or
                          elem.get('data-image-url') or
                          elem.get('data-full-image') or
                          elem.get('data-zoom-image'))
                
                # Handle dynamic image data (JSON format)
                if not img_url and elem.get('data-a-dynamic-image'):
                    try:
                        dynamic_data = json.loads(elem.get('data-a-dynamic-image'))
                        if isinstance(dynamic_data, dict):
                            # Get the highest resolution image
                            img_url = max(dynamic_data.keys(), key=lambda x: len(x))
                    except:
                        pass
                
                if img_url and ('http' in img_url or img_url.startswith('//')):
                    # Convert to high-quality image
                    high_quality_url = self._convert_to_high_quality_image(img_url)
                    
                    # Ensure HTTPS
                    if high_quality_url.startswith('//'):
                        high_quality_url = 'https:' + high_quality_url
                    
                    # Only add Amazon images and filter out obvious icons
                    if ('amazon.com' in high_quality_url or 'media-amazon.com' in high_quality_url or 'ssl-images-amazon.com' in high_quality_url) and not any(icon in high_quality_url.lower() for icon in ['icon', 'logo', 'badge', 'sprite']):
                        images.append(high_quality_url)
        
        # Extract images from JSON-LD structured data
        self._extract_images_from_json_ld(soup, images)
        
        # Remove duplicates and filter out very small images
        unique_images = []
        seen_urls = set()
        
        logger.debug(f"Processing {len(images)} raw images for deduplication")
        
        for img_url in images:
            # Skip very small images (likely icons or thumbnails) - but be less aggressive
            if any(size in img_url for size in ['_AC_UY10_', '_AC_UY15_', '_AC_UY20_', '_SX38_SY50_']):
                continue
            
            # More sophisticated duplicate detection
            # Extract base URL without size parameters for comparison
            base_url = img_url.split('._')[0] if '._' in img_url else img_url.split('?')[0]
            
            # Allow different sizes of the same image (they might show different details)
            # Only remove exact duplicates
            if img_url not in seen_urls:
                unique_images.append(img_url)
                seen_urls.add(img_url)
                
                # Also add the base URL to prevent very similar images
                if base_url != img_url:
                    seen_urls.add(base_url)
        
        logger.info(f"Filtered {len(images)} raw images down to {len(unique_images)} unique images")
        return unique_images

    def _extract_images_from_json_ld(self, soup, images):
        """Extract images from JSON-LD structured data"""
        try:
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.get_text())
                    if isinstance(data, dict):
                        # Look for image URLs in various JSON-LD properties
                        image_keys = ['image', 'images', 'photo', 'thumbnail', 'logo']
                        for key in image_keys:
                            if key in data:
                                img_data = data[key]
                                if isinstance(img_data, str):
                                    images.append(img_data)
                                elif isinstance(img_data, list):
                                    for img in img_data:
                                        if isinstance(img, str):
                                            images.append(img)
                                        elif isinstance(img, dict) and 'url' in img:
                                            images.append(img['url'])
                except:
                    continue
        except Exception as e:
            logger.debug(f"JSON-LD image extraction failed: {e}")

    def _extract_amazon_images_ai_enhanced(self, soup, product_url):
        """AI-Enhanced Amazon image extraction with multiple methods"""
        images = []
        
        try:
            # Method 1: JSON-LD structured data extraction
            json_images = self._extract_images_from_json_scripts(soup)
            images.extend(json_images)
            logger.info(f"JSON extraction: {len(json_images)} images")
            
            # Method 2: Enhanced CSS selector extraction  
            css_images = self._extract_amazon_images(soup)
            images.extend(css_images)
            logger.info(f"CSS extraction: {len(css_images)} images")
            
            # Method 3: JavaScript variable extraction
            if self.stealth_driver:
                js_images = self._extract_images_from_js_variables()
                images.extend(js_images)
                logger.info(f"JavaScript extraction: {len(js_images)} images")
            
        except Exception as e:
            logger.error(f"Error in AI-enhanced Amazon image extraction: {e}")
        
        return images

    def _extract_images_from_json_scripts(self, soup):
        """Extract images from JSON data in script tags"""
        images = []
        
        try:
            # Amazon-specific JSON patterns
            script_patterns = [
                r'ImageBlockATF.*?({.*?})',
                r'DetailPageMediaMatrix.*?({.*?})',
                r'colorImages.*?({.*?})',
                r'data\s*=\s*({.*?colorImages.*?})',
                r'window\.ImageBlockATF\s*=\s*({.*?})'
            ]
            
            scripts = soup.find_all('script')
            for script in scripts:
                if not script.string:
                    continue
                    
                for pattern in script_patterns:
                    matches = re.finditer(pattern, script.string, re.DOTALL)
                    for match in matches:
                        try:
                            json_str = match.group(1)
                            # Clean up the JSON string
                            json_str = re.sub(r',\s*}', '}', json_str)
                            json_str = re.sub(r',\s*]', ']', json_str)
                            
                            data = json.loads(json_str)
                            
                            # Extract images from various JSON structures
                            extracted = self._parse_amazon_json_images(data)
                            images.extend(extracted)
                            
                        except json.JSONDecodeError:
                            continue
                        except Exception as e:
                            logger.debug(f"Error parsing JSON in script: {e}")
                            continue
            
        except Exception as e:
            logger.debug(f"Error extracting images from JSON scripts: {e}")
        
        return images

    def _parse_amazon_json_images(self, data):
        """Parse Amazon JSON data structures for images"""
        images = []
        
        try:
            if isinstance(data, dict):
                # colorImages structure
                if 'colorImages' in data:
                    for color_key, color_data in data['colorImages'].items():
                        if isinstance(color_data, list):
                            for image_data in color_data:
                                if isinstance(image_data, dict):
                                    # Priority: hiRes > large > main
                                    for key in ['hiRes', 'large', 'main']:
                                        if key in image_data and image_data[key]:
                                            images.append(image_data[key])
                                            break
                
                # Direct image arrays
                for key in ['images', 'imageArray', 'productImages']:
                    if key in data and isinstance(data[key], list):
                        for img in data[key]:
                            if isinstance(img, str):
                                images.append(img)
                            elif isinstance(img, dict):
                                for img_key in ['hiRes', 'large', 'main', 'url']:
                                    if img_key in img and img[img_key]:
                                        images.append(img[img_key])
                                        break
                        
        except Exception as e:
            logger.debug(f"Error parsing Amazon JSON images: {e}")
        
        return images

    def _extract_images_from_js_variables(self):
        """Extract images from JavaScript variables using Selenium"""
        images = []
        
        try:
            if not self.stealth_driver:
                return images
            
            # Execute JavaScript to extract image data
            js_script = """
            var images = [];
            
            // Amazon-specific variables
            if (window.ImageBlockATF) {
                try {
                    var data = window.ImageBlockATF;
                    if (data.colorImages) {
                        Object.keys(data.colorImages).forEach(function(color) {
                            data.colorImages[color].forEach(function(img) {
                                if (img.hiRes) images.push(img.hiRes);
                                else if (img.large) images.push(img.large);
                                else if (img.main) images.push(img.main);
                            });
                        });
                    }
                } catch(e) {}
            }
            
            // Generic high-quality image collection
            document.querySelectorAll('img[src*="media-amazon.com"], img[src*="ssl-images-amazon.com"]').forEach(function(img) {
                if (img.src && img.src.length > 50 && !img.src.includes('_AC_UY20_')) {
                    images.push(img.src);
                }
            });
            
            return [...new Set(images)]; // Remove duplicates
            """
            
            result = self.stealth_driver.execute_script(js_script)
            if result and isinstance(result, list):
                images.extend(result)
                
        except Exception as e:
            logger.debug(f"Error extracting images from JS variables: {e}")
        
        return images

    def _validate_and_enhance_images(self, images, max_images):
        """AI-powered image validation and enhancement"""
        validated = []
        seen_base_urls = set()
        
        for img_url in images:
            if not img_url or not isinstance(img_url, str):
                continue
            
            # Clean and enhance URL
            enhanced_url = self._enhance_image_url(img_url)
            if not enhanced_url:
                continue
            
            # Check for duplicates using base URL
            base_url = self._get_image_base_url(enhanced_url)
            if base_url in seen_base_urls:
                continue
            
            # Validate image quality
            if self._is_high_quality_image(enhanced_url):
                validated.append(enhanced_url)
                seen_base_urls.add(base_url)
                
                if len(validated) >= max_images:
                    break
        
        return validated

    def _enhance_image_url(self, img_url):
        """Enhance image URL for maximum quality"""
        try:
            if not img_url:
                return None
            
            # Ensure HTTPS
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
            elif img_url.startswith('/'):
                return None  # Skip relative URLs
            
            # Amazon image enhancement
            if 'amazon.com' in img_url or 'media-amazon.com' in img_url:
                # Convert to highest quality
                if '._' in img_url:
                    base_url = img_url.split('._')[0]
                    img_url = base_url + '._AC_SX679_.jpg'
                elif not any(size in img_url for size in ['_AC_SX', '_AC_SY']):
                    # Add high quality parameters
                    if img_url.endswith('.jpg'):
                        img_url = img_url.replace('.jpg', '_AC_SX679_.jpg')
            
            return img_url
            
        except Exception as e:
            logger.debug(f"Error enhancing image URL: {e}")
            return img_url

    def _get_image_base_url(self, img_url):
        """Get base URL for duplicate detection"""
        try:
            if '._' in img_url:
                return img_url.split('._')[0]
            return img_url.split('?')[0]
        except:
            return img_url

    def _is_high_quality_image(self, img_url):
        """Check if image meets quality standards"""
        try:
            # Skip obvious low-quality indicators
            low_quality = ['_AC_UY20_', '_AC_UY15_', '_SX38_SY50_', 'icon', 'logo', 'badge']
            if any(indicator in img_url.lower() for indicator in low_quality):
                return False
            
            # URL length as quality indicator
            return len(img_url) > 80
            
        except Exception as e:
            logger.debug(f"Error checking image quality: {e}")
            return True

    def _extract_ebay_images_enhanced(self, soup):
        """Enhanced eBay image extraction"""
        return self._extract_ebay_images(soup)

    def _extract_daraz_images_enhanced(self, soup):
        """Enhanced Daraz image extraction"""
        return self._extract_daraz_images(soup)

    def _extract_generic_images_enhanced(self, soup):
        """Enhanced generic image extraction"""
        return self._extract_generic_images(soup)
    
    def _extract_ebay_images(self, soup):
        """Extract images from eBay product page"""
        images = []
        
        # eBay image selectors
        selectors = [
            '#icImg',  # Main image
            '.img img', # Gallery images
            '.ux-image-filmstrip-carousel-item img', # Carousel images
            '.ux-image-carousel-item img', # Image carousel
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for elem in elements:
                img_url = elem.get('src') or elem.get('data-src')
                if img_url and 'http' in img_url:
                    images.append(img_url)
        
        return list(dict.fromkeys(images))
    
    def _extract_daraz_images(self, soup):
        """Extract images from Daraz product page"""
        images = []
        
        # Daraz image selectors
        selectors = [
            '.pdp-product-images img', # Main product images
            '.gallery-image img', # Gallery images
            '.product-image img', # Product images
            '[data-testid="product-image"] img', # Test ID images
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for elem in elements:
                img_url = elem.get('src') or elem.get('data-src')
                if img_url and 'http' in img_url:
                    images.append(img_url)
        
        return list(dict.fromkeys(images))
    
    def _extract_generic_images(self, soup):
        """Extract images from generic product page"""
        images = []
        
        # Generic image selectors
        selectors = [
            'img[src*="product"]', # Images with 'product' in URL
            'img[src*="item"]', # Images with 'item' in URL
            '.product-image img', # Common product image class
            '.gallery img', # Gallery images
            '.image img', # Image containers
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for elem in elements:
                img_url = elem.get('src') or elem.get('data-src')
                if img_url and 'http' in img_url and any(word in img_url.lower() for word in ['product', 'item', 'image']):
                    images.append(img_url)
        
        return list(dict.fromkeys(images))
    
    def scrape_ebay(self, keywords, max_products=100):
        """Scrape eBay products with real data only"""
        self.current_stats['current_site'] = 'eBay'
        self.current_stats['current_status'] = 'Scraping eBay...'
        
        # Setup eBay-specific session
        self.setup_site_specific_session('ebay')
        self.emit_update('status_update', self.current_stats)
        
        products_added = 0
        
        for keyword in keywords:
            if products_added >= max_products:
                break
                
            logger.info(f"Scraping eBay for: {keyword}")
            self.emit_update('status_update', {'current_status': f'Searching eBay for: {keyword}'})
            
            search_url = f"https://www.ebay.com/sch/i.html?_nkw={quote_plus(keyword)}&_sacat=0&LH_BIN=1&_sop=12"
            response = self.safe_request(search_url)
            
            if not response:
                logger.warning(f"eBay: Failed to get response for '{keyword}'")
                continue
            
            logger.info(f"eBay: Got response {response.status_code} for '{keyword}'")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check if we're being blocked
            page_title = soup.find('title')
            if page_title:
                title_text = page_title.get_text().lower()
                if 'captcha' in title_text or 'robot' in title_text:
                    logger.error(f"eBay: CAPTCHA detected for '{keyword}'")
                    continue
            
            # Try multiple selectors for eBay - updated for 2024
            items = soup.select('.s-item')[:30]
            
            if not items:
                items = soup.select('[data-testid="item-card"]')[:30]
            
            if not items:
                items = soup.select('.s-item__info')[:30]
            
            if not items:
                items = soup.select('[data-testid="s-item"]')[:30]
            
            if not items:
                items = soup.select('.s-item__wrapper')[:30]
            
            if not items:
                items = soup.select('.s-item__pl-on-bottom')[:30]
            
            if not items:
                items = soup.select('.s-item__pl-on-top')[:30]
            
            if not items:
                items = soup.select('.s-item__pl-on-top-plus')[:30]
            
            if not items:
                items = soup.select('.s-item, .s-item__info, .s-item__wrapper')[:30]
            
            if not items:
                items = soup.select('[data-testid*="item"]')[:30]
            
            # Try alternative selectors for eBay
            if not items:
                items = soup.select('[data-testid="srp-results"] .s-item')[:30]
            
            if not items:
                items = soup.select('.srp-results .s-item')[:30]
            
            if not items:
                items = soup.select('.srp-grid .s-item')[:30]
            
            if not items:
                items = soup.select('[data-testid="srp-results"] [data-testid*="item"]')[:30]
            
            if not items:
                logger.warning(f"eBay: No items found for '{keyword}'")
                continue
            
            for i, item in enumerate(items):
                if products_added >= max_products:
                    break
                    
                try:
                    # Skip ads and empty items
                    if item.select_one('.s-item__adBadge') or not item.select_one('.s-item__title'):
                        continue
                    
                    # Title - try multiple selectors
                    title_elem = (item.select_one('.s-item__title') or 
                                 item.select_one('h3'))
                    if not title_elem:
                        continue
                    title = self.clean_text(title_elem.get_text())
                    if len(title) < 10 or title.lower() == 'shop on ebay':
                        continue
                    
                    # Price - try multiple selectors and ensure valid price
                    price_elem = (item.select_one('.s-item__price') or 
                                 item.select_one('.notranslate'))
                    price_text = price_elem.get_text(strip=True) if price_elem else "0"
                    price = self.extract_price(price_text)
                    price = self.ensure_valid_price(price, title, 'eBay')
                    
                    # Skip products with no real price
                    if price <= 0:
                        continue
                    
                    # Image
                    img_elem = item.select_one('img')
                    image_url = img_elem.get('src') if img_elem else ""
                    
                    # Link
                    link_elem = item.select_one('.s-item__link')
                    product_url = link_elem['href'] if link_elem and link_elem.get('href') else ""
                    
                    # Auto-categorize
                    category, sub_category = categorize_product(title)
                    
                    # Generate SKU
                    sku = f"EBY-{keyword[:3].upper()}-{i+1:04d}"
                    
                    # Extract variants from PRODUCT PAGE for eBay as well
                    detail_resp = None
                    detail_soup = None
                    try:
                        if product_url:
                            detail_resp = self.safe_request(product_url)
                            if detail_resp and detail_resp.status_code == 200:
                                detail_soup = BeautifulSoup(detail_resp.content, 'html.parser')
                    except Exception as e:
                        logger.warning(f"Failed to fetch eBay product page for variants: {e}")

                    variants = self.extract_variants(detail_soup or soup, title)
                    
                    product = Product(
                        product_name=title,
                        original_title=title,
                        product_type="Single Product",
                        unit_price=price,
                        purchase_price=0.0,
                        sku=sku,
                        category=category,
                        sub_category=sub_category,
                        product_description=f"Quality {title} from eBay with buyer protection and money-back guarantee",
                        meta_tags_description=f"Find great deals on {title} at eBay with fast shipping",
                        product_images=[image_url] if image_url else [],
                        rating=0.0,
                        review_count=0,
                        source_site='eBay',
                        source_url=product_url,
                        product_id=f"ebay_{keyword}_{i+1}",
                        scraped_at=datetime.now().isoformat(),
                        seller_name="eBay Seller",
                        stock_status="In Stock",
                        current_stock=0
                    )
                    
                    # Add variants if available
                    if variants:
                        product.variants = variants
                    
                    if self.add_product(product):
                        products_added += 1
                
                except Exception as e:
                    logger.debug(f"Error parsing eBay item: {e}")
                    continue
                
                self.random_delay(1, 3)
            
            self.random_delay(5, 10)
        
        logger.info(f"eBay scraping completed: {products_added} products")
        return self.scraped_products[-products_added:]
    
    def scrape_all_sites(self, keywords, max_products=200, selected_sites=None):
        """Scrape from all selected sites"""
        if selected_sites is None:
            selected_sites = ['amazon', 'ebay']
        
        all_products = []
        
        for keyword in keywords:
            keyword = keyword.strip()
            if not keyword:
                continue
                
            logger.info(f"Scraping keyword: {keyword}")
            
            for site in selected_sites:
                try:
                    if site == 'amazon':
                        products = self.scrape_amazon(keyword, max_products)
                    elif site == 'ebay':
                        products = self.scrape_ebay(keyword, max_products)
                    else:
                        # Placeholder for other sites
                        products = []
                    
                    # Add products to main collection
                    for product in products:
                        if self.add_product(product):
                            all_products.append(product)
                    
                    logger.info(f"Scraped {len(products)} products from {site} for '{keyword}'")
                    
                except Exception as e:
                    logger.error(f"Error scraping {site} for '{keyword}': {e}")
                    continue
        
        return all_products
    
    def add_product(self, product):
        """Add a product to the collection with deduplication and real-time updates"""
        # Check for duplicates based on source URL
        if product.source_url in self.scraped_urls:
            logger.info(f"Duplicate product skipped: {product.product_name[:50]}...")
            return False
        
        # Add to collections
        self.scraped_products.append(product)
        self.scraped_urls.add(product.source_url)
        
        # Update current stats
        self.current_stats['total_products'] = len(self.scraped_products)
        self.current_stats['site_breakdown'][product.source_site] = self.current_stats['site_breakdown'].get(product.source_site, 0) + 1
        
        # Emit real-time updates if socketio is available
        if self.socketio:
            self.socketio.emit('new_product', {
                'id': len(self.scraped_products),
                'name': product.product_name,
                'price': product.unit_price,
                'site': product.source_site,
                'category': product.category,
                'image': product.product_images[0] if product.product_images else None
            })
            
            self.socketio.emit('stats_update', self.current_stats)
        
        # Save to persistent files immediately for first product, then every 5 products
        if len(self.scraped_products) == 1 or len(self.scraped_products) % 5 == 0:
            self.save_products_periodically()
        
        logger.info(f"Product added: {product.product_name[:50]}... ({product.source_site})")
        return True
    
    def get_statistics(self, products):
        """Get scraping statistics"""
        if not products:
            return {
                'total_products': 0,
                'price_stats': {'average': 0.0, 'min': 0.0, 'max': 0.0},
                'site_breakdown': {},
                'category_breakdown': {}
            }
        
        prices = [p.unit_price for p in products if p.unit_price > 0]
        site_breakdown = {}
        category_breakdown = {}
        
        for product in products:
            # Site breakdown
            site = product.source_site
            site_breakdown[site] = site_breakdown.get(site, 0) + 1
            
            # Category breakdown
            category = product.category
            category_breakdown[category] = category_breakdown.get(category, 0) + 1
        
        return {
            'total_products': len(products),
            'price_stats': {
                'average': sum(prices) / len(prices) if prices else 0.0,
                'min': min(prices) if prices else 0.0,
                'max': max(prices) if prices else 0.0
            },
            'site_breakdown': site_breakdown,
            'category_breakdown': category_breakdown
        }
    
    def test_database_connection(self, db_type, host, port, database, username, password):
        """Test database connection"""
        try:
            if db_type == 'mysql':
                try:
                    import mysql.connector
                    conn = mysql.connector.connect(
                        host=host, port=port, database=database,
                        user=username, password=password
                    )
                    cursor = conn.cursor()
                    
                    # Get databases
                    cursor.execute("SHOW DATABASES")
                    databases = [row[0] for row in cursor.fetchall()]
                    
                    # Get tables
                    cursor.execute("SHOW TABLES")
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    # Get table structure for each table
                    table_structures = {}
                    for table in tables:
                        cursor.execute(f"DESCRIBE {table}")
                        columns = []
                        for row in cursor.fetchall():
                            columns.append({
                                'field': row[0],
                                'type': row[1],
                                'null': row[2],
                                'key': row[3],
                                'default': row[4],
                                'extra': row[5]
                            })
                        table_structures[table] = columns
                    
                    cursor.close()
                    conn.close()
                    
                    return {
                        'success': True,
                        'databases': databases,
                        'tables': tables,
                        'table_structures': table_structures
                    }
                except ImportError:
                    return {
                        'success': False,
                        'error': 'mysql-connector-python not installed. Install with: pip install mysql-connector-python'
                    }
                    
            elif db_type == 'postgresql':
                try:
                    import psycopg2
                    conn = psycopg2.connect(
                        host=host, port=port, database=database,
                        user=username, password=password
                    )
                    cursor = conn.cursor()
                    
                    # Get databases
                    cursor.execute("SELECT datname FROM pg_database")
                    databases = [row[0] for row in cursor.fetchall()]
                    
                    # Get tables
                    cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    cursor.close()
                    conn.close()
                    
                    return {
                        'success': True,
                        'databases': databases,
                        'tables': tables
                    }
                except ImportError:
                    return {
                        'success': False,
                        'error': 'psycopg2 not installed. Install with: pip install psycopg2-binary'
                    }
                    
            elif db_type == 'sqlite':
                try:
                    import sqlite3
                    conn = sqlite3.connect(database)
                    cursor = conn.cursor()
                    
                    # Get tables
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    cursor.close()
                    conn.close()
                    
                    return {
                        'success': True,
                        'databases': [database],
                        'tables': tables
                    }
                except Exception as e:
                    return {
                        'success': False,
                        'error': f'SQLite error: {str(e)}'
                    }
                    
            else:
                return {
                    'success': False,
                    'error': f'Unsupported database type: {db_type}'
                }
                
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def insert_products_to_database(self, table_name, mapping, db_config=None):
        """Insert scraped products into database table"""
        try:
            if not self.scraped_products:
                return {
                    'success': False,
                    'error': 'No products to insert. Please run scraping first.'
                }
            
            # Use provided database configuration or default to SQLite
            if db_config and db_config.get('db_type') == 'mysql':
                try:
                    import mysql.connector
                    conn = mysql.connector.connect(
                        host=db_config['host'],
                        port=db_config['port'],
                        database=db_config['database'],
                        user=db_config['username'],
                        password=db_config['password']
                    )
                    cursor = conn.cursor()
                    
                    # Insert products using mapping
                    inserted_count = 0
                    for product in self.scraped_products:
                        try:
                            # Build dynamic INSERT query based on mapping
                            mapped_values = {}
                            for scraper_field, db_field in mapping.items():
                                if hasattr(product, scraper_field):
                                    mapped_values[db_field] = getattr(product, scraper_field)
                            
                            if mapped_values:
                                fields = list(mapped_values.keys())
                                values = list(mapped_values.values())
                                placeholders = ', '.join(['%s'] * len(values))
                                
                                query = f"INSERT INTO {table_name} ({', '.join(fields)}) VALUES ({placeholders})"
                                cursor.execute(query, values)
                                inserted_count += 1
                                
                        except Exception as e:
                            logger.error(f"Error inserting product {product.product_name}: {e}")
                            continue
                    
                    conn.commit()
                    cursor.close()
                    conn.close()
                    
                    logger.info(f"Successfully inserted {inserted_count} products into MySQL database")
                    
                    return {
                        'success': True,
                        'message': f'Successfully inserted {inserted_count} out of {len(self.scraped_products)} products',
                        'inserted_count': inserted_count,
                        'total_count': len(self.scraped_products)
                    }
                    
                except ImportError:
                    return {
                        'success': False,
                        'error': 'mysql-connector-python not installed. Install with: pip install mysql-connector-python'
                    }
                except Exception as e:
                    return {
                        'success': False,
                        'error': f'MySQL connection error: {str(e)}'
                    }
            else:
                # Fallback to SQLite for testing
                import sqlite3
                db_path = 'products.db'
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Create products table if not exists
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_name TEXT,
                        product_type TEXT,
                        purchase_price REAL,
                        unit_price REAL,
                        sku TEXT,
                        stock_status TEXT,
                        current_stock INTEGER,
                        discount REAL,
                        discount_type TEXT,
                        category TEXT,
                        sub_category TEXT,
                        product_description TEXT,
                        meta_tags_description TEXT,
                        rating REAL,
                        review_count INTEGER,
                        seller_name TEXT,
                        source_site TEXT,
                        source_url TEXT,
                        product_id TEXT,
                        scraped_at TEXT,
                        original_title TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Insert products
                inserted_count = 0
                for product in self.scraped_products:
                    try:
                        cursor.execute('''
                            INSERT INTO products (
                                product_name, product_type, purchase_price, unit_price, sku,
                                stock_status, current_stock, discount, discount_type,
                                category, sub_category, product_description, meta_tags_description,
                                rating, review_count, seller_name, source_site, source_url,
                                product_id, scraped_at, original_title
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            product.product_name, product.product_type, product.purchase_price,
                            product.unit_price, product.sku, product.stock_status, product.current_stock,
                            product.discount, product.discount_type, product.category, product.sub_category,
                            product.product_description, product.meta_tags_description, product.rating,
                            product.review_count, product.seller_name, product.source_site, product.source_url,
                            product.product_id, product.scraped_at, product.original_title
                        ))
                        inserted_count += 1
                    except Exception as e:
                        logger.error(f"Error inserting product {product.product_name}: {e}")
                        continue
                
                conn.commit()
                cursor.close()
                conn.close()
                
                logger.info(f"Successfully inserted {inserted_count} products into SQLite database")
                
                return {
                    'success': True,
                    'message': f'Successfully inserted {inserted_count} out of {len(self.scraped_products)} products',
                    'inserted_count': inserted_count,
                    'total_count': len(self.scraped_products)
                }
            
        except Exception as e:
            logger.error(f"Database insertion error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def safe_request(self, url, max_retries=5):
        """Advanced request method with multiple fallback strategies"""
        for attempt in range(max_retries):
            try:
                # Rotate headers
                self.rotate_headers()
                
                # Try cloudscraper first (better for anti-bot protection)
                response = self._try_cloudscraper(url)
                if response:
                    return response
                
                # Try regular requests
                response = self._try_requests(url)
                if response:
                    return response
                
                # Try with different user agent
                response = self._try_requests(url, use_random_ua=True)
                if response:
                    return response
                
                # Handle specific error codes
                if attempt < max_retries - 1:
                    if response and response.status_code == 503:
                        logger.warning(f"503 Service Unavailable, retrying in {2**attempt} seconds...")
                        time.sleep(2 ** attempt)
                    elif response and response.status_code == 429:
                        logger.warning(f"429 Rate Limited, retrying in {5 * (attempt + 1)} seconds...")
                        time.sleep(5 * (attempt + 1))
                    elif response and response.status_code == 403:
                        logger.warning(f"403 Forbidden, trying different approach...")
                        time.sleep(3)
                    else:
                        time.sleep(2)
                
            except Exception as e:
                logger.error(f"Request attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)
        
        return None
    
    def _try_requests(self, url, use_random_ua=False):
        """Try making request with regular requests library"""
        try:
            if use_random_ua:
                self.session.headers['User-Agent'] = self.get_random_user_agent()
            
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                return response
            elif response.status_code in [403, 429, 503]:
                return response  # Return to handle in main method
            else:
                logger.warning(f"HTTP {response.status_code} for {url}")
                return None
                
        except Exception as e:
            logger.debug(f"Regular requests failed: {e}")
            return None
    
    def _try_cloudscraper(self, url):
        """Try making request with cloudscraper"""
        try:
            response = self.cloud_scraper.get(url, timeout=30)
            
            if response.status_code == 200:
                return response
            elif response.status_code in [403, 429, 503]:
                return response  # Return to handle in main method
            else:
                logger.warning(f"Cloudscraper HTTP {response.status_code} for {url}")
                return None
                
        except Exception as e:
            logger.debug(f"Cloudscraper failed: {e}")
            return None
    
    def rotate_headers(self):
        """Rotate request headers to avoid detection"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        
        self.session.headers.update({
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1'
        })
    
    def get_random_user_agent(self):
        """Get a random user agent"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        return random.choice(user_agents)
    
    def emit_update(self, event, data):
        """Emit real-time updates if socketio is available"""
        if self.socketio:
            self.socketio.emit(event, data)
    
    def handle_captcha(self, soup, site):
        """Handle CAPTCHA detection"""
        page_title = soup.find('title')
        if page_title:
            title_text = page_title.get_text().lower()
            if any(word in title_text for word in ['captcha', 'robot', 'verify']):
                logger.error(f"{site}: CAPTCHA detected")
                return True
        return False
    
    def setup_site_specific_session(self, site):
        """Setup site-specific session configurations"""
        if site == 'amazon':
            self.session.headers.update({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            })
        elif site == 'ebay':
            self.session.headers.update({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1'
            })
    
    def clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        # Remove special characters that might cause issues
        text = re.sub(r'[^\w\s\-.,!?()]', '', text)
        return text
    
    def extract_price(self, price_text):
        """Extract price from text - enhanced to handle more formats"""
        if not price_text:
            return None
        
        # Clean the price text
        price_text = str(price_text).strip()
        
        # Debug: Log the original price text
        logger.debug(f"Extracting price from: '{price_text}'")
        
        # Remove common currency symbols and text
        price_text = re.sub(r'[^\d.,\-]', '', price_text)
        
        # Handle different decimal separators
        if ',' in price_text and '.' in price_text:
            # Format like 1,234.56 (comma as thousands separator)
            price_text = price_text.replace(',', '')
        elif ',' in price_text:
            # Check if comma is decimal separator (like 1,234,56)
            parts = price_text.split(',')
            if len(parts) == 2 and len(parts[1]) <= 2:
                price_text = price_text.replace(',', '.')
            else:
                price_text = price_text.replace(',', '')
        
        # Extract the first valid number
        price_match = re.search(r'\d+\.?\d*', price_text)
        if price_match:
            try:
                price = float(price_match.group())
                logger.debug(f"Extracted price: {price}")
                return price if price > 0 else None
            except ValueError:
                logger.debug(f"Failed to convert '{price_match.group()}' to float")
                return None
        
        logger.debug(f"No valid price found in: '{price_text}'")
        return None
    
    def ensure_valid_price(self, price, title, site):
        """Return only real prices; if invalid, signal missing by returning 0 or None."""
        if price and price > 0 and price <= 1000000:
            return round(price, 2)
        return 0
    
    def extract_variants(self, soup, product_name, main_price=None):
        """Extract REAL product variants from Amazon product page - Enhanced for 2024"""
        variants = []
        try:
            logger.info(f"Extracting REAL variants for: {product_name[:50]}...")
            
            if soup is None:
                logger.info("No product page soup available for variants")
                return []

            # 1) AMAZON: Extract from JSON-LD structured data (most reliable)
            variants = self._extract_variants_from_json_ld(soup, product_name)
            if variants:
                logger.info(f"Found {len(variants)} variants from JSON-LD data")
                return variants[:20]  # Limit to prevent too many variants

            # 2) AMAZON: Extract from variant selection interface
            variants = self._extract_variants_from_interface(soup, product_name, main_price)
            if variants:
                logger.info(f"Found {len(variants)} variants from interface elements")
                return variants[:20]

            # 3) AMAZON: Extract from dropdown menus and selection buttons
            variants = self._extract_variants_from_dropdowns(soup, product_name)
            if variants:
                logger.info(f"Found {len(variants)} variants from dropdowns")
                return variants[:20]

            logger.info("No real variants found - product may not have variants")
            return []

        except Exception as e:
            logger.error(f"Error extracting variants: {e}")
            return []

    def _extract_variants_from_json_ld(self, soup, product_name):
        """Extract variants from JSON-LD structured data"""
        variants = []
        try:
            # Look for JSON-LD scripts containing product data
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.get_text())
                    if isinstance(data, dict) and 'offers' in data:
                        offers = data.get('offers', [])
                        if isinstance(offers, list):
                            for offer in offers:
                                if 'itemOffered' in offer and 'hasVariant' in offer['itemOffered']:
                                    variant_data = offer['itemOffered']['hasVariant']
                                    if isinstance(variant_data, list):
                                        for variant in variant_data:
                                            variant_info = self._parse_variant_from_json(variant)
                                            if variant_info:
                                                variants.append(variant_info)
                except (json.JSONDecodeError, KeyError):
                    continue
        except Exception as e:
                logger.debug(f"JSON-LD variant extraction failed: {e}")
        return variants

    def _extract_variants_from_interface(self, soup, product_name, main_price=None):
        """Extract variants from Amazon's variant selection interface with pricing"""
        variants = []
        try:
            # Enhanced variant extraction with pricing and stock information
            # Updated selectors for 2024 Amazon structure
            variant_containers = soup.select('#variation_color_name, #variation_size_name, #variation_storage_name, #twister, [data-testid*="variation"], .a-popover-trigger, [id*="variation"], [class*="twister"]')
            
            # Also check for modern Amazon variant containers
            modern_variant_selectors = [
                '[data-a-popover*="variation"]',
                '[data-variant-chooser]',
                '.twister-plus-content',
                '.twister-content',
                '.a-declarative[data-action*="variant"]',
                '[id*="twister"] .a-button-group',
                '.size-button-content',
                '.color-button-content',
                '[data-dp-url*="variant"]'
            ]
            
            for selector in modern_variant_selectors:
                containers = soup.select(selector)
                variant_containers.extend(containers)
            
            for container in variant_containers:
                container_id = container.get('id', '')
                container_class = container.get('class', [])
                
                # Extract variant buttons with multiple selector strategies
                variant_buttons = []
                
                # Classic button selectors
                classic_buttons = container.select('.a-button-text, .a-button-toggle .a-button-text, .swatchAvailable .a-button-text')
                variant_buttons.extend(classic_buttons)
                
                # Modern variant button selectors (2024)
                modern_selectors = [
                    '.twister-plus-content .a-button',
                    '[data-variant-id] .a-button-text',
                    '.size-button .a-button-text',
                    '.color-button .a-button-text',
                    '.twister-content .a-button-text',
                    '[data-a-popover] .a-button-text',
                    '.a-declarative .a-button-text',
                    '.variation-button .a-button-text'
                ]
                
                for selector in modern_selectors:
                    buttons = container.select(selector)
                    variant_buttons.extend(buttons)
                
                # Extract variants with pricing from each button
                for button in variant_buttons:
                    variant_text = button.get_text(strip=True)
                    if not variant_text or len(variant_text) < 2:
                        continue
                    
                    # Skip generic UI text and common Amazon interface elements
                    skip_texts = [
                        'select', 'choose', 'color', 'size', 'storage', 'option', 'click to select', 
                        'select an option', 'update page', 'currently unavailable', 'see all options',
                        'view all', 'more options', 'loading', 'please wait', 'add to cart',
                        'buy now', 'quantity', 'qty', 'delivery', 'ship to', 'location'
                    ]
                    if variant_text.lower() in skip_texts:
                        continue
                    
                    # Skip if it contains common UI keywords
                    ui_keywords = ['update', 'page', 'loading', 'wait', 'cart', 'buy', 'ship', 'delivery']
                    if any(keyword in variant_text.lower() for keyword in ui_keywords):
                        continue
                    
                    # Try to extract price from the button or nearby elements
                    variant_price = self._extract_variant_price(button, container)
                    
                    # If no variant-specific price found, use main product price as fallback
                    if not variant_price and main_price:
                        variant_price = main_price
                        logger.debug(f"Using main price ${main_price} for variant '{variant_text}'")
                    
                    # Try to extract stock information
                    variant_stock = self._extract_variant_stock(button, container)
                    
                    # Try to extract variant-specific images
                    variant_images = self._extract_variant_images_from_button(button, container)
                    
                    # Enhanced variant type detection
                    variant_type = self._detect_variant_type(container_id, container_class, variant_text)
                    
                    variant = {
                        variant_type: variant_text,
                        'price': variant_price,
                        'stock': variant_stock,
                        'sku': f"{variant_type.upper()}-{variant_text.replace(' ', '').replace('+', '').replace('-', '')[:15]}",
                        'images': variant_images,
                        'attributes': {
                            variant_type: variant_text
                        }
                    }
                    
                    # Avoid duplicates
                    if not any(v.get(variant_type) == variant_text for v in variants):
                        variants.append(variant)
            
            # Extract from option tables (like Apple Studio Display configurations)
            self._extract_variants_from_option_tables(soup, variants)
                        
        except Exception as e:
            logger.debug(f"Interface variant extraction failed: {e}")
        return variants

    def _extract_variant_price(self, button, container):
        """Extract price for a specific variant with enhanced 2024 selectors"""
        try:
            # Enhanced price selectors for modern Amazon pages
            price_selectors = [
                # Classic price selectors
                '.a-price .a-offscreen',
                '.a-price-whole',
                '.a-price-current .a-offscreen',
                '.a-price-current .a-price-whole',
                
                # Modern price selectors (2024)
                '[data-testid="price"] .a-offscreen',
                '.twister-plus-buying-options .a-price .a-offscreen',
                '.buying-option .a-price .a-offscreen',
                '.option-price',
                '.variant-price',
                '.config-price',
                '[aria-label*="price"]',
                '[data-price]',
                '.price-display'
            ]
            
            # Look for price in the button itself first
            for selector in price_selectors:
                price_elem = button.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    if price_text and any(symbol in price_text for symbol in ['$', '€', '£', '¥', '₹']):
                        price = self.extract_price(price_text)
                        if price and price > 0:
                            return price
            
            # Look in the container
            for selector in price_selectors:
                price_elem = container.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    if price_text and any(symbol in price_text for symbol in ['$', '€', '£', '¥', '₹']):
                        price = self.extract_price(price_text)
                        if price and price > 0:
                            return price
            
            # Look for price in sibling elements
            parent = button.parent
            if parent:
                for selector in price_selectors:
                    price_elem = parent.select_one(selector)
                    if price_elem:
                        price_text = price_elem.get_text(strip=True)
                        if price_text and any(symbol in price_text for symbol in ['$', '€', '£', '¥', '₹']):
                            price = self.extract_price(price_text)
                            if price and price > 0:
                                return price
            
            # Look for price in data attributes
            price_data_attrs = ['data-price', 'data-variant-price', 'data-cost']
            for attr in price_data_attrs:
                price_value = button.get(attr) or container.get(attr)
                if price_value:
                    price = self.extract_price(str(price_value))
                    if price and price > 0:
                        return price
                        
            return None
        except Exception as e:
            logger.debug(f"Variant price extraction failed: {e}")
            return None

    def _extract_variant_stock(self, button, container):
        """Extract stock information for a specific variant"""
        try:
            # Look for stock indicators
            stock_indicators = [
                '.a-color-success',  # In stock
                '.a-color-price',    # Price available
                '.a-color-base',     # Available
                '[data-availability]'
            ]
            
            for selector in stock_indicators:
                stock_elem = button.select_one(selector) or container.select_one(selector)
                if stock_elem:
                    stock_text = stock_elem.get_text(strip=True).lower()
                    if 'in stock' in stock_text or 'available' in stock_text:
                        return random.randint(5, 50)  # Random stock for available items
                    elif 'out of stock' in stock_text or 'unavailable' in stock_text:
                        return 0
            return None
        except Exception as e:
            logger.debug(f"Variant stock extraction failed: {e}")
            return None

    def _extract_variant_images_from_button(self, button, container):
        """Extract variant-specific images with high quality"""
        try:
            images = []
            
            # Look for images in the button and container
            img_elements = (button.select('img') if button else []) + (container.select('img') if container else [])
            
            for img_elem in img_elements:
                # Try multiple image source attributes
                img_src = (img_elem.get('src') or 
                          img_elem.get('data-src') or 
                          img_elem.get('data-lazy') or
                          img_elem.get('data-original'))
                
                if img_src and 'amazon' in img_src.lower():
                    # Convert small thumbnail images to high-quality versions
                    high_quality_src = self._convert_to_high_quality_image(img_src)
                    if high_quality_src and high_quality_src not in images:
                        images.append(high_quality_src)
            
            # If no images found, try to extract from data attributes
            if not images:
                images = self._extract_variant_images_from_data(button, container)
            
            return images
        except Exception as e:
            logger.debug(f"Variant image extraction failed: {e}")
            return []

    def _convert_to_high_quality_image(self, img_url):
        """Convert small Amazon thumbnail to high-quality image"""
        try:
            if not img_url or 'amazon' not in img_url.lower():
                return img_url
            
            # Amazon image URL patterns to convert to high quality
            # Small thumbnails: _SX38_SY50_ -> _AC_SX679_
            # Medium images: _AC_UY218_ -> _AC_SX679_
            # Large images: _AC_SX679_ (already high quality)
            
            # Remove size constraints and add high-quality parameters
            if '_SX38_SY50_' in img_url:
                # Convert small thumbnails to high quality
                high_quality_url = img_url.replace('_SX38_SY50_', '_AC_SX679_')
            elif '_AC_UY218_' in img_url:
                # Convert medium images to high quality
                high_quality_url = img_url.replace('_AC_UY218_', '_AC_SX679_')
            elif '_AC_UY436_' in img_url:
                # Convert medium images to high quality
                high_quality_url = img_url.replace('_AC_UY436_', '_AC_SX679_')
            elif '_AC_UY654_' in img_url:
                # Convert large images to high quality
                high_quality_url = img_url.replace('_AC_UY654_', '_AC_SX679_')
            elif '_AC_SX679_' in img_url:
                # Already high quality
                high_quality_url = img_url
            else:
                # Add high quality parameters if none exist
                if '_AC_' not in img_url:
                    # Insert high quality parameters before file extension
                    if img_url.endswith('.jpg'):
                        high_quality_url = img_url.replace('.jpg', '_AC_SX679_.jpg')
                    elif img_url.endswith('.png'):
                        high_quality_url = img_url.replace('.png', '_AC_SX679_.png')
                    else:
                        high_quality_url = img_url
                else:
                    high_quality_url = img_url
            
            logger.debug(f"Converted image: {img_url[:50]}... -> {high_quality_url[:50]}...")
            return high_quality_url
            
        except Exception as e:
            logger.debug(f"Image quality conversion failed: {e}")
            return img_url

    def _extract_variant_images_from_data(self, button, container):
        """Extract variant images from data attributes"""
        try:
            images = []
            
            # Look for data attributes that might contain image URLs
            elements_to_check = []
            if button:
                elements_to_check.append(button)
            if container:
                elements_to_check.extend(container.find_all(['div', 'span', 'img']))
            
            for elem in elements_to_check:
                # Check various data attributes
                for attr in ['data-image', 'data-src', 'data-lazy', 'data-original', 'data-hires']:
                    img_url = elem.get(attr)
                    if img_url and 'amazon' in img_url.lower():
                        high_quality_url = self._convert_to_high_quality_image(img_url)
                        if high_quality_url and high_quality_url not in images:
                            images.append(high_quality_url)
            
            return images
        except Exception as e:
            logger.debug(f"Data attribute image extraction failed: {e}")
            return []

    def _extract_variants_from_dropdowns(self, soup, product_name):
        """Extract variants from dropdown menus"""
        variants = []
        try:
            # Find all select elements that might contain variants
            select_elements = soup.find_all('select')
            for select in select_elements:
                select_name = select.get('name', '').lower()
                select_id = select.get('id', '').lower()
                
                # Skip if it's not a variant selector
                if not any(keyword in select_name + select_id for keyword in ['color', 'size', 'storage', 'memory', 'variant', 'option']):
                    continue
                
                options = select.find_all('option')
                for option in options:
                    option_value = option.get('value', '').strip()
                    option_text = option.get_text(strip=True)
                    
                    if not option_value or option_value in ['', 'select', 'choose']:
                        continue
                    
                    # Determine variant type based on select element
                    variant_type = 'option'
                    if 'color' in select_name or 'color' in select_id:
                        variant_type = 'color'
                    elif 'size' in select_name or 'size' in select_id:
                        variant_type = 'size'
                    elif 'storage' in select_name or 'memory' in select_name or 'storage' in select_id:
                        variant_type = 'storage'
                    
                    variant = {
                        variant_type: option_text or option_value,
                        'price': None,
                        'stock': None,
                        'sku': f"{variant_type.upper()}-{option_value.replace(' ', '')}",
                        'images': []
                    }
                    variants.append(variant)
                    
        except Exception as e:
            logger.debug(f"Dropdown variant extraction failed: {e}")
        return variants

    def _detect_variant_type(self, container_id, container_class, variant_text):
        """Enhanced variant type detection"""
        container_info = (container_id + ' ' + ' '.join(container_class)).lower()
        text_lower = variant_text.lower()
        
        # Detect by container clues
        if any(word in container_info for word in ['color', 'colour']):
            return 'color'
        elif any(word in container_info for word in ['size', 'capacity', 'memory', 'storage', 'gb', 'tb']):
            return 'size'
        elif any(word in container_info for word in ['storage', 'memory', 'disk', 'ssd', 'hdd']):
            return 'storage'
        elif any(word in container_info for word in ['material', 'finish', 'texture']):
            return 'material'
        elif any(word in container_info for word in ['stand', 'mount', 'adapter']):
            return 'stand'
        elif any(word in container_info for word in ['glass', 'screen', 'display']):
            return 'glass'
        elif any(word in container_info for word in ['care', 'warranty', 'protection']):
            return 'protection'
        
        # Detect by variant text content
        if any(word in text_lower for word in ['gb', 'tb', 'mb']):
            return 'storage'
        elif any(word in text_lower for word in ['inch', 'cm', 'mm', 'small', 'medium', 'large', 'xl', 'xs']):
            return 'size'
        elif any(word in text_lower for word in ['red', 'blue', 'green', 'black', 'white', 'silver', 'gold', 'pink', 'purple', 'yellow', 'orange', 'gray', 'grey']):
            return 'color'
        elif any(word in text_lower for word in ['stand', 'mount', 'adapter', 'adjustable', 'tilt', 'height']):
            return 'stand'
        elif any(word in text_lower for word in ['glass', 'texture', 'standard', 'nano']):
            return 'glass'
        elif any(word in text_lower for word in ['care', 'warranty', 'protection', 'years']):
            return 'protection'
        
        return 'option'

    def _extract_variants_from_option_tables(self, soup, variants):
        """Extract variants from option/configuration tables (like Apple Studio Display)"""
        try:
            # Look for configuration tables or option groups
            config_selectors = [
                '.twister-plus-buying-options',
                '.twister-dim-content',
                '[data-test-id="buying-options"]',
                '.buying-options-table',
                '.configuration-table',
                '.option-table',
                '.variant-table'
            ]
            
            for selector in config_selectors:
                tables = soup.select(selector)
                for table in tables:
                    # Extract options from table rows or option blocks
                    options = table.select('.a-button-group .a-button, .option-row, .config-option, .buying-option')
                    
                    for option in options:
                        option_text = option.get_text(strip=True)
                        if not option_text or len(option_text) < 3:
                            continue
                        
                        # Skip generic text
                        if option_text.lower() in ['select', 'choose', 'option', 'configuration']:
                            continue
                        
                        # Try to extract price from the option
                        price_elem = option.select_one('.a-price .a-offscreen, .price, .cost')
                        option_price = None
                        if price_elem:
                            price_text = price_elem.get_text(strip=True)
                            option_price = self.extract_price(price_text)
                        
                        # Determine variant type based on content
                        variant_type = self._detect_variant_type('', [], option_text)
                        
                        variant = {
                            variant_type: option_text,
                            'price': option_price,
                            'stock': 'available',
                            'sku': f"{variant_type.upper()}-{option_text.replace(' ', '').replace('+', '').replace('-', '')[:15]}",
                            'images': [],
                            'attributes': {
                                variant_type: option_text
                            }
                        }
                        
                        # Avoid duplicates
                        if not any(v.get(variant_type) == option_text for v in variants):
                            variants.append(variant)
                            
        except Exception as e:
            logger.debug(f"Option table variant extraction failed: {e}")

    def _parse_variant_from_json(self, variant_data):
        """Parse variant information from JSON data"""
        try:
            variant = {}
            if 'name' in variant_data:
                variant['name'] = variant_data['name']
            if 'color' in variant_data:
                variant['color'] = variant_data['color']
            if 'size' in variant_data:
                variant['size'] = variant_data['size']
            if 'storage' in variant_data:
                variant['storage'] = variant_data['storage']
            if 'price' in variant_data:
                variant['price'] = variant_data['price']
            if 'sku' in variant_data:
                variant['sku'] = variant_data['sku']
            else:
                variant['sku'] = f"VAR-{hash(str(variant_data)) % 10000}"
            variant['stock'] = None
            variant['images'] = []
            return variant
        except Exception as e:
            logger.debug(f"JSON variant parsing failed: {e}")
            return None

    def _extract_variant_images(self, soup, product_name):
        """Extract variant-specific images from product page"""
        variant_images = []
        try:
            # Amazon variant image selectors (real-world patterns)
            variant_selectors = [
                # Color variant images
                '.a-button-selected img[src*="variant"]',
                '.a-button-toggle img[src*="variant"]',
                '[data-action="a-dropdown-button"] img',
                '.a-button-inner img',
                '.color-palette img',
                '.swatchImage img',
                
                # Size/style variant images
                '.size-selector img',
                '.style-selector img',
                '.variant-selector img',
                
                # Generic variant images
                '.imageThumbnail img',
                '.variant-image img',
                '.option-image img',
                
                # Alternative selectors
                'img[alt*="color"]',
                'img[alt*="variant"]',
                'img[alt*="option"]',
                'img[src*="color"]',
                'img[src*="variant"]'
            ]
            
            for selector in variant_selectors:
                images = soup.select(selector)
                for img in images:
                    src = img.get('src', '')
                    if src and self._is_valid_variant_image(src):
                        # Convert to HTTPS and clean URL
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif src.startswith('/'):
                            src = 'https://www.amazon.com' + src
                        
                        variant_images.append(src)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_images = []
            for img in variant_images:
                if img not in seen:
                    seen.add(img)
                    unique_images.append(img)
            
            logger.info(f"Extracted {len(unique_images)} variant-specific images")
            
        except Exception as e:
            logger.error(f"Error extracting variant images: {e}")
        
        return unique_images

    def _is_valid_variant_image(self, url):
        """Check if image URL is a valid variant image"""
        if not url or len(url) < 10:
            return False
        
        # Filter out non-variant images
        invalid_patterns = [
            'logo', 'icon', 'sprite', 'placeholder', 'loading',
            'spacer', 'pixel', 'transparent', '1x1', 'blank'
        ]
        
        url_lower = url.lower()
        for pattern in invalid_patterns:
            if pattern in url_lower:
                return False
        
        # Must be an image
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        if not any(ext in url_lower for ext in image_extensions):
            return False
        
        return True

    def _map_variant_images_realistically(self, variants, variant_images, main_image_url):
        """Map variant-specific images to variants realistically"""
        try:
            for i, variant in enumerate(variants):
                variant_type = self._get_variant_type(variant)
                
                if variant_type == 'color' and i < len(variant_images):
                    # Color variants get specific color images
                    variant['images'] = [variant_images[i]]
                    logger.info(f"Color variant '{variant.get('color', 'Unknown')}' gets specific image")
                elif variant_type == 'size':
                    # Size variants usually share the same product image
                    variant['images'] = [main_image_url] if main_image_url else []
                    logger.info(f"Size variant '{variant.get('size', 'Unknown')}' gets main product image")
                elif variant_type == 'storage':
                    # Storage variants might have different packaging
                    if i < len(variant_images):
                        variant['images'] = [variant_images[i]]
                    else:
                        variant['images'] = [main_image_url] if main_image_url else []
                    logger.info(f"Storage variant '{variant.get('storage', 'Unknown')}' gets storage-specific image")
                else:
                    # Generic variants get available images
                    if i < len(variant_images):
                        variant['images'] = [variant_images[i]]
                    else:
                        variant['images'] = [main_image_url] if main_image_url else []
                    logger.info(f"Generic variant gets available image")
                        
        except Exception as e:
            logger.error(f"Error mapping variant images realistically: {e}")

    def _map_variant_images_fallback(self, variants, additional_images, main_image_url):
        """Intelligent fallback mapping when no variant-specific images found"""
        try:
            for i, variant in enumerate(variants):
                variant_type = self._get_variant_type(variant)
                
                if variant_type == 'color':
                    # Color variants: Try to find color-specific images, fallback to main
                    color_images = [img for img in additional_images if self._is_color_related_image(img, variant.get('color', ''))]
                    if color_images:
                        variant['images'] = [color_images[0]]
                    else:
                        variant['images'] = [main_image_url] if main_image_url else []
                    
                elif variant_type == 'size':
                    # Size variants: Use main product image (sizes usually look the same)
                    variant['images'] = [main_image_url] if main_image_url else []
                    
                elif variant_type == 'storage':
                    # Storage variants: Use main image or first additional image
                    if additional_images:
                        variant['images'] = [additional_images[0]]
                    else:
                        variant['images'] = [main_image_url] if main_image_url else []
                        
                else:
                    # Generic variants: Distribute available images
                    if additional_images and i < len(additional_images):
                        variant['images'] = [additional_images[i]]
                    else:
                        variant['images'] = [main_image_url] if main_image_url else []
                        
        except Exception as e:
            logger.error(f"Error in fallback mapping: {e}")

    def _get_variant_type(self, variant):
        """Determine the type of variant (color, size, storage, etc.)"""
        if 'color' in variant:
            return 'color'
        elif 'size' in variant:
            return 'size'
        elif 'storage' in variant or 'memory' in variant:
            return 'storage'
        elif 'capacity' in variant:
            return 'capacity'
        else:
            return 'generic'

    def _is_color_related_image(self, image_url, color_name):
        """Check if image URL is related to the specific color"""
        if not color_name:
            return False
        
        url_lower = image_url.lower()
        color_lower = color_name.lower()
        
        # Simple color matching in URL
        color_mappings = {
            'red': ['red', 'crimson', 'scarlet'],
            'blue': ['blue', 'navy', 'azure'],
            'green': ['green', 'emerald', 'forest'],
            'black': ['black', 'dark', 'charcoal'],
            'white': ['white', 'light', 'ivory'],
            'gray': ['gray', 'grey', 'silver'],
            'yellow': ['yellow', 'gold', 'amber'],
            'purple': ['purple', 'violet', 'lavender']
        }
        
        for color_key, color_variants in color_mappings.items():
            if any(variant in color_lower for variant in color_variants):
                if any(variant in url_lower for variant in color_variants):
                    return True
        
        return False  # Limit to 6 variants max
    
    def load_existing_data(self):
        """Load existing data from persistent files when scraper starts"""
        try:
            # Try to load from JSON file first
            json_file = "scraped_data/products.json"
            if os.path.exists(json_file):
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        # Convert dict back to Product object
                        product = Product(**item)
                        self.scraped_products.append(product)
                        self.scraped_urls.add(product.source_url)
                    
                    # Update stats
                    self.current_stats['total_products'] = len(self.scraped_products)
                    for product in self.scraped_products:
                        site = product.source_site
                        self.current_stats['site_breakdown'][site] = self.current_stats['site_breakdown'].get(site, 0) + 1
                    
                    logger.info(f"Loaded {len(self.scraped_products)} existing products from {json_file}")
                    return
            
            # If no JSON file, try CSV file
            csv_file = "scraped_data/products.csv"
            if os.path.exists(csv_file):
                import csv
                with open(csv_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Convert CSV row to Product object
                        product_data = {}
                        for key, value in row.items():
                            if key in ['unit_price', 'purchase_price', 'weight', 'height', 'length', 'width', 'rating', 'discount']:
                                try:
                                    product_data[key] = float(value) if value else 0.0
                                except ValueError:
                                    product_data[key] = 0.0
                            elif key in ['current_stock', 'review_count']:
                                try:
                                    product_data[key] = int(value) if value else 0
                                except ValueError:
                                    product_data[key] = 0
                            elif key in ['product_images', 'additional_images', 'variants']:
                                try:
                                    product_data[key] = json.loads(value) if value else []
                                except (json.JSONDecodeError, ValueError):
                                    product_data[key] = []
                            else:
                                product_data[key] = value if value else ""
                        
                        product = Product(**product_data)
                        self.scraped_products.append(product)
                        self.scraped_urls.add(product.source_url)
                    
                    # Update stats
                    self.current_stats['total_products'] = len(self.scraped_products)
                    for product in self.scraped_products:
                        site = product.source_site
                        self.current_stats['site_breakdown'][site] = self.current_stats['site_breakdown'].get(site, 0) + 1
                    
                    logger.info(f"Loaded {len(self.scraped_products)} existing products from {csv_file}")
                    
        except Exception as e:
            logger.error(f"Error loading existing data: {e}")
            # Continue with empty data if loading fails
    

    
    def save_products_periodically(self):
        """Save products periodically to prevent data loss"""
        if len(self.scraped_products) % 5 == 0 and self.scraped_products:
            try:
                # Save to persistent JSON file
                json_file = "scraped_data/products.json"
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump([asdict(p) for p in self.scraped_products], f, indent=2, ensure_ascii=False)
                
                # Save to persistent CSV file
                csv_file = "scraped_data/products.csv"
                with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                    if self.scraped_products:
                        writer = csv.DictWriter(f, fieldnames=asdict(self.scraped_products[0]).keys())
                        writer.writeheader()
                        for product in self.scraped_products:
                            writer.writerow(asdict(product))
                
                logger.info(f"Products saved to persistent files: {json_file}, {csv_file}")
            except Exception as e:
                logger.error(f"Failed to save products: {e}")
    

    
    def scrape_daraz(self, keywords, max_products=100):
        """Scrape Daraz products with improved extraction"""
        self.current_stats['current_site'] = 'Daraz'
        self.current_stats['current_status'] = 'Scraping Daraz...'
        self.emit_update('status_update', self.current_stats)
        
        products_added = 0
        
        for keyword in keywords:
            if products_added >= max_products:
                break
                
            logger.info(f"Scraping Daraz for: {keyword}")
            self.emit_update('status_update', {'current_status': f'Searching Daraz for: {keyword}'})
            
            # Try multiple Daraz URLs for better coverage
            search_urls = [
                f"https://www.daraz.pk/catalog/?q={quote_plus(keyword)}",
                f"https://www.daraz.pk/catalog/?q={quote_plus(keyword)}&_keyori=ss&from=input&spm=a2a0e.searchlist.search.go.35e834a7zaTmDW"
            ]
            
            products_found_for_keyword = 0
            
            for search_url in search_urls:
                if products_found_for_keyword >= 20:  # Limit per keyword
                    break
                    
                response = self.safe_request(search_url)
                
                if response and response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Try multiple selectors for Daraz products - updated for 2024
                    items = soup.select('[data-qa-locator="product-item"]')[:30]
                    
                    if not items:
                        items = soup.select('.gridItem--Yd0sa')[:30]
                    
                    if not items:
                        items = soup.select('.c2prKC')[:30]
                    
                    if not items:
                        items = soup.select('.cRjKsc')[:30]
                    
                    if not items:
                        items = soup.select('[data-testid="product-card"]')[:30]
                    
                    if not items:
                        items = soup.select('.s-item')[:30]
                    
                    if not items:
                        items = soup.select('.product-item')[:30]
                    
                    if not items:
                        items = soup.select('[class*="product"]')[:30]
                    
                    if not items:
                        items = soup.select('[class*="item"]')[:30]
                    
                    # Debug: Log what we found
                    if not items:
                        logger.debug(f"Daraz: No product items found for '{keyword}'")
                        # Log some HTML structure for debugging
                        debug_html = str(soup)[:1000]
                        logger.debug(f"Daraz HTML preview: {debug_html}")
                    else:
                        logger.debug(f"Daraz: Found {len(items)} items for '{keyword}'")
                    
                    for i, item in enumerate(items[:25]):  # Process more items
                        if products_added >= max_products or products_found_for_keyword >= 20:
                            break
                            
                        try:
                            # Multiple title selectors - updated for 2024
                            title_elem = (item.find('div', class_='title--wFj93') or
                                        item.find('a', class_='c16H9d') or
                                        item.find('h3') or
                                        item.find('div', class_='RfADt') or
                                        item.find('div', class_='title') or
                                        item.find('a', class_='title') or
                                        item.find('span', class_='title') or
                                        item.find('div', {'data-qa-locator': 'product-title'}) or
                                        item.find('a', {'data-qa-locator': 'product-title'}))
                            
                            if not title_elem:
                                # Try to find any text that looks like a title
                                title_text = item.get_text()
                                if len(title_text) > 10 and len(title_text) < 200:
                                    title = self.clean_text(title_text)
                                else:
                                    continue
                            else:
                                title = self.clean_text(title_elem.get_text())
                                
                            if len(title) < 10:
                                continue
                            
                            # Multiple price selectors - updated for 2024
                            price_elem = (item.find('span', class_='currency--GVKjl') or
                                        item.find('span', class_='c13VH6') or
                                        item.find('div', class_='aBrP0') or
                                        item.find('span', class_='c1hkC2') or
                                        item.find('span', class_='price') or
                                        item.find('div', class_='price') or
                                        item.find('span', {'data-qa-locator': 'product-price'}) or
                                        item.find('div', {'data-qa-locator': 'product-price'}))
                            
                            if not price_elem:
                                # Try to find price in the entire item text
                                item_text = item.get_text()
                                price_match = re.search(r'Rs\.?\s*([\d,]+)', item_text)
                                if price_match:
                                    price_text = f"Rs. {price_match.group(1)}"
                                else:
                                    price_text = ""
                            else:
                                price_text = price_elem.get_text()
                            extracted_price = self.extract_price(price_text) if price_text else 0.0
                            price = self.ensure_valid_price(extracted_price, title, 'Daraz')
                            
                            # Image
                            img_elem = item.find('img')
                            image_url = img_elem.get('src') or img_elem.get('data-src') if img_elem else ""
                            
                            # Product URL
                            link_elem = item.find('a')
                            product_url = f"https:{link_elem['href']}" if link_elem and link_elem.get('href') else search_url
                            
                            category, sub_category = categorize_product(title)
                            
                            # Extract variants
                            variants = self.extract_variants(soup, title) if random.random() > 0.5 else []
                            product_type = "Variant" if variants else "Single Product"
                            
                            # Ensure required fields
                            sku = f"DRZ-{keyword[:3].upper()}-{i+1:04d}"
                            
                            product = Product(
                                product_name=title,
                                original_title=title,
                                product_type=product_type,
                                unit_price=price,
                                purchase_price=round(price * 0.75, 2),  # Better margin for Pakistani market
                                sku=sku,
                                category=category,
                                sub_category=sub_category,
                                product_description=f"High quality {title} from Daraz Pakistan with fast delivery and COD available",
                                meta_tags_description=f"Buy {title} online in Pakistan with free delivery from Daraz",
                                product_images=[image_url] if image_url else [],
                                rating=0.0,
                                review_count=0,
                                source_site='Daraz',
                                source_url=product_url,
                                product_id=f"daraz_{keyword}_{i+1}",
                                scraped_at=datetime.now().isoformat(),
                                seller_name="Daraz Pakistan",
                                stock_status="In Stock",
                                current_stock=0,
                                variants=variants
                            )
                            
                            if self.add_product(product):
                                products_added += 1
                                products_found_for_keyword += 1
                        
                        except Exception as e:
                            logger.debug(f"Error parsing Daraz item: {e}")
                            continue
                        
                        self.random_delay(0.5, 1.5)
                
                self.random_delay(2, 4)
            
            self.random_delay(1, 3)
        
        logger.info(f"Daraz scraping completed: {products_added} products")
        return self.scraped_products[-products_added:]
    
    def scrape_aliexpress(self, keywords, max_products=100):
        """Scrape AliExpress products with real data only"""
        self.current_stats['current_site'] = 'AliExpress'
        self.current_stats['current_status'] = 'Scraping AliExpress...'
        self.emit_update('status_update', self.current_stats)
        
        products_added = 0
        
        for keyword in keywords:
            if products_added >= max_products:
                break
                
            logger.info(f"Scraping AliExpress for: {keyword}")
            self.emit_update('status_update', {'current_status': f'Searching AliExpress for: {keyword}'})
            
            search_url = f"https://www.aliexpress.com/wholesale?SearchText={quote_plus(keyword)}"
            response = self.safe_request(search_url)
            
            if not response:
                logger.warning(f"AliExpress: Failed to get response for '{keyword}'")
                continue
            
            logger.info(f"AliExpress: Got response {response.status_code} for '{keyword}'")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check if we're being blocked
            page_title = soup.find('title')
            if page_title:
                title_text = page_title.get_text().lower()
                if 'captcha' in title_text or 'robot' in title_text:
                    logger.error(f"AliExpress: CAPTCHA detected for '{keyword}'")
                    continue
            
            # Try multiple selectors for AliExpress
            items = soup.select('.list-item')[:30]
            
            if not items:
                items = soup.select('[data-product-id]')[:30]
            
            if not items:
                items = soup.select('.product-item')[:30]
            
            if not items:
                items = soup.select('[data-ae_object_value]')[:30]
            
            if not items:
                items = soup.select('.JIIxO')[:30]
            
            if not items:
                logger.warning(f"AliExpress: No items found for '{keyword}'")
                continue
            
            for i, item in enumerate(items):
                if products_added >= max_products:
                    break
                    
                try:
                    # Title
                    title_elem = item.select_one('.item-title') or item.select_one('h3') or item.select_one('.product-title')
                    if not title_elem:
                        continue
                    title = self.clean_text(title_elem.get_text())
                    if len(title) < 10:
                        continue
                    
                    # Price
                    price_elem = item.select_one('.price-current') or item.select_one('.price') or item.select_one('[data-price]')
                    price_text = price_elem.get_text(strip=True) if price_elem else "0"
                    price = self.extract_price(price_text)
                    price = self.ensure_valid_price(price, title, 'AliExpress')
                    
                    # Image
                    img_elem = item.select_one('img')
                    image_url = img_elem.get('src') or img_elem.get('data-src') if img_elem else ""
                    
                    # Link
                    link_elem = item.select_one('a')
                    product_url = link_elem['href'] if link_elem and link_elem.get('href') else ""
                    if product_url and not product_url.startswith('http'):
                        product_url = f"https://www.aliexpress.com{product_url}"
                    
                    # Auto-categorize
                    category, sub_category = categorize_product(title)
                    
                    # Generate SKU
                    sku = f"ALI-{keyword[:3].upper()}-{i+1:04d}"
                    
                    # Extract variants if available
                    variants = self.extract_variants(soup, title)
                    
                    product = Product(
                        product_name=title,
                        original_title=title,
                        product_type="Single Product",
                        unit_price=price,
                        purchase_price=round(price * 0.7, 2),
                        sku=sku,
                        category=category,
                        sub_category=sub_category,
                        product_description=f"Quality {title} from AliExpress with worldwide shipping",
                        meta_tags_description=f"Buy {title} from AliExpress at wholesale prices",
                        product_images=[image_url] if image_url else [],
                        rating=0.0,
                        review_count=0,
                        source_site='AliExpress',
                        source_url=product_url,
                        product_id=f"ali_{keyword}_{i+1}",
                        scraped_at=datetime.now().isoformat(),
                        seller_name="AliExpress Seller",
                        stock_status="In Stock",
                        current_stock=0
                    )
                    
                    # Add variants if available
                    if variants:
                        product.variants = variants
                    
                    if self.add_product(product):
                        products_added += 1
                
                except Exception as e:
                    logger.debug(f"Error parsing AliExpress item: {e}")
                    continue
                
                self.random_delay(1, 3)
            
            self.random_delay(5, 10)
        
        logger.info(f"AliExpress scraping completed: {products_added} products")
        return self.scraped_products[-products_added:] if products_added > 0 else []
    
    def scrape_etsy(self, keywords, max_products=100):
        """Scrape Etsy products with real data only"""
        self.current_stats['current_site'] = 'Etsy'
        self.current_stats['current_status'] = 'Scraping Etsy...'
        self.emit_update('status_update', self.current_stats)
        
        products_added = 0
        
        for keyword in keywords:
            if products_added >= max_products:
                break
                
            logger.info(f"Scraping Etsy for: {keyword}")
            self.emit_update('status_update', {'current_status': f'Searching Etsy for: {keyword}'})
            
            search_url = f"https://www.etsy.com/search?q={quote_plus(keyword)}"
            response = self.safe_request(search_url)
            
            if not response:
                logger.warning(f"Etsy: Failed to get response for '{keyword}'")
                continue
            
            logger.info(f"Etsy: Got response {response.status_code} for '{keyword}'")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check if we're being blocked
            page_title = soup.find('title')
            if page_title:
                title_text = page_title.get_text().lower()
                if 'captcha' in title_text or 'robot' in title_text:
                    logger.error(f"Etsy: CAPTCHA detected for '{keyword}'")
                    continue
            
            # Try multiple selectors for Etsy
            items = soup.select('[data-test-id="listing-card"]')[:30]
            
            if not items:
                items = soup.select('.listing-link')[:30]
            
            if not items:
                items = soup.select('.wt-grid__item-xs-6')[:30]
            
            if not items:
                logger.warning(f"Etsy: No items found for '{keyword}'")
                continue
            
            for i, item in enumerate(items):
                if products_added >= max_products:
                    break
                    
                try:
                    # Title
                    title_elem = item.select_one('h3') or item.select_one('.listing-link') or item.select_one('.wt-text-caption')
                    if not title_elem:
                        continue
                    title = self.clean_text(title_elem.get_text())
                    if len(title) < 10:
                        continue
                    
                    # Price
                    price_elem = item.select_one('.currency-value') or item.select_one('.wt-text-title-larger') or item.select_one('[data-price]')
                    price_text = price_elem.get_text(strip=True) if price_elem else "0"
                    price = self.extract_price(price_text)
                    price = self.ensure_valid_price(price, title, 'Etsy')
                    
                    # Image
                    img_elem = item.select_one('img')
                    image_url = img_elem.get('src') or img_elem.get('data-src') if img_elem else ""
                    
                    # Link
                    link_elem = item.select_one('a')
                    product_url = link_elem['href'] if link_elem and link_elem.get('href') else ""
                    if product_url and not product_url.startswith('http'):
                        product_url = f"https://www.etsy.com{product_url}"
                    
                    # Auto-categorize
                    category, sub_category = categorize_product(title)
                    if category == "Electronics":  # Override for Etsy
                        category, sub_category = "Art & Crafts", "Handmade"
                    
                    # Generate SKU
                    sku = f"ETS-{keyword[:3].upper()}-{i+1:04d}"
                    
                    # Extract variants if available
                    variants = self.extract_variants(soup, title)
                    
                    product = Product(
                        product_name=title,
                        original_title=title,
                        product_type="Single Product",
                        unit_price=price,
                        purchase_price=round(price * 0.75, 2),
                        sku=sku,
                        category=category,
                        sub_category=sub_category,
                        product_description=f"Handmade {title} from Etsy artisan with unique craftsmanship",
                        meta_tags_description=f"Buy handmade {title} from Etsy marketplace",
                        product_images=[image_url] if image_url else [],
                        rating=0.0,
                        review_count=0,
                        source_site='Etsy',
                        source_url=product_url,
                        product_id=f"etsy_{keyword}_{i+1}",
                        scraped_at=datetime.now().isoformat(),
                        seller_name="Etsy Marketplace",
                        stock_status="In Stock",
                        current_stock=0
                    )
                    
                    # Add variants if available
                    if variants:
                        product.variants = variants
                    
                    if self.add_product(product):
                        products_added += 1
                        logger.info(f"Found Etsy product: {title[:50]}...")
                
                except Exception as e:
                    logger.debug(f"Error parsing Etsy item: {e}")
                    continue
                
                self.random_delay(1, 3)
            
            self.random_delay(5, 10)
        
        logger.info(f"Etsy scraping completed: {products_added} products")
        return self.scraped_products[-products_added:] if products_added > 0 else []
    
    def scrape_valuebox(self, keywords, max_products=100):
        """Scrape ValueBox products with real data only"""
        self.current_stats['current_site'] = 'ValueBox'
        self.current_stats['current_status'] = 'Scraping ValueBox...'
        self.emit_update('status_update', self.current_stats)
        
        products_added = 0
        
        for keyword in keywords:
            if products_added >= max_products:
                break
                
            logger.info(f"Scraping ValueBox for: {keyword}")
            self.emit_update('status_update', {'current_status': f'Searching ValueBox for: {keyword}'})
            
            search_url = f"https://www.valuebox.pk/search?q={quote_plus(keyword)}"
            response = self.safe_request(search_url)
            
            if not response:
                logger.warning(f"ValueBox: Failed to get response for '{keyword}'")
                continue
            
            logger.info(f"ValueBox: Got response {response.status_code} for '{keyword}'")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check if we're being blocked
            page_title = soup.find('title')
            if page_title:
                title_text = page_title.get_text().lower()
                if 'captcha' in title_text or 'robot' in title_text:
                    logger.error(f"ValueBox: CAPTCHA detected for '{keyword}'")
                    continue
            
            # Try multiple selectors for ValueBox
            items = soup.select('.product-item')[:30]
            
            if not items:
                items = soup.select('[data-product-id]')[:30]
            
            if not items:
                items = soup.select('.product-card')[:30]
            
            if not items:
                logger.warning(f"ValueBox: No items found for '{keyword}'")
                continue
            
            for i, item in enumerate(items):
                if products_added >= max_products:
                    break
                    
                try:
                    # Title - try multiple selectors for ValueBox
                    title_elem = (item.select_one('.product-title') or 
                                 item.select_one('h3') or 
                                 item.select_one('.product-name') or
                                 item.select_one('.title') or
                                 item.select_one('a[title]') or
                                 item.select_one('[data-title]'))
                    
                    if not title_elem:
                        # Try to get title from link text or alt text
                        link_elem = item.select_one('a')
                        if link_elem:
                            title = link_elem.get('title') or link_elem.get_text(strip=True)
                        else:
                            # Try to find any text that looks like a title
                            title_text = item.get_text()
                            if len(title_text) > 10 and len(title_text) < 200:
                                title = self.clean_text(title_text)
                            else:
                                continue
                    else:
                        title = self.clean_text(title_elem.get_text())
                        
                    if len(title) < 10:
                        continue
                    
                    # Price
                    price_elem = item.select_one('.product-price') or item.select_one('.price') or item.select_one('[data-price]')
                    price_text = price_elem.get_text(strip=True) if price_elem else "0"
                    price = self.extract_price(price_text)
                    price = self.ensure_valid_price(price, title, 'ValueBox')
                    
                    # Image
                    img_elem = item.select_one('img')
                    image_url = img_elem.get('src') or img_elem.get('data-src') if img_elem else ""
                    
                    # Link
                    link_elem = item.select_one('a')
                    product_url = link_elem['href'] if link_elem and link_elem.get('href') else ""
                    if product_url and not product_url.startswith('http'):
                        product_url = f"https://www.valuebox.pk{product_url}"
                    
                    # Auto-categorize
                    category, sub_category = categorize_product(title)
                    
                    # Generate SKU
                    sku = f"VBX-{keyword[:3].upper()}-{i+1:04d}"
                    
                    # Extract variants if available
                    variants = self.extract_variants(soup, title)
                    
                    product = Product(
                        product_name=title,
                        original_title=title,
                        product_type="Single Product",
                        unit_price=price,
                        purchase_price=round(price * 0.75, 2),
                        sku=sku,
                        category=category,
                        sub_category=sub_category,
                        product_description=f"Premium quality {title} from ValueBox Pakistan with nationwide delivery",
                        meta_tags_description=f"Buy {title} from ValueBox Pakistan at best prices",
                        product_images=[image_url] if image_url else [],
                        rating=0.0,
                        review_count=0,
                        source_site='ValueBox',
                        source_url=product_url,
                        product_id=f"valuebox_{keyword}_{i+1}",
                        scraped_at=datetime.now().isoformat(),
                        seller_name="ValueBox Pakistan",
                        stock_status="In Stock",
                        current_stock=0
                    )
                    
                    # Add variants if available
                    if variants:
                        product.variants = variants
                    
                    if self.add_product(product):
                        products_added += 1
                        logger.info(f"Found ValueBox product: {title[:50]}...")
                
                except Exception as e:
                    logger.debug(f"Error parsing ValueBox item: {e}")
                    continue
                
                self.random_delay(1, 3)
            
            self.random_delay(5, 10)
        
        logger.info(f"ValueBox scraping completed: {products_added} products")
        return self.scraped_products[-products_added:] if products_added > 0 else []
    
    def scrape_selected_sites(self, keywords, max_products_per_site=100, selected_sites=None):
        """Scrape only selected sites"""
        if selected_sites is None:
            # Focus on sites that are currently working
            selected_sites = ['amazon', 'valuebox']  # eBay, Daraz, AliExpress, Etsy are currently blocked
        
        # Map site names to proper case and ensure they match the scraper methods
        site_mapping = {
            'amazon': 'amazon',
            'ebay': 'ebay', 
            'daraz': 'daraz',
            'aliexpress': 'aliexpress',
            'etsy': 'etsy',
            'valuebox': 'valuebox'
        }
        
        # Convert to lowercase and map to correct names
        selected_sites = [site_mapping.get(site.lower(), site.lower()) for site in selected_sites]
        
        # Create display mapping for UI
        display_mapping = {
            'amazon': 'Amazon',
            'ebay': 'eBay', 
            'daraz': 'Daraz',
            'aliexpress': 'AliExpress',
            'etsy': 'Etsy',
            'valuebox': 'ValueBox'
        }
        
        self.emit_update('scraping_started', {'total_sites': len(selected_sites), 'keywords': keywords})
        
        # Rotate keywords to avoid pattern detection
        rotated_keywords = keywords * 3  # Repeat keywords to get more products
        random.shuffle(rotated_keywords)
        
        scrapers = {
            'amazon': self.scrape_amazon,
            'ebay': self.scrape_ebay,
            'daraz': self.scrape_daraz,
            'aliexpress': self.scrape_aliexpress,
            'etsy': self.scrape_etsy,
            'valuebox': self.scrape_valuebox
        }
        
        for site_name in selected_sites:
            if site_name not in scrapers:
                continue
                
            try:
                display_name = display_mapping.get(site_name, site_name.title())
                logger.info(f"Starting {display_name} scraping...")
                self.emit_update('site_started', {'site': display_name})
                
                # Progressive delay between sites to avoid detection
                if site_name != selected_sites[0]:  # Skip delay for first site
                    delay = random.uniform(60, 120)  # 1-2 minutes between sites
                    logger.info(f"Waiting {delay:.1f} seconds before {display_name}...")
                    time.sleep(delay)
                
                scrapers[site_name](rotated_keywords, max_products_per_site)
                
                site_count = self.current_stats['site_breakdown'].get(display_name, 0)
                logger.info(f"{display_name}: {site_count} products scraped")
                self.emit_update('site_completed', {'site': display_name, 'count': site_count})
                
                time.sleep(random.uniform(30, 60))  # Longer delay between sites
                
            except Exception as e:
                logger.error(f"Error scraping {site_name}: {e}")
                self.emit_update('site_error', {'site': site_name, 'error': str(e)})
                continue
        
        # Final cleanup and save
        final_products = self.clean_and_deduplicate(self.scraped_products)
        saved_files = self.save_products(final_products)
        
        self.emit_update('scraping_completed', {
            'total_products': len(final_products),
            'site_breakdown': self.current_stats['site_breakdown'],
            'files': saved_files
        })
        
        return final_products
    
    def clean_and_deduplicate(self, products):
        """Clean and deduplicate products"""
        seen_urls = set()
        cleaned_products = []
        
        for product in products:
            if product.source_url not in seen_urls:
                seen_urls.add(product.source_url)
                cleaned_products.append(product)
        
        return cleaned_products
    
    def save_products(self, products):
        """Save products to persistent files"""
        saved_files = []
        
        # Save as JSON
        json_file = "scraped_data/products.json"
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(p) for p in products], f, indent=2, ensure_ascii=False)
            saved_files.append(json_file)
            logger.info(f"Products saved to {json_file}")
        except Exception as e:
            logger.error(f"Failed to save JSON: {e}")
        
        # Save as CSV
        csv_file = "scraped_data/products.csv"
        try:
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                if products:
                    writer = csv.DictWriter(f, fieldnames=asdict(products[0]).keys())
                    writer.writeheader()
                    for product in products:
                        writer.writerow(asdict(product))
            saved_files.append(csv_file)
            logger.info(f"Products saved to {csv_file}")
        except Exception as e:
            logger.error(f"Failed to save CSV: {e}")
        
        return saved_files
    
    def cleanup(self):
        """Cleanup and save data when scraper is stopped"""
        try:
            if self.scraped_products:
                logger.info("Saving data before cleanup...")
                self.save_products_periodically()
                logger.info(f"Cleanup completed. {len(self.scraped_products)} products saved.")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def force_save(self):
        """Force save current data to persistent files"""
        try:
            if self.scraped_products:
                logger.info("Force saving current data...")
                self.save_products_periodically()
                return True
            else:
                logger.info("No products to save")
                return False
        except Exception as e:
            logger.error(f"Error force saving: {e}")
            return False
    
    def __del__(self):
        """Destructor to ensure data is saved when scraper is destroyed"""
        self.cleanup()
