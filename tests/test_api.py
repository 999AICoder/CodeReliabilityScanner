import pytest
from flask.testing import FlaskClient
from app import app
import json

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_analyze_endpoint(client):
    test_data = {
        'code': 'def test(): pass',
        'question': 'What does this do?'
    }
    response = client.post('/analyze', 
                          data=json.dumps(test_data),
                          content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'response' in data

def test_invalid_input(client):
    test_data = {
        'code': 'invalid python code }',
        'question': 'What?'
    }
    response = client.post('/analyze', 
                          data=json.dumps(test_data),
                          content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_missing_required_fields(client):
    test_data = {'code': 'def test(): pass'}  # Missing question
    response = client.post('/analyze', 
                          data=json.dumps(test_data),
                          content_type='application/json')
    assert response.status_code == 400

def test_large_input_validation(client):
    test_data = {
        'code': 'x' * 1000000,  # Very large code input
        'question': 'What does this do?'
    }
    response = client.post('/analyze', 
                          data=json.dumps(test_data),
                          content_type='application/json')
    assert response.status_code == 400
