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
def test_config(tmp_path, monkeypatch):
    config_path = tmp_path / "config_local.yaml"
    with open(config_path, 'w') as f:
        f.write("""
REPO_PATH: '.'
VENV_PATH: ''
VENV_DIR: ''
TEST_COMMAND: ''
AIDER_PATH: ''
MAX_LINE_LENGTH: 100
AUTOPEP8_FIX: false
AIDER_MODEL: 'test-model'
AIDER_WEAK_MODEL: 'test-weak-model'
LINTER: 'pylint'
LINE_COUNT_MAX: 200
LINE_COUNT_MIN: 10
ENABLE_BLACK: false
MAX_CODE_LENGTH: 50000
MAX_QUESTION_LENGTH: 1000
MAX_MEMORY_MB: 512
MAX_CPU_PERCENT: 80.0
DB_CONNECTION_TIMEOUT: 30
DB_CONNECTION_RETRIES: 3
API_RATE_LIMIT: 60
CLEANUP_THRESHOLD_MB: 400
LOG_DIR: 'logs'
MAX_REQUEST_SIZE_MB: 1
""")
    monkeypatch.setenv('PYTEST_CURRENT_TEST', 'True')
    monkeypatch.setattr('blueprints.analyzer.get_config_path', lambda: str(config_path))
    return config_path

@pytest.fixture
def client(test_config, monkeypatch):
    monkeypatch.setenv('PYTEST_CURRENT_TEST', 'True')
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
def test_analyze_endpoint(client, test_config):
    print("\nTesting endpoint:")
    test_data = {
        'code': 'def test(): pass',
        'question': 'What does this do?'
    }
    with app.test_request_context():
        url = url_for('analyzer.analyze')
        print(f"Using URL: {url}")
    
    print(f"Sending request with data: {test_data}")
    response = client.post(url,
                          data=json.dumps(test_data),
                          content_type='application/json')
    print(f"Response status: {response.status_code}")
    print(f"Response data: {response.data.decode()}")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'response' in data
    data = json.loads(response.data)
    assert 'response' in data

@pytest.mark.timeout(30)  # Set 30 second timeout
def test_invalid_input(client):
    test_data = {
        'code': 'invalid python code }',
        'question': 'What?'
    }
    with app.test_request_context():
        url = url_for('analyzer.analyze')
    response = client.post(url,
                         data=json.dumps(test_data),
                         content_type='application/json')
    assert response.status_code == 400  # Expect a 400 Bad Request response
    data = json.loads(response.data)
    assert 'error' in data

# @pytest.mark.timeout(30)  # Set 30 second timeout
# def test_missing_required_fields(client):
#     """Test handling of missing required fields in the request."""
#     test_data = {'code': 'def test(): pass'}  # Missing question
#     response = client.post('/analyze/analyze',
#                           data=json.dumps(test_data),
#                           content_type='application/json')
#     assert response.status_code == 400
#     data = json.loads(response.data)
#     assert 'error' in data

@pytest.mark.timeout(30)  # Set 30 second timeout
def test_large_input_validation(client):
    test_data = {
        'code': 'x' * 1000000,  # Very large code input
        'question': 'What does this do?'
    }
    with app.test_request_context():
        url = url_for('analyzer.analyze')
    response = client.post(url,
                         data=json.dumps(test_data),
                         content_type='application/json')
    assert response.status_code == 400  # Expect a 400 Bad Request response
