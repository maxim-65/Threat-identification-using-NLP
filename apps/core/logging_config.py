"""
Logging and Monitoring Configuration
Provides structured logging for API calls, model training, and errors
"""
import logging
import logging.handlers
from pathlib import Path
from django.conf import settings


class RequestLogger:
    """Handles all API request and system logging"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RequestLogger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.log_dir = Path(settings.BASE_DIR) / 'logs'
        self.log_dir.mkdir(exist_ok=True)
        
        # API request logger
        self.api_logger = self._setup_logger(
            'api_requests',
            self.log_dir / 'api_requests.log',
            level=logging.INFO
        )
        
        # Model training logger
        self.training_logger = self._setup_logger(
            'model_training',
            self.log_dir / 'model_training.log',
            level=logging.INFO
        )
        
        # Error logger
        self.error_logger = self._setup_logger(
            'errors',
            self.log_dir / 'errors.log',
            level=logging.ERROR
        )
        
        # Performance logger
        self.performance_logger = self._setup_logger(
            'performance',
            self.log_dir / 'performance.log',
            level=logging.DEBUG
        )
        
        self._initialized = True
    
    @staticmethod
    def _setup_logger(name, log_file, level=logging.INFO):
        """Configure a logger with file rotation"""
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Clear existing handlers to avoid duplicates
        if logger.handlers:
            logger.handlers.clear()
        
        # File handler with rotation (10MB max, keep 5 files)
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=5
        )
        
        # Format: timestamp | level | message
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def log_api_request(self, method, endpoint, status_code, response_time_ms, user_agent=None):
        """Log API request with metrics"""
        self.api_logger.info(
            f"{method} {endpoint} | Status: {status_code} | "
            f"Response: {response_time_ms}ms | UA: {user_agent or 'Unknown'}"
        )
    
    def log_prediction(self, endpoint, input_length, prediction, confidence, inference_time_ms):
        """Log prediction request"""
        self.api_logger.info(
            f"PREDICTION {endpoint} | Input: {input_length}chars | "
            f"Result: {prediction} | Confidence: {confidence} | Inference: {inference_time_ms}ms"
        )
    
    def log_training_start(self, dataset_name, rows):
        """Log training start"""
        self.training_logger.info(f"TRAINING_START | Dataset: {dataset_name} | Size: {rows} rows")
    
    def log_training_complete(self, models_trained, best_model, best_f1, duration_seconds):
        """Log training completion"""
        self.training_logger.info(
            f"TRAINING_COMPLETE | Models: {models_trained} | "
            f"Best: {best_model} (F1: {best_f1}%) | Duration: {duration_seconds}s"
        )
    
    def log_error(self, endpoint, error_msg, exception=None):
        """Log error with optional exception"""
        self.error_logger.error(
            f"{endpoint} | Error: {error_msg} | Exception: {str(exception) if exception else 'N/A'}"
        )
    
    def log_performance(self, operation, duration_ms, success=True):
        """Log performance metrics"""
        status = "SUCCESS" if success else "FAILED"
        self.performance_logger.debug(f"{status} | {operation} | {duration_ms}ms")


# Global logger instance - lazily initialized on first use
logger = None

def get_logger():
    """Get or create the global logger instance"""
    global logger
    if logger is None:
        logger = RequestLogger()
    return logger

