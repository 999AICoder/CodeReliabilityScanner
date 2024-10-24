"""Configuration schema validation module."""
from typing import Dict, Any, List
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ConfigSchema:
    """Schema for configuration validation."""
    REPO_PATH: Path
    VENV_PATH: Path
    VENV_DIR: str
    TEST_COMMAND: str
    AIDER_PATH: str
    MAX_LINE_LENGTH: int
    AUTOPEP8_FIX: bool
    AIDER_MODEL: str
    AIDER_WEAK_MODEL: str
    AIDER_API_KEY: str
    LINTER: str
    LINE_COUNT_MAX: int
    LINE_COUNT_MIN: int
    ENABLE_BLACK: bool
    MAX_CODE_LENGTH: int
    MAX_QUESTION_LENGTH: int
    
    # Language support
    SUPPORTED_LANGUAGES: List[str]
    LANGUAGE_MAX_LENGTHS: Dict[str, int]
    DANGEROUS_PATTERNS: Dict[str, List[str]]
    
    # Resource management limits
    max_memory_mb: int = 512
    max_cpu_percent: float = 80.0
    db_connection_timeout: int = 30
    db_connection_retries: int = 3
    api_rate_limit: int = 60  # requests per minute
    cleanup_threshold_mb: int = 400
    log_dir: str = 'logs'
    
    @classmethod
    def validate(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration dictionary against schema."""
        validated = {}
        
        # Required fields validation
        required_fields = [
            ('REPO_PATH', str, '.'),
            ('VENV_PATH', str, ''),
            ('VENV_DIR', str, ''),
            ('TEST_COMMAND', str, ''),
            ('AIDER_PATH', str, ''),
            ('MAX_LINE_LENGTH', int, 100),
            ('AUTOPEP8_FIX', bool, False),
            ('AIDER_MODEL', str, 'openrouter/anthropic/claude-3.5-sonnet:beta'),
            ('AIDER_WEAK_MODEL', str, 'openrouter/anthropic/claude-3-haiku-20240307'),
            ('LINTER', str, 'pylint'),
            ('LINE_COUNT_MAX', int, 200),
            ('LINE_COUNT_MIN', int, 10),
            ('ENABLE_BLACK', bool, False),
            ('MAX_CODE_LENGTH', int, 50000),
            ('MAX_QUESTION_LENGTH', int, 1000),
            ('MAX_MEMORY_MB', int, 512),
            ('MAX_CPU_PERCENT', float, 80.0),
            ('DB_CONNECTION_TIMEOUT', int, 30),
            ('DB_CONNECTION_RETRIES', int, 3),
            ('API_RATE_LIMIT', int, 60),
            ('CLEANUP_THRESHOLD_MB', int, 400),
            ('LOG_DIR', str, 'logs')
        ]
        
        for field_name, field_type, default_value in required_fields:
            try:
                value = config.get(field_name, default_value)
                if not isinstance(value, field_type):
                    value = field_type(value)
                validated[field_name] = value
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid configuration for {field_name}: {str(e)}")
        
        # Validate language-specific configurations
        supported_languages = config.get('SUPPORTED_LANGUAGES', [])
        if not isinstance(supported_languages, list):
            raise ValueError("SUPPORTED_LANGUAGES must be a list")
        validated['SUPPORTED_LANGUAGES'] = supported_languages

        language_max_lengths = config.get('LANGUAGE_MAX_LENGTHS', {})
        if not isinstance(language_max_lengths, dict):
            raise ValueError("LANGUAGE_MAX_LENGTHS must be a dictionary")
        if 'default' not in language_max_lengths:
            raise ValueError("LANGUAGE_MAX_LENGTHS must include a 'default' value")
        validated['LANGUAGE_MAX_LENGTHS'] = language_max_lengths

        dangerous_patterns = config.get('DANGEROUS_PATTERNS', {})
        if not isinstance(dangerous_patterns, dict):
            raise ValueError("DANGEROUS_PATTERNS must be a dictionary")
        if 'default' not in dangerous_patterns:
            raise ValueError("DANGEROUS_PATTERNS must include a 'default' value")
        validated['DANGEROUS_PATTERNS'] = dangerous_patterns

        # Additional validation rules
        if validated['LINE_COUNT_MIN'] >= validated['LINE_COUNT_MAX']:
            raise ValueError("LINE_COUNT_MIN must be less than LINE_COUNT_MAX")
            
        if validated['MAX_CPU_PERCENT'] > 100 or validated['MAX_CPU_PERCENT'] < 0:
            raise ValueError("MAX_CPU_PERCENT must be between 0 and 100")
            
        if validated['API_RATE_LIMIT'] < 1:
            raise ValueError("API_RATE_LIMIT must be positive")

        # Validate that all supported languages have corresponding max lengths
        for lang in supported_languages:
            if lang not in language_max_lengths and 'default' not in language_max_lengths:
                raise ValueError(f"Missing max length configuration for language: {lang}")
            
        return validated
