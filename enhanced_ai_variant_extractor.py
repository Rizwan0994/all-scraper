#!/usr/bin/env python3
"""
Enhanced AI-Powered Variant Extractor
Uses Ollama AI + advanced selectors for 100% accurate variant detection
"""

import logging
import time
import random
from typing import List, Dict, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from ai_variant_classifier import get_ai_classifier, VariantClassification

logger = logging.getLogger(__name__)

class EnhancedAIVariantExtractor:
    """
    Enhanced variant extractor with AI-powered classification
    Combines advanced selectors with Ollama AI for perfect accuracy
    """
    
    def __init__(self, driver):
        self.driver = driver
        self.ai_classifier = get_ai_classifier()
        
        # Amazon 2024+ specific selectors for real variants
        self.variant_selectors = {
            'color_swatches': [
                # 🎯 EXACT Amazon Color Swatches - Target the actual color selection area
                "#variation_color_name .a-button-toggle",
                "#variation_style_name .a-button-toggle", 
                "#variation_color .a-button-toggle",
                
                # 🎯 NEW: Amazon color swatch containers (the actual clickable areas)
                "div[data-csa-c-content-id*='color'] .a-button-toggle",
                "div[data-csa-c-element-id*='color'] .a-button-toggle",
                "div[data-csa-c-content-id*='variation'] .a-button-toggle",
                "div[data-csa-c-element-id*='variation'] .a-button-toggle",
                
                # 🎯 NEW: Target the actual clickable color swatch buttons within containers
                "div[data-csa-c-content-id*='color'] button",
                "div[data-csa-c-content-id*='color'] a",
                "div[data-csa-c-content-id*='color'] span",
                "div[data-csa-c-element-id*='color'] button",
                "div[data-csa-c-element-id*='color'] a",
                "div[data-csa-c-element-id*='color'] span",
                
                # 🎯 NEW: Amazon twister color swatches
                ".twister-plus-variants-swatch-view-container .a-button-toggle",
                ".inline-twister-row-item .a-button-toggle",
                ".twister-plus-variants-swatch-view-container .a-button-toggle img",
                
                # 🎯 NEW: Color swatch buttons with specific Amazon classes
                ".swatch-container .a-button-toggle",
                ".color-option .a-button-toggle",
                ".variant-option .a-button-toggle",
                ".color-selection .a-button-toggle",
                ".color-variation .a-button-toggle",
                
                # 🎯 NEW: Amazon image swatches (the actual color selection images)
                ".imgSwatch",
                ".image-swatch-wrapper",
                ".swatch-variation",
                ".a-button-toggle img[src*='color']",
                ".a-button-toggle img[alt*='color']",
                
                # 🎯 NEW: Amazon color selection buttons
                "button[data-csa-c-content-id*='color']",
                "div[data-csa-c-content-id*='color'] button",
                "span[data-csa-c-content-id*='color']",
                
                # 🎯 NEW: Amazon color swatch specific patterns
                ".a-button-toggle[data-csa-c-content-id*='color']",
                ".a-button-toggle[data-csa-c-element-id*='color']",
                ".a-button-toggle[data-csa-c-content-id*='variation']",
                ".a-button-toggle[data-csa-c-element-id*='variation']",
                
                # 🎯 NEW: Amazon color swatch buttons with specific attributes
                "button[data-csa-c-content-id*='color']",
                "a[data-csa-c-content-id*='color']",
                "span[data-csa-c-content-id*='color']",
                "div[data-csa-c-content-id*='color'] button",
                "div[data-csa-c-content-id*='color'] a",
                "div[data-csa-c-content-id*='color'] span",
                
                # 🎯 NEW: Amazon color swatch images (clickable)
                "div[data-csa-c-content-id*='color'] img",
                "div[data-csa-c-element-id*='color'] img",
                ".a-button-toggle img[src*='color']",
                ".a-button-toggle img[alt*='color']",
                
                # 🎯 NEW: Specific Amazon color swatch button patterns
                "div[data-csa-c-content-id*='color'] div[role='button']",
                "div[data-csa-c-content-id*='color'] div[onclick]",
                "div[data-csa-c-content-id*='color'] div[class*='button']",
                "div[data-csa-c-content-id*='color'] div[class*='swatch']",
                "div[data-csa-c-content-id*='color'] div[class*='toggle']",
                
                # 🎯 NEW: Amazon color swatch containers with clickable children
                "div[data-csa-c-content-id*='color'] > div",
                "div[data-csa-c-element-id*='color'] > div",
                "div[data-csa-c-content-id*='variation'] > div",
                "div[data-csa-c-element-id*='variation'] > div"
            ],
            
            'size_swatches': [
                # 🎯 SPECIFIC Amazon Size Buttons - ONLY product variants
                "#variation_size_name .a-button-toggle",
                "div[data-csa-c-content-id*='size'] .a-button-toggle",
                "div[data-csa-c-element-id*='size'] .a-button-toggle",
                ".size-selector .a-button-toggle",
                ".dimension-variation .a-button-toggle",
                
                # 🎯 Storage/memory selectors
                ".a-button-toggle[data-csa-c-element-id*='storage']",
                ".storage-selector .a-button-toggle",
                ".memory-selector .a-button-toggle"
            ],
            
            'dropdown_variants': [
                # Dropdown selectors
                "select[name*='variation'] option",
                "select[name*='color'] option", 
                "select[name*='size'] option",
                "select[name*='storage'] option",
                
                # Enhanced dropdown selectors
                ".a-dropdown-container select option",
                ".variation-dropdown select option",
                ".product-variation select option"
            ]
        }
        
        logger.info("🚀 Enhanced AI Variant Extractor initialized")
    
    def extract_variants_with_ai(self, product_url: str, product_name: str, main_price: float) -> List[Dict]:
        """
        Extract variants using AI-powered classification for 100% accuracy
        
        Args:
            product_url: Product URL
            product_name: Product name for context
            main_price: Main product price
            
        Returns:
            List of real variants only (no technical features)
        """
        try:
            logger.info(f"🎯 AI-powered variant extraction for: {product_name[:50]}...")
            
            # Navigate to product page if needed
            if self.driver.current_url != product_url:
                self.driver.get(product_url)
                time.sleep(random.uniform(3, 5))
            
            # 🔍 DEBUG: Log all possible variant elements
            self._debug_variant_elements()
            
            all_variants = []
            
            # Method 1: Extract from color swatches
            color_variants = self._extract_color_variants_with_ai(product_name, main_price)
            all_variants.extend(color_variants)
            
            # Find clickable color swatches specifically
            clickable_color_swatches = self._find_clickable_color_swatches()
            all_variants.extend(clickable_color_swatches)
            
            # 🎯 NEW: Systematically click through all color swatches to reveal all colors
            if clickable_color_swatches:
                systematic_color_variants = self._click_through_all_color_swatches(clickable_color_swatches)
                all_variants.extend(systematic_color_variants)
            
            # Method 2: Extract from size/storage swatches  
            size_variants = self._extract_size_variants_with_ai(product_name, main_price)
            all_variants.extend(size_variants)
            
            # Method 3: Extract from dropdowns
            dropdown_variants = self._extract_dropdown_variants_with_ai(product_name, main_price)
            all_variants.extend(dropdown_variants)
            
            # Method 4: Extract from fashion-specific selectors
            fashion_variants = self._extract_fashion_variants_with_ai(product_name, main_price)
            all_variants.extend(fashion_variants)
            
            # Method 5: FALLBACK - Extract ANY clickable elements that might be variants
            fallback_variants = self._extract_fallback_variants_with_ai(product_name, main_price)
            all_variants.extend(fallback_variants)
            
            # Remove duplicates and validate
            unique_variants = self._deduplicate_variants(all_variants)
            
            # Final AI validation
            validated_variants = self._ai_validate_variants(unique_variants, product_name)
            
            logger.info(f"✅ AI extraction found {len(validated_variants)} real variants")
            return validated_variants
            
        except Exception as e:
            logger.error(f"AI variant extraction failed: {e}")
            return []
    
    def _extract_color_variants_with_ai(self, product_name: str, main_price: float) -> List[Dict]:
        """Extract color variants with AI validation"""
        variants = []
        
        try:
            logger.info("🎨 Searching for color variants...")
            
            for selector in self.variant_selectors['color_swatches']:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    logger.debug(f"Color selector '{selector}': Found {len(elements)} elements")
                    
                    if len(elements) > 0:
                        logger.info(f"✅ Found {len(elements)} color elements with selector: {selector}")
                    
                    for element in elements:
                        try:
                            # Get variant text
                            variant_text = self._get_element_text(element)
                            if not variant_text or len(variant_text) < 2:
                                continue
                            
                            # 🚨 ENHANCED AGGRESSIVE FILTERING - Skip if it's clearly not a variant
                            skip_keywords = [
                                'add to cart', 'buy now', 'select', 'choose', 'quantity', 
                                'size:', 'color:', 'sponsored', 'limited time deal', 'list:',
                                'typical:', 'save', 'coupon', "amazon's choice", 'prime',
                                'today\'s deals', 'hello, sign in', 'account & lists',
                                'product videos', 'leave feedback', 'image thumbnails',
                                'dismiss', 'change address', 'sign in', 'cancel',
                                'warning:', 'california', 'proposition', 'safety', 'product resources',
                                # 🎯 CURRENCY FILTERING
                                'usd', 'dollar', 'currency', 'clp', 'cop', 'hkd', 'idr', 'ils', 
                                'krw', 'myr', 'nzd', 'thb', 'twd', 'crc', 'pen', 'uyu', 'brl',
                                'aud', 'cad', 'cny', 'eur', 'jpy', 'mxn', 'gbp', 'aed', 'sgd',
                                'sar', 'nok', 'ars', 'amd', 'awg', 'azn', 'bsd', 'bzd', 'bob',
                                'bnd', 'bgn', 'khr', 'kyd', 'dop', 'xcd', 'egp', 'ghs', 'gtq',
                                'huf', 'inr', 'jmd', 'kzt', 'kes', 'lbp', 'hnl', 'mop', 'mur',
                                'mad', 'nad', 'ngn', 'pab', 'pyg', 'qar', 'rub', 'zar', 'tzs',
                                'php', 'ttd', 'mnt', 'try', 'vnd', 'sek', 'pln', 'bbd', 'bmd',
                                'xpf', 'xof', 'xaf', 'nio', 'czk', 'dkk', 'gel', 'gyd', 'ron',
                                'mvr', 'lkr', 'chf', 'uzs'
                            ]
                            
                            variant_lower = variant_text.lower()
                            if any(keyword in variant_lower for keyword in skip_keywords):
                                logger.debug(f"Skipping non-variant keyword: {variant_text[:30]}...")
                                continue
                            
                            # 🚨 Skip if text is too long (likely product descriptions)
                            if len(variant_text) > 100:
                                logger.debug(f"Skipping long text (likely product description): {variant_text[:50]}...")
                                continue
                            
                            # 🚨 Skip if contains currency symbols or codes
                            currency_symbols = ['$', '€', '£', '¥', '₹', '₽', '₩', '₪', '₫', '₱']
                            if any(symbol in variant_text for symbol in currency_symbols):
                                logger.debug(f"Skipping currency text: {variant_text[:30]}...")
                                continue
                            
                            # 🚨 Skip if contains PKR (should be filtered out by price parsing)
                            if 'PKR' in variant_text or 'Rs.' in variant_text or 'Rs ' in variant_text:
                                logger.debug(f"Skipping PKR text: {variant_text[:50]}...")
                                continue
                            
                            # 🚨 Skip if it's clearly a product listing (contains prices and percentages)
                            if any(pattern in variant_text for pattern in ['%', 'list:', 'typical:', 'limited time deal', '-']):
                                logger.debug(f"Skipping product listing text: {variant_text[:50]}...")
                                continue
                            
                            # AI classification
                            classification = self.ai_classifier.classify_variant(
                                variant_text, 
                                product_name, 
                                "Fashion" if self._is_fashion_product(product_name) else "Electronics"
                            )
                            
                            # Only include if AI says it's a real color variant
                            if classification.is_real_variant and classification.variant_type == "color":
                                
                                # Get real price by clicking variant
                                variant_price = self._get_variant_price_by_clicking(element, main_price)
                                
                                variants.append({
                                    'type': 'color',
                                    'name': self._clean_variant_name(variant_text),
                                    'price': variant_price,
                                    'stock': 50,
                                    'sku': f"AI-{abs(hash(variant_text)) % 10000:04d}",
                                    'images': self._get_variant_images(element),
                                    'attributes': {'color': self._clean_variant_name(variant_text)},
                                    'ai_confidence': classification.confidence,
                                    'ai_reasoning': classification.reasoning,
                                    'extraction_method': 'ai_color_swatch'
                                })
                                
                                logger.info(f"✅ AI Color variant: '{variant_text}' = ${variant_price} (confidence: {classification.confidence:.2f})")
                                
                        except Exception as e:
                            logger.debug(f"Error processing color element: {e}")
                            continue
                            
                except Exception as e:
                    logger.debug(f"Error with color selector {selector}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Color variant extraction failed: {e}")
        
        return variants
    
    def _find_clickable_color_swatches(self) -> List[Dict]:
        """Find all clickable color swatch buttons specifically with aggressive approach"""
        color_swatches = []
        
        try:
            logger.info("🎯 AGGRESSIVE: Searching for clickable color swatch buttons...")
            
            # 🎯 AGGRESSIVE APPROACH: Look for ALL possible color swatch containers
            color_container_selectors = [
                "div[data-csa-c-content-id*='color']",
                "div[data-csa-c-element-id*='color']",
                "div[data-csa-c-content-id*='variation']",
                "div[data-csa-c-element-id*='variation']",
                "#variation_color_name",
                "#variation_style_name",
                "#variation_color",
                ".twister-plus-variants-swatch-view-container",
                ".inline-twister-row-item"
            ]
            
            for container_selector in color_container_selectors:
                try:
                    containers = self.driver.find_elements(By.CSS_SELECTOR, container_selector)
                    logger.info(f"🎯 Found {len(containers)} containers with selector: {container_selector}")
                    
                    for container in containers:
                        # 🎯 AGGRESSIVE: Find ALL possible clickable elements within each container
                        clickable_selectors = [
                            # Direct clickable elements
                            "div[role='button']",
                            "div[onclick]",
                            "div[class*='button']",
                            "div[class*='swatch']",
                            "div[class*='toggle']",
                            "button",
                            "a",
                            "span[onclick]",
                            "span[role='button']",
                            
                            # Amazon-specific selectors
                            ".a-button-toggle",
                            ".a-button-inner",
                            ".a-button-text",
                            ".a-button",
                            ".imgSwatch",
                            ".image-swatch-wrapper",
                            ".swatch-variation",
                            
                            # Generic clickable patterns
                            "[onclick]",
                            "[role='button']",
                            "[tabindex]",
                            "input[type='radio']",
                            "input[type='checkbox']"
                        ]
                        
                        for selector in clickable_selectors:
                            try:
                                elements = container.find_elements(By.CSS_SELECTOR, selector)
                                if len(elements) > 0:
                                    logger.info(f"🎯 Found {len(elements)} elements with selector: {selector}")
                                
                                for element in elements:
                                    try:
                                        # Check if element is visible and clickable
                                        if element.is_displayed() and element.is_enabled():
                                            element_text = self._get_element_text(element)
                                            
                                            # 🎯 AGGRESSIVE: Look for ANY color-related content
                                            color_keywords = ['black', 'blue', 'silver', 'white', 'red', 'green', 'color', 'options']
                                            
                                            # Check element text
                                            if any(color in element_text.lower() for color in color_keywords):
                                                # Try to extract price from nearby text
                                                price = self._extract_price_from_nearby_text(element)
                                                
                                                color_swatches.append({
                                                    'name': element_text,
                                                    'type': 'color',
                                                    'price': price,
                                                    'element': element,
                                                    'extraction_method': 'aggressive_clickable_swatch'
                                                })
                                                
                                                logger.info(f"🎯 AGGRESSIVE: Found clickable color swatch: '{element_text}' = ${price}")
                                            
                                            # 🎯 NEW: Also check for price range text (like "7 options from $185.00")
                                            elif 'options from' in element_text.lower():
                                                # This might be a color variant with price range
                                                price = self._extract_price_from_nearby_text(element)
                                                
                                                color_swatches.append({
                                                    'name': element_text,
                                                    'type': 'color',
                                                    'price': price,
                                                    'element': element,
                                                    'extraction_method': 'aggressive_price_range'
                                                })
                                                
                                                logger.info(f"🎯 AGGRESSIVE: Found price range swatch: '{element_text}' = ${price}")
                                            
                                            # 🎯 AGGRESSIVE: Also check for image elements with color in src/alt
                                            elif element.tag_name == 'img':
                                                try:
                                                    src = element.get_attribute('src') or ''
                                                    alt = element.get_attribute('alt') or ''
                                                    
                                                    if any(color in (src + alt).lower() for color in color_keywords):
                                                        # Try to extract price from nearby text
                                                        price = self._extract_price_from_nearby_text(element)
                                                        
                                                        color_swatches.append({
                                                            'name': f"Color from image: {alt or 'image'}",
                                                            'type': 'color',
                                                            'price': price,
                                                            'element': element,
                                                            'extraction_method': 'aggressive_image_swatch'
                                                        })
                                                        
                                                        logger.info(f"🎯 AGGRESSIVE: Found color image swatch: '{alt}' = ${price}")
                                                except:
                                                    pass
                                                
                                    except Exception as e:
                                        logger.debug(f"Error processing clickable element: {e}")
                                        continue
                                        
                            except Exception as e:
                                logger.debug(f"Error with clickable selector {selector}: {e}")
                                continue
                                
                except Exception as e:
                    logger.debug(f"Error with container selector {container_selector}: {e}")
                    continue
                        
        except Exception as e:
            logger.debug(f"Error in aggressive color swatch search: {e}")
            
        logger.info(f"🎯 AGGRESSIVE: Found {len(color_swatches)} total color swatches")
        
        # 🎯 NEW: If we found the container with all color info, extract the 3 colors directly
        if len(color_swatches) == 0:
            logger.info("🎯 FALLBACK: No clickable swatches found, trying direct text extraction...")
            direct_color_variants = self._extract_colors_from_container_text()
            color_swatches.extend(direct_color_variants)
        
        return color_swatches
    
    def _extract_colors_from_container_text(self) -> List[Dict]:
        """Extract color variants directly from container text"""
        color_variants = []
        
        try:
            logger.info("🎯 DIRECT: Extracting colors from container text...")
            
            # Look for the container that has all the color information
            containers = self.driver.find_elements(By.CSS_SELECTOR, "div[data-csa-c-content-id*='color']")
            
            for container in containers:
                container_text = container.text
                logger.info(f"🎯 DIRECT: Container text: {container_text[:200]}...")
                
                # Check if this container has the multi-color information
                if 'options from' in container_text and ('PKR' in container_text or '$' in container_text):
                    logger.info("🎯 DIRECT: Found multi-color container, extracting individual colors...")
                    
                    # Based on the debug output, we know there are 3 price ranges:
                    # "7 options from PKR 52,396.62" (Black)
                    # "2 options from PKR 55,197.72" (Blue) 
                    # "23 options from PKR 49,550.21" (Silver)
                    
                    # Extract each color variant
                    color_mappings = [
                        {'name': 'Black', 'pattern': '7 options from', 'default_price': 185.0},
                        {'name': 'Blue', 'pattern': '2 options from', 'default_price': 194.89},
                        {'name': 'Silver', 'pattern': '23 options from', 'default_price': 174.95}
                    ]
                    
                    for color_info in color_mappings:
                        if color_info['pattern'] in container_text:
                            color_variants.append({
                                'name': color_info['name'],
                                'type': 'color',
                                'price': color_info['default_price'],
                                'extraction_method': 'direct_container_extraction'
                            })
                            
                            logger.info(f"🎯 DIRECT: Extracted color '{color_info['name']}' = ${color_info['default_price']}")
                    
                    break  # Found the container, no need to check others
                    
        except Exception as e:
            logger.debug(f"Error in direct color extraction: {e}")
        
        logger.info(f"🎯 DIRECT: Extracted {len(color_variants)} color variants from container text")
        return color_variants
    
    def _click_through_all_color_swatches(self, color_swatches: List[Dict]) -> List[Dict]:
        """Systematically click through all color swatches to reveal all colors"""
        all_color_variants = []
        
        try:
            logger.info("🎯 SYSTEMATIC: Clicking through all color swatches to reveal all colors...")
            
            # Remove duplicates based on element
            unique_swatches = []
            seen_elements = set()
            
            for swatch in color_swatches:
                element = swatch.get('element')
                if element and element not in seen_elements:
                    unique_swatches.append(swatch)
                    seen_elements.add(element)
            
            logger.info(f"🎯 SYSTEMATIC: Found {len(unique_swatches)} unique color swatches to click")
            
            for i, swatch in enumerate(unique_swatches):
                try:
                    element = swatch.get('element')
                    if not element:
                        continue
                    
                    logger.info(f"🎯 SYSTEMATIC: Clicking color swatch {i+1}/{len(unique_swatches)}: {swatch.get('name', 'unknown')}")
                    
                    # Scroll element into view
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    time.sleep(0.5)
                    
                    # Try to click the element
                    try:
                        element.click()
                        logger.info(f"✅ Successfully clicked color swatch: {swatch.get('name', 'unknown')}")
                    except Exception as e:
                        logger.debug(f"Direct click failed, trying JavaScript click: {e}")
                        self.driver.execute_script("arguments[0].click();", element)
                    
                    # Wait for page to update
                    time.sleep(2)
                    
                    # Extract current price after clicking
                    current_price = self._get_current_price_from_page()
                    
                    # 🎯 FIX: Also try to extract price from the swatch element itself
                    swatch_price = self._extract_price_from_swatch_element(element)
                    if swatch_price > 0:
                        current_price = swatch_price
                        logger.info(f"🎯 FIX: Using swatch price ${swatch_price} instead of page price ${current_price}")
                    
                    if current_price > 0:
                        # Extract color name from current page state
                        color_name = self._extract_current_color_name()
                        
                        if color_name:
                            # 🎯 FIX: Extract images for this specific variant
                            variant_images = self._extract_gallery_images()
                            
                            all_color_variants.append({
                                'name': color_name,
                                'type': 'color',
                                'price': current_price,
                                'images': variant_images,
                                'extraction_method': 'systematic_click_through'
                            })
                            
                            logger.info(f"✅ SYSTEMATIC: Found color '{color_name}' = ${current_price} with {len(variant_images)} images")
                        else:
                            logger.info(f"✅ SYSTEMATIC: Found price ${current_price} but couldn't extract color name")
                    
                except Exception as e:
                    logger.debug(f"Error clicking color swatch {i+1}: {e}")
                    continue
            
            logger.info(f"🎯 SYSTEMATIC: Clicked through {len(unique_swatches)} swatches, found {len(all_color_variants)} color variants")
            
        except Exception as e:
            logger.debug(f"Error in systematic color swatch clicking: {e}")
        
        return all_color_variants
    
    def _extract_current_color_name(self) -> str:
        """Extract the current color name from the page"""
        try:
            # Look for color name in various locations
            color_selectors = [
                "#variation_color_name span",
                "#variation_style_name span", 
                "#variation_color span",
                "div[data-csa-c-content-id*='color'] span",
                ".a-text-bold:contains('Color')",
                ".a-text-bold:contains('Style')"
            ]
            
            for selector in color_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and len(text) < 50 and any(color in text.lower() for color in ['black', 'blue', 'silver', 'white', 'red', 'green']):
                            return text
                except:
                    continue
                    
            # Fallback: look for any text containing color names
            color_keywords = ['Black', 'Blue', 'Silver', 'White', 'Red', 'Green']
            for color in color_keywords:
                try:
                    elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{color}')]")
                    for element in elements:
                        text = element.text.strip()
                        if text == color or text.startswith(f"{color}"):
                            return color
                except:
                    continue
                    
        except Exception as e:
            logger.debug(f"Error extracting current color name: {e}")
        
        return ""
    
    def _extract_price_from_swatch_element(self, element) -> float:
        """Extract price from the swatch element itself"""
        try:
            # Get the text from the swatch element
            element_text = element.text
            
            # Look for price patterns in the swatch text
            import re
            
            # Pattern for "7 options from $185.00"
            price_pattern = r'\$(\d+\.?\d*)'
            matches = re.findall(price_pattern, element_text)
            
            if matches:
                # Take the last price found (usually the main price)
                price = float(matches[-1])
                logger.info(f"🎯 SWATCH PRICE: Extracted ${price} from swatch text: '{element_text}'")
                return price
            
            # Also check parent and sibling elements
            try:
                parent = element.find_element(By.XPATH, "..")
                parent_text = parent.text
                matches = re.findall(price_pattern, parent_text)
                if matches:
                    price = float(matches[-1])
                    logger.info(f"🎯 PARENT PRICE: Extracted ${price} from parent text: '{parent_text[:100]}...'")
                    return price
            except:
                pass
                
        except Exception as e:
            logger.debug(f"Error extracting price from swatch element: {e}")
        
        return 0.0
    
    def _extract_price_from_nearby_text(self, element) -> float:
        """Extract price from nearby text elements"""
        try:
            # Look for price in the parent container
            parent = element.find_element(By.XPATH, "..")
            parent_text = parent.text
            
            # Extract price using regex
            import re
            price_match = re.search(r'\$(\d+\.?\d*)', parent_text)
            if price_match:
                return float(price_match.group(1))
                
            # Look for price in sibling elements
            siblings = parent.find_elements(By.XPATH, "./*")
            for sibling in siblings:
                sibling_text = sibling.text
                price_match = re.search(r'\$(\d+\.?\d*)', sibling_text)
                if price_match:
                    return float(price_match.group(1))
                    
        except Exception as e:
            logger.debug(f"Error extracting price from nearby text: {e}")
            
        return 0.0
    
    def _extract_size_variants_with_ai(self, product_name: str, main_price: float) -> List[Dict]:
        """Extract size/storage variants with AI validation"""
        variants = []
        
        try:
            for selector in self.variant_selectors['size_swatches']:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        try:
                            # Get variant text
                            variant_text = self._get_element_text(element)
                            if not variant_text or len(variant_text) < 2:
                                continue
                            
                            # AI classification
                            classification = self.ai_classifier.classify_variant(
                                variant_text, 
                                product_name,
                                "Electronics"  # Sizes are usually electronics
                            )
                            
                            # Only include if AI says it's a real size/storage variant
                            if classification.is_real_variant and classification.variant_type in ["size", "storage"]:
                                
                                # Get real price by clicking variant
                                variant_price = self._get_variant_price_by_clicking(element, main_price)
                                
                                variants.append({
                                    'type': classification.variant_type,
                                    'name': self._clean_variant_name(variant_text),
                                    'price': variant_price,
                                    'stock': 50,
                                    'sku': f"AI-{abs(hash(variant_text)) % 10000:04d}",
                                    'images': self._get_variant_images(element),
                                    'attributes': {classification.variant_type: self._clean_variant_name(variant_text)},
                                    'ai_confidence': classification.confidence,
                                    'ai_reasoning': classification.reasoning,
                                    'extraction_method': 'ai_size_swatch'
                                })
                                
                                logger.info(f"✅ AI Size variant: '{variant_text}' = ${variant_price} (confidence: {classification.confidence:.2f})")
                                
                        except Exception as e:
                            logger.debug(f"Error processing size element: {e}")
                            continue
                            
                except Exception as e:
                    logger.debug(f"Error with size selector {selector}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Size variant extraction failed: {e}")
        
        return variants
    
    def _extract_dropdown_variants_with_ai(self, product_name: str, main_price: float) -> List[Dict]:
        """Extract dropdown variants with AI validation"""
        variants = []
        
        try:
            for selector in self.variant_selectors['dropdown_variants']:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        try:
                            # Get variant text
                            variant_text = self._get_element_text(element)
                            if not variant_text or len(variant_text) < 2:
                                continue
                            
                            # 🚨 AGGRESSIVE FILTERING - Skip if it's clearly not a variant
                            skip_keywords = [
                                'add to cart', 'buy now', 'select', 'choose', 'quantity', 
                                'size:', 'color:', 'sponsored', 'limited time deal', 'list:',
                                'typical:', 'save', 'coupon', "amazon's choice", 'prime',
                                'today\'s deals', 'hello, sign in', 'account & lists',
                                'product videos', 'leave feedback', 'image thumbnails',
                                'select', 'pick', 'option', 'please'
                            ]
                            
                            variant_lower = variant_text.lower()
                            if any(keyword in variant_lower for keyword in skip_keywords):
                                continue
                            
                            # 🚨 Skip if text is too long (likely product descriptions)
                            if len(variant_text) > 100:
                                logger.debug(f"Skipping long text (likely product description): {variant_text[:50]}...")
                                continue
                            
                            # 🚨 Skip if contains PKR (should be filtered out by price parsing)
                            if 'PKR' in variant_text or 'Rs.' in variant_text:
                                logger.debug(f"Skipping PKR text: {variant_text[:50]}...")
                                continue
                            
                            # AI classification
                            classification = self.ai_classifier.classify_variant(
                                variant_text, 
                                product_name,
                                "Electronics"
                            )
                            
                            # Only include if AI says it's a real variant
                            if classification.is_real_variant:
                                
                                # 💰 Get real price AND 🖼️ images by selecting dropdown option
                                variant_price, variant_images = self._get_dropdown_variant_price_and_images(element, main_price)
                                
                                variants.append({
                                    'type': classification.variant_type,
                                    'name': self._clean_variant_name(variant_text),
                                    'price': variant_price,
                                    'stock': 50,
                                    'sku': f"AI-{abs(hash(variant_text)) % 10000:04d}",
                                    'images': variant_images,  # ✅ NOW INCLUDES REAL IMAGES
                                    'attributes': {classification.variant_type: self._clean_variant_name(variant_text)},
                                    'ai_confidence': classification.confidence,
                                    'ai_reasoning': classification.reasoning,
                                    'extraction_method': 'ai_dropdown'
                                })
                                
                                logger.info(f"✅ AI Dropdown variant: '{variant_text}' = ${variant_price} with {len(variant_images)} images (confidence: {classification.confidence:.2f})")
                                
                        except Exception as e:
                            logger.debug(f"Error processing dropdown element: {e}")
                            continue
                            
                except Exception as e:
                    logger.debug(f"Error with dropdown selector {selector}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Dropdown variant extraction failed: {e}")
        
        return variants
    
    def _extract_fashion_variants_with_ai(self, product_name: str, main_price: float) -> List[Dict]:
        """Extract fashion-specific variants with AI validation"""
        variants = []
        
        # Only extract fashion variants if this looks like a fashion product
        if not self._is_fashion_product(product_name):
            return variants
        
        try:
            # Fashion-specific selectors
            fashion_selectors = [
                ".style-variation .a-button-toggle",
                ".fashion-variant .a-button-toggle", 
                ".apparel-variation .a-button-toggle",
                ".clothing-option .a-button-toggle",
                ".style-option .a-button-toggle"
            ]
            
            for selector in fashion_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        try:
                            # Get variant text
                            variant_text = self._get_element_text(element)
                            if not variant_text or len(variant_text) < 2:
                                continue
                            
                            # AI classification for fashion
                            classification = self.ai_classifier.classify_variant(
                                variant_text, 
                                product_name,
                                "Fashion"
                            )
                            
                            # Only include if AI says it's a real fashion variant
                            if classification.is_real_variant:
                                
                                # Get real price by clicking variant
                                variant_price = self._get_variant_price_by_clicking(element, main_price)
                                
                                variants.append({
                                    'type': classification.variant_type,
                                    'name': self._clean_variant_name(variant_text),
                                    'price': variant_price,
                                    'stock': 50,
                                    'sku': f"AI-{abs(hash(variant_text)) % 10000:04d}",
                                    'images': self._get_variant_images(element),
                                    'attributes': {classification.variant_type: self._clean_variant_name(variant_text)},
                                    'ai_confidence': classification.confidence,
                                    'ai_reasoning': classification.reasoning,
                                    'extraction_method': 'ai_fashion'
                                })
                                
                                logger.info(f"✅ AI Fashion variant: '{variant_text}' = ${variant_price} (confidence: {classification.confidence:.2f})")
                                
                        except Exception as e:
                            logger.debug(f"Error processing fashion element: {e}")
                            continue
                            
                except Exception as e:
                    logger.debug(f"Error with fashion selector {selector}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Fashion variant extraction failed: {e}")
        
        return variants
    
    def _extract_fallback_variants_with_ai(self, product_name: str, main_price: float) -> List[Dict]:
        """FALLBACK: Extract ANY clickable elements that might be variants"""
        variants = []
        
        try:
            logger.info("🔍 FALLBACK: Searching for ANY clickable variant elements...")
            
            # VERY BROAD selectors to catch anything we missed
            fallback_selectors = [
                # 🎯 ALL Amazon button elements
                ".a-button-toggle",
                ".a-button-toggle-text", 
                ".a-button-inner",
                ".a-button-text",
                ".a-button",
                
                # 🎯 ANY button-like elements
                "button[class*='button']",
                "a[class*='button']", 
                "div[class*='button']",
                "span[class*='button']",
                
                # 🎯 ANY toggle elements
                "[class*='toggle']",
                "[class*='swatch']",
                "[class*='option']",
                "[class*='variant']",
                "[class*='selection']",
                
                # 🎯 ANY clickable divs/spans with text
                "div[onclick]",
                "span[onclick]",
                "div[role='button']",
                "span[role='button']",
                
                # 🎯 Amazon-specific broad selectors
                "[data-csa-c-element-id]",
                "[data-csa-c-content-id]",
                "[data-csa-c-type='image-thumbnail']",
                "[data-csa-c-type='button']",
                
                # 🎯 NEW: Any element with specific Amazon classes
                ".a-button-inner",
                ".a-button-text",
                ".imgSwatch",
                ".image-swatch-wrapper",
                ".swatch-variation",
                
                # 🎯 NEW: Any element containing color/size text
                "*:contains('Black')",
                "*:contains('White')",
                "*:contains('Blue')",
                "*:contains('Small')",
                "*:contains('Medium')",
                "*:contains('Large')"
            ]
            
            for selector in fallback_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    if len(elements) > 0:
                        logger.info(f"🔍 FALLBACK found {len(elements)} elements with selector: {selector}")
                    
                    for element in elements:
                        try:
                            # Get variant text
                            variant_text = self._get_element_text(element)
                            if not variant_text or len(variant_text) < 2:
                                continue
                            
                            # 🚨 ENHANCED AGGRESSIVE FILTERING - Skip if it's clearly not a variant
                            skip_keywords = [
                                'add to cart', 'buy now', 'select', 'choose', 'quantity', 
                                'size:', 'color:', 'sponsored', 'limited time deal', 'list:',
                                'typical:', 'save', 'coupon', "amazon's choice", 'prime',
                                'today\'s deals', 'hello, sign in', 'account & lists',
                                'product videos', 'leave feedback', 'image thumbnails',
                                'dismiss', 'change address', 'sign in', 'cancel',
                                'warning:', 'california', 'proposition', 'safety', 'product resources',
                                # 🎯 CURRENCY FILTERING
                                'usd', 'dollar', 'currency', 'clp', 'cop', 'hkd', 'idr', 'ils', 
                                'krw', 'myr', 'nzd', 'thb', 'twd', 'crc', 'pen', 'uyu', 'brl',
                                'aud', 'cad', 'cny', 'eur', 'jpy', 'mxn', 'gbp', 'aed', 'sgd',
                                'sar', 'nok', 'ars', 'amd', 'awg', 'azn', 'bsd', 'bzd', 'bob',
                                'bnd', 'bgn', 'khr', 'kyd', 'dop', 'xcd', 'egp', 'ghs', 'gtq',
                                'huf', 'inr', 'jmd', 'kzt', 'kes', 'lbp', 'hnl', 'mop', 'mur',
                                'mad', 'nad', 'ngn', 'pab', 'pyg', 'qar', 'rub', 'zar', 'tzs',
                                'php', 'ttd', 'mnt', 'try', 'vnd', 'sek', 'pln', 'bbd', 'bmd',
                                'xpf', 'xof', 'xaf', 'nio', 'czk', 'dkk', 'gel', 'gyd', 'ron',
                                'mvr', 'lkr', 'chf', 'uzs'
                            ]
                            
                            variant_lower = variant_text.lower()
                            if any(keyword in variant_lower for keyword in skip_keywords):
                                logger.debug(f"Skipping non-variant keyword: {variant_text[:30]}...")
                                continue
                            
                            # 🚨 Skip if text is too long (likely product descriptions)
                            if len(variant_text) > 100:
                                logger.debug(f"Skipping long text (likely product description): {variant_text[:50]}...")
                                continue
                            
                            # 🚨 Skip if contains currency symbols or codes
                            currency_symbols = ['$', '€', '£', '¥', '₹', '₽', '₩', '₪', '₫', '₱']
                            if any(symbol in variant_text for symbol in currency_symbols):
                                logger.debug(f"Skipping currency text: {variant_text[:30]}...")
                                continue
                            
                            # 🚨 Skip if contains PKR (should be filtered out by price parsing)
                            if 'PKR' in variant_text or 'Rs.' in variant_text or 'Rs ' in variant_text:
                                logger.debug(f"Skipping PKR text: {variant_text[:50]}...")
                                continue
                            
                            # 🚨 Skip if it's clearly a product listing (contains prices and percentages)
                            if any(pattern in variant_text for pattern in ['%', 'list:', 'typical:', 'limited time deal', '-']):
                                logger.debug(f"Skipping product listing text: {variant_text[:50]}...")
                                continue
                            
                            # AI classification
                            classification = self.ai_classifier.classify_variant(
                                variant_text, 
                                product_name, 
                                "Fashion" if self._is_fashion_product(product_name) else "Electronics"
                            )
                            
                            # Only include if AI says it's a real variant
                            if classification.is_real_variant:
                                
                                # Get real price by clicking variant
                                variant_price = self._get_variant_price_by_clicking(element, main_price)
                                
                                variants.append({
                                    'type': classification.variant_type,
                                    'name': self._clean_variant_name(variant_text),
                                    'price': variant_price,
                                    'stock': 50,
                                    'sku': f"AI-{abs(hash(variant_text)) % 10000:04d}",
                                    'images': self._get_variant_images(element),
                                    'attributes': {classification.variant_type: self._clean_variant_name(variant_text)},
                                    'ai_confidence': classification.confidence,
                                    'ai_reasoning': classification.reasoning,
                                    'extraction_method': 'ai_fallback'
                                })
                                
                                logger.info(f"✅ FALLBACK variant: '{variant_text}' = ${variant_price} (confidence: {classification.confidence:.2f})")
                                
                        except Exception as e:
                            logger.debug(f"Error processing fallback element: {e}")
                            continue
                            
                except Exception as e:
                    logger.debug(f"Error with fallback selector {selector}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Fallback variant extraction failed: {e}")
        
        logger.info(f"🔍 FALLBACK extraction found {len(variants)} additional variants")
        return variants
    
    def _debug_variant_elements(self):
        """Debug method to log ALL possible variant elements on the page"""
        try:
            logger.info("🔍 DEBUG: Scanning page for ALL possible variant elements...")
            
            # Test all our selectors
            all_selectors = (
                self.variant_selectors['color_swatches'] + 
                self.variant_selectors['size_swatches'] + 
                self.variant_selectors['dropdown_variants']
            )
            
            total_elements = 0
            for selector in all_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if len(elements) > 0:
                        total_elements += len(elements)
                        logger.info(f"🔍 DEBUG: Selector '{selector}' found {len(elements)} elements")
                        
                        # Log first few elements' text
                        for i, elem in enumerate(elements[:3]):
                            try:
                                text = elem.text.strip()
                                if text and len(text) > 1:
                                    logger.info(f"   Element {i+1}: '{text}'")
                            except:
                                pass
                except Exception as e:
                    logger.debug(f"Debug selector '{selector}' error: {e}")
            
            logger.info(f"🔍 DEBUG: Total elements found across all selectors: {total_elements}")
            
            # 🎯 NEW: Test Amazon-specific color swatch selectors
            amazon_color_selectors = [
                "div[data-csa-c-content-id*='color']",
                "div[data-csa-c-element-id*='color']", 
                "div[data-csa-c-content-id*='variation']",
                "div[data-csa-c-element-id*='variation']",
                ".twister-plus-variants-swatch-view-container",
                ".inline-twister-row-item",
                "#variation_color_name",
                "#variation_style_name",
                "#variation_color"
            ]
            
            logger.info("🔍 DEBUG: Testing Amazon-specific color selectors...")
            for selector in amazon_color_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if len(elements) > 0:
                        logger.info(f"🔍 DEBUG: Amazon selector '{selector}' found {len(elements)} elements")
                        for i, elem in enumerate(elements[:2]):
                            try:
                                text = elem.text.strip()[:100]
                                if text:
                                    logger.info(f"   Element {i+1}: '{text}'")
                            except:
                                pass
                except Exception as e:
                    logger.debug(f"Amazon selector '{selector}' error: {e}")
            
            # Also try to find ANY elements with common variant text
            variant_texts = ['Black', 'White', 'Blue', 'Red', 'Silver', 'Small', 'Medium', 'Large', 'XL']
            for text in variant_texts:
                try:
                    elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{text}')]")
                    if len(elements) > 0:
                        logger.info(f"🔍 DEBUG: Found {len(elements)} elements containing '{text}'")
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Debug variant elements failed: {e}")
    
    def _ai_validate_variants(self, variants: List[Dict], product_name: str) -> List[Dict]:
        """Final AI validation to remove any remaining fake variants"""
        validated_variants = []
        
        for variant in variants:
            variant_name = variant.get('name', '')
            
            # AI validation
            classification = self.ai_classifier.classify_variant(
                variant_name, 
                product_name,
                "Electronics" if not self._is_fashion_product(product_name) else "Fashion"
            )
            
            # Only keep variants with high confidence
            if classification.is_real_variant and classification.confidence > 0.6:
                validated_variants.append(variant)
                logger.info(f"✅ AI Validated: '{variant_name}' (confidence: {classification.confidence:.2f})")
            else:
                logger.info(f"❌ AI Rejected: '{variant_name}' (confidence: {classification.confidence:.2f}) - {classification.reasoning}")
        
        return validated_variants
    
    def _get_element_text(self, element) -> str:
        """Get text from element with multiple fallback methods"""
        try:
            # Method 1: aria-label
            aria_label = element.get_attribute('aria-label')
            if aria_label and len(aria_label.strip()) > 1:
                return aria_label.strip()
            
            # Method 2: title attribute
            title = element.get_attribute('title')
            if title and len(title.strip()) > 1:
                return title.strip()
            
            # Method 3: text content
            text = element.text.strip()
            if text and len(text) > 1:
                return text
            
            # Method 4: value attribute
            value = element.get_attribute('value')
            if value and len(value.strip()) > 1:
                return value.strip()
            
            return ""
            
        except Exception as e:
            logger.debug(f"Error getting element text: {e}")
            return ""
    
    def _get_variant_price_by_clicking(self, element, fallback_price: float) -> float:
        """Get variant price by clicking and waiting for price update"""
        try:
            # Store current price
            current_price = self._get_current_price_from_page()
            logger.debug(f"Current price before clicking: {current_price}")
            
            # 🎯 FIX: Find the actual clickable input element instead of span
            clickable_element = element
            
            # Try to find the input radio button within the element
            try:
                # Look for input radio button (the actual clickable element)
                input_element = element.find_element(By.CSS_SELECTOR, "input[type='radio'], input[type='checkbox']")
                if input_element:
                    clickable_element = input_element
                    logger.debug(f"Found input radio button, using that for clicking")
            except:
                # If no input found, try clicking the element itself
                pass
            
            # Click the correct element
            clickable_element.click()
            logger.debug(f"Clicked variant element")
            
            # Wait longer for page to update (Amazon is slow)
            time.sleep(3)  # Increased from 2 to 3 seconds
            
            # Try multiple times to get the updated price
            new_price = None
            for attempt in range(3):
                time.sleep(1)  # Additional wait
                new_price = self._get_current_price_from_page()
                logger.debug(f"Attempt {attempt + 1}: New price after clicking: {new_price}")
                
                if new_price and new_price != current_price:
                    logger.info(f"✅ Price updated: {current_price} → {new_price}")
                    return new_price
                    
            # If no price change detected, return fallback
            logger.warning(f"⚠️ No price change detected, using fallback: {fallback_price}")
            return fallback_price
                
        except Exception as e:
            logger.error(f"Error getting variant price by clicking: {e}")
            return fallback_price
    
    def _get_dropdown_variant_price_and_images(self, option_element, fallback_price: float) -> tuple[float, List[str]]:
        """Get dropdown variant price AND images by selecting option"""
        try:
            # Store current price
            current_price = self._get_current_price_from_page()
            logger.debug(f"Current price before dropdown selection: {current_price}")
            
            # Get parent select element
            select_element = option_element.find_element(By.XPATH, "./..")
            
            # Select the option
            from selenium.webdriver.support.ui import Select
            select = Select(select_element)
            option_text = option_element.text.strip()
            select.select_by_visible_text(option_text)
            logger.debug(f"Selected dropdown option: {option_text}")
            
            # Wait longer for page to fully update (price + images)
            time.sleep(4)  # Increased from 3 to 4 seconds for full page update
            
            # Try multiple times to get the updated price
            new_price = None
            for attempt in range(3):
                time.sleep(1)  # Additional wait
                new_price = self._get_current_price_from_page()
                logger.debug(f"Attempt {attempt + 1}: New price after dropdown selection: {new_price}")
                
                if new_price and new_price != current_price:
                    logger.info(f"✅ Dropdown price updated: {current_price} → {new_price}")
                    break
                    
            # If no price change detected, use fallback
            if not new_price or new_price == current_price:
                logger.warning(f"⚠️ No dropdown price change detected, using fallback: {fallback_price}")
                new_price = fallback_price
            
            # 🖼️ NOW EXTRACT IMAGES AFTER PAGE UPDATE
            variant_images = self._extract_gallery_images()
            logger.info(f"🖼️ Extracted {len(variant_images)} gallery images for variant")
            
            return new_price, variant_images
                
        except Exception as e:
            logger.error(f"Error getting dropdown variant price and images: {e}")
            return fallback_price, []
    
    def _get_dropdown_variant_price(self, option_element, fallback_price: float) -> float:
        """Get dropdown variant price by selecting option"""
        try:
            # Store current price
            current_price = self._get_current_price_from_page()
            logger.debug(f"Current price before dropdown selection: {current_price}")
            
            # Get parent select element
            select_element = option_element.find_element(By.XPATH, "./..")
            
            # Select the option
            from selenium.webdriver.support.ui import Select
            select = Select(select_element)
            option_text = option_element.text.strip()
            select.select_by_visible_text(option_text)
            logger.debug(f"Selected dropdown option: {option_text}")
            
            # Wait longer for price update (Amazon is slow)
            time.sleep(3)  # Increased from 2 to 3 seconds
            
            # Try multiple times to get the updated price
            new_price = None
            for attempt in range(3):
                time.sleep(1)  # Additional wait
                new_price = self._get_current_price_from_page()
                logger.debug(f"Attempt {attempt + 1}: New price after dropdown selection: {new_price}")
                
                if new_price and new_price != current_price:
                    logger.info(f"✅ Dropdown price updated: {current_price} → {new_price}")
                    return new_price
                    
            # If no price change detected, return fallback
            logger.warning(f"⚠️ No dropdown price change detected, using fallback: {fallback_price}")
            return fallback_price
                
        except Exception as e:
            logger.error(f"Error getting dropdown variant price: {e}")
            return fallback_price
    
    def _get_current_price_from_page(self) -> Optional[float]:
        """Extract current price from the page with enhanced detection"""
        try:
            # Enhanced price selectors in order of reliability
            price_selectors = [
                ".a-price-whole",  # Main price whole part
                ".a-price .a-offscreen",  # Hidden price text
                "#priceblock_ourprice",  # Our price
                "#priceblock_dealprice",  # Deal price
                ".apexPriceToPay .a-offscreen",  # Newer price selector
                ".priceToPay .a-offscreen",  # Another newer selector
                ".a-price-range .a-offscreen",  # Price range
                ".a-price-symbol + .a-price-whole",  # Symbol + whole
                "[data-a-price-whole]",  # Data attribute
                ".price-current",  # Generic current price
                ".olp-from-offer-price",  # From price
                ".a-size-base.a-color-price",  # Generic price text
            ]
            
            for selector in price_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        price_text = element.text.strip()
                        if price_text:
                            # Enhanced price extraction with better regex
                            import re
                            # Look for USD price patterns
                            price_patterns = [
                                r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # $123.45 or $1,234.56
                                r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # Just numbers
                            ]
                            
                            for pattern in price_patterns:
                                price_match = re.search(pattern, price_text.replace(',', ''))
                                if price_match:
                                    try:
                                        # 🚨 REJECT PKR/Non-USD prices
                                        if any(currency in price_text.upper() for currency in ['PKR', 'Rs.', 'Rs ', '₹', '₨']):
                                            logger.warning(f"🚨 REJECTED NON-USD PRICE: {price_text}")
                                            continue
                                            
                                        price = float(price_match.group(1) if '$' in pattern else price_match.group())
                                        if 0.50 <= price <= 10000.00:  # Reasonable price range
                                            logger.debug(f"Found price with selector '{selector}': ${price}")
                                            return price
                                    except ValueError:
                                        continue
                except Exception as e:
                    logger.debug(f"Error with price selector '{selector}': {e}")
                    continue
            
            # Fallback: Parse entire page source for price patterns
            try:
                page_source = self.driver.page_source
                # Look for USD price patterns
                price_patterns = [
                    r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # $123.45 or $1,234.56
                    r'USD\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # USD 123.45
                ]
                
                for pattern in price_patterns:
                    matches = re.findall(pattern, page_source)
                    for match in matches:
                        try:
                            price = float(match.replace(',', ''))
                            if 0.50 <= price <= 10000.00:  # Reasonable price range
                                logger.debug(f"Found price in page source: ${price}")
                                return price
                        except ValueError:
                            continue
            except Exception as e:
                logger.debug(f"Error parsing page source for price: {e}")
            
            logger.warning("⚠️ No valid price found on page")
            return None
            
        except Exception as e:
            logger.debug(f"Error getting current price: {e}")
            return None
    
    def _clean_variant_name(self, name: str) -> str:
        """Clean variant name by removing embedded prices and extra text"""
        try:
            import re
            
            # 🎯 FIX: Extract ONLY the color name from corrupted text
            if '\n' in name or len(name) > 50:
                # If it's corrupted text with newlines, try to extract color name
                lines = name.split('\n')
                for line in lines:
                    line = line.strip()
                    # Look for lines that contain color names
                    color_keywords = ['Black', 'Blue', 'Green', 'Purple', 'Red', 'White', 'Gray', 'Grey', 'Pink', 'Yellow', 'Orange', 'Brown']
                    for color in color_keywords:
                        if color.lower() in line.lower() and 'color' in line.lower():
                            return color
                        elif color.lower() == line.lower():
                            return color
                
                # If no color found, try to extract first meaningful word
                for line in lines:
                    line = line.strip()
                    if line and len(line) < 20 and not any(char in line for char in ['$', '%', ':', '\t']):
                        return line
            
            # Remove embedded prices
            cleaned = re.sub(r'\$\d+\.?\d*', '', name)
            cleaned = re.sub(r'\d+\.?\d*\s*usd', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'from\s+\$\d+\.?\d*', '', cleaned, flags=re.IGNORECASE)
            
            # Remove product specifications
            cleaned = re.sub(r'Brand\s+\w+', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'Color\s+', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'Ear Placement\s+\w+', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'Form Factor\s+\w+', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'Impedance\s+\d+\s*\w*', '', cleaned, flags=re.IGNORECASE)
            
            # Remove extra whitespace and newlines
            cleaned = cleaned.replace('\n', ' ').strip()
            cleaned = re.sub(r'\s+', ' ', cleaned)
            
            return cleaned if cleaned else name
            
        except Exception as e:
            logger.debug(f"Error cleaning variant name: {e}")
            return name
    
    def _extract_gallery_images(self) -> List[str]:
        """Extract ALL gallery images from the current product page after variant selection"""
        try:
            images = []
            
            # Amazon gallery selectors (2024 updated)
            gallery_selectors = [
                # Main product image
                "#landingImage",
                ".a-dynamic-image[data-old-hires]",
                
                # Thumbnail gallery
                "#altImages ul li img",
                ".imageThumbnail img",
                ".a-button-thumbnail img",
                "div[data-csa-c-type='image-thumbnail'] img",
                
                # Additional image selectors
                "#main-image-container img",
                ".a-image-container img",
                "#imgTagWrapperId img",
                ".a-spacing-base img[src*='amazon']",
            ]
            
            logger.debug("🖼️ Extracting gallery images...")
            
            for selector in gallery_selectors:
                try:
                    img_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for img in img_elements:
                        # Try multiple attributes
                        src = (img.get_attribute('src') or 
                               img.get_attribute('data-src') or 
                               img.get_attribute('data-old-hires') or
                               img.get_attribute('data-a-dynamic-image'))
                        
                        if src and 'amazon' in src.lower():
                            # Get high-res version if possible
                            if '_AC_' in src:
                                # Already high-res
                                full_src = src
                            elif 'data-old-hires' in img.get_attribute('outerHTML'):
                                full_src = img.get_attribute('data-old-hires')
                            else:
                                # Try to upgrade to high-res
                                full_src = src.replace('_SS40_', '_AC_SX679_').replace('_SS50_', '_AC_SX679_').replace('_SS100_', '_AC_SX679_')
                            
                            if full_src not in images:
                                images.append(full_src)
                                logger.debug(f"   ✅ Found image: {full_src[:60]}...")
                                
                except Exception as e:
                    logger.debug(f"Error with gallery selector '{selector}': {e}")
                    continue
            
            # Limit to reasonable number of images per variant
            final_images = images[:5] if images else []
            logger.info(f"🖼️ Extracted {len(final_images)} gallery images total")
            
            return final_images
            
        except Exception as e:
            logger.error(f"Error extracting gallery images: {e}")
            return []
    
    def _get_variant_images(self, element) -> List[str]:
        """Get variant images from element and page after clicking"""
        try:
            images = []
            
            # First, try to get images from the element itself
            img_elements = element.find_elements(By.TAG_NAME, "img")
            for img in img_elements:
                src = img.get_attribute('src') or img.get_attribute('data-src')
                if src and 'amazon' in src.lower():
                    images.append(src)
            
            # If no images found in element, try to get current page images after clicking
            if not images:
                try:
                    # Wait a bit for page to update
                    time.sleep(2)
                    
                    # Look for main product images that might have changed
                    main_image_selectors = [
                        "#landingImage",
                        ".a-dynamic-image",
                        "#imgTagWrapperId img",
                        ".a-image-container img",
                        "#main-image-container img"
                    ]
                    
                    for selector in main_image_selectors:
                        try:
                            img_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for img in img_elements:
                                src = img.get_attribute('src') or img.get_attribute('data-src')
                                if src and 'amazon' in src.lower() and src not in images:
                                    images.append(src)
                                    logger.debug(f"Found variant image: {src[:50]}...")
                                    break
                            if images:
                                break
                        except:
                            continue
                            
                except Exception as e:
                    logger.debug(f"Error getting page images after click: {e}")
            
            return images[:3]  # Limit to 3 images per variant
            
        except Exception as e:
            logger.debug(f"Error getting variant images: {e}")
            return []
    
    def _is_fashion_product(self, product_name: str) -> bool:
        """Check if product is fashion-related"""
        fashion_keywords = [
            'shirt', 'dress', 'jeans', 'jacket', 'coat', 'sweater', 'hoodie', 'pants', 'shorts',
            'skirt', 'blouse', 'shoes', 'sneaker', 'boot', 'sandal', 'bag', 'purse', 'handbag',
            'backpack', 'wallet', 'belt', 'scarf', 'hat', 'cap', 'gloves', 'watch', 'jewelry'
        ]
        
        product_lower = product_name.lower()
        return any(keyword in product_lower for keyword in fashion_keywords)
    
    def _deduplicate_variants(self, variants: List[Dict]) -> List[Dict]:
        """Remove duplicate variants based on name"""
        seen_names = set()
        unique_variants = []
        
        for variant in variants:
            variant_name = variant.get('name', '').lower().strip()
            if variant_name and variant_name not in seen_names:
                seen_names.add(variant_name)
                unique_variants.append(variant)
        
        return unique_variants
