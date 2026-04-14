"""
Analytics Service Module
Handles chart data processing and aggregation for threat detection metrics
"""
from django.db.models import Avg, Count, Q
from apps.Remote_User.models import detection_ratio, detection_accuracy, cyber_threat_identification


class AnalyticsService:
    """Service for generating analytics and chart data"""
    
    @staticmethod
    def get_threat_ratio_data():
        """Get detection ratio data aggregated by threat type"""
        return detection_ratio.objects.values('names').annotate(
            ratio_avg=Avg('ratio')
        ).order_by('-ratio_avg')
    
    @staticmethod
    def get_accuracy_data():
        """Get model accuracy data aggregated by model name"""
        return detection_accuracy.objects.values('names').annotate(
            accuracy_avg=Avg('ratio')
        ).order_by('-accuracy_avg')
    
    @staticmethod
    def get_threat_statistics():
        """Get overall threat/safe prediction counts"""
        all_predictions = cyber_threat_identification.objects.all()
        return {
            'total_predictions': all_predictions.count(),
            'threat_found': all_predictions.filter(Prediction='Cyber Threat Found').count(),
            'threat_safe': all_predictions.filter(Prediction='No Cyber Threat Found').count(),
        }
    
    @staticmethod
    def get_chart_data(chart_type='line'):
        """
        Get chart data in standardized format
        chart_type: 'line', 'bar', 'pie'
        """
        threat_data = AnalyticsService.get_threat_ratio_data()
        accuracy_data = AnalyticsService.get_accuracy_data()
        stats = AnalyticsService.get_threat_statistics()
        
        return {
            'threat_ratios': list(threat_data),
            'accuracies': list(accuracy_data),
            'statistics': stats,
            'chart_type': chart_type,
        }
    
    @staticmethod
    def get_model_performance_summary():
        """Get summary of best/avg model performance"""
        accuracy_data = list(AnalyticsService.get_accuracy_data())
        
        if not accuracy_data:
            return {
                'total_models': 0,
                'best_model': '--',
                'best_score': None,
                'avg_score': None,
            }
        
        scores = [d['accuracy_avg'] for d in accuracy_data if d['accuracy_avg']]
        best_model = accuracy_data[0] if accuracy_data else None
        
        return {
            'total_models': len(accuracy_data),
            'best_model': best_model['names'] if best_model else '--',
            'best_score': round(best_model['accuracy_avg'], 2) if best_model else None,
            'avg_score': round(sum(scores) / len(scores), 2) if scores else None,
        }
