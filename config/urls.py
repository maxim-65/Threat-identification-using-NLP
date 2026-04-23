"""automated_emerging_cyber_threat_identification URL Configuration

The `urlpatterns` list routes URLs to main_app. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from apps.Remote_User import views as remoteuser
from apps.core import api
from config import settings
from apps.Service_Provider import views as serviceprovider
from django.conf.urls.static import static
from django.urls import path


urlpatterns = [
    path('admin/', admin.site.urls),
    
    # User Routes
    path('', remoteuser.index, name="index"),
    path('login/', remoteuser.login, name="remote_user_login"),
    path('login/', remoteuser.login, name="login"),
    path('Register1/', remoteuser.Register1, name="Register1"),
    path('Predict_Cyber_Threat_Identification_Type/', remoteuser.Predict_Cyber_Threat_Identification_Type, name="Predict_Cyber_Threat_Identification_Type"),
    path('ViewYourProfile/', remoteuser.ViewYourProfile, name="ViewYourProfile"),
    
    # Service Provider Routes
    path('serviceproviderlogin/', serviceprovider.serviceproviderlogin, name="service_provider_login"),
    path('serviceproviderlogin/', serviceprovider.serviceproviderlogin, name="serviceproviderlogin"),
    path('service_provider_home/', serviceprovider.service_provider_home, name="service_provider_home"),
    path('View_Remote_Users/', serviceprovider.View_Remote_Users, name="View_Remote_Users"),
    path('charts/<str:chart_type>/', serviceprovider.charts, name="charts"),
    path('charts1/<str:chart_type>/', serviceprovider.charts1, name="charts1"),
    path('likeschart/<str:like_chart>/', serviceprovider.likeschart, name="likeschart"),
    path('View_Predicted_Cyber_Threat_Identification_Type_Ratio/', serviceprovider.View_Predicted_Cyber_Threat_Identification_Type_Ratio, name="View_Predicted_Cyber_Threat_Identification_Type_Ratio"),
    path('train_models/', serviceprovider.train_models, name="train_models"),
    path('train_model/', serviceprovider.train_model, name="train_model"),
    path('refresh_prediction_model_cache/', serviceprovider.refresh_prediction_model_cache, name="refresh_prediction_model_cache"),
    path('View_Predicted_Cyber_Threat_Identification_Type/', serviceprovider.View_Predicted_Cyber_Threat_Identification_Type, name="View_Predicted_Cyber_Threat_Identification_Type"),
    path('Download_Predicted_DataSets/', serviceprovider.Download_Predicted_DataSets, name="Download_Predicted_DataSets"),
    path('view_prediction_audit_log/', serviceprovider.view_prediction_audit_log, name="view_prediction_audit_log"),
    path('download_prediction_audit_log/', serviceprovider.download_prediction_audit_log, name="download_prediction_audit_log"),
    path('download_prediction_audit_log_csv/', serviceprovider.download_prediction_audit_log_csv, name="download_prediction_audit_log_csv"),
    path('view_user_prediction_history/<str:username>/', serviceprovider.view_user_prediction_history, name="view_user_prediction_history"),
    
    # REST API Endpoints (v2.0)
    path('api/predict/', api.predict_threat, name="api_predict"),
    path('api/batch_predict/', api.batch_predict, name="api_batch_predict"),
    path('api/metrics/', api.model_metrics, name="api_metrics"),
    path('api/health/', api.health_check, name="api_health_check"),
    path('api/docs/', api.api_documentation, name="api_docs"),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
