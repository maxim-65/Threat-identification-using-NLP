#!/usr/bin/env python
"""Test script to validate refactored code imports and syntax"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

django.setup()

# Test imports
print("[TEST] Importing core services...")
try:
    from apps.core.services import AnalyticsService, TrainingService, AuditService
    print("✓ Core services imported successfully")
except Exception as e:
    print(f"✗ Error importing services: {e}")
    sys.exit(1)

print("[TEST] Importing decorators...")
try:
    from apps.core.utils.decorators import require_service_provider, require_remote_user
    print("✓ Decorators imported successfully")
except Exception as e:
    print(f"✗ Error importing decorators: {e}")
    sys.exit(1)

print("[TEST] Importing context processors...")
try:
    from apps.core.utils.context_processors import global_context, analytics_context
    print("✓ Context processors imported successfully")
except Exception as e:
    print(f"✗ Error importing context processors: {e}")
    sys.exit(1)

print("[TEST] Importing Service Provider views...")
try:
    from apps.Service_Provider import views as sp_views
    print("✓ Service Provider views imported successfully")
except Exception as e:
    print(f"✗ Error importing Service Provider views: {e}")
    sys.exit(1)

print("[TEST] Testing AnalyticsService methods...")
try:
    from apps.Remote_User.models import detection_accuracy, detection_ratio, cyber_threat_identification
    
    # Test each service method
    threat_stats = AnalyticsService.get_threat_statistics()
    assert isinstance(threat_stats, dict), "threat_stats should be dict"
    assert 'total_predictions' in threat_stats, "Missing total_predictions"
    print("✓ AnalyticsService.get_threat_statistics() works")
    
    accuracy_data = list(AnalyticsService.get_accuracy_data())
    print(f"✓ AnalyticsService.get_accuracy_data() works ({len(accuracy_data)} records)")
    
    summary = AnalyticsService.get_model_performance_summary()
    assert isinstance(summary, dict), "summary should be dict"
    print("✓ AnalyticsService.get_model_performance_summary() works")
    
except Exception as e:
    print(f"✗ Error testing AnalyticsService: {e}")
    sys.exit(1)

print("[TEST] Testing AuditService methods...")
try:
    from apps.Remote_User.models import prediction_audit
    
    # Test audit filtering
    audit_log = AuditService.get_filtered_audit_log(quick_filter='')
    print(f"✓ AuditService.get_filtered_audit_log() works ({audit_log.count()} records)")
    
    stats = AuditService.get_audit_statistics()
    assert isinstance(stats, dict), "stats should be dict"
    print("✓ AuditService.get_audit_statistics() works")
    
except Exception as e:
    print(f"✗ Error testing AuditService: {e}")
    sys.exit(1)

print("[TEST] Testing TrainingService methods...")
try:
    # Test data normalization
    import pandas as pd
    df = pd.DataFrame({
        'tweet_text': ['threat1', 'safe1'],
        'Label': [1, 0]
    })
    normalized_df = TrainingService.normalize_labels(df)
    assert normalized_df['Label'].tolist() == [1, 0], "Labels not normalized correctly"
    print("✓ TrainingService.normalize_labels() works")
    
except Exception as e:
    print(f"✗ Error testing TrainingService: {e}")
    sys.exit(1)

print("\n" + "="*50)
print("✅ ALL TESTS PASSED!")
print("="*50)
