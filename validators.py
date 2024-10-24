"""Input validation utilities for the application."""
from config import Config
from typing import Optional, Tuple

def get_config_path():
    """Get the appropriate config file path based on environment."""
    import os
    if os.environ.get('DOCKER_ENV'):
        return 'config_docker.yaml'
    return 'config_local.yaml'

def detect_language(code: str) -> Optional[str]:
    """
    Attempt to detect the programming language from the code.
    
    Args:
        code (str): The code to analyze
        
    Returns:
        Optional[str]: Detected language or None if unable to determine
    """
    # Simple language detection based on common patterns
    indicators = {
        'python': ['.py', 'def ', 'import ', 'class ', 'print('],
        'javascript': ['function ', 'const ', 'let ', 'var ', 'console.log'],
        'java': ['public class ', 'private ', 'protected ', 'System.out'],
        'cpp': ['#include', 'using namespace', 'std::'],
        'csharp': ['using System;', 'namespace ', 'public class'],
        'go': ['package ', 'func ', 'import ('],
        'rust': ['fn ', 'let mut ', 'use std'],
        'typescript': ['interface ', 'type ', 'export class'],
        'ruby': ['def ', 'require ', 'module ', 'puts '],
        'php': ['<?php', 'function ', 'echo ', '$']
    }
    
    code_lower = code.lower()
    matches = {}
    
    for lang, patterns in indicators.items():
        matches[lang] = sum(1 for pattern in patterns if pattern.lower() in code_lower)
    
    if matches:
        best_match = max(matches.items(), key=lambda x: x[1])
        if best_match[1] > 0:
            return best_match[0]
    
    return None

def validate_input(code: str, question: str, language: str = None) -> Tuple[bool, str]:
    """
    Validate the input data.
    
    Args:
        code (str): The code to validate
        question (str): The question to validate
        
    Returns:
        tuple[bool, str]: (is_valid, error_message)
    """
    config = Config(get_config_path())
    
    if not code or not code.strip():
        return False, "Code cannot be empty"

    # Detect language if not provided
    if not language:
        language = detect_language(code)
    
    if language and language not in config.supported_languages:
        return False, f"Unsupported programming language: {language}"
    
    # Get language-specific max length
    max_length = config.language_max_lengths.get(
        language,
        config.language_max_lengths['default']
    )
    
    # Length checks
    if len(code) > max_length:
        return False, f"Code exceeds maximum length of {max_length} characters for {language or 'unknown'} language"
    if len(question) > config.max_question_length:
        return False, f"Question exceeds maximum length of {config.max_question_length} characters"
        
    # Sanitize inputs
    code = sanitize_input(code)
    question = sanitize_input(question)
    
    # Safety validation
    is_safe, error_msg = validate_code_safety(code, language, config)
    if not is_safe:
        return False, error_msg
    
    return True, ""

def validate_code_safety(code: str, language: str, config: Config) -> Tuple[bool, str]:
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
