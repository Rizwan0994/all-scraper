#!/usr/bin/env python3
"""
Advanced Amazon Variant Extractor
Handles complex JavaScript-rendered variant data with proper interaction
"""

import time
import json
import logging
import re
from typing import List, Dict, Any, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class AmazonVariantExtractor:
    """Advanced Amazon variant extractor with proper JavaScript interaction"""
    
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
        
    def extract_variants_comprehensive(self, product_url: str, product_name: str, main_price: float) -> List[Dict]:
        """
        Comprehensive variant extraction with proper JavaScript interaction
        """
        variants = []
        
        try:
            logger.info(f"Extracting variants for: {product_name[:50]}...")
            
            # Navigate to product page
            self.driver.get(product_url)
            time.sleep(3)
            
            # Wait for page to load completely
            self._wait_for_page_load()
            
            # Method 1: Extract from variation containers (most reliable)
            variants.extend(self._extract_from_variation_containers())
            
            # Method 2: Extract from dropdown selectors
            variants.extend(self._extract_from_dropdowns())
            
            # Method 3: Extract from button groups
            variants.extend(self._extract_from_button_groups())
            
            # Method 4: Extract from JSON-LD structured data
            variants.extend(self._extract_from_json_ld())
            
            # Method 5: Extract from data attributes
            variants.extend(self._extract_from_data_attributes())
            
            # Method 6: Interactive extraction (click and extract)
            variants.extend(self._extract_interactively())
            
            # Clean and deduplicate variants
            variants = self._clean_variants(variants, main_price)
            
            logger.info(f"Found {len(variants)} clean variants")
            return variants
            
        except Exception as e:
            logger.error(f"Variant extraction failed: {e}")
            return []
    
    def _wait_for_page_load(self):
        """Wait for page to load completely"""
        try:
            # Wait for main content to load
            self.wait.until(EC.presence_of_element_located((By.ID, "dp-container")))
            time.sleep(2)
            
            # Wait for any loading indicators to disappear
            try:
                self.wait.until_not(EC.presence_of_element_located((By.CLASS_NAME, "a-spinner")))
            except TimeoutException:
                pass
                
        except TimeoutException:
            logger.warning("Page load timeout, continuing anyway")
    
    def _extract_from_variation_containers(self) -> List[Dict]:
        """Extract variants from Amazon's variation containers"""
        variants = []
        
        try:
            # Common variation container selectors
            selectors = [
                '#variation_color_name',
                '#variation_size_name', 
                '#variation_storage_name',
                '#variation_style_name',
                '#variation_pattern_name',
                '#variation_material_name',
                '#variation_edition_name',
                '#variation_format_name',
                '#variation_platform_name',
                '#variation_operating_system_name',
                '#variation_connectivity_technology_name',
                '#variation_screen_size_name',
                '#variation_resolution_name',
                '#variation_cpu_model_name',
                '#variation_ram_memory_installed_size_name',
                '#variation_hard_disk_size_name',
                '#variation_graphics_coprocessor_name',
                '#variation_brand_name',
                '#variation_model_name',
                '#variation_item_model_number_name',
                '#variation_color_name ul',
                '#variation_size_name ul',
                '#variation_storage_name ul',
                '.a-button-group',
                '.a-button-toggle-group',
                '[data-cy="color-picker"]',
                '[data-testid="variant-color"]',
                '[data-testid="variant-size"]',
                '[data-testid="variant-storage"]',
                '.variation-container',
                '.variation-wrapper',
                '.a-button[data-action="a-dropdown-button"]',
                '.a-button-toggle[data-action="a-dropdown-button"]'
            ]
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        variants.extend(self._extract_variants_from_element(element))
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.debug(f"Variation container extraction failed: {e}")
            
        return variants
    
    def _extract_from_dropdowns(self) -> List[Dict]:
        """Extract variants from dropdown selectors"""
        variants = []
        
        try:
            # Find all select elements
            selects = self.driver.find_elements(By.TAG_NAME, "select")
            
            for select in selects:
                try:
                    # Check if it's a variation dropdown
                    select_id = select.get_attribute("id") or ""
                    select_name = select.get_attribute("name") or ""
                    
                    # Skip quantity selectors
                    if any(qty in select_id.lower() or qty in select_name.lower() 
                           for qty in ['quantity', 'qty', 'amount']):
                        continue
                    
                    # Get options
                    options = select.find_elements(By.TAG_NAME, "option")
                    
                    for option in options:
                        option_text = option.text.strip()
                        option_value = option.get_attribute("value") or ""
                        
                        # Skip placeholder options
                        if (option_text in ['Select', 'Choose', 'Size', 'Color', 'Please select'] or
                            not option_text or len(option_text) < 2):
                            continue
                        
                        # Skip quantity-like options
                        if (option_text.isdigit() or 
                            option_text.endswith('+') or 
                            option_text.startswith('Qty')):
                            continue
                        
                        variant = {
                            'type': self._detect_variant_type(select_id, select_name, option_text),
                            'name': option_text,
                            'value': option_value,
                            'price': None,  # Will be filled later
                            'stock': 50,
                            'sku': f"VAR-{hash(option_text) % 10000:04d}",
                            'images': None,  # Let universal scraper handle image mapping
                            'attributes': {self._detect_variant_type(select_id, select_name, option_text): option_text}
                        }
                        variants.append(variant)
                        
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.debug(f"Dropdown extraction failed: {e}")
            
        return variants
    
    def _extract_color_swatches(self) -> List[Dict]:
        """Extract color variants from image swatches specifically"""
        variants = []
        
        try:
            # Look for color swatch containers
            color_selectors = [
                '.a-button-group .a-button[data-action="a-dropdown-button"]',
                '.a-button-toggle-group .a-button[data-action="a-dropdown-button"]',
                '.a-button[data-action="a-dropdown-button"]',
                '.a-button-toggle[data-action="a-dropdown-button"]',
                # Color-specific selectors
                '.a-button[aria-label*="color"]',
                '.a-button[aria-label*="Color"]',
                '.a-button[title*="color"]',
                '.a-button[title*="Color"]',
                # Image swatch selectors
                '.swatch-container .swatch-button',
                '.color-swatch-container .a-button',
                '.variation-selector-box .a-button'
            ]
            
            for selector in color_selectors:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for button in buttons:
                        try:
                            button_text = button.text.strip()
                            button_aria = button.get_attribute('aria-label') or ''
                            button_title = button.get_attribute('title') or ''
                            
                            # Extract color name from text, aria-label, or title
                            color_name = button_text or button_aria or button_title
                            
                            # Skip if no meaningful color name
                            if (not color_name or len(color_name) < 2 or
                                color_name.lower() in ['select', 'choose', 'color', 'size'] or
                                'video' in color_name.lower() or 'photo' in color_name.lower()):
                                continue
                            
                            # Clean up color name
                            color_name = color_name.replace('Color:', '').replace('color:', '').strip()
                            
                            variant = {
                                'type': 'color',
                                'name': color_name,
                                'value': color_name,
                                'price': None,  # Will be updated after click
                                'stock': 50,
                                'sku': f"COLOR-{hash(color_name) % 10000:04d}",
                                'images': None,  # Let universal scraper handle image mapping
                                'attributes': {'color': color_name}
                            }
                            variants.append(variant)
                            
                        except Exception as e:
                            continue
                            
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.debug(f"Color swatch extraction failed: {e}")
        
        return variants

    def _extract_from_button_groups(self) -> List[Dict]:
        """Extract variants from button groups"""
        variants = []
        
        # First try to extract color swatches specifically
        variants.extend(self._extract_color_swatches())
        
        try:
            # Find button groups - prioritize color and variant selectors
            button_selectors = [
                # Color variant selectors (highest priority)
                '.a-button-group .a-button[data-action="a-dropdown-button"]',
                '.a-button-toggle-group .a-button[data-action="a-dropdown-button"]',
                '.a-button[data-action="a-dropdown-button"]',
                '.a-button-toggle[data-action="a-dropdown-button"]',
                # Color swatch selectors
                '.a-button-group .a-button',
                '.a-button-toggle-group .a-button',
                '.a-button-group button',
                '.a-button-toggle-group button',
                # Generic selectors
                '[role="radiogroup"] button',
                '[role="radiogroup"] [role="radio"]',
                # Additional color-specific selectors
                '.a-button[aria-label*="color"]',
                '.a-button[aria-label*="Color"]',
                '.a-button[title*="color"]',
                '.a-button[title*="Color"]'
            ]
            
            for selector in button_selectors:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for button in buttons:
                        try:
                            button_text = button.text.strip()
                            
                            # Skip empty or invalid buttons
                            if (not button_text or len(button_text) < 2 or
                                button_text in ['Select', 'Choose', 'Size', 'Color'] or
                                button_text.isdigit() or button_text.endswith('+')):
                                continue
                            
                            # Get button attributes
                            button_id = button.get_attribute("id") or ""
                            button_class = button.get_attribute("class") or ""
                            
                            variant = {
                                'type': self._detect_variant_type(button_id, button_class, button_text),
                                'name': button_text,
                                'value': button.get_attribute("value") or button_text,
                                'price': None,
                                'stock': 50,
                                'sku': f"VAR-{hash(button_text) % 10000:04d}",
                                'images': None,  # Let universal scraper handle image mapping
                                'attributes': {self._detect_variant_type(button_id, button_class, button_text): button_text}
                            }
                            variants.append(variant)
                            
                        except Exception as e:
                            continue
                            
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.debug(f"Button group extraction failed: {e}")
            
        return variants
    
    def _extract_from_json_ld(self) -> List[Dict]:
        """Extract variants from JSON-LD structured data"""
        variants = []
        
        try:
            # Find JSON-LD scripts
            scripts = self.driver.find_elements(By.CSS_SELECTOR, 'script[type="application/ld+json"]')
            
            for script in scripts:
                try:
                    json_data = json.loads(script.get_attribute("innerHTML"))
                    
                    # Look for offers with variations
                    if isinstance(json_data, dict):
                        offers = json_data.get('offers', [])
                        if not isinstance(offers, list):
                            offers = [offers]
                        
                        for offer in offers:
                            if isinstance(offer, dict):
                                # Check for variant information
                                if 'itemCondition' in offer or 'availability' in offer:
                                    variant_name = offer.get('name', '')
                                    variant_price = offer.get('price', '')
                                    
                                    if variant_name and variant_name != json_data.get('name', ''):
                                        variant = {
                                            'type': 'variant',
                                            'name': variant_name,
                                            'value': variant_name,
                                            'price': self._parse_price(variant_price),
                                            'stock': 50,
                                            'sku': f"VAR-{hash(variant_name) % 10000:04d}",
                                            'images': None,  # Let universal scraper handle image mapping
                                            'attributes': {'variant': variant_name}
                                        }
                                        variants.append(variant)
                                        
                except (json.JSONDecodeError, KeyError):
                    continue
                    
        except Exception as e:
            logger.debug(f"JSON-LD extraction failed: {e}")
            
        return variants
    
    def _extract_from_data_attributes(self) -> List[Dict]:
        """Extract variants from data attributes"""
        variants = []
        
        try:
            # Look for elements with variant data attributes
            selectors = [
                '[data-variation-name]',
                '[data-variant-name]',
                '[data-option-name]',
                '[data-color-name]',
                '[data-size-name]',
                '[data-storage-name]',
                '[data-style-name]'
            ]
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        variant_name = (element.get_attribute("data-variation-name") or
                                      element.get_attribute("data-variant-name") or
                                      element.get_attribute("data-option-name") or
                                      element.get_attribute("data-color-name") or
                                      element.get_attribute("data-size-name") or
                                      element.get_attribute("data-storage-name") or
                                      element.get_attribute("data-style-name"))
                        
                        if variant_name and len(variant_name.strip()) > 1:
                            variant = {
                                'type': self._detect_variant_type_from_selector(selector),
                                'name': variant_name.strip(),
                                'value': variant_name.strip(),
                                'price': None,
                                'stock': 50,
                                'sku': f"VAR-{hash(variant_name) % 10000:04d}",
                                'images': None,  # Let universal scraper handle image mapping
                                'attributes': {self._detect_variant_type_from_selector(selector): variant_name.strip()}
                            }
                            variants.append(variant)
                            
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.debug(f"Data attribute extraction failed: {e}")
            
        return variants
    
    def _extract_interactively(self) -> List[Dict]:
        """Extract variants by interacting with the page"""
        variants = []
        
        try:
            # Find clickable variation elements
            clickable_selectors = [
                '.a-button-group button',
                '.a-button-toggle-group button',
                '[data-action="a-dropdown-button"]',
                '.variation-container button',
                '.variation-wrapper button'
            ]
            
            for selector in clickable_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        try:
                            # Click the element to reveal variant information
                            self.driver.execute_script("arguments[0].click();", element)
                            time.sleep(1)
                            
                            # Extract information after click
                            variant_info = self._extract_variant_info_after_click(element)
                            if variant_info:
                                variants.append(variant_info)
                                
                        except Exception as e:
                            continue
                            
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.debug(f"Interactive extraction failed: {e}")
            
        return variants
    
    def _extract_variants_from_element(self, element) -> List[Dict]:
        """Extract variants from a specific element"""
        variants = []
        
        try:
            # Get all child elements that might contain variant info
            child_elements = element.find_elements(By.CSS_SELECTOR, "button, option, li, span, div")
            
            for child in child_elements:
                try:
                    text = child.text.strip()
                    
                    # Skip invalid text
                    if (not text or len(text) < 2 or
                        text in ['Select', 'Choose', 'Size', 'Color'] or
                        text.isdigit() or text.endswith('+')):
                        continue
                    
                    variant = {
                        'type': 'variant',
                        'name': text,
                        'value': text,
                        'price': None,
                        'stock': 50,
                        'sku': f"VAR-{hash(text) % 10000:04d}",
                        'images': None,  # Let universal scraper handle image mapping
                        'attributes': {'variant': text}
                    }
                    variants.append(variant)
                    
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.debug(f"Element variant extraction failed: {e}")
            
        return variants
    
    def _extract_variant_info_after_click(self, element) -> Optional[Dict]:
        """Extract variant information after clicking an element"""
        try:
            # Wait for any dynamic content to load
            time.sleep(1)
            
            # Look for updated price or variant information
            price_element = self.driver.find_element(By.CSS_SELECTOR, ".a-price-whole, .a-price .a-offscreen")
            price_text = price_element.text if price_element else ""
            
            variant_name = element.text.strip()
            
            if variant_name and len(variant_name) > 1:
                return {
                    'type': 'variant',
                    'name': variant_name,
                    'value': variant_name,
                    'price': self._parse_price(price_text),
                    'stock': 50,
                    'sku': f"VAR-{hash(variant_name) % 10000:04d}",
                    'images': [],
                    'attributes': {'variant': variant_name}
                }
                
        except Exception as e:
            logger.debug(f"Post-click extraction failed: {e}")
            
        return None
    
    def _detect_variant_type(self, element_id: str, element_class: str, variant_text: str) -> str:
        """Detect the type of variant based on context"""
        context = (element_id + " " + element_class + " " + variant_text).lower()
        
        if any(color_word in context for color_word in ['color', 'colour', 'black', 'white', 'red', 'blue', 'green']):
            return 'color'
        elif any(size_word in context for size_word in ['size', 'small', 'medium', 'large', 'xl', 'xxl']):
            return 'size'
        elif any(storage_word in context for storage_word in ['storage', 'gb', 'tb', 'memory', 'ram']):
            return 'storage'
        elif any(style_word in context for style_word in ['style', 'model', 'edition', 'version']):
            return 'style'
        else:
            return 'variant'
    
    def _detect_variant_type_from_selector(self, selector: str) -> str:
        """Detect variant type from CSS selector"""
        if 'color' in selector:
            return 'color'
        elif 'size' in selector:
            return 'size'
        elif 'storage' in selector:
            return 'storage'
        elif 'style' in selector:
            return 'style'
        else:
            return 'variant'
    
    def _parse_price(self, price_text: str) -> Optional[float]:
        """Parse price from text"""
        try:
            if not price_text:
                return None
                
            # Remove currency symbols and extract number
            import re
            price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
            if price_match:
                return float(price_match.group())
        except:
            pass
        return None
    
    def _clean_variants(self, variants: List[Dict], main_price: float) -> List[Dict]:
        """Clean and deduplicate variants with enhanced filtering"""
        cleaned = []
        seen = set()
        
        # Enhanced invalid patterns
        invalid_patterns = [
            r'^\d+\+?$',  # Numbers with optional +
            r'^qty',  # Quantity indicators
            r'^quantity',  # Quantity indicators
            r'add to list',  # UI elements
            r'update page',  # UI elements
            r'select',  # Placeholder text
            r'choose',  # Placeholder text
            r'please select',  # Placeholder text
            r'videos?',  # Media content indicators
            r'\d+\s*videos?',  # Number of videos
            r'photos?',  # Media content indicators
            r'\d+\s*photos?',  # Number of photos
            r'images?',  # Media content indicators
            r'\d+\s*images?',  # Number of images
            r'^all departments$',  # Navigation elements
            r'^arts & crafts$',  # Navigation elements
            r'^automotive$',  # Navigation elements
            r'^baby$',  # Navigation elements
            r'^beauty & personal care$',  # Navigation elements
            r'^books$',  # Navigation elements
            r'^boys\' fashion$',  # Navigation elements
            r'^computers$',  # Navigation elements
            r'^deals$',  # Navigation elements
            r'^digital music$',  # Navigation elements
            r'^electronics$',  # Navigation elements
            r'^girls\' fashion$',  # Navigation elements
            r'^health & household$',  # Navigation elements
            r'^home & kitchen$',  # Navigation elements
            r'^industrial & scientific$',  # Navigation elements
            r'^kindle store$',  # Navigation elements
            r'^luggage$',  # Navigation elements
            r'^men\'s fashion$',  # Navigation elements
            r'^movies & tv$',  # Navigation elements
            r'^music, cds & vinyl$',  # Navigation elements
            r'^pet supplies$',  # Navigation elements
            r'^prime video$',  # Navigation elements
            r'^software$',  # Navigation elements
            r'^sports & outdoors$',  # Navigation elements
            r'^tools & home improvement$',  # Navigation elements
            r'^toys & games$',  # Navigation elements
            r'^video games$',  # Navigation elements
            r'^women\'s fashion$',  # Navigation elements
        ]
        
        for variant in variants:
            # Skip invalid variants
            if not variant.get('name') or len(variant.get('name', '')) < 2:
                continue
            
            name = variant['name'].strip()
            
            # Check against invalid patterns
            is_invalid = False
            for pattern in invalid_patterns:
                if re.match(pattern, name.lower()):
                    is_invalid = True
                    break
            
            if is_invalid:
                continue
            
            # Additional checks
            if (name.isdigit() or name.endswith('+') or 
                name.startswith('Qty') or name in ['Add to List', 'Update Page']):
                continue
            
            # Create unique key
            key = f"{variant['type']}_{name}"
            if key in seen:
                continue
            seen.add(key)
            
            # Set default price if not set
            if variant.get('price') is None:
                variant['price'] = main_price
            
            # Ensure required fields
            variant.setdefault('stock', 50)
            variant.setdefault('sku', f"VAR-{hash(name) % 10000:04d}")
            variant.setdefault('images', None)  # Let universal scraper handle image mapping
            variant.setdefault('attributes', {variant['type']: name})
            
            cleaned.append(variant)
        
        return cleaned
