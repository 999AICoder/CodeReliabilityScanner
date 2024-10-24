import os
import html
from flask import Blueprint, render_template, request, jsonify
from config import Config
from aider_interrogator import Agent
from validators import validate_input
from exceptions import (
    AiderTimeoutError, 
    AiderProcessError, 
    CodeValidationError, 
    MaxRetriesExceededError
)

analyzer = Blueprint('analyzer', __name__)

_config_path_override = None

def set_config_path_override(path):
     """Set the config file path override."""
     global _config_path_override
     _config_path_override = path

def get_config_path():
     """Get the appropriate config file path based on environment."""
     global _config_path_override
     if _config_path_override:
         return _config_path_override
     if os.environ.get('DOCKER_ENV'):
         return 'config_docker.yaml'
     return 'config_local.yaml'


def get_config():
    """Get configuration instance."""
    config_path = get_config_path()
    try:
        return Config(config_path)
    except Exception as e:
        raise ValueError(f"Missing required configuration: {str(e)}")

def handle_analyzer_error(e):
    """Handle errors that occur during code analysis."""
    error_message = str(e) or "An unexpected error occurred"
    status_code = getattr(e, 'status_code', 500)
    
    if isinstance(e, AiderTimeoutError):
        error_message = "The request timed out. Please try again with a smaller code sample."
        status_code = 408
    elif isinstance(e, CodeValidationError):
        error_message = str(e)
        status_code = 400
    elif isinstance(e, AiderProcessError):
        error_message = "Failed to process the code. Please try again."
        status_code = 500
    elif isinstance(e, MaxRetriesExceededError):
        error_message = "Maximum retries exceeded. Please try again later."
        status_code = 503
    elif isinstance(e, ValueError):
        error_message = str(e)
        status_code = 400
    
    if request.is_json:
        return jsonify({'error': error_message}), status_code
    return render_template('error.html', error=error_message), status_code

@analyzer.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@analyzer.route('/analyze', methods=['GET', 'POST'])
def analyze():
    if request.method == 'POST':
        try:
            if not request.is_json and not request.form.get('code'):
                return jsonify({'error': 'No code provided'}), 400
            if request.is_json:
                data = request.get_json()
                code = data.get('code', '').strip()
                question = data.get('question', '')
                
                # Validate input
                is_valid, error_message = validate_input(code, question)
                if not is_valid:
                    return jsonify({'error': error_message}), 400
                
                config = get_config()
                agent = Agent(config)
                
                response = agent.interrogate_code(code, question)
                return jsonify({'response': response})
            else:
                code = request.form.get('code', '').strip()
                question = "As the worlds greatest developer what reliability concerns do you see in the code provided? Do not provide any code in your response"
                
                # Validate input
                is_valid, error_message = validate_input(code, question)
                if not is_valid:
                    return render_template('error.html', error=error_message), 400
                
                config = Config(get_config_path())
                agent = Agent(config)
                
                response = agent.interrogate_code(code, question)
                safe_response = html.escape(response)
                
                template_params = {
                    'response': safe_response,
                    'code': html.escape(code)
                }
                if not os.environ.get('DOCKER_ENV'):
                    template_params['question'] = html.escape(question)
                
                return render_template('result.html', **template_params)
            
        except Exception as e:
            return handle_analyzer_error(e)
    
    return render_template('analyze.html')
