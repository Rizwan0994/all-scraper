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
    
    def _extract_variant_type_from_selector(self, selector: str, element) -> str:
        """Extract variant type from selector and element context"""
        try:
            # Check selector for type hints
            selector_lower = selector.lower()
            
            if any(x in selector_lower for x in ['style', 'color', 'colour']):
                return 'style'
            elif any(x in selector_lower for x in ['size', 'dimensions']):
                return 'size'
            elif any(x in selector_lower for x in ['storage', 'memory', 'gb', 'tb']):
                return 'storage'
            elif any(x in selector_lower for x in ['network', 'carrier', 'unlocked']):
                return 'network'
            elif any(x in selector_lower for x in ['model', 'configuration', 'config']):
                return 'model'
            
            # Check element attributes and text
            element_id = (element.get_attribute('id') or '').lower()
            element_class = (element.get_attribute('class') or '').lower()
            element_text = (element.text or '').lower()
            
            if any(x in element_id for x in ['style', 'color']):
                return 'style'
            elif any(x in element_id for x in ['size']):
                return 'size'
            elif any(x in element_id for x in ['storage', 'memory']):
                return 'storage'
            elif any(x in element_id for x in ['network', 'carrier']):
                return 'network'
            elif any(x in element_id for x in ['model', 'config']):
                return 'model'
            
            # Check text content for hints
            if any(x in element_text for x in ['gb', 'tb', 'storage']):
                return 'storage'
            elif any(x in element_text for x in ['att', 'verizon', 't-mobile', 'unlocked', 'carrier']):
                return 'network'
            elif any(x in element_text for x in ['small', 'medium', 'large', 'xl', 'xxl']):
                return 'size'
            
            return 'variant'  # Default fallback
            
        except Exception:
            return 'variant'

    def _extract_interactively(self) -> List[Dict]:
        """Extract variant information by interacting with the page - ENHANCED FOR PERFECT DATA"""
        variants = []
        found_variant_groups = []
        
        try:
            logger.info("🎯 Starting ENHANCED interactive variant extraction...")
            
            # Enhanced selectors for variant containers
            variant_container_selectors = [
                # Style variants (color/design)
                "[data-feature-name='variation'] .a-button-group .a-button",
                "[data-feature-name='variation'] [role='radiogroup'] .a-button",
                "#variation_style_name .a-button",
                ".a-button-group[role='radiogroup'] .a-button",
                "[id*='style'] .a-button",
                
                # Size variants
                "#variation_size_name .a-button",
                "[data-feature-name='size'] .a-button",
                ".size-button-text .a-button",
                "[id*='size'] .a-button",
                
                # Configuration/Model variants  
                "[data-feature-name='configuration'] .a-button",
                "#variation_configuration .a-button",
                "[id*='configuration'] .a-button",
                "[id*='model'] .a-button",
                
                # Storage/Memory variants
                "#variation_storage .a-button", 
                "[data-feature-name='storage'] .a-button",
                "[id*='storage'] .a-button",
                "[id*='memory'] .a-button",
                
                # Network/Carrier variants
                "[data-feature-name='network'] .a-button",
                "#variation_network .a-button",
                "[id*='network'] .a-button",
                "[id*='carrier'] .a-button",
                
                # Generic fallbacks
                ".a-button-toggle .a-button",
                "[data-action='a-dropdown-button'] .a-button",
                ".a-declarative .a-button[aria-label]"
            ]
            
            for selector in variant_container_selectors:
                try:
                    logger.debug(f"🔍 Checking selector: {selector}")
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    if elements:
                        logger.info(f"✅ Found {len(elements)} potential variants with selector: {selector}")
                        
                        # Extract variant type from selector/container
                        variant_type = self._extract_variant_type_from_selector(selector, elements[0])
                        
                        group_variants = []
                        for i, element in enumerate(elements):
                            try:
                                # Skip if element is not visible or clickable
                                if not element.is_displayed() or not element.is_enabled():
                                    continue
                                
                                logger.info(f"🖱️ Clicking variant {i+1}/{len(elements)}: {element.text[:30]}...")
                                
                                # Scroll element into view
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                                time.sleep(1)
                                
                                # Try multiple click methods
                                clicked = False
                                click_methods = [
                                    lambda: element.click(),
                                    lambda: self.driver.execute_script("arguments[0].click();", element),
                                    lambda: ActionChains(self.driver).move_to_element(element).click().perform()
                                ]
                                
                                for method in click_methods:
                                    try:
                                        method()
                                        clicked = True
                                        break
                                    except Exception as e:
                                        logger.debug(f"Click method failed: {e}")
                                        continue
                                
                                if not clicked:
                                    logger.warning(f"❌ Could not click element: {element.text}")
                                    continue
                                
                                # Enhanced wait for page updates
                                time.sleep(3)  # Increased wait time
                                
                                # Extract comprehensive variant data
                                variant_data = self._extract_variant_info_after_click(element)
                                
                                if variant_data:
                                    variant_data['type'] = variant_type  # Override with detected type
                                    group_variants.append(variant_data)
                                    logger.info(f"✅ Successfully extracted: {variant_data['name']} (${variant_data.get('price', 'N/A')})")
                                else:
                                    logger.warning(f"⚠️ No variant data extracted for: {element.text}")
                                
                                # Brief pause between clicks
                                time.sleep(1)
                                
                            except Exception as e:
                                logger.error(f"❌ Error processing variant element: {e}")
                                continue
                        
                        if group_variants:
                            variants.extend(group_variants)
                            found_variant_groups.append({
                                'type': variant_type,
                                'count': len(group_variants),
                                'selector': selector
                            })
                            logger.info(f"🎉 Added {len(group_variants)} {variant_type} variants")
                            
                            # If we found a good number of variants, we can stop
                            if len(variants) >= 15:  # Reasonable limit
                                break
                                
                except Exception as e:
                    logger.debug(f"Selector failed: {selector} - {e}")
                    continue
            
            # Final summary
            if variants:
                logger.info(f"🎉 EXTRACTION COMPLETE: Found {len(variants)} total variants across {len(found_variant_groups)} groups")
                for group in found_variant_groups:
                    logger.info(f"   📋 {group['type']}: {group['count']} variants (selector: {group['selector'][:50]}...)")
            else:
                logger.warning("❌ No variants found with interactive extraction")
                
        except Exception as e:
            logger.error(f"❌ Interactive extraction failed: {e}")
        
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
        """Extract variant information after clicking an element - ENHANCED FOR PERFECT DATA"""
        try:
            # 🚀 ENHANCED WAIT STRATEGY - Wait longer for content to fully load
            print(f"⏳ Waiting for variant data to load...")
            time.sleep(4)  # Increased wait time for content to fully load
            
            # Wait for critical elements with multiple attempts
            wait_attempts = 0
            while wait_attempts < 3:
                try:
                    # Wait for price to potentially update
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".a-price, #priceblock_ourprice, #priceblock_dealprice, .a-price-whole")))
                    time.sleep(2)  # Additional wait for full update
                    break
                except TimeoutException:
                    wait_attempts += 1
                    time.sleep(1)
            
            variant_name = element.text.strip()
            aria_label = element.get_attribute('aria-label') or ''
            data_value = element.get_attribute('data-value') or ''
            title = element.get_attribute('title') or ''
            
            # Get the best variant name
            variant_name = variant_name or aria_label or data_value or title
            
            if not variant_name or len(variant_name) <= 1:
                print(f"❌ No valid variant name found")
                return None
            
            print(f"🔍 Extracting data for variant: {variant_name}")
            
            # 🎯 ENHANCED REAL VARIANT PRICE EXTRACTION
            price = None
            price_found = False
            try:
                # Enhanced price selectors with priority order
                enhanced_price_selectors = [
                    # Primary price locations
                    ".a-price .a-offscreen",  # Most common
                    ".a-price-whole",
                    ".a-price.a-text-price.a-size-medium.apexPriceToPay .a-offscreen",
                    
                    # Deal and sale prices
                    "#priceblock_dealprice",
                    "#priceblock_ourprice", 
                    ".a-price-range .a-offscreen",
                    "[data-a-strike='true'] + .a-offscreen",
                    ".a-price.a-text-price .a-offscreen",
                    
                    # Alternative price locations
                    ".a-price.a-text-price.header-price .a-offscreen",
                    ".a-price.a-text-normal .a-offscreen",
                    ".a-button-selected .a-price .a-offscreen",
                    
                    # Buy box prices
                    "#buybox .a-price .a-offscreen",
                    "[data-feature-name='buybox'] .a-price .a-offscreen",
                    
                    # Variant-specific prices
                    "[data-action='a-dropdown-button'] .a-price .a-offscreen",
                    ".a-button-selected .a-price-whole"
                ]
                
                for selector in enhanced_price_selectors:
                    try:
                        price_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for price_element in price_elements:
                            if price_element and price_element.is_displayed():
                                price_text = price_element.text or price_element.get_attribute('textContent') or price_element.get_attribute('innerHTML')
                                if price_text:
                                    parsed_price = self._parse_price(price_text)
                                    if parsed_price and parsed_price > 0:
                                        price = parsed_price
                                        price_found = True
                                        print(f"💰 Found price ${price} for {variant_name} using selector: {selector}")
                                        break
                        if price_found:
                            break
                    except Exception as e:
                        continue
                        
                # If no price found, try to extract from page text
                if not price_found:
                    try:
                        page_text = self.driver.find_element(By.TAG_NAME, "body").text
                        import re
                        price_matches = re.findall(r'\$[\d,]+\.?\d*', page_text)
                        if price_matches:
                            for match in price_matches[:3]:  # Check first 3 price matches
                                parsed_price = self._parse_price(match)
                                if parsed_price and parsed_price > 0:
                                    price = parsed_price
                                    print(f"💰 Found price ${price} from page text")
                                    break
                    except Exception:
                        pass
                        
            except Exception as e:
                print(f"❌ Price extraction failed: {e}")
            
            # 🎯 ENHANCED REAL VARIANT IMAGES EXTRACTION
            images = []
            try:
                print(f"🔍 Extracting images...")
                # Wait for main image to potentially change
                time.sleep(2)
                
                # Enhanced image selectors with priority
                enhanced_image_selectors = [
                    # Main product images
                    "#landingImage",  # Main product image
                    ".a-dynamic-image",  # Dynamic images
                    "#imgTagWrapperId img",  # Image wrapper
                    "#main-image-container img",  # Alternative main image
                    
                    # High resolution images
                    "[data-old-hires]",  # High-res images
                    "[data-a-hires]",  # Alternative high-res
                    "[data-zoom-src]",  # Zoom images
                    
                    # Thumbnail and gallery images
                    ".item.imageThumbnail img",  # Thumbnail images
                    "#altImages img",  # Alternative images
                    ".a-image-wrapper img",  # Alternative wrapper
                    "#imageBlock img",  # Image block
                    
                    # Variant-specific images
                    ".a-button-selected img",  # Selected variant images
                    "[aria-selected='true'] img"  # Selected elements with images
                ]
                
                collected_images = set()  # Use set to avoid duplicates
                
                for selector in enhanced_image_selectors:
                    try:
                        img_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for img in img_elements:
                            if not img.is_displayed():
                                continue
                                
                            # Get various image sources with priority
                            sources = [
                                img.get_attribute('data-old-hires'),  # Highest quality first
                                img.get_attribute('data-a-hires'),
                                img.get_attribute('data-zoom-src'),
                                img.get_attribute('src'),
                                img.get_attribute('data-src'),
                                img.get_attribute('data-lazy-src')
                            ]
                            
                            for src in sources:
                                if (src and 'http' in src and 
                                    'amazon.com/images' in src and
                                    src not in collected_images and
                                    not any(skip in src for skip in ['spinner', 'loading', '1x1', 'spacer', 'transparent'])):
                                    collected_images.add(src)
                                    print(f"🖼️ Found image: {src[:80]}...")
                                    
                            if len(collected_images) >= 5:  # Collect more images
                                break
                                
                        if len(collected_images) >= 5:  # Stop if we have enough images
                            break
                            
                    except Exception as e:
                        continue
                
                images = list(collected_images)[:10]  # Limit to 10 images
                print(f"🖼️ Collected {len(images)} images for {variant_name}")
                        
            except Exception as e:
                print(f"❌ Image extraction failed: {e}")
            
            # 🎯 ENHANCED REAL STOCK STATUS EXTRACTION
            stock = 50  # Default
            stock_status = "In Stock"
            try:
                print(f"📦 Extracting stock status...")
                enhanced_stock_selectors = [
                    "#availability span",
                    ".a-color-success",
                    ".a-color-state", 
                    ".a-color-price",
                    "[data-feature-name='availability'] span",
                    "#availability .a-color-success",
                    "#availability .a-color-state",
                    "#buybox #availability span",
                    ".availability-msg",
                    "#availability",
                    "[data-feature-name='availability']"
                ]
                
                for selector in enhanced_stock_selectors:
                    try:
                        stock_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for stock_element in stock_elements:
                            if stock_element.is_displayed():
                                stock_text = (stock_element.text or stock_element.get_attribute('textContent') or '').lower().strip()
                                
                                if not stock_text:
                                    continue
                                
                                print(f"📋 Stock text found: {stock_text}")
                                
                                if 'in stock' in stock_text:
                                    stock_status = "In Stock"
                                    stock = 50
                                elif 'out of stock' in stock_text or 'unavailable' in stock_text:
                                    stock_status = "Out of Stock"
                                    stock = 0
                                elif 'only' in stock_text and 'left' in stock_text:
                                    # Extract number from "Only 3 left in stock"
                                    import re
                                    match = re.search(r'only (\d+) left', stock_text)
                                    if match:
                                        stock = int(match.group(1))
                                        stock_status = f"Only {stock} left"
                                elif 'temporarily out' in stock_text:
                                    stock_status = "Temporarily Out"
                                    stock = 0
                                elif any(word in stock_text for word in ['available', 'ready', 'ships']):
                                    stock_status = "Available"
                                    stock = 25
                                    
                                print(f"📦 Stock for {variant_name}: {stock_status} ({stock})")
                                break
                        if stock != 50:  # Found specific stock info
                            break
                    except Exception:
                        continue
                        
            except Exception as e:
                print(f"❌ Stock extraction failed: {e}")
            
            # 🎯 ENHANCED ATTRIBUTE EXTRACTION
            additional_info = {}
            try:
                # Extract additional variant attributes
                element_id = element.get_attribute('id') or ''
                element_class = element.get_attribute('class') or ''
                data_value = element.get_attribute('data-value') or ''
                
                # Try to extract color from various attributes
                if any(color_indicator in element_class.lower() for color_indicator in ['color', 'swatch']):
                    additional_info['color'] = variant_name
                elif any(size_indicator in element_class.lower() for size_indicator in ['size']):
                    additional_info['size'] = variant_name
                elif any(storage_indicator in variant_name.lower() for storage_indicator in ['gb', 'tb', 'storage']):
                    additional_info['storage'] = variant_name
                
                # Add data attributes
                if data_value:
                    additional_info['data_value'] = data_value
                    
            except Exception as e:
                print(f"⚠️ Additional info extraction failed: {e}")
                additional_info = {}

            # 🎯 CREATE COMPREHENSIVE VARIANT DATA
            variant_data = {
                'type': self._detect_variant_type(element.get_attribute('id') or '', 
                                                element.get_attribute('class') or '', 
                                                variant_name),
                'name': variant_name,
                'value': variant_name,
                'price': price,
                'stock': stock,
                'stock_status': stock_status,
                'sku': f"VAR-{hash(variant_name) % 10000:04d}",
                'images': images,
                'attributes': {
                    'variant': variant_name,
                    'extracted_at': time.time(),
                    **additional_info
                }
            }
            
            logger.info(f"✅ Extracted complete variant: {variant_name} - ${price} - {len(images)} images")
            return variant_data
                
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
        """Enhanced price parsing for better accuracy"""
        try:
            if not price_text:
                return None
                
            # Clean the price text
            price_text = price_text.strip()
            
            # Handle different currency formats
            import re
            
            # Remove common currency symbols and words
            price_text = re.sub(r'[^\d.,\-\s]', '', price_text)
            price_text = price_text.replace('USD', '').replace('$', '').strip()
            
            # Handle price ranges (take the first price)
            if '-' in price_text and not price_text.startswith('-'):
                price_text = price_text.split('-')[0].strip()
            
            # Handle comma as thousands separator vs decimal
            if ',' in price_text and '.' in price_text:
                # Format like "1,234.56"
                price_text = price_text.replace(',', '')
            elif ',' in price_text and price_text.count(',') == 1:
                # Check if it's thousands separator or decimal
                parts = price_text.split(',')
                if len(parts[1]) == 2:  # Likely decimal (e.g., "12,99")
                    price_text = price_text.replace(',', '.')
                else:  # Likely thousands (e.g., "1,234")
                    price_text = price_text.replace(',', '')
            
            # Remove any remaining non-numeric characters except decimal point
            price_text = re.sub(r'[^\d.]', '', price_text)
            
            if not price_text:
                return None
            
            # Convert to float
            price = float(price_text)
            
            # Validate reasonable price range
            if 0.01 <= price <= 999999:
                return round(price, 2)
                
        except (ValueError, AttributeError):
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
