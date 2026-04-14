"""
Decorators for role-based access control and common view functionality
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def require_remote_user(view_func):
    """Decorator to ensure user is logged in as Remote User"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'Remote_User_ID' not in request.session:
            messages.error(request, 'Please login to access this page')
            return redirect('/login/')
        return view_func(request, *args, **kwargs)
    return wrapper


def require_service_provider(view_func):
    """Decorator to ensure user is logged in as Service Provider"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'Service_Provider_ID' not in request.session:
            messages.error(request, 'Please login as Service Provider')
            return redirect('/serviceproviderlogin/')
        return view_func(request, *args, **kwargs)
    return wrapper


def handle_db_errors(view_func):
    """Decorator to gracefully handle database errors in views"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('/')
    return wrapper
