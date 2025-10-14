#!/usr/bin/env python3
"""
Enhanced Variant Price Extractor
Focuses specifically on extracting real variant prices from Amazon
"""

import logging
import re
import time
import random
from typing import List, Dict, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)

class EnhancedVariantPriceExtractor:
    """
    Enhanced extractor that focuses on getting REAL variant prices
    """
    
    def __init__(self, driver):
        self.driver = driver
        logger.info("🚀 Enhanced Variant Price Extractor initialized")
    
    def extract_variants_with_real_prices(self, product_url: str, product_name: str, main_price: float) -> List[Dict]:
        """
        Extract variants with their REAL prices by interacting with the page
        """
        try:
            logger.info(f"🎯 Extracting variants with real prices for: {product_name[:50]}...")
            
            # Navigate to the product page if not already there
            if self.driver.current_url != product_url:
                self.driver.get(product_url)
                time.sleep(random.uniform(3, 5))
            
            variants = []
            
            # Method 1: Extract from variant selection containers with price updates
            variants.extend(self._extract_interactive_variants())
            
            # Method 2: Extract from dropdown menus with prices
            variants.extend(self._extract_dropdown_variants())
            
            # Method 3: Extract from swatch containers (colors, sizes)
            variants.extend(self._extract_swatch_variants())
            
            # Clean and deduplicate
            cleaned_variants = self._clean_and_deduplicate_variants(variants, main_price)
            
            logger.info(f"🎯 Enhanced extraction found {len(cleaned_variants)} variants with real prices")
            return cleaned_variants
            
        except Exception as e:
            logger.error(f"Enhanced variant extraction failed: {e}")
            return []
    
    def _extract_interactive_variants(self) -> List[Dict]:
        """Extract variants by clicking on them and capturing price changes"""
        variants = []
        
        try:
            # Find all clickable variant options
            variant_selectors = [
                "li[data-defaultasin] .a-button",
                ".twister-plus-buying-options li .a-button",
                "#variation_color_name li .a-button",
                "#variation_size_name li .a-button",
                "#variation_style_name li .a-button",
                ".a-button[data-action='a-dropdown-button']"
            ]
            
            for selector in variant_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    logger.info(f"🔍 Found {len(elements)} elements with selector: {selector}")
                    
                    for i, element in enumerate(elements[:10]):  # Limit to first 10 to avoid too many clicks
                        try:
                            # Get variant info before clicking
                            variant_text = element.get_attribute('aria-label') or element.text.strip()
                            if not variant_text or len(variant_text) < 2:
                                continue
                            
                            # Skip if it's summary text
                            if any(skip in variant_text.lower() for skip in ['see available', 'options from', 'starting from']):
                                continue
                            
                            logger.info(f"🖱️ Clicking variant: {variant_text}")
                            
                            # Scroll into view and click
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                            time.sleep(0.5)
                            
                            # Click the element
                            element.click()
                            time.sleep(2)  # Wait for price update
                            
                            # Extract the updated price
                            current_price = self._get_current_price()
                            
                            # Extract variant type
                            variant_type = self._detect_variant_type(variant_text, selector)
                            
                            variants.append({
                                'type': variant_type,
                                'name': variant_text,
                                'price': current_price,
                                'stock': 50,
                                'sku': f"ENH-{abs(hash(variant_text)) % 10000:04d}",
                                'images': [],
                                'attributes': {variant_type: variant_text},
                                'extraction_method': 'interactive'
                            })
                            
                            logger.info(f"✅ Extracted: {variant_text} = ${current_price}")
                            
                        except Exception as e:
                            logger.debug(f"Error clicking element {i}: {e}")
                            continue
                            
                except Exception as e:
                    logger.debug(f"Error with selector {selector}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Interactive extraction failed: {e}")
        
        return variants
    
    def _extract_dropdown_variants(self) -> List[Dict]:
        """Extract variants from dropdown menus - ENHANCED for Amazon"""
        variants = []
        
        try:
            # ENHANCED Amazon dropdown selectors - more specific and accurate
            dropdown_selectors = [
                # Amazon-specific dropdown selectors
                "select[name*='dropdown_selected']",
                "select[data-action='a-dropdown-select']",
                ".a-dropdown-container select",
                "select[id*='native_dropdown']",
                "select[autocomplete='list']",
                # Generic dropdowns as fallback
                "select[data-csa-c-element-id*='dropdown']",
                "select.a-native-dropdown"
            ]
            
            for selector in dropdown_selectors:
                try:
                    dropdowns = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    logger.info(f"Found {len(dropdowns)} dropdowns with selector: {selector}")
                    
                    for dropdown in dropdowns:
                        try:
                            # Get dropdown label/context to understand what type of variant this is
                            dropdown_label = ""
                            try:
                                # Look for associated label
                                dropdown_id = dropdown.get_attribute('id')
                                if dropdown_id:
                                    label_element = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{dropdown_id}']")
                                    dropdown_label = label_element.text.strip()
                            except:
                                # Try parent container for context
                                try:
                                    parent = dropdown.find_element(By.XPATH, "./..")
                                    dropdown_label = parent.get_attribute('data-feature-name') or parent.get_attribute('class')
                                except:
                                    pass
                            
                            options = dropdown.find_elements(By.TAG_NAME, "option")
                            logger.info(f"Dropdown '{dropdown_label}' has {len(options)} options")
                            
                            for option in options[1:]:  # Skip first option (usually placeholder)
                                try:
                                    # ENHANCED text extraction - try multiple methods
                                    option_text = None
                                    
                                    # Method 1: Direct text content
                                    if option.text and option.text.strip():
                                        option_text = option.text.strip()
                                    
                                    # Method 2: innerHTML parsing for complex structures
                                    if not option_text or len(option_text) < 2:
                                        try:
                                            inner_html = option.get_attribute('innerHTML')
                                            if inner_html:
                                                # Remove HTML tags and get clean text
                                                import re
                                                clean_text = re.sub(r'<[^>]+>', '', inner_html).strip()
                                                if clean_text and len(clean_text) > 1:
                                                    option_text = clean_text
                                        except:
                                            pass
                                    
                                    # Method 3: Value as fallback only if it's meaningful
                                    if not option_text or len(option_text) < 2:
                                        option_value = option.get_attribute('value')
                                        if option_value and len(option_value) > 2 and not option_value.isdigit():
                                            option_text = option_value
                                    
                                    if not option_text or len(option_text) < 2:
                                        logger.debug(f"Skipping option with insufficient text: '{option_text}'")
                                        continue
                                    
                                    # 💰 ENHANCED: Extract embedded price from variant text
                                    embedded_price = self._extract_price_from_variant_text(option_text)
                                    clean_name = self._clean_variant_name(option_text)
                                    
                                    # Use clean name for validation
                                    if not clean_name or len(clean_name) < 2:
                                        logger.debug(f"Skipping variant with insufficient clean name: '{clean_name}'")
                                        continue
                                    
                                    # Enhanced validation - skip placeholder/invalid options
                                    skip_patterns = [
                                        'select', 'choose', 'please select', 'pick', 'option',
                                        'available', 'selection', 'default', 'none'
                                    ]
                                    if any(skip in clean_name.lower() for skip in skip_patterns):
                                        logger.debug(f"Skipping placeholder option: '{clean_name}'")
                                        continue
                                    
                                    # Skip numeric-only options unless they're storage/memory sizes
                                    if clean_name.isdigit() and not any(storage_hint in dropdown_label.lower() for storage_hint in ['storage', 'memory', 'gb', 'tb']):
                                        logger.debug(f"Skipping numeric option without storage context: '{clean_name}'")
                                        continue
                                    
                                    # Select this option to get real price (if no embedded price found)
                                    current_price = embedded_price
                                    
                                    if not current_price:
                                        try:
                                            option.click()
                                            time.sleep(1.5)  # Wait for price update
                                            current_price = self._get_current_price()
                                        except Exception as click_error:
                                            logger.debug(f"Could not click option '{clean_name}': {click_error}")
                                            current_price = self._get_current_price()
                                    
                                    # Enhanced variant type detection
                                    variant_type = self._detect_variant_type(clean_name, dropdown_label or selector)
                                    
                                    variants.append({
                                        'type': variant_type,
                                        'name': clean_name,  # Use clean name without embedded prices
                                        'price': current_price or 0.0,
                                        'stock': 50,
                                        'sku': f"ENH-{abs(hash(clean_name)) % 10000:04d}",
                                        'images': [],
                                        'attributes': {variant_type: clean_name},
                                        'extraction_method': 'dropdown_enhanced',
                                        'dropdown_context': dropdown_label,
                                        'raw_text': option_text  # Keep original for debugging
                                    })
                                    
                                    price_source = "embedded" if embedded_price else "page"
                                    logger.info(f"✅ ENHANCED Dropdown variant: '{clean_name}' (type: {variant_type}) = ${current_price} ({price_source})")
                                
                                
                                except Exception as e:
                                    logger.debug(f"Error processing option: {e}")
                                    continue
                                    
                        except Exception as dropdown_error:
                            logger.debug(f"Error processing dropdown: {dropdown_error}")
                            continue
                            
                except Exception as e:
                    logger.debug(f"Error with dropdown selector {selector}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Dropdown extraction failed: {e}")
        
        logger.info(f"🎯 ENHANCED dropdown extraction found {len(variants)} variants")
        return variants
    
    def _extract_swatch_variants(self) -> List[Dict]:
        """Extract variants from color/size swatches - ENHANCED for Amazon"""
        variants = []
        
        try:
            # ENHANCED Amazon swatch selectors - comprehensive and accurate for 2024
            swatch_selectors = [
                # 🎯 AMAZON 2024 VARIANT SELECTORS - Based on S25 Ultra structure
                # Color variant swatches (most common)
                ".a-button-toggle[data-csa-c-element-id*='color'] .a-button-text",
                ".a-button-toggle[data-csa-c-element-id*='variation'] .a-button-text", 
                ".a-button-toggle .a-button-text",  # Generic variant buttons
                
                # Storage/Size variant buttons  
                ".a-button-toggle[data-csa-c-element-id*='size'] .a-button-text",
                ".a-button-toggle[data-csa-c-element-id*='storage'] .a-button-text",
                
                # Image-based color swatches (like in S25 Ultra)
                ".a-button-toggle img[alt*='Color']",
                ".a-button-toggle img[alt*='color']",
                ".a-button-toggle[title*='Color']",
                ".a-button-toggle[title*='color']",
                
                # Modern Amazon variant containers (2024 structure)
                "[data-feature-name='variation'] .a-button-toggle",
                "[data-csa-c-element-id*='variation'] .a-button-toggle", 
                ".a-unordered-list .a-button-toggle",
                
                # Fallback patterns (older structure)
                ".a-button-thumbnail",  # Keep as last resort
                "[data-feature-name='variation'] .a-button",
                ".variation_color_name .a-button",
                ".variation_size_name .a-button",
                ".variation_style_name .a-button"
            ]
            
            for selector in swatch_selectors:
                try:
                    swatches = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    logger.info(f"Found {len(swatches)} swatches with selector: {selector}")
                    
                    for swatch in swatches[:12]:  # Limit to first 12 swatches for performance
                        try:
                            # ENHANCED swatch text extraction - multiple methods for 2024 Amazon
                            swatch_text = None
                            
                            # Method 1: Image alt text (for color swatches like S25 Ultra)
                            try:
                                img = swatch.find_element(By.TAG_NAME, "img")
                                alt_text = img.get_attribute('alt')
                                if alt_text and len(alt_text) > 2:
                                    swatch_text = alt_text
                                    logger.debug(f"🖼️ Got variant from image alt: '{alt_text}'")
                            except:
                                pass
                            
                            # Method 2: aria-label (most reliable for accessibility)
                            if not swatch_text:
                                swatch_text = swatch.get_attribute('aria-label')
                                if swatch_text and swatch_text.strip():
                                    swatch_text = swatch_text.strip()
                                    logger.debug(f"🏷️ Got variant from aria-label: '{swatch_text}'")
                            
                            # Method 3: title attribute
                            if not swatch_text or len(swatch_text) < 2:
                                title_attr = swatch.get_attribute('title')
                                if title_attr and title_attr.strip():
                                    swatch_text = title_attr.strip()
                                    logger.debug(f"📋 Got variant from title: '{swatch_text}'")
                            
                            # Method 4: direct text content (.a-button-text)
                            if not swatch_text or len(swatch_text) < 2:
                                text_content = swatch.text.strip()
                                if text_content and len(text_content) > 1:
                                    swatch_text = text_content
                                    logger.debug(f"📝 Got variant from text: '{text_content}'")
                            
                            # Method 5: nested span or div text
                            if not swatch_text or len(swatch_text) < 2:
                                try:
                                    nested_text = swatch.find_element(By.CSS_SELECTOR, "span, div, .a-button-text").text.strip()
                                    if nested_text and len(nested_text) > 1:
                                        swatch_text = nested_text
                                        logger.debug(f"🔍 Got variant from nested text: '{nested_text}'")
                                except:
                                    pass
                            
                            # Method 6: data attributes (last resort)
                            if not swatch_text or len(swatch_text) < 2:
                                for attr in ['data-value', 'data-variant', 'data-option', 'data-csa-c-element-id']:
                                    attr_value = swatch.get_attribute(attr)
                                    if attr_value and len(attr_value) > 2 and not attr_value.isdigit():
                                        swatch_text = attr_value
                                        logger.debug(f"🔧 Got variant from {attr}: '{attr_value}'")
                                        break
                            
                            if not swatch_text or len(swatch_text) < 2:
                                logger.debug(f"Skipping swatch with insufficient text")
                                continue
                            
                            # 💰 ENHANCED: Extract embedded price and clean name
                            embedded_price = self._extract_price_from_variant_text(swatch_text)
                            clean_name = self._clean_variant_name(swatch_text)
                            
                            # 🚨 CRITICAL DEBUG: Log the exact text extraction process
                            logger.info(f"🔍 SWATCH DEBUG - Raw text: '{swatch_text[:100]}...'")
                            logger.info(f"🔍 SWATCH DEBUG - Embedded price: ${embedded_price}")
                            logger.info(f"🔍 SWATCH DEBUG - Clean name: '{clean_name}'")
                            
                            # Enhanced validation - clean up the text
                            if not clean_name or len(clean_name) < 2:
                                logger.debug(f"Skipping swatch with insufficient clean name: '{clean_name}'")
                                continue
                            
                            # Skip invalid swatch patterns
                            skip_patterns = [
                                'click to expand', 'see more', 'view all', 'show more',
                                'select', 'choose', 'pick', 'available', 'options'
                            ]
                            if any(skip in clean_name.lower() for skip in skip_patterns):
                                logger.debug(f"Skipping invalid swatch: '{clean_name}'")
                                continue
                            
                            # Click the swatch to get updated pricing (if no embedded price)
                            current_price = embedded_price
                            
                            if not current_price:
                                try:
                                    # Scroll into view and click
                                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", swatch)
                                    time.sleep(0.5)
                                    
                                    # Try different click methods
                                    try:
                                        swatch.click()
                                    except:
                                        # Fallback to JavaScript click
                                        self.driver.execute_script("arguments[0].click();", swatch)
                                    
                                    time.sleep(2)  # Wait for price update
                                    current_price = self._get_current_price()
                                    
                                except Exception as click_error:
                                    logger.debug(f"Could not interact with swatch '{clean_name}': {click_error}")
                                    current_price = self._get_current_price()
                            
                            # Enhanced variant type detection with context
                            variant_type = self._detect_variant_type(clean_name, selector)
                            
                            # Get swatch image if available
                            swatch_image = self._extract_swatch_image(swatch)
                            
                            variants.append({
                                'type': variant_type,
                                'name': clean_name,  # Use clean name without embedded prices
                                'price': current_price or 0.0,
                                'stock': 50,
                                'sku': f"ENH-{abs(hash(clean_name)) % 10000:04d}",
                                'images': [swatch_image] if swatch_image else [],
                                'attributes': {variant_type: clean_name},
                                'extraction_method': 'swatch_enhanced',
                                'selector_used': selector,
                                'raw_text': swatch_text  # Keep original for debugging
                            })
                            
                            price_source = "embedded" if embedded_price else "page"
                            logger.info(f"✅ ENHANCED Swatch variant: '{clean_name}' (type: {variant_type}) = ${current_price} ({price_source})")
                            
                        except Exception as e:
                            logger.debug(f"Error processing swatch: {e}")
                            continue
                            
                except Exception as e:
                    logger.debug(f"Error with swatch selector {selector}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Swatch extraction failed: {e}")
        
        logger.info(f"🎯 ENHANCED swatch extraction found {len(variants)} variants")
        return variants
    
    def _clean_variant_text(self, text: str) -> str:
        """Clean and normalize variant text - ENHANCED with price extraction"""
        if not text:
            return ""
        
        # Remove common prefixes/suffixes
        text = text.strip()
        
        # Remove newlines and normalize whitespace
        text = ' '.join(text.split())
        
        # Remove "Click to select" type phrases
        clean_patterns = [
            r'click to select\s*',
            r'select\s*',
            r'choose\s*',
            r'\s*-\s*click.*',
            r'\s*\(.*click.*\)',
        ]
        
        import re
        for pattern in clean_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE).strip()
        
        return text
    
    def _extract_price_from_variant_text(self, variant_text: str) -> Optional[float]:
        """Extract price from variant text that contains embedded prices"""
        if not variant_text:
            return None
            
        import re
        
        # Look for price patterns in the text
        price_patterns = [
            r'\$(\d+(?:\.\d{2})?)',  # $123.45 or $123
            r'(\d+(?:\.\d{2})?)\s*dollars?',  # 123.45 dollars
            r'USD\s*(\d+(?:\.\d{2})?)',  # USD 123.45
            r'(\d+(?:\.\d{2})?\$)',  # 123.45$
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, variant_text, re.IGNORECASE)
            if matches:
                try:
                    # Get the last (most specific) price found
                    price_str = matches[-1].replace('$', '').replace(',', '')
                    price = float(price_str)
                    if price > 0:
                        logger.info(f"💰 Extracted embedded price ${price} from variant text: '{variant_text[:50]}...'")
                        return price
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def _clean_variant_name(self, variant_text: str) -> str:
        """Clean variant name by removing embedded prices and formatting - ENHANCED"""
        if not variant_text:
            return ""
        
        import re
        
        # 🚨 CRITICAL DEBUG: Log the input
        logger.debug(f"🧹 CLEANING INPUT: '{variant_text[:100]}...'")
        
        # Remove embedded prices and option counts - ENHANCED PATTERNS
        price_patterns = [
            r'\$\d+(?:,\d{3})*(?:\.\d{2})?',  # Remove $123,456.78
            r'PKR\s*\d+(?:,\d{3})*(?:\.\d{2})?',  # Remove PKR 12,345.67
            r'Rs\.?\s*\d+(?:,\d{3})*(?:\.\d{2})?',  # Remove Rs. 12,345.67
            r'\d+(?:\.\d{2})?\s*dollars?',  # Remove 123.45 dollars
            r'USD\s*\d+(?:,\d{3})*(?:\.\d{2})?',  # Remove USD 123.45
            r'\d+\s+options?\s+from\s+(?:PKR|Rs\.?|\$)\s*\d+(?:[\.,]\d+)*',  # Remove "2 options from PKR 569.99"
            r'\d+\s+options?',  # Remove "2 options"
            r'from\s+(?:PKR|Rs\.?|\$)\s*\d+(?:[\.,]\d+)*',  # Remove "from PKR 569.99"
            r'from\s+\$[\d,]*\.?\d*',  # Remove "from $1,139.99"
            r'from\s+,[\d,]*\.?\d*',  # Remove "from ,139.99" (malformed)
            r'from\s*$',  # Remove trailing "from"
            r'\+$',  # Remove trailing + signs
        ]
        
        clean_name = variant_text
        for pattern in price_patterns:
            before = clean_name
            clean_name = re.sub(pattern, '', clean_name, flags=re.IGNORECASE)
            if before != clean_name:
                logger.debug(f"🧹 REMOVED '{pattern}': '{before}' → '{clean_name}'")
        
        # Clean up whitespace and formatting
        clean_name = ' '.join(clean_name.split())  # Remove extra whitespace and newlines
        clean_name = clean_name.strip(' |,.-\n\r\t')  # Remove trailing separators and whitespace
        
        # 🚨 CRITICAL DEBUG: Log the output
        logger.debug(f"🧹 CLEANING OUTPUT: '{clean_name}'")
        
        # 🚨 ENHANCED VALIDATION: Reject meaningless variants
        if self._is_meaningless_variant(clean_name, variant_text):
            logger.warning(f"🚨 REJECTED MEANINGLESS VARIANT: '{clean_name}' from '{variant_text[:50]}...'")
            return ""
        
        return clean_name
    
    def _is_meaningless_variant(self, clean_name: str, original_text: str) -> bool:
        """Check if a variant name is meaningless and should be rejected"""
        if not clean_name or len(clean_name.strip()) == 0:
            return True
        
        # Reject pure numbers with + signs (like "2+", "5+", "4+")
        if re.match(r'^\d+\+?$', clean_name.strip()):
            return True
        
        # Reject very short suspicious names
        if len(clean_name.strip()) <= 2 and clean_name.strip() in ['2+', '3+', '4+', '5+', '6+', '7+', '8+', '9+']:
            return True
        
        # Reject if it's just whitespace or punctuation
        if re.match(r'^[\s\W]*$', clean_name):
            return True
        
        return False
    
    def _extract_swatch_image(self, swatch_element) -> str:
        """Extract image URL from swatch element"""
        try:
            # Look for image within the swatch
            img = swatch_element.find_element(By.TAG_NAME, "img")
            return img.get_attribute("src") or img.get_attribute("data-src")
        except:
            # Look for background image in style
            try:
                style = swatch_element.get_attribute("style")
                if style and "background-image" in style:
                    import re
                    match = re.search(r'url\(["\']?([^"\']+)["\']?\)', style)
                    if match:
                        return match.group(1)
            except:
                pass
        
        return None
    
    def _get_current_price(self) -> float:
        """Get the current price displayed on the page - ENHANCED for 2024 Amazon"""
        price_selectors = [
            # 🎯 AMAZON 2024 PRICE SELECTORS - Based on S25 Ultra structure
            # Main price display (most reliable)
            ".a-price.a-text-price.a-size-medium.apexPriceToPay .a-offscreen",
            ".a-price[data-a-price-type='minPrice'] .a-offscreen",
            ".a-price.reinventPricePriceToPayMargin .a-offscreen",
            "#apex_desktop .a-price .a-offscreen",
            
            # Variant-specific price displays
            ".a-price.a-size-medium.a-color-price .a-offscreen",  # Variant price
            ".a-price.a-text-price .a-offscreen",
            ".a-price .a-offscreen",
            
            # Alternative price formats
            ".a-price-whole",
            "#priceblock_dealprice", 
            "#priceblock_ourprice",
            ".a-price-range .a-offscreen",
            
            # Mobile/responsive price selectors
            ".a-size-medium.a-color-price",
            ".a-price-symbol + .a-price-whole"
        ]
        
        for selector in price_selectors:
            try:
                price_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for price_element in price_elements:
                    if price_element and price_element.is_displayed():
                        price_text = price_element.text.strip()
                        parsed_price = self._parse_price(price_text)
                        if parsed_price and parsed_price > 0:
                            logger.debug(f"💰 Found price ${parsed_price} using selector: {selector}")
                            return parsed_price
            except Exception as e:
                logger.debug(f"Error with price selector {selector}: {e}")
                continue
        
        # 🆕 NEW: Try to extract price from variant button text (for S25 Ultra style)
        try:
            # Look for price in the currently selected variant button
            selected_variant_buttons = self.driver.find_elements(By.CSS_SELECTOR, ".a-button-toggle.a-button-selected")
            for button in selected_variant_buttons:
                button_text = button.text
                embedded_price = self._extract_price_from_variant_text(button_text)
                if embedded_price and embedded_price > 0:
                    logger.info(f"💰 Found price ${embedded_price} from selected variant button: '{button_text[:30]}...'")
                    return embedded_price
        except Exception as e:
            logger.debug(f"Error extracting price from variant buttons: {e}")
        
        logger.debug("⚠️ No price found with any selector")
        return 0.0
    
    def _parse_price(self, price_text: str) -> Optional[float]:
        """Parse price string into float - ONLY REAL USD PRICES"""
        if not price_text:
            return None
        
        original_text = price_text
        
        # 🚨 AGGRESSIVE REJECTION OF NON-USD CURRENCIES
        non_usd_currencies = [
            'PKR', 'AED', 'GBP', 'EUR', 'Rs', '₨', '₹', 'د.إ',
            'rupee', 'rupees', 'pkr', 'aed', 'gbp', 'eur',
            'rs.', 'rs ', '₹', '₨', 'د.إ', '£', '€'
        ]
        
        price_upper = price_text.upper()
        for currency in non_usd_currencies:
            if currency.upper() in price_upper:
                logger.warning(f"🚨 REJECTED NON-USD CURRENCY '{currency}' in: {price_text}")
                return None
        
        # 🚨 ADDITIONAL PKR DETECTION
        if 'PKR' in price_upper or 'Rs.' in price_upper or 'Rs ' in price_upper:
            logger.warning(f"🚨 REJECTED PAKISTANI CURRENCY: {price_text}")
            return None
        
        # Only accept prices with $ symbol or clear USD indication
        if '$' not in price_text and 'USD' not in price_text.upper():
            # If it's just a number, it might be USD without symbol
            if not re.match(r'^\d+\.?\d*$', price_text.strip()):
                logger.warning(f"🚨 REJECTED PRICE WITHOUT USD INDICATOR: {price_text}")
                return None
        
        # Remove currency symbols and clean
        price_text = re.sub(r'[^\d.,\-\s]', '', price_text)
        price_text = price_text.replace(',', '')
        
        # Extract number
        price_match = re.search(r'(\d+\.?\d*)', price_text)
        if price_match:
            try:
                price = float(price_match.group(1))
                
                # 🚨 REAL PRICE VALIDATION: Only reasonable USD prices
                if price < 0.01:
                    logger.warning(f"🚨 REJECTED TOO LOW: ${price} from '{original_text}'")
                    return None
                
                if price > 5000:  # Most products under $5000
                    logger.warning(f"🚨 REJECTED TOO HIGH: ${price} from '{original_text}' (likely foreign currency)")
                    return None
                
                logger.info(f"✅ ACCEPTED USD PRICE: ${price} from '{original_text}'")
                return round(price, 2)
            except:
                pass
        
        return None
    
    def _detect_variant_type(self, variant_text: str, selector: str) -> str:
        """Detect the type of variant based on text and selector"""
        text_lower = variant_text.lower()
        selector_lower = selector.lower()
        
        # Check selector first
        if 'color' in selector_lower:
            return 'color'
        elif 'size' in selector_lower:
            return 'size'
        elif 'style' in selector_lower:
            return 'style'
        elif 'storage' in selector_lower:
            return 'storage'
        
        # Check text content
        color_keywords = ['black', 'white', 'red', 'blue', 'green', 'yellow', 'pink', 'purple', 'orange', 'gray', 'grey', 'silver', 'gold']
        size_keywords = ['small', 'medium', 'large', 'xl', 'xxl', 's', 'm', 'l', 'inch', 'cm']
        storage_keywords = ['gb', 'tb', 'mb']
        
        if any(color in text_lower for color in color_keywords):
            return 'color'
        elif any(size in text_lower for size in size_keywords):
            return 'size'
        elif any(storage in text_lower for storage in storage_keywords):
            return 'storage'
        elif 'pack' in text_lower or 'count' in text_lower:
            return 'pack'
        elif 'ads' in text_lower or 'lockscreen' in text_lower:
            return 'ads'
        
        return 'variant'
    
    def _clean_and_deduplicate_variants(self, variants: List[Dict], main_price: float) -> List[Dict]:
        """Clean and deduplicate variants - ENHANCED with smarter filtering"""
        if not variants:
            return []
        
        cleaned = []
        seen_names = set()
        
        logger.info(f"🔍 Starting variant cleaning: {len(variants)} raw variants")
        
        for variant in variants:
            name = variant.get('name', '').strip()
            if not name or len(name) < 2:
                logger.debug(f"Skipping variant with insufficient name: '{name}'")
                continue
            
            # Skip duplicates (case-insensitive, normalized)
            name_key = name.lower().replace(' ', '').replace('-', '').replace('_', '')
            if name_key in seen_names:
                logger.debug(f"Skipping duplicate variant: '{name}'")
                continue
            seen_names.add(name_key)
            
            # ENHANCED invalid pattern detection - more specific
            invalid_patterns = [
                # Navigation/UI text patterns
                'see available options', 'see all options', 'view all options',
                'there are', 'options from', 'starting from', 'price hidden',
                'visit the', 'click to expand', 'show more options',
                
                # Placeholder patterns  
                'please select', 'make a selection', 'choose option',
                'select your', 'pick your', 'default option',
                
                # Summary/count patterns
                'available in', 'comes in', 'options available',
                'total options', 'more options', 'additional options'
            ]
            
            # Only reject if it's clearly invalid (not just contains keywords)
            is_invalid = False
            for pattern in invalid_patterns:
                if pattern in name.lower():
                    # Additional check: if it's a short match within a longer valid name, keep it
                    if len(name) > len(pattern) + 5:  # Give some buffer for valid variants
                        continue
                    is_invalid = True
                    logger.debug(f"Rejecting invalid pattern variant: '{name}' (matched: {pattern})")
                    break
            
            if is_invalid:
                continue
            
            # ENHANCED: Don't reject single words or short names that could be valid
            # Colors like "Black", "Blue", sizes like "XL", "M", storage like "32GB"
            if len(name) >= 2:  # Allow 2+ character variants (like "XL", "M", etc.)
                # Special handling for numeric-only variants
                if name.isdigit():
                    # Only reject pure numbers if they're not storage/memory related
                    variant_type = variant.get('type', 'variant')
                    extraction_method = variant.get('extraction_method', '')
                    dropdown_context = variant.get('dropdown_context', '').lower()
                    
                    # Keep if it's likely storage/memory
                    if any(storage_hint in dropdown_context for storage_hint in ['storage', 'memory', 'gb', 'tb', 'capacity']):
                        logger.info(f"✅ Keeping numeric storage variant: '{name}' (context: {dropdown_context})")
                    elif variant_type in ['storage', 'memory', 'capacity']:
                        logger.info(f"✅ Keeping numeric variant by type: '{name}' (type: {variant_type})")
                    else:
                        logger.debug(f"Rejecting standalone numeric variant: '{name}' (no storage context)")
                        continue
            
            # ENHANCED price handling - preserve extracted prices
            original_price = variant.get('price', 0)
            if original_price <= 0:
                variant['price'] = main_price
                logger.debug(f"Using main price ${main_price} for variant '{name}'")
            else:
                logger.debug(f"Preserving extracted price ${original_price} for variant '{name}'")
            
            # Ensure required fields
            if 'type' not in variant:
                variant['type'] = 'variant'
            if 'stock' not in variant:
                variant['stock'] = 50
            if 'images' not in variant:
                variant['images'] = []
            if 'attributes' not in variant:
                variant['attributes'] = {variant['type']: name}
            
            cleaned.append(variant)
            logger.info(f"✅ ACCEPTED variant: '{name}' (type: {variant.get('type')}, price: ${variant.get('price')}, method: {variant.get('extraction_method')})")
        
        logger.info(f"🎯 ENHANCED cleaning complete: {len(variants)} → {len(cleaned)} variants")
        return cleaned
