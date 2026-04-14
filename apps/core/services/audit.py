"""
Audit Service Module
Handles prediction audit log filtering, pagination, and report generation
"""
from django.db.models import Count, Q
from django.utils import timezone
from datetime import date, timedelta
from apps.Remote_User.models import prediction_audit


class AuditService:
    """Service for managing prediction audit logs"""
    
    @staticmethod
    def apply_date_range_filter(queryset, from_date=None, to_date=None):
        """Apply date range filtering to audit queryset"""
        if from_date:
            try:
                queryset = queryset.filter(created_at__date__gte=from_date)
            except:
                pass
        
        if to_date:
            try:
                queryset = queryset.filter(created_at__date__lte=to_date)
            except:
                pass
        
        return queryset
    
    @staticmethod
    def apply_quick_filter(queryset, quick_filter=''):
        """Apply quick predefined filters"""
        today = date.today()
        
        if quick_filter == 'today':
            queryset = queryset.filter(created_at__date=today)
        elif quick_filter == 'last7':
            seven_days_ago = today - timedelta(days=7)
            queryset = queryset.filter(created_at__date__gte=seven_days_ago)
        elif quick_filter == 'threat':
            queryset = queryset.filter(predicted_label='Cyber Threat Found')
        elif quick_filter == 'safe':
            queryset = queryset.filter(predicted_label='No Cyber Threat Found')
        
        return queryset
    
    @staticmethod
    def apply_label_filter(queryset, label=''):
        """Filter by prediction label"""
        if label in ['Cyber Threat Found', 'No Cyber Threat Found']:
            queryset = queryset.filter(predicted_label=label)
        return queryset
    
    @staticmethod
    def apply_username_filter(queryset, username=''):
        """Filter by username (case-insensitive)"""
        if username:
            queryset = queryset.filter(username__icontains=username)
        return queryset
    
    @staticmethod
    def apply_confidence_filter(queryset, min_confidence=''):
        """Filter by minimum confidence level"""
        if min_confidence:
            try:
                min_conf = int(min_confidence)
                queryset = queryset.filter(confidence__gte=min_conf)
            except:
                pass
        return queryset
    
    @staticmethod
    def get_filtered_audit_log(
        from_date=None,
        to_date=None,
        quick_filter='',
        label='',
        username='',
        min_confidence='',
    ):
        """Get filtered audit log with all filters applied"""
        queryset = prediction_audit.objects.all()
        
        queryset = AuditService.apply_date_range_filter(queryset, from_date, to_date)
        queryset = AuditService.apply_quick_filter(queryset, quick_filter)
        queryset = AuditService.apply_label_filter(queryset, label)
        queryset = AuditService.apply_username_filter(queryset, username)
        queryset = AuditService.apply_confidence_filter(queryset, min_confidence)
        
        return queryset.order_by('-created_at')
    
    @staticmethod
    def get_audit_statistics(queryset=None):
        """Get summary statistics from audit log"""
        if queryset is None:
            queryset = prediction_audit.objects.all()
        
        return {
            'total_predictions': queryset.count(),
            'threat_found': queryset.filter(
                predicted_label='Cyber Threat Found'
            ).count(),
            'threat_safe': queryset.filter(
                predicted_label='No Cyber Threat Found'
            ).count(),
            'avg_confidence': queryset.aggregate(
                avg=Count('confidence')
            )['avg'] or 0,
        }
    
    @staticmethod
    def get_trend_by_date(queryset=None):
        """Get prediction trends by date"""
        if queryset is None:
            queryset = prediction_audit.objects.all()
        
        return (
            queryset
            .extra(select={'date': 'DATE(created_at)'})
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )
    
    @staticmethod
    def get_top_users(limit=10):
        """Get users with most predictions"""
        return (
            prediction_audit.objects
            .values('username')
            .annotate(count=Count('id'))
            .order_by('-count')[:limit]
        )
