"""
REST API Module
Provides programmatic access to threat detection and model metrics
"""
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg, Count

from apps.Remote_User.models import detection_accuracy, prediction_audit
from apps.core.services import AnalyticsService, TrainingService


@csrf_exempt
@require_http_methods(["POST"])
def predict_threat(request):
    """
    REST API endpoint for single threat prediction
    
    POST /api/predict/
    Body: {"text": "suspicious text here"}
    
    Returns: {
        "success": true,
        "prediction": "Cyber Threat Found",
        "confidence": 0.87,
        "model_used": "Logistic Regression"
    }
    """
    try:
        data = json.loads(request.body)
        text_input = data.get('text', '').strip()
        
        if not text_input:
            return JsonResponse({
                'success': False,
                'error': 'Text field is required and cannot be empty'
            }, status=400)
        
        if len(text_input) > 3000:
            return JsonResponse({
                'success': False,
                'error': 'Text exceeds maximum length of 3000 characters'
            }, status=400)
        
        # Use best model (Logistic Regression - 79.34% accuracy)
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        import pandas as pd
        
        try:
            # Load and train on default dataset (in production, load saved model)
            df = TrainingService.load_default_dataset()
            df = TrainingService.normalize_labels(df)
            
            vectorizer = TfidfVectorizer(max_features=500, max_df=0.8, min_df=2)
            X = vectorizer.fit_transform(df['tweet_text'].astype(str))
            y = df['Label']
            
            model = LogisticRegression(max_iter=200)
            model.fit(X, y)
            
            # Predict
            text_vec = vectorizer.transform([text_input])
            prediction = model.predict(text_vec)[0]
            confidence = float(model.predict_proba(text_vec)[0].max())
            
            prediction_label = "Cyber Threat Found" if prediction == 1 else "No Cyber Threat Found"
            
            return JsonResponse({
                'success': True,
                'prediction': prediction_label,
                'confidence': round(confidence, 3),
                'model_used': 'Logistic Regression',
                'input_length': len(text_input)
            })
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Model prediction failed: {str(e)}'
            }, status=500)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def batch_predict(request):
    """
    REST API endpoint for batch threat predictions
    
    POST /api/batch_predict/
    Body: {"texts": ["text1", "text2", ...]}
    
    Returns: {
        "success": true,
        "results": [
            {"text": "text1", "prediction": "Threat Found", "confidence": 0.85},
            ...
        ]
    }
    """
    try:
        data = json.loads(request.body)
        texts = data.get('texts', [])
        
        if not isinstance(texts, list):
            return JsonResponse({
                'success': False,
                'error': 'texts field must be a list'
            }, status=400)
        
        if len(texts) == 0:
            return JsonResponse({
                'success': False,
                'error': 'texts list cannot be empty'
            }, status=400)
        
        if len(texts) > 100:
            return JsonResponse({
                'success': False,
                'error': 'Maximum 100 texts per batch. Got: ' + str(len(texts))
            }, status=400)
        
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.linear_model import LogisticRegression
            
            df = TrainingService.load_default_dataset()
            df = TrainingService.normalize_labels(df)
            
            vectorizer = TfidfVectorizer(max_features=500, max_df=0.8, min_df=2)
            X = vectorizer.fit_transform(df['tweet_text'].astype(str))
            y = df['Label']
            
            model = LogisticRegression(max_iter=200)
            model.fit(X, y)
            
            # Batch predict
            texts_vec = vectorizer.transform(texts)
            predictions = model.predict(texts_vec)
            confidences = model.predict_proba(texts_vec).max(axis=1)
            
            results = []
            for text, pred, conf in zip(texts, predictions, confidences):
                pred_label = "Cyber Threat Found" if pred == 1 else "No Cyber Threat Found"
                results.append({
                    'text': text[:100] + '...' if len(text) > 100 else text,
                    'prediction': pred_label,
                    'confidence': round(float(conf), 3)
                })
            
            return JsonResponse({
                'success': True,
                'batch_size': len(texts),
                'results': results
            })
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Batch prediction failed: {str(e)}'
            }, status=500)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def model_metrics(request):
    """
    REST API endpoint for current model metrics and performance
    
    GET /api/metrics/
    
    Returns: {
        "success": true,
        "models": [
            {
                "name": "Logistic Regression",
                "accuracy": 79.34,
                "status": "best_model"
            },
            ...
        ],
        "predictions_summary": {
            "total": 28,
            "threats_found": 24,
            "no_threats": 4,
            "threat_ratio": "85.71%"
        }
    }
    """
    try:
        # Get model accuracies
        accuracies = list(detection_accuracy.objects.all().values('names', 'ratio'))
        
        # Parse accuracy data
        models_data = []
        best_accuracy = 0
        best_model_name = None
        
        for acc in accuracies:
            try:
                # Extract accuracy from ratio field (format: "79.34% (P:... R:... F1:...)")
                ratio_str = str(acc['ratio']).split('%')[0].strip()
                accuracy_val = float(ratio_str)
                
                if accuracy_val > best_accuracy:
                    best_accuracy = accuracy_val
                    best_model_name = acc['names']
                
                models_data.append({
                    'name': acc['names'],
                    'accuracy': accuracy_val,
                    'status': 'best_model' if accuracy_val == best_accuracy else 'active'
                })
            except:
                models_data.append({
                    'name': acc['names'],
                    'accuracy': None,
                    'status': 'unknown'
                })
        
        # Get prediction statistics
        total_preds = prediction_audit.objects.count()
        threat_preds = prediction_audit.objects.filter(predicted_label='Cyber Threat Found').count()
        no_threat_preds = total_preds - threat_preds
        threat_ratio = round((threat_preds / total_preds * 100), 2) if total_preds > 0 else 0
        
        return JsonResponse({
            'success': True,
            'models': models_data,
            'predictions_summary': {
                'total': total_preds,
                'threats_found': threat_preds,
                'no_threats': no_threat_preds,
                'threat_ratio': f'{threat_ratio}%'
            },
            'best_model': best_model_name,
            'best_accuracy': best_accuracy
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def health_check(request):
    """
    REST API endpoint for service health check
    
    GET /api/health/
    
    Returns: {"status": "healthy", "service": "Threat Detection API"}
    """
    try:
        # Verify database connectivity
        total_models = detection_accuracy.objects.count()
        total_predictions = prediction_audit.objects.count()
        
        return JsonResponse({
            'status': 'healthy',
            'service': 'Threat Detection API',
            'models_available': total_models,
            'predictions_recorded': total_predictions
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=503)


@require_http_methods(["GET"])
def api_documentation(request):
    """
    REST API documentation endpoint
    
    GET /api/docs/
    """
    docs = {
        'service': 'Automated Emerging Cyber Threat Identification API',
        'version': '2.0',
        'endpoints': [
            {
                'url': '/api/predict/',
                'method': 'POST',
                'description': 'Single threat prediction',
                'params': {'text': 'string (max 3000 chars)'},
                'returns': {
                    'success': 'boolean',
                    'prediction': 'string',
                    'confidence': 'float (0-1)',
                    'model_used': 'string'
                }
            },
            {
                'url': '/api/batch_predict/',
                'method': 'POST',
                'description': 'Batch threat predictions (up to 100)',
                'params': {'texts': 'list of strings'},
                'returns': {
                    'success': 'boolean',
                    'batch_size': 'int',
                    'results': 'list of predictions'
                }
            },
            {
                'url': '/api/metrics/',
                'method': 'GET',
                'description': 'Get current model metrics and statistics',
                'returns': {
                    'success': 'boolean',
                    'models': 'list',
                    'predictions_summary': 'dict'
                }
            },
            {
                'url': '/api/health/',
                'method': 'GET',
                'description': 'Service health check',
                'returns': {
                    'status': 'string',
                    'models_available': 'int',
                    'predictions_recorded': 'int'
                }
            }
        ],
        'examples': {
            'predict': {
                'request': 'POST /api/predict/\n{"text": "suspicious activity detected"}',
                'response': '{"success": true, "prediction": "Cyber Threat Found", "confidence": 0.87}'
            },
            'metrics': {
                'request': 'GET /api/metrics/',
                'response': '{"success": true, "best_model": "Logistic Regression", "best_accuracy": 79.34}'
            }
        }
    }
    return JsonResponse(docs)
