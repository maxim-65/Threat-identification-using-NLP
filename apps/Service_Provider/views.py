"""
Service Provider Views - Refactored to use core services
Handles admin/analytics dashboard, model training, and audit logging
"""
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from pathlib import Path
import xlwt
import csv
from datetime import date

# Import services
from apps.core.services import AnalyticsService, TrainingService, AuditService
from apps.core.utils.decorators import require_service_provider
from apps.Remote_User.models import ClientRegister_Model, prediction_audit

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def serviceproviderlogin(request):
    """Service provider login handler"""
    if request.method == 'POST':
        provider_email = request.POST.get('email', '').strip()
        provider_password = request.POST.get('password', '').strip()
        
        if provider_email == 'admin@provider' and provider_password == 'admin123':
            request.session['Service_Provider_ID'] = 'admin'
            request.session['username'] = provider_email
            messages.success(request, 'Login successful')
            return redirect('/service_provider_home/')
        else:
            messages.error(request, 'Invalid credentials')
    
    return render(request, 'SProvider/serviceproviderlogin.html')


@require_service_provider
def service_provider_home(request):
    """Service provider home dashboard"""
    try:
        remote_users = ClientRegister_Model.objects.count()
        predicted_records = prediction_audit.objects.count()
        training_models = len(list(AnalyticsService.get_accuracy_data()))
        audit_records = prediction_audit.objects.count()
        
        stats = AnalyticsService.get_threat_statistics()
        threat_found = stats.get('threat_found', 0)
        threat_safe = stats.get('threat_safe', 0)
        
        return render(request, 'SProvider/service_provider_home.html', {
            'remote_users': remote_users,
            'predicted_records': predicted_records,
            'training_models': training_models,
            'audit_records': audit_records,
            'threat_found': threat_found,
            'threat_safe': threat_safe,
        })
    except Exception as e:
        messages.error(request, f'Dashboard error: {str(e)}')
        return render(request, 'SProvider/service_provider_home.html', {
            'error': str(e)
        })


@require_service_provider
def View_Remote_Users(request):
    """List all remote users with pagination"""
    users = ClientRegister_Model.objects.all().order_by('-id')
    paginator = Paginator(users, 15)
    page = paginator.get_page(request.GET.get('page', 1))
    
    return render(request, 'SProvider/View_Remote_Users.html', {
        'objects': page.object_list,
        'page_obj': page,
    })


@require_service_provider
def train_model(request):
    """Show cached training results from default dataset"""
    try:
        results = list(AnalyticsService.get_accuracy_data())
        summary = AnalyticsService.get_model_performance_summary()
        status_msg = 'Showing cached training results'
        
        if request.GET.get('refreshed') == '1':
            status_msg = 'Model cache refreshed successfully'
        
        return render(request, 'model_training.html', {
            'page_title': 'Model Training Results',
            'results': results,
            'summary': summary,
            'status_message': status_msg,
            'show_refresh': True,
            'show_upload': False,
        })
    except Exception as e:
        messages.error(request, str(e))
        return render(request, 'model_training.html', {
            'page_title': 'Model Training Results',
            'results': [],
            'status_message': f'Error: {str(e)}',
            'show_refresh': True,
            'show_upload': False,
        })


