#!/usr/bin/env python3
"""
AI-Powered Variant Classifier using Ollama
Distinguishes between real selectable variants vs technical features
"""

import json
import requests
import logging
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class VariantClassification:
    """Result of variant classification"""
    is_real_variant: bool
    variant_type: str  # 'color', 'size', 'storage', 'material', 'style'
    confidence: float  # 0.0 to 1.0
    reasoning: str

class OllamaVariantClassifier:
    """
    AI-powered variant classifier using Ollama llama3.2:3b
    Runs locally on RTX 50 GPU for maximum speed
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model = "llama3.2:3b"
        self.classification_cache = {}  # Cache results for speed
        
        # Test connection
        self._test_ollama_connection()
        
        logger.info("🤖 Ollama AI Variant Classifier initialized")
    
    def _test_ollama_connection(self):
        """Test if Ollama is running and accessible"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Ollama connection successful")
            else:
                logger.error("❌ Ollama connection failed")
        except Exception as e:
            logger.error(f"❌ Cannot connect to Ollama: {e}")
            raise ConnectionError("Ollama is not running. Please start it with: ollama serve")
    
    def classify_variant(self, variant_text: str, product_context: str, product_category: str = None) -> VariantClassification:
        """
        Classify if a variant text represents a real selectable variant
        
        Args:
            variant_text: The variant text to classify (e.g., "Black", "Hybrid ANC Technology")
            product_context: Product name/description for context
            product_category: Product category (Electronics, Fashion, etc.)
        
        Returns:
            VariantClassification with results
        """
        # Check cache first for speed
        cache_key = f"{variant_text}_{product_context}"
        if cache_key in self.classification_cache:
            return self.classification_cache[cache_key]
        
        # Use rule-based classification as primary method (more reliable)
        try:
            result = self._fallback_classification(variant_text, product_context)
            
            # Cache result
            self.classification_cache[cache_key] = result
            
            logger.info(f"🎯 Rule-based Classification: '{variant_text}' -> {result.variant_type} (confidence: {result.confidence:.2f})")
            
            return result
            
        except Exception as e:
            logger.error(f"Rule-based classification failed: {e}")
            # Final fallback
            return VariantClassification(
                is_real_variant=False,
                variant_type="none",
                confidence=0.0,
                reasoning="Classification failed"
            )
    
    def _create_classification_prompt(self, variant_text: str, product_context: str, product_category: str = None) -> str:
        """Create optimized prompt for variant classification"""
        
        prompt = f"""Is "{variant_text}" a selectable product variant?

Examples of selectable variants: Black, White, Red, Blue, Small, Large, 64GB, 128GB, Cotton, Leather
Examples of technical features: Hybrid ANC, Bluetooth, Wireless, Fast Charging, Battery Life

Answer in this exact format:
is_real_variant: true/false
variant_type: color/size/storage/material/none
confidence: 0.0-1.0
reasoning: explanation"""

        return prompt
    
    def _get_ai_classification(self, prompt: str) -> str:
        """Get classification from Ollama AI"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Low temperature for consistent results
                    "top_p": 0.9,
                    "max_tokens": 200
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return ""
                
        except Exception as e:
            logger.error(f"Ollama API request failed: {e}")
            return ""
    
    def _parse_classification_response(self, ai_response: str, variant_text: str) -> VariantClassification:
        """Parse AI response into VariantClassification object"""
        try:
            # Clean response
            cleaned_response = ai_response.strip()
            logger.debug(f"AI Response: {cleaned_response}")
            
            # Try to parse key-value format first
            is_real = False
            variant_type = "none"
            confidence = 0.0
            reasoning = ""
            
            # Parse key-value format
            lines = cleaned_response.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('is_real_variant:'):
                    value = line.split(':', 1)[1].strip()
                    is_real = value.lower() in ['true', 'yes', '1']
                elif line.startswith('variant_type:'):
                    variant_type = line.split(':', 1)[1].strip().lower()
                elif line.startswith('confidence:'):
                    try:
                        confidence = float(line.split(':', 1)[1].strip())
                    except:
                        confidence = 0.0
                elif line.startswith('reasoning:'):
                    reasoning = line.split(':', 1)[1].strip()
            
            # If we got valid data, return it
            if reasoning:  # If we found reasoning, we likely parsed the format correctly
                return VariantClassification(
                    is_real_variant=is_real,
                    variant_type=variant_type,
                    confidence=confidence,
                    reasoning=reasoning
                )
            
            # Fallback: Try to find JSON object
            json_match = re.search(r'\{[^}]*\}', cleaned_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                logger.debug(f"Found JSON in response: {json_str}")
                
                try:
                    data = json.loads(json_str)
                    
                    # Validate and convert data
                    is_real = data.get("is_real_variant", False)
                    if isinstance(is_real, str):
                        is_real = is_real.lower() in ['true', 'yes', '1']
                    
                    variant_type = str(data.get("variant_type", "none")).lower()
                    confidence = float(data.get("confidence", 0.0))
                    reasoning = str(data.get("reasoning", ""))
                    
                    return VariantClassification(
                        is_real_variant=is_real,
                        variant_type=variant_type,
                        confidence=confidence,
                        reasoning=reasoning
                    )
                except json.JSONDecodeError as e:
                    logger.debug(f"JSON decode error: {e}, trying fallback parsing")
                    return self._parse_fallback_response(cleaned_response, variant_text)
            else:
                # Fallback parsing if no format found
                return self._parse_fallback_response(cleaned_response, variant_text)
                
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            return self._fallback_classification(variant_text, "")
    
    def _parse_fallback_response(self, ai_response: str, variant_text: str) -> VariantClassification:
        """Fallback parsing if JSON parsing fails"""
        response_lower = ai_response.lower()
        
        # Check for positive indicators
        is_real = any(word in response_lower for word in ["true", "real", "selectable", "yes", "variant"])
        
        # Determine variant type from response
        variant_type = "none"
        if "color" in response_lower:
            variant_type = "color"
        elif "size" in response_lower:
            variant_type = "size"
        elif "storage" in response_lower:
            variant_type = "storage"
        elif "material" in response_lower:
            variant_type = "material"
        
        # If no clear type but marked as real, try to infer from variant text
        if is_real and variant_type == "none":
            variant_lower = variant_text.lower()
            if any(color in variant_lower for color in ["black", "white", "red", "blue", "green", "pink", "silver", "gold"]):
                variant_type = "color"
            elif any(size in variant_lower for size in ["small", "medium", "large", "xs", "s", "m", "l", "xl"]):
                variant_type = "size"
            elif any(storage in variant_lower for storage in ["gb", "tb"]):
                variant_type = "storage"
        
        return VariantClassification(
            is_real_variant=is_real,
            variant_type=variant_type,
            confidence=0.6 if is_real else 0.4,
            reasoning="Fallback parsing"
        )
    
    def _fallback_classification(self, variant_text: str, product_context: str) -> VariantClassification:
        """Enhanced rule-based classification - more reliable than AI"""
        
        variant_lower = variant_text.lower().strip()
        
        # Enhanced real variant patterns with more comprehensive matching
        real_patterns = {
            'color': [
                # Basic colors
                r'\b(black|white|red|blue|green|yellow|pink|purple|orange|brown|gray|grey|silver|gold|rose|navy|teal|maroon|beige|cream|tan|burgundy|turquoise|magenta|cyan|lime|indigo|violet)\b',
                # Color variations
                r'\b(dark|light|bright|pale|deep|vivid|muted|soft|bold|neon)\s+(black|white|red|blue|green|yellow|pink|purple|orange|brown|gray|grey|silver|gold|rose|navy|teal|maroon|beige|cream|tan|burgundy|turquoise|magenta|cyan|lime|indigo|violet)\b',
                # Specific color names
                r'\b(midnight|charcoal|ivory|pearl|ruby|sapphire|emerald|amber|coral|lavender|mint|peach|salmon|crimson|forest|sky|royal|electric|neon)\b'
            ],
            'size': [
                # Standard sizes
                r'\b(xs|s|m|l|xl|xxl|xxxl|small|medium|large|extra large|tiny|mini|regular|big|huge|petite|plus)\b',
                # Size variations
                r'\b(extra small|extra large|extra extra large|small medium|large medium|small large|medium large)\b',
                # Numeric sizes
                r'\b\d+\s*(inch|inches|cm|mm|oz|pounds?|lbs?|kg|grams?|g)\b'
            ],
            'storage': [
                # Storage capacities
                r'\b(16gb|32gb|64gb|128gb|256gb|512gb|1tb|2tb|4tb|8tb|8gb|4gb|2gb|1gb|32mb|64mb|128mb|256mb|512mb)\b',
                # Storage variations
                r'\b(\d+\s*gb|\d+\s*tb|\d+\s*mb|\d+\s*gb\s*ssd|\d+\s*tb\s*hdd|\d+\s*gb\s*ram|\d+\s*tb\s*storage)\b'
            ],
            'material': [
                # Common materials
                r'\b(cotton|leather|plastic|metal|wood|glass|ceramic|fabric|silk|wool|denim|canvas|polyester|nylon|spandex|lycra|bamboo|hemp|linen|cashmere|alpaca|suede|vinyl|rubber|foam|foam|memory foam|latex|gel|waterproof|breathable)\b',
                # Material combinations
                r'\b(cotton blend|cotton polyester|leather trim|metal frame|wood handle|glass surface|ceramic coating|fabric lining|silk lining|wool blend)\b'
            ]
        }
        
        # Enhanced fake variant patterns (technical features)
        fake_patterns = [
            # Technology terms
            r'\b(technology|anc|bluetooth|wireless|active|noise|cancelling|hybrid|fast|quick|instant|premium|ultra|high|performance|advanced|intelligent|smart|digital|cloud|enabled|enhanced|optimized)\b',
            # Time/performance specs
            r'\b(playtime|battery|life|hours|minutes|charging|connect|sync|pair|range|distance|speed|power|energy|efficiency|capacity|duration|runtime)\b',
            # Feature descriptions
            r'\b(waterproof|water resistant|shockproof|dustproof|scratch resistant|anti glare|anti fingerprint|anti bacterial|anti microbial|hypoallergenic|organic|natural|eco friendly|sustainable|recyclable)\b',
            # Quality descriptors
            r'\b(premium|professional|commercial|industrial|heavy duty|lightweight|portable|compact|foldable|adjustable|removable|detachable|reversible|dual|multi|single|triple|quad)\b'
        ]
        
        # Check for fake patterns first (higher priority)
        for pattern in fake_patterns:
            if re.search(pattern, variant_lower):
                return VariantClassification(
                    is_real_variant=False,
                    variant_type="none",
                    confidence=0.95,
                    reasoning=f"Technical feature detected: {pattern}"
                )
        
        # Check for real variant patterns
        for variant_type, patterns in real_patterns.items():
            for pattern in patterns:
                if re.search(pattern, variant_lower):
                    return VariantClassification(
                        is_real_variant=True,
                        variant_type=variant_type,
                        confidence=0.9,
                        reasoning=f"Real {variant_type} variant detected"
                    )
        
        # Additional checks for edge cases
        # Check if it's a simple color word
        if variant_lower in ['black', 'white', 'red', 'blue', 'green', 'yellow', 'pink', 'purple', 'orange', 'brown', 'gray', 'grey', 'silver', 'gold']:
            return VariantClassification(
                is_real_variant=True,
                variant_type="color",
                confidence=0.95,
                reasoning="Simple color word"
            )
        
        # Check if it's a simple size word
        if variant_lower in ['small', 'medium', 'large', 'xs', 's', 'm', 'l', 'xl', 'xxl']:
            return VariantClassification(
                is_real_variant=True,
                variant_type="size",
                confidence=0.95,
                reasoning="Simple size word"
            )
        
        # Check if it's storage capacity
        if re.search(r'\d+\s*(gb|tb|mb)', variant_lower):
            return VariantClassification(
                is_real_variant=True,
                variant_type="storage",
                confidence=0.9,
                reasoning="Storage capacity detected"
            )
        
        # Default: not a real variant
        return VariantClassification(
            is_real_variant=False,
            variant_type="none",
            confidence=0.7,
            reasoning="No clear pattern match - likely not a variant"
        )
    
    def batch_classify(self, variants: List[Dict], product_context: str, product_category: str = None) -> List[Tuple[Dict, VariantClassification]]:
        """
        Classify multiple variants in batch for efficiency
        
        Args:
            variants: List of variant dictionaries
            product_context: Product context
            product_category: Product category
        
        Returns:
            List of (variant_dict, classification) tuples
        """
        results = []
        
        for variant in variants:
            variant_text = variant.get('name', '') or variant.get('text', '')
            if variant_text:
                classification = self.classify_variant(variant_text, product_context, product_category)
                results.append((variant, classification))
            else:
                # Empty variant
                results.append((variant, VariantClassification(
                    is_real_variant=False,
                    variant_type="none",
                    confidence=0.0,
                    reasoning="Empty variant text"
                )))
        
        logger.info(f"🤖 Batch classified {len(variants)} variants")
        return results
    
    def get_statistics(self) -> Dict:
        """Get classifier statistics"""
        return {
            "cache_size": len(self.classification_cache),
            "model": self.model,
            "ollama_url": self.ollama_url
        }

# Global classifier instance
_ai_classifier = None

def get_ai_classifier() -> OllamaVariantClassifier:
    """Get global AI classifier instance"""
    global _ai_classifier
    if _ai_classifier is None:
        _ai_classifier = OllamaVariantClassifier()
    return _ai_classifier

def classify_variant_quick(variant_text: str, product_context: str) -> bool:
    """Quick classification function for simple use cases"""
    classifier = get_ai_classifier()
    result = classifier.classify_variant(variant_text, product_context)
    return result.is_real_variant and result.confidence > 0.7
