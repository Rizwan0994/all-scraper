#!/usr/bin/env python3
"""
Amazon API Intelligence & Network Analysis
Reverse engineering Amazon's variant APIs for 95%+ accuracy
"""

import asyncio
import json
import re
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import aiohttp
from urllib.parse import urljoin, parse_qs, urlparse

logger = logging.getLogger(__name__)

@dataclass
class AmazonAPIEndpoint:
    """Amazon API endpoint information"""
    url: str
    method: str
    headers: Dict[str, str]
    params: Dict[str, Any]
    response_format: str
    variant_data: bool = False
    price_data: bool = False
    stock_data: bool = False

class AmazonAPIIntelligence:
    """
    Amazon API reverse engineering and intelligence gathering
    Discovers and utilizes Amazon's internal variant APIs
    """
    
    def __init__(self, page):
        self.page = page
        self.session = None
        self.discovered_apis = []
        self.session_tokens = {}
        
        # Known Amazon API patterns
        self.api_patterns = {
            'variant_apis': [
                r'/gp/product/ajax/ref=.*',
                r'/api/.*variant.*',
                r'/twister/.*',
                r'/gp/twister/.*',
                r'/dp/ajax/.*'
            ],
            'price_apis': [
                r'/gp/product/ajax/price.*',
                r'/api/.*price.*',
                r'/pricing/.*',
                r'/gp/offer-listing/ajax/.*'
            ],
            'stock_apis': [
                r'/gp/product/ajax/availability.*',
                r'/api/.*stock.*',
                r'/inventory/.*'
            ]
        }
        
        # Common Amazon headers
        self.amazon_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'X-Requested-With': 'XMLHttpRequest',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        }
    
    async def initialize_session(self):
        """Initialize HTTP session for API calls"""
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=30,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self.amazon_headers
        )
        
        logger.info("✅ Amazon API session initialized")
    
    async def discover_variant_apis(self) -> List[AmazonAPIEndpoint]:
        """Discover Amazon's variant APIs through network monitoring"""
        if not self.session:
            await self.initialize_session()
        
        discovered_apis = []
        
        try:
            # Set up network monitoring
            await self.page.route("**/*", self._intercept_network_request)
            
            # Extract session tokens
            await self._extract_session_tokens()
            
            # Trigger variant-related requests by interacting with page
            await self._trigger_variant_requests()
            
            # Analyze discovered APIs
            for api in self.discovered_apis:
                if self._is_variant_api(api):
                    discovered_apis.append(api)
            
            logger.info(f"🔍 Discovered {len(discovered_apis)} variant APIs")
            return discovered_apis
            
        except Exception as e:
            logger.error(f"❌ API discovery failed: {e}")
            return []
    
    async def _intercept_network_request(self, route):
        """Intercept and analyze network requests"""
        request = route.request
        
        try:
            # Check if this is an API request
            if self._is_amazon_api_request(request):
                # Store API information
                api_endpoint = AmazonAPIEndpoint(
                    url=request.url,
                    method=request.method,
                    headers=dict(request.headers),
                    params=self._extract_request_params(request),
                    response_format='json',
                    variant_data=self._contains_variant_data(request.url),
                    price_data=self._contains_price_data(request.url),
                    stock_data=self._contains_stock_data(request.url)
                )
                
                self.discovered_apis.append(api_endpoint)
                logger.debug(f"🔍 Discovered API: {request.method} {request.url[:100]}...")
        
        except Exception as e:
            logger.debug(f"Request interception error: {e}")
        
        # Continue with the request
        await route.continue_()
    
    def _is_amazon_api_request(self, request) -> bool:
        """Check if request is an Amazon API call"""
        url = request.url.lower()
        
        # Check for API patterns
        api_indicators = [
            '/ajax/', '/api/', '/gp/', '/twister/', '/dp/ajax',
            'json', 'xhr', 'fetch'
        ]
        
        return any(indicator in url for indicator in api_indicators)
    
    def _contains_variant_data(self, url: str) -> bool:
        """Check if URL contains variant-related data"""
        url_lower = url.lower()
        variant_keywords = [
            'variant', 'twister', 'color', 'size', 'storage', 'style', 'asin'
        ]
        return any(keyword in url_lower for keyword in variant_keywords)
    
    def _contains_price_data(self, url: str) -> bool:
        """Check if URL contains price-related data"""
        url_lower = url.lower()
        price_keywords = ['price', 'cost', 'offer', 'deal']
        return any(keyword in url_lower for keyword in price_keywords)
    
    def _contains_stock_data(self, url: str) -> bool:
        """Check if URL contains stock-related data"""
        url_lower = url.lower()
        stock_keywords = ['stock', 'availability', 'inventory', 'quantity']
        return any(keyword in url_lower for keyword in stock_keywords)
    
    def _extract_request_params(self, request) -> Dict[str, Any]:
        """Extract parameters from request"""
        params = {}
        
        try:
            # Extract URL parameters
            parsed_url = urlparse(request.url)
            url_params = parse_qs(parsed_url.query)
            params.update({k: v[0] if len(v) == 1 else v for k, v in url_params.items()})
            
            # Extract POST data if available
            if request.method == 'POST' and request.post_data:
                # Try to parse as JSON
                try:
                    post_data = json.loads(request.post_data)
                    params.update(post_data)
                except:
                    # Try to parse as form data
                    post_params = parse_qs(request.post_data)
                    params.update({k: v[0] if len(v) == 1 else v for k, v in post_params.items()})
        
        except Exception as e:
            logger.debug(f"Parameter extraction error: {e}")
        
        return params
    
    async def _extract_session_tokens(self):
        """Extract Amazon session tokens from page"""
        try:
            # Extract CSRF token
            csrf_token = await self.page.evaluate("""
                () => {
                    const meta = document.querySelector('meta[name="csrf-token"]');
                    return meta ? meta.getAttribute('content') : null;
                }
            """)
            
            if csrf_token:
                self.session_tokens['csrf_token'] = csrf_token
            
            # Extract session ID
            session_id = await self.page.evaluate("""
                () => {
                    const cookies = document.cookie.split(';');
                    for (let cookie of cookies) {
                        const [name, value] = cookie.trim().split('=');
                        if (name === 'session-id') {
                            return value;
                        }
                    }
                    return null;
                }
            """)
            
            if session_id:
                self.session_tokens['session_id'] = session_id
            
            # Extract other tokens from JavaScript variables
            tokens = await self.page.evaluate("""
                () => {
                    const tokens = {};
                    
                    // Common Amazon token patterns
                    if (window.ue_token) tokens.ue_token = window.ue_token;
                    if (window.csrfToken) tokens.csrfToken = window.csrfToken;
                    if (window.sessionId) tokens.sessionId = window.sessionId;
                    
                    return tokens;
                }
            """)
            
            self.session_tokens.update(tokens)
            
            logger.info(f"🔑 Extracted {len(self.session_tokens)} session tokens")
            
        except Exception as e:
            logger.error(f"❌ Token extraction failed: {e}")
    
    async def _trigger_variant_requests(self):
        """Trigger variant-related API requests by interacting with page"""
        try:
            # Find and interact with variant elements
            variant_selectors = [
                '#variation_color_name .a-button',
                '#variation_storage_name .a-button',
                '#variation_style_name .a-button',
                '#variation_ads_name .a-button'
            ]
            
            for selector in variant_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        # Click first element to trigger API calls
                        await elements[0].click()
                        await asyncio.sleep(1.0)  # Wait for API calls
                        logger.debug(f"🖱️ Triggered API calls with: {selector}")
                except Exception as e:
                    logger.debug(f"Interaction failed: {selector} - {e}")
                    continue
            
        except Exception as e:
            logger.error(f"❌ Failed to trigger variant requests: {e}")
    
    def _is_variant_api(self, api: AmazonAPIEndpoint) -> bool:
        """Check if API endpoint is variant-related"""
        return api.variant_data or any(
            re.search(pattern, api.url) for pattern in self.api_patterns['variant_apis']
        )
    
    async def call_variant_api(self, api: AmazonAPIEndpoint, asin: str, variant_params: Dict) -> Optional[Dict]:
        """Call Amazon variant API with proper authentication"""
        if not self.session:
            await self.initialize_session()
        
        try:
            # Prepare headers with session tokens
            headers = self.amazon_headers.copy()
            headers.update(api.headers)
            
            if 'csrf_token' in self.session_tokens:
                headers['X-CSRF-Token'] = self.session_tokens['csrf_token']
            
            # Prepare parameters
            params = api.params.copy()
            params.update(variant_params)
            params['asin'] = asin
            
            # Make API call
            if api.method.upper() == 'GET':
                async with self.session.get(api.url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.debug(f"✅ API call successful: {api.url[:50]}...")
                        return data
            else:
                async with self.session.post(api.url, json=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.debug(f"✅ API call successful: {api.url[:50]}...")
                        return data
            
            logger.warning(f"⚠️ API call failed: {response.status}")
            return None
            
        except Exception as e:
            logger.error(f"❌ API call failed: {e}")
            return None
    
    async def extract_variant_data_from_api(self, api_response: Dict) -> List[Dict]:
        """Extract variant data from API response"""
        variants = []
        
        try:
            # Common Amazon API response patterns
            if 'variants' in api_response:
                variants.extend(self._parse_variants_array(api_response['variants']))
            
            if 'twisterData' in api_response:
                variants.extend(self._parse_twister_data(api_response['twisterData']))
            
            if 'dimensionValuesDisplayData' in api_response:
                variants.extend(self._parse_dimension_data(api_response['dimensionValuesDisplayData']))
            
            # Look for nested variant data
            for key, value in api_response.items():
                if isinstance(value, dict) and ('asin' in value or 'price' in value):
                    variant_data = self._extract_single_variant(value)
                    if variant_data:
                        variants.append(variant_data)
            
            logger.info(f"📊 Extracted {len(variants)} variants from API response")
            return variants
            
        except Exception as e:
            logger.error(f"❌ API data extraction failed: {e}")
            return []
    
    def _parse_variants_array(self, variants_data: List[Dict]) -> List[Dict]:
        """Parse variants array from API response"""
        parsed_variants = []
        
        for variant in variants_data:
            parsed_variant = {
                'asin': variant.get('asin'),
                'price': self._extract_price_from_api(variant),
                'availability': variant.get('availability', 'Unknown'),
                'attributes': {}
            }
            
            # Extract variant attributes
            for key, value in variant.items():
                if key in ['color', 'size', 'storage', 'style']:
                    parsed_variant['attributes'][key] = value
            
            parsed_variants.append(parsed_variant)
        
        return parsed_variants
    
    def _parse_twister_data(self, twister_data: Dict) -> List[Dict]:
        """Parse Amazon twister data (variant combinations)"""
        variants = []
        
        try:
            if 'colorImages' in twister_data:
                for color, data in twister_data['colorImages'].items():
                    variant = {
                        'attributes': {'color': color},
                        'images': data.get('hiRes', []),
                        'asin': data.get('asin')
                    }
                    variants.append(variant)
            
            if 'dimensionValuesDisplayData' in twister_data:
                dimension_data = twister_data['dimensionValuesDisplayData']
                for dimension, values in dimension_data.items():
                    for value_key, value_data in values.items():
                        variant = {
                            'attributes': {dimension: value_data.get('displayValue', value_key)},
                            'asin': value_data.get('asin'),
                            'price': self._extract_price_from_api(value_data)
                        }
                        variants.append(variant)
        
        except Exception as e:
            logger.error(f"❌ Twister data parsing failed: {e}")
        
        return variants
    
    def _parse_dimension_data(self, dimension_data: Dict) -> List[Dict]:
        """Parse dimension values display data"""
        variants = []
        
        try:
            for dimension, values in dimension_data.items():
                for value_key, value_data in values.items():
                    variant = {
                        'attributes': {dimension: value_data.get('displayValue', value_key)},
                        'asin': value_data.get('asin'),
                        'price': self._extract_price_from_api(value_data),
                        'availability': value_data.get('availability', 'Unknown')
                    }
                    variants.append(variant)
        
        except Exception as e:
            logger.error(f"❌ Dimension data parsing failed: {e}")
        
        return variants
    
    def _extract_single_variant(self, variant_data: Dict) -> Optional[Dict]:
        """Extract single variant from API data"""
        try:
            variant = {
                'asin': variant_data.get('asin'),
                'price': self._extract_price_from_api(variant_data),
                'availability': variant_data.get('availability', 'Unknown'),
                'attributes': {}
            }
            
            # Extract attributes
            attribute_keys = ['color', 'size', 'storage', 'style', 'pattern', 'material']
            for key in attribute_keys:
                if key in variant_data:
                    variant['attributes'][key] = variant_data[key]
            
            return variant if variant['asin'] else None
            
        except Exception as e:
            logger.debug(f"Single variant extraction failed: {e}")
            return None
    
    def _extract_price_from_api(self, data: Dict) -> Optional[float]:
        """Extract price from API data"""
        try:
            # Common price fields in Amazon APIs
            price_fields = [
                'price', 'listPrice', 'salePrice', 'displayPrice',
                'priceToPayDisplayValue', 'pricePerUnit'
            ]
            
            for field in price_fields:
                if field in data:
                    price_value = data[field]
                    
                    # Handle different price formats
                    if isinstance(price_value, (int, float)):
                        return float(price_value)
                    elif isinstance(price_value, str):
                        # Parse price string
                        price_match = re.search(r'[\d,]+\.?\d*', price_value.replace(',', ''))
                        if price_match:
                            return float(price_match.group().replace(',', ''))
                    elif isinstance(price_value, dict):
                        # Handle nested price objects
                        if 'value' in price_value:
                            return float(price_value['value'])
                        if 'amount' in price_value:
                            return float(price_value['amount'])
            
            return None
            
        except Exception as e:
            logger.debug(f"Price extraction failed: {e}")
            return None
    
    async def cleanup(self):
        """Clean up session resources"""
        if self.session:
            await self.session.close()
            logger.info("✅ API session cleaned up")

class AmazonNetworkAnalyzer:
    """
    Advanced network traffic analysis for Amazon pages
    Identifies patterns and extracts variant data from network requests
    """
    
    def __init__(self, page):
        self.page = page
        self.network_requests = []
        self.api_responses = []
    
    async def start_monitoring(self):
        """Start monitoring network traffic"""
        await self.page.route("**/*", self._capture_request)
        self.page.on("response", self._capture_response)
        logger.info("🔍 Network monitoring started")
    
    async def _capture_request(self, route):
        """Capture network requests"""
        request = route.request
        
        # Store request information
        request_info = {
            'url': request.url,
            'method': request.method,
            'headers': dict(request.headers),
            'post_data': request.post_data,
            'timestamp': asyncio.get_event_loop().time()
        }
        
        self.network_requests.append(request_info)
        
        # Continue with the request
        await route.continue_()
    
    async def _capture_response(self, response):
        """Capture network responses"""
        try:
            if response.request.url.endswith(('.json', '.ajax')) or 'json' in response.headers.get('content-type', ''):
                response_data = {
                    'url': response.url,
                    'status': response.status,
                    'headers': dict(response.headers),
                    'body': await response.text(),
                    'timestamp': asyncio.get_event_loop().time()
                }
                
                self.api_responses.append(response_data)
        
        except Exception as e:
            logger.debug(f"Response capture failed: {e}")
    
    def analyze_variant_patterns(self) -> Dict[str, Any]:
        """Analyze network traffic for variant patterns"""
        analysis = {
            'variant_requests': [],
            'price_requests': [],
            'stock_requests': [],
            'patterns': {}
        }
        
        # Analyze requests
        for request in self.network_requests:
            url_lower = request['url'].lower()
            
            if any(pattern in url_lower for pattern in ['variant', 'twister', 'color', 'size']):
                analysis['variant_requests'].append(request)
            
            if any(pattern in url_lower for pattern in ['price', 'cost', 'offer']):
                analysis['price_requests'].append(request)
            
            if any(pattern in url_lower for pattern in ['stock', 'availability', 'inventory']):
                analysis['stock_requests'].append(request)
        
        # Analyze responses
        for response in self.api_responses:
            try:
                response_json = json.loads(response['body'])
                
                # Look for variant data patterns
                if self._contains_variant_data(response_json):
                    analysis['patterns']['variant_response'] = {
                        'url': response['url'],
                        'structure': self._analyze_json_structure(response_json)
                    }
            
            except json.JSONDecodeError:
                continue
        
        logger.info(f"📊 Network analysis: {len(analysis['variant_requests'])} variant requests found")
        return analysis
    
    def _contains_variant_data(self, data: Dict) -> bool:
        """Check if JSON data contains variant information"""
        if isinstance(data, dict):
            variant_keys = ['variants', 'twisterData', 'colorImages', 'dimensionValuesDisplayData', 'asin']
            return any(key in data for key in variant_keys)
        return False
    
    def _analyze_json_structure(self, data: Dict, max_depth: int = 3) -> Dict:
        """Analyze JSON structure to understand data format"""
        if max_depth <= 0:
            return {"type": type(data).__name__}
        
        if isinstance(data, dict):
            structure = {"type": "dict", "keys": {}}
            for key, value in list(data.items())[:10]:  # Limit to first 10 keys
                structure["keys"][key] = self._analyze_json_structure(value, max_depth - 1)
            return structure
        
        elif isinstance(data, list):
            structure = {"type": "list", "length": len(data)}
            if data:
                structure["item_structure"] = self._analyze_json_structure(data[0], max_depth - 1)
            return structure
        
        else:
            return {"type": type(data).__name__, "sample": str(data)[:100]}

# Integration example
async def integrate_api_intelligence(professional_extractor, product_url: str):
    """Integrate API intelligence with professional extractor"""
    
    # Initialize API intelligence
    api_intel = AmazonAPIIntelligence(professional_extractor.page)
    network_analyzer = AmazonNetworkAnalyzer(professional_extractor.page)
    
    try:
        # Navigate to product page
        await professional_extractor._navigate_professionally(product_url)
        
        # Start network monitoring
        await network_analyzer.start_monitoring()
        
        # Discover APIs
        variant_apis = await api_intel.discover_variant_apis()
        
        # Analyze network patterns
        network_analysis = network_analyzer.analyze_variant_patterns()
        
        # Use discovered APIs to enhance variant extraction
        enhanced_variants = []
        
        for api in variant_apis:
            if api.variant_data:
                # Extract ASIN from current page
                asin = await professional_extractor._extract_current_asin()
                if asin:
                    # Call API for variant data
                    api_response = await api_intel.call_variant_api(api, asin, {})
                    if api_response:
                        api_variants = await api_intel.extract_variant_data_from_api(api_response)
                        enhanced_variants.extend(api_variants)
        
        logger.info(f"🚀 API Intelligence: Enhanced with {len(enhanced_variants)} API-sourced variants")
        return enhanced_variants, network_analysis
        
    finally:
        await api_intel.cleanup()

if __name__ == "__main__":
    print("🔬 Amazon API Intelligence Module")
    print("This module provides API reverse engineering capabilities")
    print("Use with professional_variant_extractor.py for enhanced accuracy")