@require_service_provider
def train_models(request):
    """Train models from uploaded CSV file"""
    if request.method == 'POST':
        uploaded_file = request.FILES.get('dataset_file')
        
        if not uploaded_file:
            messages.error(request, 'Please upload a CSV file')
            return render(request, 'model_training.html', {
                'page_title': 'Train New Models',
                'results': [],
                'status_message': 'Upload a CSV file to train models',
                'show_refresh': False,
                'show_upload': True,
            })
        
        try:
            df = TrainingService.load_uploaded_dataset(uploaded_file)
            results, vectorizer, models = TrainingService.train_models(df)
            TrainingService.store_training_results(results)
            summary = TrainingService.get_summary_statistics(results)
            
            messages.success(request, f'Training completed: {uploaded_file.name}')
            
            return render(request, 'model_training.html', {
                'page_title': 'Train New Models',
                'results': results,
                'summary': summary,
                'status_message': f'Successfully trained on {uploaded_file.name}',
                'show_refresh': False,
                'show_upload': True,
            })
        except Exception as exc:
            messages.error(request, str(exc))
            return render(request, 'model_training.html', {
                'page_title': 'Train New Models',
                'results': [],
                'status_message': f'Error: {str(exc)}',
                'show_refresh': False,
                'show_upload': True,
            })
    
    return render(request, 'model_training.html', {
        'page_title': 'Train New Models',
        'results': [],
        'status_message': 'Upload a CSV file to train and evaluate models',
        'show_refresh': False,
        'show_upload': True,
    })


@require_service_provider
def refresh_prediction_model_cache(request):
    """Refresh the prediction model cache"""
    try:
        from apps.Remote_User.views import clear_prediction_model_cache
        clear_prediction_model_cache()
        messages.success(request, 'Model cache refreshed')
    except Exception as e:
        messages.error(request, f'Refresh failed: {str(e)}')
    
    return redirect('/train_model/?refreshed=1')


@require_service_provider
def View_Predicted_Cyber_Threat_Identification_Type(request):
    """View all predictions with statistics"""
    from apps.Remote_User.models import cyber_threat_identification
    
    predictions = cyber_threat_identification.objects.all()
    threat_found_count = predictions.filter(Prediction='Cyber Threat Found').count()
    no_threat_count = predictions.filter(Prediction='No Cyber Threat Found').count()
    total_count = predictions.count()
    
    paginator = Paginator(predictions.order_by('-id'), 20)
    page = paginator.get_page(request.GET.get('page', 1))
    
    return render(request, 'SProvider/View_Predicted_Cyber_Threat_Identification_Type.html', {
        'list_objects': page.object_list,
        'page_obj': page,
        'threat_found_count': threat_found_count,
        'no_threat_count': no_threat_count,
        'total_count': total_count,
    })


@require_service_provider
def View_Predicted_Cyber_Threat_Identification_Type_Ratio(request):
    """View threat ratio data"""
    data = list(AnalyticsService.get_threat_ratio_data())
    stats = [
        {'label': 'Total Ratios', 'value': len(data)},
        {'label': 'Avg Ratio', 'value': f"{sum(d.get('ratio_avg', 0) for d in data) / len(data):.2f}%" if data else '0%'},
    ]
    
    return render(request, 'analytics_chart.html', {
        'chart_title': 'Threat Detection Ratio',
        'items': data,
        'col1_header': 'Threat Type',
        'col2_header': 'Detection Ratio',
        'statistics': stats,
    })


@require_service_provider
def charts(request, chart_type='line'):
    """Display threat ratio charts"""
    data = list(AnalyticsService.get_threat_ratio_data())
    stats = [
        {'label': 'Chart Points', 'value': len(data)},
        {'label': 'Data Type', 'value': 'Threat Ratio'},
    ]
    
    return render(request, 'analytics_chart.html', {
        'chart_title': 'Threat Detection Ratio (Chart View)',
        'items': data,
        'col1_header': 'Threat Type',
        'col2_header': 'Ratio %',
        'statistics': stats,
        'chart_type': chart_type,
    })


@require_service_provider
def charts1(request, chart_type='line'):
    """Display accuracy charts"""
    data = list(AnalyticsService.get_accuracy_data())
    stats = [
        {'label': 'Models', 'value': len(data)},
        {'label': 'Data Type', 'value': 'Accuracy'},
    ]
    
    return render(request, 'analytics_chart.html', {
        'chart_title': 'Model Accuracy Results',
        'items': data,
        'col1_header': 'Model Name',
        'col2_header': 'Accuracy %',
        'statistics': stats,
        'chart_type': chart_type,
    })


