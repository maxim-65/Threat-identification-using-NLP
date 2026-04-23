"""
Input Validation Module
Provides sanitization and validation for all user inputs
"""
import re
from html import escape


class InputValidator:
    """Validates and sanitizes all user inputs"""
    
    # Maximum lengths
    MAX_TEXT_LENGTH = 3000
    MAX_BATCH_SIZE = 100
    MAX_FILENAME_LENGTH = 255
    MAX_USERNAME_LENGTH = 255
    
    # Regex patterns
    SAFE_TEXT_PATTERN = re.compile(r'^[\w\s\.\,\;\:\!\?\-\(\)\"\']+$', re.UNICODE)
    FILENAME_PATTERN = re.compile(r'^[\w\-\. ]+$')
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\.@]+$')
    
    @staticmethod
    def validate_text_input(text, max_length=MAX_TEXT_LENGTH):
        """
        Validate and sanitize text input
        
        Returns: (is_valid, cleaned_text, error_message)
        """
        if not text:
            return False, None, "Text cannot be empty"
        
        if not isinstance(text, str):
            return False, None, "Text must be a string"
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        if len(text) == 0:
            return False, None, "Text cannot be only whitespace"
        
        if len(text) > max_length:
            return False, None, f"Text exceeds maximum length of {max_length} characters"
        
        # Sanitize HTML/script injections
        text = escape(text)
        
        return True, text, None
    
    @staticmethod
    def validate_batch_texts(texts):
        """
        Validate batch text input
        
        Returns: (is_valid, cleaned_texts, error_message)
        """
        if not isinstance(texts, list):
            return False, None, "texts must be a list"
        
        if len(texts) == 0:
            return False, None, "texts list cannot be empty"
        
        if len(texts) > InputValidator.MAX_BATCH_SIZE:
            return False, None, f"Maximum {InputValidator.MAX_BATCH_SIZE} texts allowed, got {len(texts)}"
        
        # Validate each text
        cleaned_texts = []
        for i, text in enumerate(texts):
            is_valid, cleaned, error = InputValidator.validate_text_input(text)
            if not is_valid:
                return False, None, f"Text {i+1}: {error}"
            cleaned_texts.append(cleaned)
        
        return True, cleaned_texts, None
    
    @staticmethod
    def validate_filename(filename):
        """
        Validate uploaded filename
        
        Returns: (is_valid, cleaned_filename, error_message)
        """
        if not filename or not isinstance(filename, str):
            return False, None, "Invalid filename"
        
        filename = filename.strip()
        
        if len(filename) == 0:
            return False, None, "Filename cannot be empty"
        
        if len(filename) > InputValidator.MAX_FILENAME_LENGTH:
            return False, None, f"Filename too long (max {InputValidator.MAX_FILENAME_LENGTH})"
        
        # Allow only safe characters
        if not InputValidator.FILENAME_PATTERN.match(filename):
            return False, None, "Filename contains invalid characters"
        
        return True, filename, None
    
    @staticmethod
    def validate_csv_data(data):
        """
        Validate CSV data structure
        
        Returns: (is_valid, error_message)
        """
        if not isinstance(data, dict):
            return False, "CSV data must be a dictionary"
        
        required_columns = {'tweet_text', 'Label'}
        actual_columns = set(data.keys())
        
        if not required_columns.issubset(actual_columns):
            return False, f"Missing required columns: {required_columns - actual_columns}"
        
        return True, None
    
    @staticmethod
    def sanitize_string(value):
        """Sanitize any string by escaping HTML"""
        if not isinstance(value, str):
            return str(value)
        return escape(value)
    
    @staticmethod
    def validate_numeric_range(value, min_val=None, max_val=None):
        """
        Validate numeric value is within range
        
        Returns: (is_valid, error_message)
        """
        try:
            num = float(value)
            
            if min_val is not None and num < min_val:
                return False, f"Value must be >= {min_val}"
            
            if max_val is not None and num > max_val:
                return False, f"Value must be <= {max_val}"
            
            return True, None
        except (ValueError, TypeError):
            return False, "Value must be numeric"
    
    @staticmethod
    def validate_chart_type(chart_type):
        """Validate chart type from user input"""
        valid_types = {'bar', 'line', 'pie', 'doughnut', 'radar', 'area'}
        
        if chart_type not in valid_types:
            return False, f"Invalid chart type. Must be one of: {valid_types}"
        
        return True, None
    
    @staticmethod
    def extract_safe_dict(data, allowed_keys):
        """
        Extract only allowed keys from dictionary
        Prevents key injection attacks
        
        Returns: Dictionary with only allowed keys
        """
        return {k: v for k, v in data.items() if k in allowed_keys}
