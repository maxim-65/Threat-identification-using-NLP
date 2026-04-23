"""
Training Service Module
Handles ML model training, evaluation, and result storage with advanced metrics and explainability
"""
from pathlib import Path
import pandas as pd
import numpy as np
from django.db import transaction
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn import svm
from sklearn.linear_model import LogisticRegression
from sklearn.tree import ExtraTreeClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
)

from apps.Remote_User.models import detection_accuracy, detection_ratio


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATASET_PATH = PROJECT_ROOT / 'data' / 'Datasets.csv'


class TrainingService:
    """Service for handling model training and evaluation"""
    
    @staticmethod
    def load_default_dataset():
        """Load the default training dataset"""
        if not DATASET_PATH.exists():
            raise FileNotFoundError(f"Dataset not found at {DATASET_PATH}")
        return pd.read_csv(DATASET_PATH)
    
    @staticmethod
    def load_uploaded_dataset(uploaded_file):
        """Load and validate uploaded CSV dataset"""
        try:
            df = pd.read_csv(uploaded_file)
            required_cols = {'tweet_text', 'Label'}
            actual_cols = set(df.columns)
            
            if not required_cols.issubset(actual_cols):
                raise ValueError(
                    f"Missing required columns. Expected: {required_cols}, "
                    f"Got: {actual_cols}"
                )
            return df
        except Exception as e:
            raise ValueError(f"Failed to load CSV: {str(e)}")
    
    @staticmethod
    def normalize_labels(df):
        """Normalize label column to binary 0/1 format"""
        df = df.copy()
        
        def normalize_value(val):
            if isinstance(val, str):
                val_lower = val.lower().strip()
                if val_lower in ['cyber threat found', 'threat', '1', 'true', 'yes']:
                    return 1
                return 0
            return 1 if int(val) == 1 else 0
        
        df['Label'] = df['Label'].apply(normalize_value)
        return df
    
    @staticmethod
    def train_models(df):
        """
        Train multiple ML models with advanced metrics, SMOTE for imbalance handling,
        and feature importance extraction
        """
        # Lazy import SMOTE only when needed
        try:
            from imblearn.over_sampling import SMOTE
            use_smote = True
        except ImportError:
            print("Warning: imbalanced-learn not installed. Running without SMOTE.")
            use_smote = False
        
        df = TrainingService.normalize_labels(df)
        
        # Vectorize text using TF-IDF (improved from CountVectorizer)
        vectorizer = TfidfVectorizer(max_features=500, max_df=0.8, min_df=2)
        X = vectorizer.fit_transform(df['tweet_text'].astype(str))
        y = df['Label']
        
        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Apply SMOTE to handle class imbalance (if available)
        if use_smote:
            smote = SMOTE(random_state=42, k_neighbors=3)
            X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)
        else:
            X_train_balanced, y_train_balanced = X_train, y_train
        
        # Train models
        models = {
            'Multinomial Naive Bayes': MultinomialNB(),
            'Support Vector Machine': svm.SVC(kernel='rbf', probability=True),
            'Logistic Regression': LogisticRegression(max_iter=200),
            'Extra Tree Classifier': ExtraTreeClassifier(n_estimators=100, random_state=42),
        }
        
        results = []
        feature_importance_dict = {}
        
        for model_name, model in models.items():
            # Train on balanced data
            model.fit(X_train_balanced, y_train_balanced)
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            accuracy = round(accuracy_score(y_test, y_pred) * 100, 2)
            precision = round(precision_score(y_test, y_pred, zero_division=0) * 100, 2)
            recall = round(recall_score(y_test, y_pred, zero_division=0) * 100, 2)
            f1 = round(f1_score(y_test, y_pred, zero_division=0) * 100, 2)
            
            # Get confusion matrix
            cm = confusion_matrix(y_test, y_pred)
            tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (cm[0, 0], 0, 0, cm[1, 1])
            
            # Extract feature importance
            top_features = TrainingService.get_feature_importance(
                model, model_name, vectorizer, X_train_balanced
            )
            
            result = {
                'name': model_name,
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'confusion_matrix': {'tn': int(tn), 'fp': int(fp), 'fn': int(fn), 'tp': int(tp)},
                'top_features': top_features,
            }
            
            results.append(result)
            feature_importance_dict[model_name] = top_features
        
        return results, vectorizer, models
    
    @staticmethod
    def get_feature_importance(model, model_name, vectorizer, X_train):
        """
        Extract feature importance from trained models
        Provides model explainability for recruiters
        """
        feature_names = np.array(vectorizer.get_feature_names_out())
        top_features = []
        
        try:
            # For tree-based models and Logistic Regression
            if hasattr(model, 'coef_'):
                # Logistic Regression coefficients
                coef = model.coef_[0]
                top_indices = np.argsort(np.abs(coef))[-5:][::-1]
                top_features = [
                    {'feature': feature_names[i], 'importance': round(float(coef[i]), 4)}
                    for i in top_indices
                ]
            elif hasattr(model, 'feature_importances_'):
                # Tree-based models
                importances = model.feature_importances_
                top_indices = np.argsort(importances)[-5:][::-1]
                top_features = [
                    {'feature': feature_names[i], 'importance': round(float(importances[i]), 4)}
                    for i in top_indices
                ]
        except Exception as e:
            print(f"Could not extract features for {model_name}: {str(e)}")
        
        return top_features
    
    @staticmethod
    def store_training_results(results):
        """Store advanced training results to database (metrics displayed in dashboard)"""
        with transaction.atomic():
            detection_accuracy.objects.all().delete()
            for result in results:
                # Store main accuracy + other metrics as formatted string
                metric_display = f"{result['accuracy']}% (P:{result['precision']}% R:{result['recall']}% F1:{result['f1_score']}%)"
                detection_accuracy.objects.create(
                    names=result['name'],
                    ratio=metric_display  # Store all metrics in ratio field
                )
        return results
    
    @staticmethod
    def get_summary_statistics(results):
        """Generate comprehensive summary statistics from training results"""
        if not results:
            return {
                'total_models': 0,
                'best_model': '--',
                'best_accuracy': None,
                'avg_accuracy': None,
                'best_f1': None,
                'avg_recall': None,
            }
        
        accuracies = [r['accuracy'] for r in results]
        f1_scores = [r['f1_score'] for r in results]
        recalls = [r['recall'] for r in results]
        best_result = max(results, key=lambda x: x['f1_score'])  # Use F1 as primary metric
        
        return {
            'total_models': len(results),
            'best_model': best_result['name'],
            'best_accuracy': round(max(accuracies), 2),
            'avg_accuracy': round(sum(accuracies) / len(accuracies), 2),
            'best_f1': round(max(f1_scores), 2),
            'avg_recall': round(sum(recalls) / len(recalls), 2),
            'best_model_metrics': {
                'accuracy': best_result['accuracy'],
                'precision': best_result['precision'],
                'recall': best_result['recall'],
                'f1_score': best_result['f1_score'],
            }
        }
