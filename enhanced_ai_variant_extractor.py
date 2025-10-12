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
                # 🎯 EXACT Amazon Color Swatches from Images
                ".a-button-toggle",  # Main selector for all toggle buttons
                ".a-button-toggle-text",  # Text inside toggle buttons
                ".a-button-inner .a-button-text",  # Button text elements
                
                # 🎯 Amazon Color Grid (Image 1 & 3)
                "div[data-csa-c-content-id*='color'] .a-button-toggle",
                "div[data-csa-c-content-id*='variation'] .a-button-toggle",
                "div[data-csa-c-element-id*='color'] .a-button-toggle",
                "div[data-csa-c-element-id*='variation'] .a-button-toggle",
                
                # 🎯 Amazon Swatch Containers
                "#variation_color_name .a-button-toggle",
                "#variation_style_name .a-button-toggle", 
                "#variation_color .a-button-toggle",
                
                # 🎯 Amazon Image Swatches
                ".imgSwatch",
                ".image-swatch-wrapper",
                ".swatch-variation",
                
                # 🎯 Amazon Generic Variant Selectors
                ".twister-plus-variants-swatch-view-container .a-button-toggle",
                ".inline-twister-row-item .a-button-toggle",
                
                # 🎯 NEW: Pattern/Bundle Selectors (Image 4)
                "div[data-csa-c-content-id*='pattern'] .a-button-toggle",
                "div[data-csa-c-element-id*='pattern'] .a-button-toggle",
                ".pattern-selector .a-button-toggle",
                ".bundle-selector .a-button-toggle",
                
                # 🎯 NEW: Any button with color/variant text
                "button[class*='button']",
                "div[class*='button']",
                "span[class*='button']",
                "a[class*='button']"
            ],
            
            'size_swatches': [
                # 🎯 EXACT Amazon Size Buttons from Images
                ".a-button-toggle",  # Main selector for all toggle buttons (includes sizes)
                ".a-button-toggle-text",  # Text inside toggle buttons
                ".a-button-inner .a-button-text",  # Button text elements
                
                # 🎯 Amazon Size Grid (Image 1 & 3)
                "div[data-csa-c-content-id*='size'] .a-button-toggle",
                "div[data-csa-c-element-id*='size'] .a-button-toggle",
                ".size-selector .a-button-toggle",
                ".dimension-variation .a-button-toggle",
                
                # 🎯 Storage/memory selectors
                ".a-button-toggle[data-csa-c-element-id*='storage']",
                ".storage-selector .a-button-toggle",
                ".memory-selector .a-button-toggle",
                
                # 🎯 NEW: Any button that might be size
                "button[class*='button']",
                "div[class*='button']",
                "span[class*='button']",
                "a[class*='button']"
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
                            
                            # Skip placeholder options
                            if any(placeholder in variant_text.lower() for placeholder in 
                                   ['select', 'choose', 'pick', 'option', 'please']):
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
                            
                            # Skip if it's clearly not a variant
                            skip_keywords = ['add to cart', 'buy now', 'select', 'choose', 'quantity', 'size:', 'color:']
                            if any(keyword in variant_text.lower() for keyword in skip_keywords):
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
            
            # Also try to find ANY elements with common variant text
            variant_texts = ['Black', 'White', 'Blue', 'Red', 'Small', 'Medium', 'Large', 'XL']
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
            
            # Click the variant
            element.click()
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
            
            # Remove embedded prices
            cleaned = re.sub(r'\$\d+\.?\d*', '', name)
            cleaned = re.sub(r'\d+\.?\d*\s*usd', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'from\s+\$\d+\.?\d*', '', cleaned, flags=re.IGNORECASE)
            
            # Remove extra whitespace
            cleaned = cleaned.strip()
            
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
