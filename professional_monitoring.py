#!/usr/bin/env python3
"""
Professional Monitoring & Quality Assurance System
Real-time monitoring, validation, and quality control for 95%+ accuracy
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import statistics
import hashlib
from pathlib import Path

# Optional dependencies for advanced monitoring
try:
    import psutil
    SYSTEM_MONITORING_AVAILABLE = True
except ImportError:
    SYSTEM_MONITORING_AVAILABLE = False

try:
    import aiofiles
    ASYNC_FILE_AVAILABLE = True
except ImportError:
    ASYNC_FILE_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class ExtractionMetrics:
    """Metrics for extraction performance"""
    timestamp: str
    product_url: str
    product_name: str
    extraction_time: float
    variants_found: int
    variants_validated: int
    success_rate: float
    confidence_scores: List[float]
    errors: List[str]
    warnings: List[str]
    data_quality_score: float
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

@dataclass
class QualityReport:
    """Quality assurance report"""
    report_id: str
    timestamp: str
    total_extractions: int
    successful_extractions: int
    overall_success_rate: float
    average_confidence: float
    average_quality_score: float
    common_errors: Dict[str, int]
    performance_metrics: Dict[str, float]
    recommendations: List[str]

class ProfessionalMonitor:
    """
    Professional monitoring system for variant extraction
    Tracks performance, quality, and provides real-time insights
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.metrics_history = []
        self.quality_thresholds = {
            'minimum_success_rate': 0.85,  # 85% minimum success rate
            'minimum_confidence': 0.70,    # 70% minimum confidence
            'minimum_quality_score': 0.75, # 75% minimum quality score
            'maximum_extraction_time': 30.0 # 30 seconds max
        }
        
        # Performance tracking
        self.performance_stats = {
            'total_extractions': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'total_variants_found': 0,
            'total_extraction_time': 0.0,
            'start_time': time.time()
        }
        
        # Quality tracking
        self.quality_issues = {
            'low_confidence_variants': [],
            'invalid_prices': [],
            'missing_images': [],
            'duplicate_variants': [],
            'extraction_timeouts': []
        }
        
        # Alert system
        self.alert_handlers = []
        
        logger.info("📊 Professional Monitor initialized")
    
    async def start_extraction_monitoring(self, product_url: str, product_name: str) -> str:
        """Start monitoring an extraction process"""
        extraction_id = hashlib.md5(f"{product_url}_{time.time()}".encode()).hexdigest()[:12]
        
        logger.info(f"🔍 Starting extraction monitoring: {extraction_id}")
        logger.info(f"📍 Product: {product_name[:50]}...")
        logger.info(f"🔗 URL: {product_url}")
        
        return extraction_id
    
    async def record_extraction_metrics(self, extraction_id: str, metrics: ExtractionMetrics):
        """Record metrics for an extraction"""
        try:
            # Update performance stats
            self.performance_stats['total_extractions'] += 1
            self.performance_stats['total_variants_found'] += metrics.variants_found
            self.performance_stats['total_extraction_time'] += metrics.extraction_time
            
            if metrics.success_rate >= self.quality_thresholds['minimum_success_rate']:
                self.performance_stats['successful_extractions'] += 1
            else:
                self.performance_stats['failed_extractions'] += 1
            
            # Store metrics
            self.metrics_history.append(metrics)
            
            # Check quality thresholds
            await self._check_quality_thresholds(metrics)
            
            # Log metrics
            logger.info(f"📊 Extraction {extraction_id} completed:")
            logger.info(f"   ⏱️ Time: {metrics.extraction_time:.2f}s")
            logger.info(f"   🎯 Variants: {metrics.variants_found} found, {metrics.variants_validated} validated")
            logger.info(f"   ✅ Success Rate: {metrics.success_rate:.1%}")
            logger.info(f"   🏆 Quality Score: {metrics.data_quality_score:.2f}")
            
            if metrics.confidence_scores:
                avg_confidence = statistics.mean(metrics.confidence_scores)
                logger.info(f"   🎯 Avg Confidence: {avg_confidence:.2f}")
            
            # Save metrics to file
            await self._save_metrics_to_file(metrics)
            
        except Exception as e:
            logger.error(f"❌ Failed to record metrics: {e}")
    
    async def _check_quality_thresholds(self, metrics: ExtractionMetrics):
        """Check if metrics meet quality thresholds"""
        alerts = []
        
        # Check success rate
        if metrics.success_rate < self.quality_thresholds['minimum_success_rate']:
            alerts.append(f"Low success rate: {metrics.success_rate:.1%} < {self.quality_thresholds['minimum_success_rate']:.1%}")
        
        # Check confidence scores
        if metrics.confidence_scores:
            avg_confidence = statistics.mean(metrics.confidence_scores)
            if avg_confidence < self.quality_thresholds['minimum_confidence']:
                alerts.append(f"Low confidence: {avg_confidence:.2f} < {self.quality_thresholds['minimum_confidence']:.2f}")
        
        # Check quality score
        if metrics.data_quality_score < self.quality_thresholds['minimum_quality_score']:
            alerts.append(f"Low quality score: {metrics.data_quality_score:.2f} < {self.quality_thresholds['minimum_quality_score']:.2f}")
        
        # Check extraction time
        if metrics.extraction_time > self.quality_thresholds['maximum_extraction_time']:
            alerts.append(f"Slow extraction: {metrics.extraction_time:.1f}s > {self.quality_thresholds['maximum_extraction_time']:.1f}s")
        
        # Send alerts
        for alert in alerts:
            await self._send_alert('quality_threshold', alert, metrics)
    
    async def _send_alert(self, alert_type: str, message: str, metrics: ExtractionMetrics):
        """Send quality alert"""
        alert_data = {
            'type': alert_type,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'product_url': metrics.product_url,
            'product_name': metrics.product_name,
            'metrics': asdict(metrics)
        }
        
        logger.warning(f"⚠️ ALERT [{alert_type}]: {message}")
        
        # Call alert handlers
        for handler in self.alert_handlers:
            try:
                await handler(alert_data)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")
    
    async def _save_metrics_to_file(self, metrics: ExtractionMetrics):
        """Save metrics to file for analysis"""
        if not ASYNC_FILE_AVAILABLE:
            return
        
        try:
            metrics_dir = Path('monitoring_data')
            metrics_dir.mkdir(exist_ok=True)
            
            # Save to daily file
            date_str = datetime.now().strftime('%Y-%m-%d')
            metrics_file = metrics_dir / f'extraction_metrics_{date_str}.jsonl'
            
            async with aiofiles.open(metrics_file, 'a') as f:
                await f.write(json.dumps(asdict(metrics)) + '\n')
        
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")
    
    def generate_quality_report(self, hours_back: int = 24) -> QualityReport:
        """Generate quality assurance report"""
        try:
            # Filter recent metrics
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            recent_metrics = [
                m for m in self.metrics_history 
                if datetime.fromisoformat(m.timestamp) >= cutoff_time
            ]
            
            if not recent_metrics:
                return QualityReport(
                    report_id=f"QR-{int(time.time())}",
                    timestamp=datetime.now().isoformat(),
                    total_extractions=0,
                    successful_extractions=0,
                    overall_success_rate=0.0,
                    average_confidence=0.0,
                    average_quality_score=0.0,
                    common_errors={},
                    performance_metrics={},
                    recommendations=["No recent extractions to analyze"]
                )
            
            # Calculate statistics
            total_extractions = len(recent_metrics)
            successful_extractions = sum(1 for m in recent_metrics if m.success_rate >= 0.8)
            overall_success_rate = successful_extractions / total_extractions
            
            # Confidence scores
            all_confidence_scores = []
            for m in recent_metrics:
                all_confidence_scores.extend(m.confidence_scores)
            average_confidence = statistics.mean(all_confidence_scores) if all_confidence_scores else 0.0
            
            # Quality scores
            quality_scores = [m.data_quality_score for m in recent_metrics]
            average_quality_score = statistics.mean(quality_scores)
            
            # Common errors
            error_counts = {}
            for m in recent_metrics:
                for error in m.errors:
                    error_counts[error] = error_counts.get(error, 0) + 1
            
            # Performance metrics
            extraction_times = [m.extraction_time for m in recent_metrics]
            performance_metrics = {
                'average_extraction_time': statistics.mean(extraction_times),
                'median_extraction_time': statistics.median(extraction_times),
                'max_extraction_time': max(extraction_times),
                'min_extraction_time': min(extraction_times),
                'total_variants_found': sum(m.variants_found for m in recent_metrics),
                'average_variants_per_product': statistics.mean([m.variants_found for m in recent_metrics])
            }
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                overall_success_rate, average_confidence, average_quality_score, 
                error_counts, performance_metrics
            )
            
            return QualityReport(
                report_id=f"QR-{int(time.time())}",
                timestamp=datetime.now().isoformat(),
                total_extractions=total_extractions,
                successful_extractions=successful_extractions,
                overall_success_rate=overall_success_rate,
                average_confidence=average_confidence,
                average_quality_score=average_quality_score,
                common_errors=dict(sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
                performance_metrics=performance_metrics,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"❌ Quality report generation failed: {e}")
            return QualityReport(
                report_id=f"QR-ERROR-{int(time.time())}",
                timestamp=datetime.now().isoformat(),
                total_extractions=0,
                successful_extractions=0,
                overall_success_rate=0.0,
                average_confidence=0.0,
                average_quality_score=0.0,
                common_errors={},
                performance_metrics={},
                recommendations=[f"Report generation failed: {e}"]
            )
    
    def _generate_recommendations(self, success_rate: float, confidence: float, 
                                quality_score: float, errors: Dict, performance: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Success rate recommendations
        if success_rate < 0.8:
            recommendations.append("🔧 Success rate below 80%. Review and update extraction selectors.")
        elif success_rate < 0.9:
            recommendations.append("📈 Success rate good but can be improved. Fine-tune validation rules.")
        
        # Confidence recommendations
        if confidence < 0.7:
            recommendations.append("🎯 Low confidence scores. Enhance AI validation and pattern recognition.")
        elif confidence < 0.8:
            recommendations.append("🔍 Consider improving variant name cleaning and standardization.")
        
        # Quality recommendations
        if quality_score < 0.75:
            recommendations.append("🏆 Quality score needs improvement. Focus on data validation and enrichment.")
        
        # Performance recommendations
        if performance.get('average_extraction_time', 0) > 20:
            recommendations.append("⚡ Slow extraction times. Optimize selectors and reduce wait times.")
        
        # Error-based recommendations
        top_errors = list(errors.keys())[:3]
        for error in top_errors:
            if 'timeout' in error.lower():
                recommendations.append("⏱️ Frequent timeouts detected. Increase timeout values or optimize page loading.")
            elif 'price' in error.lower():
                recommendations.append("💰 Price extraction issues. Review price selectors and parsing logic.")
            elif 'image' in error.lower():
                recommendations.append("🖼️ Image extraction problems. Update image selectors and quality filters.")
        
        # General recommendations
        if not recommendations:
            recommendations.append("✅ System performing well. Continue monitoring for consistency.")
        
        return recommendations
    
    def get_real_time_stats(self) -> Dict[str, Any]:
        """Get real-time performance statistics"""
        current_time = time.time()
        uptime = current_time - self.performance_stats['start_time']
        
        stats = {
            'uptime_seconds': uptime,
            'uptime_formatted': f"{uptime/3600:.1f} hours",
            'total_extractions': self.performance_stats['total_extractions'],
            'successful_extractions': self.performance_stats['successful_extractions'],
            'failed_extractions': self.performance_stats['failed_extractions'],
            'success_rate': (
                self.performance_stats['successful_extractions'] / 
                max(self.performance_stats['total_extractions'], 1)
            ),
            'total_variants_found': self.performance_stats['total_variants_found'],
            'average_variants_per_product': (
                self.performance_stats['total_variants_found'] / 
                max(self.performance_stats['total_extractions'], 1)
            ),
            'average_extraction_time': (
                self.performance_stats['total_extraction_time'] / 
                max(self.performance_stats['total_extractions'], 1)
            ),
            'extractions_per_hour': (
                self.performance_stats['total_extractions'] / max(uptime / 3600, 0.01)
            )
        }
        
        # Add system stats if available
        if SYSTEM_MONITORING_AVAILABLE:
            stats.update({
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent
            })
        
        return stats
    
    async def export_metrics(self, format: str = 'json', hours_back: int = 24) -> str:
        """Export metrics data"""
        try:
            # Filter recent metrics
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            recent_metrics = [
                m for m in self.metrics_history 
                if datetime.fromisoformat(m.timestamp) >= cutoff_time
            ]
            
            if format.lower() == 'json':
                export_data = {
                    'export_timestamp': datetime.now().isoformat(),
                    'hours_back': hours_back,
                    'total_records': len(recent_metrics),
                    'metrics': [asdict(m) for m in recent_metrics],
                    'summary': self.get_real_time_stats()
                }
                
                filename = f"metrics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                
                if ASYNC_FILE_AVAILABLE:
                    async with aiofiles.open(filename, 'w') as f:
                        await f.write(json.dumps(export_data, indent=2))
                else:
                    with open(filename, 'w') as f:
                        json.dump(export_data, f, indent=2)
                
                logger.info(f"📊 Metrics exported to: {filename}")
                return filename
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
        
        except Exception as e:
            logger.error(f"❌ Metrics export failed: {e}")
            return ""
    
    def add_alert_handler(self, handler):
        """Add alert handler function"""
        self.alert_handlers.append(handler)
        logger.info(f"📢 Alert handler added: {handler.__name__}")

class QualityValidator:
    """
    Quality validation system for extracted variant data
    Ensures data meets professional standards
    """
    
    def __init__(self):
        self.validation_rules = {
            'variant_name': {
                'min_length': 2,
                'max_length': 100,
                'forbidden_patterns': [
                    r'see available', r'options from', r'starting at',
                    r'make a.*selection', r'click.*see', r'there are \d+'
                ]
            },
            'price': {
                'min_value': 0.01,
                'max_value': 10000.0,
                'required': True
            },
            'images': {
                'min_count': 1,
                'max_count': 10,
                'quality_check': True
            },
            'asin': {
                'pattern': r'^[A-Z0-9]{10}$',
                'required': False
            }
        }
        
        logger.info("🔍 Quality Validator initialized")
    
    async def validate_variant_data(self, variant_data: Dict) -> Dict[str, Any]:
        """Comprehensive validation of variant data"""
        validation_result = {
            'is_valid': True,
            'quality_score': 1.0,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        try:
            # Validate variant name
            name_validation = self._validate_variant_name(variant_data.get('name', ''))
            validation_result['errors'].extend(name_validation['errors'])
            validation_result['warnings'].extend(name_validation['warnings'])
            validation_result['quality_score'] *= name_validation['score']
            
            # Validate price
            price_validation = self._validate_price(variant_data.get('price'))
            validation_result['errors'].extend(price_validation['errors'])
            validation_result['quality_score'] *= price_validation['score']
            
            # Validate images
            images_validation = self._validate_images(variant_data.get('images', []))
            validation_result['warnings'].extend(images_validation['warnings'])
            validation_result['quality_score'] *= images_validation['score']
            
            # Validate ASIN
            asin_validation = self._validate_asin(variant_data.get('asin'))
            validation_result['warnings'].extend(asin_validation['warnings'])
            validation_result['quality_score'] *= asin_validation['score']
            
            # Overall validity
            validation_result['is_valid'] = (
                len(validation_result['errors']) == 0 and 
                validation_result['quality_score'] >= 0.6
            )
            
            # Generate suggestions
            validation_result['suggestions'] = self._generate_validation_suggestions(validation_result)
            
        except Exception as e:
            validation_result['errors'].append(f"Validation error: {e}")
            validation_result['is_valid'] = False
            validation_result['quality_score'] = 0.0
        
        return validation_result
    
    def _validate_variant_name(self, name: str) -> Dict[str, Any]:
        """Validate variant name"""
        result = {'errors': [], 'warnings': [], 'score': 1.0}
        
        if not name:
            result['errors'].append("Variant name is missing")
            result['score'] = 0.0
            return result
        
        # Length check
        if len(name) < self.validation_rules['variant_name']['min_length']:
            result['errors'].append(f"Variant name too short: {len(name)} < {self.validation_rules['variant_name']['min_length']}")
            result['score'] *= 0.5
        
        if len(name) > self.validation_rules['variant_name']['max_length']:
            result['warnings'].append(f"Variant name very long: {len(name)} > {self.validation_rules['variant_name']['max_length']}")
            result['score'] *= 0.8
        
        # Pattern check
        name_lower = name.lower()
        for pattern in self.validation_rules['variant_name']['forbidden_patterns']:
            if re.search(pattern, name_lower):
                result['errors'].append(f"Variant name contains forbidden pattern: '{pattern}'")
                result['score'] *= 0.3
        
        return result
    
    def _validate_price(self, price: Any) -> Dict[str, Any]:
        """Validate price value"""
        result = {'errors': [], 'score': 1.0}
        
        if price is None:
            if self.validation_rules['price']['required']:
                result['errors'].append("Price is required but missing")
                result['score'] = 0.0
            return result
        
        try:
            price_float = float(price)
            
            if price_float < self.validation_rules['price']['min_value']:
                result['errors'].append(f"Price too low: ${price_float} < ${self.validation_rules['price']['min_value']}")
                result['score'] *= 0.5
            
            if price_float > self.validation_rules['price']['max_value']:
                result['errors'].append(f"Price too high: ${price_float} > ${self.validation_rules['price']['max_value']}")
                result['score'] *= 0.7
        
        except (ValueError, TypeError):
            result['errors'].append(f"Invalid price format: {price}")
            result['score'] = 0.0
        
        return result
    
    def _validate_images(self, images: List[str]) -> Dict[str, Any]:
        """Validate image list"""
        result = {'warnings': [], 'score': 1.0}
        
        if not images:
            result['warnings'].append("No images found for variant")
            result['score'] *= 0.8
            return result
        
        if len(images) < self.validation_rules['images']['min_count']:
            result['warnings'].append(f"Few images: {len(images)} < {self.validation_rules['images']['min_count']}")
            result['score'] *= 0.9
        
        if len(images) > self.validation_rules['images']['max_count']:
            result['warnings'].append(f"Many images: {len(images)} > {self.validation_rules['images']['max_count']}")
            result['score'] *= 0.95
        
        # Basic URL validation
        invalid_urls = 0
        for image_url in images:
            if not isinstance(image_url, str) or not image_url.startswith(('http://', 'https://')):
                invalid_urls += 1
        
        if invalid_urls > 0:
            result['warnings'].append(f"{invalid_urls} invalid image URLs found")
            result['score'] *= max(0.5, 1.0 - (invalid_urls / len(images)))
        
        return result
    
    def _validate_asin(self, asin: str) -> Dict[str, Any]:
        """Validate ASIN format"""
        result = {'warnings': [], 'score': 1.0}
        
        if not asin:
            result['warnings'].append("ASIN missing")
            result['score'] *= 0.9
            return result
        
        if not re.match(self.validation_rules['asin']['pattern'], asin):
            result['warnings'].append(f"Invalid ASIN format: {asin}")
            result['score'] *= 0.8
        
        return result
    
    def _generate_validation_suggestions(self, validation_result: Dict) -> List[str]:
        """Generate suggestions based on validation results"""
        suggestions = []
        
        if validation_result['errors']:
            suggestions.append("Fix critical errors before proceeding")
        
        if validation_result['quality_score'] < 0.8:
            suggestions.append("Improve data quality by addressing warnings")
        
        if validation_result['warnings']:
            suggestions.append("Consider enhancing data extraction for missing optional fields")
        
        return suggestions

# Integration example
async def integrate_professional_monitoring(extractor, product_url: str, product_name: str):
    """Integrate professional monitoring with extraction process"""
    
    # Initialize monitoring
    monitor = ProfessionalMonitor()
    validator = QualityValidator()
    
    # Start monitoring
    extraction_id = await monitor.start_extraction_monitoring(product_url, product_name)
    start_time = time.time()
    
    try:
        # Run extraction (placeholder - replace with actual extraction)
        variants = await extractor.extract_variants_professional(product_url, product_name)
        
        # Validate each variant
        validated_variants = []
        validation_errors = []
        validation_warnings = []
        confidence_scores = []
        
        for variant in variants:
            validation_result = await validator.validate_variant_data(asdict(variant))
            
            if validation_result['is_valid']:
                validated_variants.append(variant)
                confidence_scores.append(variant.confidence_score)
            else:
                validation_errors.extend(validation_result['errors'])
                validation_warnings.extend(validation_result['warnings'])
        
        # Calculate metrics
        extraction_time = time.time() - start_time
        success_rate = len(validated_variants) / max(len(variants), 1)
        
        # Calculate data quality score
        quality_scores = []
        for variant in validated_variants:
            validation = await validator.validate_variant_data(asdict(variant))
            quality_scores.append(validation['quality_score'])
        
        data_quality_score = statistics.mean(quality_scores) if quality_scores else 0.0
        
        # Create metrics
        metrics = ExtractionMetrics(
            timestamp=datetime.now().isoformat(),
            product_url=product_url,
            product_name=product_name,
            extraction_time=extraction_time,
            variants_found=len(variants),
            variants_validated=len(validated_variants),
            success_rate=success_rate,
            confidence_scores=confidence_scores,
            errors=validation_errors,
            warnings=validation_warnings,
            data_quality_score=data_quality_score
        )
        
        # Record metrics
        await monitor.record_extraction_metrics(extraction_id, metrics)
        
        # Generate report
        quality_report = monitor.generate_quality_report(hours_back=1)
        
        logger.info("📊 Professional monitoring complete")
        logger.info(f"🎯 Quality Report: {quality_report.overall_success_rate:.1%} success rate")
        
        return validated_variants, quality_report
        
    except Exception as e:
        # Record failure
        error_metrics = ExtractionMetrics(
            timestamp=datetime.now().isoformat(),
            product_url=product_url,
            product_name=product_name,
            extraction_time=time.time() - start_time,
            variants_found=0,
            variants_validated=0,
            success_rate=0.0,
            confidence_scores=[],
            errors=[str(e)],
            warnings=[],
            data_quality_score=0.0
        )
        
        await monitor.record_extraction_metrics(extraction_id, error_metrics)
        raise

if __name__ == "__main__":
    print("📊 Professional Monitoring & Quality Assurance System")
    print("This module provides comprehensive monitoring and validation")
    print("Use with professional_variant_extractor.py for quality control")
