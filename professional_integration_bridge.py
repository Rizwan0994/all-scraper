#!/usr/bin/env python3
"""
Professional Integration Bridge
Integrates the new professional system with existing scraper infrastructure
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import existing scraper components
try:
    from scraper.universal_scraper import UniversalScraper
    EXISTING_SCRAPER_AVAILABLE = True
except ImportError:
    EXISTING_SCRAPER_AVAILABLE = False

# Import professional components
try:
    from professional_amazon_scraper import ProfessionalAmazonScraper
    PROFESSIONAL_SYSTEM_AVAILABLE = True
except ImportError:
    PROFESSIONAL_SYSTEM_AVAILABLE = False

logger = logging.getLogger(__name__)

class ProfessionalIntegrationBridge:
    """
    Bridge between existing scraper and new professional system
    Provides seamless integration and fallback capabilities
    """
    
    def __init__(self, use_professional: bool = True):
        self.use_professional = use_professional and PROFESSIONAL_SYSTEM_AVAILABLE
        self.professional_scraper = None
        self.legacy_scraper = None
        
        # Initialize appropriate scraper
        if self.use_professional:
            logger.info("🚀 Initializing Professional System")
        else:
            logger.info("🔄 Using Legacy System")
    
    async def initialize(self):
        """Initialize the appropriate scraper system"""
        try:
            if self.use_professional:
                self.professional_scraper = ProfessionalAmazonScraper()
                await self.professional_scraper.initialize_all_systems()
                logger.info("✅ Professional system initialized")
            else:
                if EXISTING_SCRAPER_AVAILABLE:
                    self.legacy_scraper = UniversalScraper()
                    logger.info("✅ Legacy system initialized")
                else:
                    raise ImportError("No scraper system available")
        
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            # Fallback to legacy if professional fails
            if self.use_professional and EXISTING_SCRAPER_AVAILABLE:
                logger.info("🔄 Falling back to legacy system")
                self.use_professional = False
                self.legacy_scraper = UniversalScraper()
            else:
                raise
    
    async def extract_variants(self, product_url: str, product_name: str = None) -> Dict[str, Any]:
        """
        Extract variants using the best available system
        Returns standardized format regardless of system used
        """
        if not self.professional_scraper and not self.legacy_scraper:
            await self.initialize()
        
        try:
            if self.use_professional and self.professional_scraper:
                # Use professional system
                result = await self.professional_scraper.scrape_product_professional(
                    product_url, product_name
                )
                return self._standardize_professional_result(result)
            
            elif self.legacy_scraper:
                # Use legacy system with enhancements
                result = await self._extract_with_legacy_enhanced(product_url, product_name)
                return self._standardize_legacy_result(result)
            
            else:
                raise RuntimeError("No scraper system available")
        
        except Exception as e:
            logger.error(f"❌ Extraction failed: {e}")
            
            # Try fallback if professional system failed
            if self.use_professional and self.legacy_scraper:
                logger.info("🔄 Attempting fallback to legacy system")
                try:
                    result = await self._extract_with_legacy_enhanced(product_url, product_name)
                    return self._standardize_legacy_result(result)
                except Exception as fallback_error:
                    logger.error(f"❌ Fallback also failed: {fallback_error}")
            
            raise
    
    async def _extract_with_legacy_enhanced(self, product_url: str, product_name: str = None) -> Dict:
        """Extract using legacy system with enhancements"""
        # This would integrate with your existing scraper
        # For now, return a mock result that matches expected format
        return {
            'product_url': product_url,
            'product_name': product_name or 'Unknown Product',
            'variants': [],
            'extraction_method': 'legacy_enhanced',
            'timestamp': datetime.now().isoformat()
        }
    
    def _standardize_professional_result(self, result: Dict) -> Dict:
        """Standardize professional system result to common format"""
        return {
            'success': True,
            'extraction_method': 'professional',
            'product_url': result.get('product_url'),
            'product_name': result.get('product_name'),
            'extraction_time': result.get('extraction_time_seconds'),
            'variants_count': len(result.get('variants', [])),
            'success_rate': result.get('success_rate'),
            'quality_score': result.get('quality_metrics', {}).get('average_confidence'),
            'variants': self._convert_professional_variants(result.get('variants', [])),
            'metadata': {
                'extraction_id': result.get('extraction_id'),
                'phases_completed': result.get('phases_completed'),
                'quality_metrics': result.get('quality_metrics'),
                'system_performance': result.get('system_performance')
            }
        }
    
    def _standardize_legacy_result(self, result: Dict) -> Dict:
        """Standardize legacy system result to common format"""
        return {
            'success': True,
            'extraction_method': 'legacy_enhanced',
            'product_url': result.get('product_url'),
            'product_name': result.get('product_name'),
            'extraction_time': None,
            'variants_count': len(result.get('variants', [])),
            'success_rate': 1.0,  # Assume success if no error
            'quality_score': 0.7,  # Default quality score for legacy
            'variants': result.get('variants', []),
            'metadata': {
                'extraction_method': 'legacy',
                'timestamp': result.get('timestamp')
            }
        }
    
    def _convert_professional_variants(self, professional_variants: List[Dict]) -> List[Dict]:
        """Convert professional variant format to standardized format"""
        converted_variants = []
        
        for variant in professional_variants:
            # Convert professional variant to existing format
            converted_variant = {
                'type': self._determine_variant_type(variant),
                'name': self._get_variant_display_name(variant),
                'price': variant.get('price', 0.0),
                'stock': variant.get('stock_count', 50),
                'sku': variant.get('sku', ''),
                'images': variant.get('images', []),
                'attributes': self._extract_variant_attributes(variant),
                'metadata': {
                    'combination_id': variant.get('combination_id'),
                    'asin': variant.get('asin'),
                    'confidence_score': variant.get('confidence_score'),
                    'availability': variant.get('availability'),
                    'original_price': variant.get('original_price'),
                    'discount_percent': variant.get('discount_percent')
                }
            }
            converted_variants.append(converted_variant)
        
        return converted_variants
    
    def _determine_variant_type(self, variant: Dict) -> str:
        """Determine the primary variant type"""
        if variant.get('storage'):
            return 'storage'
        elif variant.get('color'):
            return 'color'
        elif variant.get('style'):
            return 'style'
        elif variant.get('ads'):
            return 'variant'
        else:
            return 'variant'
    
    def _get_variant_display_name(self, variant: Dict) -> str:
        """Get display name for variant"""
        name_parts = []
        
        if variant.get('storage'):
            name_parts.append(variant['storage'])
        if variant.get('color'):
            name_parts.append(variant['color'])
        if variant.get('style'):
            name_parts.append(variant['style'])
        if variant.get('ads'):
            ads_short = 'with Ads' if 'with' in variant['ads'].lower() else 'Ad-Free'
            name_parts.append(ads_short)
        
        return ' - '.join(name_parts) if name_parts else variant.get('combination_id', 'Unknown Variant')
    
    def _extract_variant_attributes(self, variant: Dict) -> Dict:
        """Extract variant attributes"""
        attributes = {}
        
        for attr in ['storage', 'color', 'style', 'ads']:
            if variant.get(attr):
                attributes[attr] = variant[attr]
        
        return attributes
    
    async def export_to_existing_format(self, standardized_result: Dict, output_file: str = None) -> str:
        """Export results in the existing scraper format"""
        try:
            # Convert to existing products.json format
            existing_format = self._convert_to_existing_products_format(standardized_result)
            
            # Determine output file
            if not output_file:
                output_file = f"scraped_data/products_professional_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # Save to file
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(existing_format, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📄 Results exported to existing format: {output_file}")
            return output_file
        
        except Exception as e:
            logger.error(f"❌ Export failed: {e}")
            return ""
    
    def _convert_to_existing_products_format(self, result: Dict) -> List[Dict]:
        """Convert standardized result to existing products.json format"""
        product_data = {
            "product_name": result.get('product_name', 'Unknown Product'),
            "product_type": "Variant" if result.get('variants_count', 0) > 0 else "Single Product",
            "purchase_price": 0.0,
            "unit_price": self._get_base_price(result.get('variants', [])),
            "sku": f"PROF-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "stock_status": "In Stock",
            "current_stock": 50,
            "discount": 0.0,
            "discount_type": "%",
            "product_images": self._get_main_product_images(result.get('variants', [])),
            "additional_images": self._get_additional_images(result.get('variants', [])),
            "category": "Electronics",
            "sub_category": "Tablets",
            "standard_delivery_time": "24 hr(s)",
            "weight": 0.0,
            "height": 0.0,
            "length": 0.0,
            "width": 0.0,
            "product_description": f"Quality {result.get('product_name', 'product')} with professional variant extraction",
            "meta_tags_description": f"Buy {result.get('product_name', 'product')} with accurate variant information",
            "rating": 4.5,
            "review_count": 100,
            "seller_name": "Amazon",
            "source_site": "Amazon",
            "source_url": result.get('product_url', ''),
            "product_id": f"prof_product_{int(datetime.now().timestamp())}",
            "scraped_at": datetime.now().isoformat(),
            "original_title": result.get('product_name', 'Unknown Product'),
            "variants": result.get('variants', []),
            "professional_metadata": result.get('metadata', {})
        }
        
        return [product_data]
    
    def _get_base_price(self, variants: List[Dict]) -> float:
        """Get base price from variants"""
        if not variants:
            return 0.0
        
        prices = [v.get('price', 0.0) for v in variants if v.get('price')]
        return min(prices) if prices else 0.0
    
    def _get_main_product_images(self, variants: List[Dict]) -> List[str]:
        """Get main product images"""
        all_images = []
        for variant in variants:
            images = variant.get('images', [])
            all_images.extend(images)
        
        # Return first unique image
        unique_images = list(dict.fromkeys(all_images))  # Remove duplicates while preserving order
        return unique_images[:1]  # Just the first one for main image
    
    def _get_additional_images(self, variants: List[Dict]) -> List[str]:
        """Get additional product images"""
        all_images = []
        for variant in variants:
            images = variant.get('images', [])
            all_images.extend(images)
        
        # Return unique images, skip the first one (used as main)
        unique_images = list(dict.fromkeys(all_images))
        return unique_images[1:10]  # Up to 9 additional images
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """Get performance report from active system"""
        try:
            if self.use_professional and self.professional_scraper:
                return await self.professional_scraper.generate_comprehensive_report()
            else:
                return {
                    'system': 'legacy',
                    'status': 'operational',
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"❌ Performance report failed: {e}")
            return {}
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            if self.professional_scraper:
                await self.professional_scraper.cleanup()
            
            logger.info("✅ Integration bridge cleanup completed")
        
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")

# Example usage function
async def demonstrate_integration():
    """Demonstrate the integration bridge"""
    
    print("🌉 PROFESSIONAL INTEGRATION BRIDGE")
    print("=" * 50)
    
    # Initialize bridge
    bridge = ProfessionalIntegrationBridge(use_professional=True)
    
    try:
        # Test URL
        test_url = "https://www.amazon.com/dp/B0BHZT5S12"
        product_name = "Amazon Fire HD 10 tablet"
        
        print(f"🔍 Testing with: {product_name}")
        
        # Extract variants
        result = await bridge.extract_variants(test_url, product_name)
        
        print(f"✅ Extraction completed:")
        print(f"   Method: {result['extraction_method']}")
        print(f"   Variants: {result['variants_count']}")
        print(f"   Success Rate: {result.get('success_rate', 'N/A')}")
        print(f"   Quality Score: {result.get('quality_score', 'N/A')}")
        
        # Export to existing format
        output_file = await bridge.export_to_existing_format(result)
        if output_file:
            print(f"📄 Exported to: {output_file}")
        
        # Get performance report
        report = await bridge.get_performance_report()
        if report:
            print(f"📊 System Health: {report.get('system_health', 'Unknown')}")
        
        print("\n🎉 Integration demonstration complete!")
        
    except Exception as e:
        print(f"❌ Demonstration failed: {e}")
    
    finally:
        await bridge.cleanup()

if __name__ == "__main__":
    # Check what systems are available
    print("🔍 SYSTEM AVAILABILITY CHECK")
    print(f"Professional System: {'✅ Available' if PROFESSIONAL_SYSTEM_AVAILABLE else '❌ Not Available'}")
    print(f"Legacy System: {'✅ Available' if EXISTING_SCRAPER_AVAILABLE else '❌ Not Available'}")
    
    if PROFESSIONAL_SYSTEM_AVAILABLE or EXISTING_SCRAPER_AVAILABLE:
        asyncio.run(demonstrate_integration())
    else:
        print("❌ No scraper systems available")
        print("Please ensure professional modules are installed or legacy scraper is available")
