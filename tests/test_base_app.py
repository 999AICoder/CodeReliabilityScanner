import os
import pytest
from base_app import create_base_app

def test_secret_key_from_env():
    """Test that SECRET_KEY is properly set from environment variable."""
    test_key = 'test-secret-key'
    os.environ['SECRET_KEY'] = test_key
    app = create_base_app()
    assert app.config['SECRET_KEY'] == test_key
    os.environ.pop('SECRET_KEY')  # Clean up

def test_secret_key_default():
    """Test that SECRET_KEY falls back to default when env var is not set."""
    if 'SECRET_KEY' in os.environ:
        os.environ.pop('SECRET_KEY')
    app = create_base_app()
    assert app.config['SECRET_KEY'] == 'dev-key-change-in-production'

def test_csrf_protection_enabled():
    """Test that CSRF protection is enabled."""
    app = create_base_app()
    assert app.config['WTF_CSRF_ENABLED'] is True
