"""Input validation utilities for the application."""
import re
from typing import Tuple
from exceptions import CodeValidationError
from config import Config

def get_config_path():
    """Get the appropriate config file path based on environment."""
    import os
    if os.environ.get('DOCKER_ENV'):
        return 'config_docker.yaml'
    return 'config_local.yaml'

def validate_input(code: str, question: str) -> tuple[bool, str]:
    """
    Validate the input data.
    
    Args:
        code (str): The code to validate
        question (str): The question to validate
        
    Returns:
        tuple[bool, str]: (is_valid, error_message)
    """
    # Load config for validation limits
    config = Config(get_config_path())
    
    # Basic empty checks
    if not code or not code.strip():
        return False, "Code cannot be empty"
        
    # Length checks
    if len(code) > config.max_code_length:
        return False, f"Code exceeds maximum length of {config.max_code_length} characters"
    if len(question) > config.max_question_length:
        return False, f"Question exceeds maximum length of {config.max_question_length} characters"
        
    # Sanitize inputs
    code = sanitize_input(code)
    question = sanitize_input(question)
    
    # Safety validation
    is_safe, error_msg = validate_code_safety(code)
    if not is_safe:
        return False, error_msg
    
    return True, ""

def validate_code_safety(code: str) -> tuple[bool, str]:
    """
    Validate code for potentially unsafe patterns.
    
    Args:
        code (str): The code to validate
        
    Returns:
        tuple[bool, str]: (is_valid, error_message)
    """
    try:
        # set strictness - will want to move this to the config
        strict = False
        # Check for potentially dangerous imports
        dangerous_imports = [
            'os.system', 'subprocess.call', 'subprocess.run', 'eval', 'exec',
            '__import__', 'importlib', 'pty', 'popen'
        ]
        if strict:
            for imp in dangerous_imports:
                if imp.lower() in code.lower():
                    return False, f"Potentially unsafe code pattern detected: {imp}"
                
        # Check for reasonable line lengths
        max_line_length = 500
        for line in code.splitlines():
            if len(line) > max_line_length:
                return False, f"Line exceeds maximum length of {max_line_length} characters"
                
        # Check for valid encoding
        try:
            code.encode('utf-8')
        except UnicodeEncodeError:
            return False, "Invalid character encoding detected"
            
        return True, ""
        
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def sanitize_input(text: str) -> str:
    """
    Sanitize input text by removing potentially dangerous characters.
    
    Args:
        text (str): Text to sanitize
        
    Returns:
        str: Sanitized text
    """
    # Remove null bytes
    text = text.replace('\0', '')
    
    # Remove control characters except newlines and tabs
    text = ''.join(char for char in text if char == '\n' or char == '\t' or not chr(0) <= char <= chr(31))
    
    return text
