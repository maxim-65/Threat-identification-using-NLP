"""
Model Persistence Module
Handles saving and loading trained models for fast inference
"""
import os
import pickle
import joblib
from pathlib import Path
from django.conf import settings


class ModelManager:
    """Manages model serialization and caching"""
    
    MODEL_DIR = Path(settings.BASE_DIR) / 'models'
    
    @classmethod
    def ensure_model_dir(cls):
        """Create models directory if it doesn't exist"""
        cls.MODEL_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def save_model(cls, model, model_name):
        """
        Save trained model to disk using joblib (faster than pickle)
        
        Args:
            model: Trained sklearn model
            model_name: Name of the model (e.g., 'logistic_regression')
        """
        cls.ensure_model_dir()
        model_path = cls.MODEL_DIR / f"{model_name}.joblib"
        
        try:
            joblib.dump(model, model_path)
            print(f"✓ Model saved: {model_path}")
            return str(model_path)
        except Exception as e:
            print(f"✗ Failed to save model: {str(e)}")
            return None
    
    @classmethod
    def load_model(cls, model_name):
        """
        Load trained model from disk
        
        Args:
            model_name: Name of the model to load
            
        Returns:
            Loaded model or None if not found
        """
        model_path = cls.MODEL_DIR / f"{model_name}.joblib"
        
        if not model_path.exists():
            return None
        
        try:
            model = joblib.load(model_path)
            print(f"✓ Model loaded: {model_path}")
            return model
        except Exception as e:
            print(f"✗ Failed to load model: {str(e)}")
            return None
    
    @classmethod
    def save_vectorizer(cls, vectorizer):
        """Save TF-IDF vectorizer to disk"""
        cls.ensure_model_dir()
        vectorizer_path = cls.MODEL_DIR / "tfidf_vectorizer.joblib"
        
        try:
            joblib.dump(vectorizer, vectorizer_path)
            print(f"✓ Vectorizer saved: {vectorizer_path}")
            return str(vectorizer_path)
        except Exception as e:
            print(f"✗ Failed to save vectorizer: {str(e)}")
            return None
    
    @classmethod
    def load_vectorizer(cls):
        """Load TF-IDF vectorizer from disk"""
        vectorizer_path = cls.MODEL_DIR / "tfidf_vectorizer.joblib"
        
        if not vectorizer_path.exists():
            return None
        
        try:
            vectorizer = joblib.load(vectorizer_path)
            print(f"✓ Vectorizer loaded: {vectorizer_path}")
            return vectorizer
        except Exception as e:
            print(f"✗ Failed to load vectorizer: {str(e)}")
            return None
    
    @classmethod
    def model_exists(cls, model_name):
        """Check if a model file exists"""
        model_path = cls.MODEL_DIR / f"{model_name}.joblib"
        return model_path.exists()
    
    @classmethod
    def vectorizer_exists(cls):
        """Check if vectorizer exists"""
        vectorizer_path = cls.MODEL_DIR / "tfidf_vectorizer.joblib"
        return vectorizer_path.exists()
    
    @classmethod
    def get_latest_model_timestamp(cls):
        """Get timestamp of latest model save"""
        if not cls.MODEL_DIR.exists():
            return None
        
        joblib_files = list(cls.MODEL_DIR.glob("*.joblib"))
        if not joblib_files:
            return None
        
        latest_file = max(joblib_files, key=lambda p: p.stat().st_mtime)
        return latest_file.stat().st_mtime
    
    @classmethod
    def cleanup_models(cls):
        """Delete all saved models"""
        if not cls.MODEL_DIR.exists():
            return
        
        try:
            for model_file in cls.MODEL_DIR.glob("*.joblib"):
                model_file.unlink()
            print(f"✓ All models cleaned up")
        except Exception as e:
            print(f"✗ Failed to cleanup models: {str(e)}")
    
    @classmethod
    def get_model_size_mb(cls, model_name):
        """Get size of saved model in MB"""
        model_path = cls.MODEL_DIR / f"{model_name}.joblib"
        if not model_path.exists():
            return 0
        
        size_bytes = model_path.stat().st_size
        return round(size_bytes / (1024 * 1024), 2)
