import pytest
from flask.testing import FlaskClient
import sys
from pathlib import Path
from flask import url_for
# Add the directory containing agent_v2.py to the PYTHONPATH
sys.path.append(str(Path(__file__).resolve().parent.parent))
from app import app
import json

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SERVER_NAME'] = 'localhost'
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    with app.test_client() as client:
        with app.app_context():
            print("\nRegistered routes:")
            for rule in app.url_map.iter_rules():
                print(f"{rule.endpoint}: {rule.rule}")
            yield client

@pytest.mark.timeout(30)  # Set 30 second timeout
def test_analyze_endpoint(client):
    print("\nTesting endpoint:")
    test_data = {
        'code': 'def test(): pass',
        'question': 'What does this do?'
    }
    with app.test_request_context():
        url = url_for('analyzer.analyze')
        print(f"Using URL: {url}")
    response = client.post(url,
                          data=json.dumps(test_data),
                          content_type='application/json')
    print(f"Response status: {response.status_code}")
    if response.status_code != 200:
        print(f"Response data: {response.data}")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'response' in data

@pytest.mark.timeout(30)  # Set 30 second timeout
def test_invalid_input(client):
    test_data = {
        'code': 'invalid python code }',
        'question': 'What?'
    }
    response = client.post('/analyze/analyze',
                          data=json.dumps(test_data),
                          content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

@pytest.mark.timeout(30)  # Set 30 second timeout
def test_missing_required_fields(client):
    """Test handling of missing required fields in the request."""
    test_data = {'code': 'def test(): pass'}  # Missing question
    response = client.post('/analyze/analyze',
                          data=json.dumps(test_data),
                          content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

@pytest.mark.timeout(30)  # Set 30 second timeout
def test_large_input_validation(client):
    test_data = {
        'code': 'x' * 1000000,  # Very large code input
        'question': 'What does this do?'
    }
    response = client.post('/analyze/analyze',
                          data=json.dumps(test_data),
                          content_type='application/json')
    assert response.status_code == 400
