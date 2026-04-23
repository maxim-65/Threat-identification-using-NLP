"""
Advanced Monitoring and Metrics Endpoints
Production-ready performance tracking and observability
"""
import json
import psutil
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Avg, Max
from django.utils import timezone

from apps.Remote_User.models import prediction_audit, detection_accuracy
from apps.core.logging_config import get_logger
from apps.core.model_manager import ModelManager


@require_http_methods(["GET"])
def system_metrics(request):
    """
    GET /api/system_metrics/
    Get system performance metrics (CPU, memory, disk, uptime)
    """
    logger = get_logger()
    
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available_mb = memory.available / (1024 * 1024)
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_free_mb = disk.free / (1024 * 1024)
        
        logger.performance_logger.debug(
            f"System metrics | CPU: {cpu_percent}% | Memory: {memory_percent}% | Disk: {disk_percent}%"
        )
        
        return JsonResponse({
            'success': True,
            'system': {
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count
                },
                'memory': {
                    'percent': memory_percent,
                    'available_mb': round(memory_available_mb, 2)
                },
                'disk': {
                    'percent': disk_percent,
                    'free_mb': round(disk_free_mb, 2)
                }
            }
        })
    
    except Exception as e:
        logger.error_logger.error(f"System metrics endpoint | Error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def prediction_stats(request):
    """
    GET /api/prediction_stats/
    Get detailed prediction statistics and trends
    """
    logger = get_logger()
    
    try:
        # Overall stats
        total_predictions = prediction_audit.objects.count()
        threat_predictions = prediction_audit.objects.filter(predicted_label='Cyber Threat Found').count()
        no_threat_predictions = total_predictions - threat_predictions
        
        threat_ratio = round((threat_predictions / total_predictions * 100), 2) if total_predictions > 0 else 0
        
        # Avg confidence
        avg_confidence = prediction_audit.objects.aggregate(
            avg_conf=Avg('confidence')
        )['avg_conf'] or 0
        
        # Last 24 hours
        last_24h = timezone.now() - timedelta(hours=24)
        predictions_last_24h = prediction_audit.objects.filter(
            created_at__gte=last_24h
        ).count()
        
        # Top users
        top_users = prediction_audit.objects.values('username').annotate(
            count=Count('id'),
            avg_conf=Avg('confidence')
        ).order_by('-count')[:5]
        
        logger.performance_logger.debug(
            f"Prediction stats | Total: {total_predictions} | "
            f"Threats: {threat_predictions} ({threat_ratio}%) | Last 24h: {predictions_last_24h}"
        )
        
        return JsonResponse({
            'success': True,
            'predictions': {
                'total': total_predictions,
                'threats_found': threat_predictions,
                'no_threats': no_threat_predictions,
                'threat_ratio_percent': threat_ratio,
                'avg_confidence': round(avg_confidence, 3),
                'last_24h_count': predictions_last_24h
            },
            'top_users': list(top_users)
        })
    
    except Exception as e:
        logger.error_logger.error(f"Prediction stats endpoint | Error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def model_status(request):
    """
    GET /api/model_status/
    Get current model status, caching info, and training history
    """
    logger = get_logger()
    
    try:
        # Model accuracies
        models = list(detection_accuracy.objects.all().values('names', 'ratio'))
        
        # Model files status
        model_status = []
        for model_name in ['multinomial_naive_bayes', 'support_vector_machine', 'logistic_regression', 'extra_tree_classifier']:
            exists = ModelManager.model_exists(model_name)
            size_mb = ModelManager.get_model_size_mb(model_name) if exists else 0
            model_status.append({
                'name': model_name.replace('_', ' ').title(),
                'cached': exists,
                'size_mb': size_mb
            })
        
        # Vectorizer status
        vectorizer_cached = ModelManager.vectorizer_exists()
        vectorizer_size = ModelManager.get_model_size_mb('tfidf_vectorizer') if vectorizer_cached else 0
        
        logger.performance_logger.debug(
            f"Model status | Models cached: {sum(1 for m in model_status if m['cached'])} | "
            f"Vectorizer cached: {vectorizer_cached}"
        )
        
        return JsonResponse({
            'success': True,
            'models': models,
            'model_files': model_status,
            'vectorizer': {
                'cached': vectorizer_cached,
                'size_mb': vectorizer_size
            },
            'total_model_size_mb': round(sum(m['size_mb'] for m in model_status) + vectorizer_size, 2)
        })
    
    except Exception as e:
        logger.error_logger.error(f"Model status endpoint | Error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def api_stats(request):
    """
    GET /api/stats/
    Aggregate statistics for dashboards
    """
    try:
        # Combine all metrics
        total_predictions = prediction_audit.objects.count()
        threat_predictions = prediction_audit.objects.filter(predicted_label='Cyber Threat Found').count()
        models_count = detection_accuracy.objects.count()
        
        threat_ratio = round((threat_predictions / total_predictions * 100), 2) if total_predictions > 0 else 0
        
        return JsonResponse({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'statistics': {
                'total_predictions': total_predictions,
                'threats_detected': threat_predictions,
                'threat_detection_rate': f"{threat_ratio}%",
                'models_trained': models_count,
                'api_version': '2.2'
            }
        })
    
    except Exception as e:
        logger.error_logger.error(f"API stats endpoint | Error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
