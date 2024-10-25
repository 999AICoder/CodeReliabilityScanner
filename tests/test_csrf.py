import pytest
from flask import url_for
import json

@pytest.fixture
def app(setup_test_config):
    from base_app import create_base_app
    from blueprints.analyzer import analyzer
    
    app = create_base_app()
    app.config['TESTING'] = True
    app.config['SERVER_NAME'] = 'localhost'
    # Enable CSRF for testing
    app.config['WTF_CSRF_ENABLED'] = True
    # Register the analyzer blueprint
    app.register_blueprint(analyzer)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_csrf_token_present(client):
    """Test that CSRF token is present in the form."""
    response = client.get('/analyze')
    assert response.status_code == 200
    assert b'csrf_token' in response.data

def test_csrf_protection_post(client):
    """Test that POST requests without CSRF token are rejected."""
    response = client.post('/analyze', data={
        'code': 'print("hello")',
        'question': 'What does this do?'
    })
    assert response.status_code == 400
    assert b'CSRF token validation failed' in response.data

def test_csrf_protection_json(client):
    """Test that JSON requests without CSRF token are rejected."""
    response = client.post('/analyze/analyze',
                         data=json.dumps({
                             'code': 'print("hello")',
                             'question': 'What does this do?'
                         }),
                         content_type='application/json')
    assert response.status_code == 400
    assert b'CSRF token validation failed' in response.data

def test_csrf_token_validation(client):
    """Test that requests with valid CSRF token are accepted."""
    # First get a valid CSRF token
    response = client.get('/analyze')
    html = response.data.decode()
    
    # Extract CSRF token from the form
    import re
    csrf_token = re.search('name="csrf_token" value="(.+?)"', html).group(1)
    
    # Make request with valid token
    response = client.post('/analyze', data={
        'csrf_token': csrf_token,
        'code': 'print("hello")',
        'question': 'What does this do?'
    })
    assert response.status_code == 200

def test_csrf_token_invalid(client):
    """Test that requests with invalid CSRF token are rejected."""
    response = client.post('/analyze', data={
        'csrf_token': 'invalid-token',
        'code': 'print("hello")',
        'question': 'What does this do?'
    })
    assert response.status_code == 400
    assert b'CSRF token validation failed' in response.data
