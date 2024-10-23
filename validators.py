"""Input validation utilities for the application."""
import re
from typing import Tuple

def validate_code_safety(code: str) -> Tuple[bool, str]:
    """
    Validate code for potentially unsafe patterns.
    
    Args:
        code (str): The code to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
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
