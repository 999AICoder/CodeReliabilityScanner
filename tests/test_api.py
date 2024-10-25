import pytest
from flask import url_for
import json
import sys
from pathlib import Path
# Add the directory containing agent_v2.py to the PYTHONPATH
sys.path.append(str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def app(setup_test_config):
    # Import app only after config is set up
    from base_app import create_base_app
    from blueprints.analyzer import analyzer
    
    app = create_base_app()
    app.config['TESTING'] = True
    app.config['SERVER_NAME'] = 'localhost'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['LANGUAGE_MAX_LENGTHS'] = {
        'default': 50000,
        'python': 50000
        }

    app.config['DANGEROUS_PATTERNS'] = {
        'default': ['rm -rf', 'sudo', 'chmod'],
        'python': ['os.system', 'subprocess']
    }
    app.register_blueprint(analyzer)
    return app

@pytest.fixture
def client(app):
    with app.test_client() as client:
        with app.app_context():
            yield client

@pytest.mark.timeout(30)  # Set 30 second timeout
def test_analyze_endpoint(client, app):
    print("\nTesting endpoint:")
    test_data = {
        'code': 'def test(): pass',
        'question': 'What does this do?'
    }
    with client.application.test_request_context():
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
    with client.application.test_request_context():
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
    with client.application.test_request_context():
        url = url_for('analyzer.analyze')
    response = client.post(url,
                         data=json.dumps(test_data),
                         content_type='application/json')
    assert response.status_code == 400  # Expect a 400 Bad Request response

def test_result_template_rendering(client):
    """Test that the result template renders correctly with all required URLs."""
    test_data = {
        'code': 'def test(): pass',
        'language': 'python'
    }
    response = client.post(url_for('analyzer.analyze'), data=test_data)
    assert response.status_code == 200
    
    # Check that the response contains the correct URLs
    html_content = response.data.decode()
    assert 'href="/analyze"' in html_content
    
    # Test that we can access the "Back to Home" link
    back_to_home_response = client.get('/analyze')
    assert back_to_home_response.status_code == 200