@require_service_provider
def likeschart(request, like_chart='bar'):
    """Display accuracy bar chart"""
    data = list(AnalyticsService.get_accuracy_data())
    stats = [
        {'label': 'Models Evaluated', 'value': len(data)},
        {'label': 'Chart Type', 'value': 'Bar Chart'},
    ]
    
    return render(request, 'analytics_chart.html', {
        'chart_title': 'Model Accuracy (Bar Chart)',
        'items': data,
        'col1_header': 'Model',
        'col2_header': 'Accuracy',
        'statistics': stats,
        'chart_type': 'bar',
    })


@require_service_provider
def view_prediction_audit_log(request):
    """View prediction audit log with filtering and pagination"""
    from_date = request.GET.get('from_date', '').strip()
    to_date = request.GET.get('to_date', '').strip()
    quick = request.GET.get('quick', '').strip()
    username = request.GET.get('username', '').strip()
    label = request.GET.get('label', '').strip()
    min_confidence = request.GET.get('min_confidence', '').strip()
    
    # Get filtered audit log
    audit_log = AuditService.get_filtered_audit_log(
        from_date=from_date,
        to_date=to_date,
        quick_filter=quick,
        username=username,
        label=label,
        min_confidence=min_confidence,
    )
    
    # Get statistics
    stats = AuditService.get_audit_statistics(audit_log)
    top_users = list(AuditService.get_top_users(10))
    
    # Pagination
    paginator = Paginator(audit_log, 25)
    page = paginator.get_page(request.GET.get('page', 1))
    
    return render(request, 'SProvider/View_Prediction_Audit_Log.html', {
        'page_obj': page,
        'records': page.object_list,
        'statistics': stats,
        'top_users': top_users,
        'filters': {
            'from_date': from_date,
            'to_date': to_date,
            'quick': quick,
            'username': username,
            'label': label,
            'min_confidence': min_confidence,
        },
    })


@require_service_provider
def view_user_prediction_history(request, username):
    """View prediction history for a specific user"""
    records = prediction_audit.objects.filter(username=username).order_by('-created_at')[:500]
    stats = {
        'total': records.count(),
        'threat_found': records.filter(predicted_label='Cyber Threat Found').count(),
        'threat_safe': records.filter(predicted_label='No Cyber Threat Found').count(),
    }
    
    return_to = request.GET.get('return_to', '').strip()
    back_url = '/view_prediction_audit_log/'
    if return_to:
        back_url = f'/view_prediction_audit_log/?{return_to}'
    
    return render(request, 'SProvider/View_User_Prediction_History.html', {
        'records': records,
        'username': username,
        'back_url': back_url,
        'stats': stats,
    })


@require_service_provider
def Download_Predicted_DataSets(request):
    """Download prediction data as XLS"""
    try:
        predictions = prediction_audit.objects.all().values_list(
            'username', 'fid', 'predicted_label', 'confidence', 'created_at'
        )
        
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Predictions')
        
        headers = ['Username', 'FID', 'Predicted Label', 'Confidence %', 'Date']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header)
        
        for row, record in enumerate(predictions, start=1):
            for col, value in enumerate(record):
                worksheet.write(row, col, str(value))
        
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename="predictions.xls"'
        workbook.save(response)
        return response
    except Exception as e:
        messages.error(request, f'Download error: {str(e)}')
        return redirect('/service_provider_home/')


@require_service_provider  
def download_prediction_audit_log(request):
    """Download audit log as XLS"""
    return Download_Predicted_DataSets(request)


@require_service_provider
def download_prediction_audit_log_csv(request):
    """Download audit log as CSV"""
    try:
        records = prediction_audit.objects.all().values()
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="audit_log.csv"'
        
        if records:
            writer = csv.DictWriter(response, fieldnames=records[0].keys())
            writer.writeheader()
            writer.writerows(records)
        
        return response
    except Exception as e:
        messages.error(request, f'Download error: {str(e)}')
        return redirect('/service_provider_home/')
