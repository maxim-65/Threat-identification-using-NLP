"""
Training Service Module
Handles ML model training, evaluation, and result storage
"""
from pathlib import Path
import pandas as pd
from django.db import transaction
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn import svm
from sklearn.linear_model import LogisticRegression
from sklearn.tree import ExtraTreeClassifier
from sklearn.metrics import accuracy_score

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
        """Train multiple ML models and return results with accuracy scores"""
        df = TrainingService.normalize_labels(df)
        
        # Vectorize text
        vectorizer = CountVectorizer(max_features=500)
        X = vectorizer.fit_transform(df['tweet_text'].astype(str))
        y = df['Label']
        
        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train models
        models = {
            'Multinomial Naive Bayes': MultinomialNB(),
            'Support Vector Machine': svm.SVC(),
            'Logistic Regression': LogisticRegression(max_iter=100),
            'Extra Tree Classifier': ExtraTreeClassifier(n_estimators=100),
        }
        
        results = []
        for model_name, model in models.items():
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            accuracy = round(accuracy_score(y_test, y_pred) * 100, 2)
            results.append({
                'name': model_name,
                'accuracy': accuracy,
            })
        
        return results, vectorizer, models
    
    @staticmethod
    def store_training_results(results):
        """Store training results to database"""
        with transaction.atomic():
            detection_accuracy.objects.all().delete()
            for result in results:
                detection_accuracy.objects.create(
                    names=result['name'],
                    ratio=result['accuracy']
                )
        return results
    
    @staticmethod
    def get_summary_statistics(results):
        """Generate summary statistics from training results"""
        if not results:
            return {
                'total_models': 0,
                'best_model': '--',
                'best_score': None,
                'avg_score': None,
            }
        
        accuracies = [r['accuracy'] for r in results]
        best_result = max(results, key=lambda x: x['accuracy'])
        
        return {
            'total_models': len(results),
            'best_model': best_result['name'],
            'best_score': round(max(accuracies), 2),
            'avg_score': round(sum(accuracies) / len(accuracies), 2),
        }
