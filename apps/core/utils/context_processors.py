"""
Context processors for shared template context
"""
from django.utils import timezone
from apps.core.services import AnalyticsService


def global_context(request):
    """Add global context data to all templates"""
    return {
        'current_year': timezone.now().year,
        'app_name': 'Automated Emerging Cyber Threat Identification',
    }


def analytics_context(request):
    """Add analytics data to context for dashboards"""
    try:
        stats = AnalyticsService.get_threat_statistics()
        return {'analytics': stats}
    except:
        return {'analytics': {}}


def user_context(request):
    """Add user session data to context"""
    return {
        'is_remote_user': 'Remote_User_ID' in request.session,
        'is_service_provider': 'Service_Provider_ID' in request.session,
        'current_user': request.session.get('username', ''),
    }
