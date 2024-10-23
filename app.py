import os
from flask import Flask, request, render_template, abort, jsonify
from flask_wtf.csrf import CSRFProtect
from exceptions import AiderTimeoutError, AiderProcessError, CodeValidationError, MaxRetriesExceededError
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFError
from flask_talisman import Talisman
from pathlib import Path
from aider_interrogator import Agent
from config import Config
import html
from werkzeug.exceptions import RequestEntityTooLarge


def get_config_path():
    """Get the appropriate config file path based on environment."""
    if os.environ.get('DOCKER_ENV'):
        return 'config_docker.yaml'
    return 'config_local.yaml'

# Load config for validation limits
# config_path = get_config_path()
config = Config(get_config_path())
MAX_CODE_LENGTH = config.max_code_length
MAX_QUESTION_LENGTH = config.max_question_length

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # In production, use a secure secret key
csrf = CSRFProtect(app)
# Set a secret key for CSRF protection - in production this should come from environment/config
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-here')
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024  # 1MB max-limit

# Initialize security extensions
csrf = CSRFProtect(app)
is_development = os.environ.get('FLASK_ENV') == 'development'
Talisman(app, 
         content_security_policy={
             'default-src': "'self'",
             'script-src': ["'self'", 
                          'cdnjs.cloudflare.com',
                          "'unsafe-inline'"],  # Required for Prism.js
             'style-src': ["'self'", 
                         'cdn.jsdelivr.net',
                         'cdnjs.cloudflare.com',
                         "'unsafe-inline'"],  # Required for Bootstrap and Prism.js
             'font-src': ["'self'"],
             'img-src': ["'self'"],
         },
         force_https=False,  # Disable HTTPS enforcement
         force_file_save=False,
         strict_transport_security=False if is_development else True,
         session_cookie_secure=False if is_development else True)

from validators import validate_code_safety, sanitize_input

def validate_input(code: str, question: str) -> tuple[bool, str]:
    """
    Validate the input data.
    
    Args:
        code (str): The code to validate
        question (str): The question to validate
        
    Returns:
        tuple[bool, str]: (is_valid, error_message)
    """
    # Basic empty checks
    if not code or not code.strip():
        return False, "Code cannot be empty"
        
    # Length checks
    if len(code) > MAX_CODE_LENGTH:
        return False, f"Code exceeds maximum length of {MAX_CODE_LENGTH} characters"
    if len(question) > MAX_QUESTION_LENGTH:
        return False, f"Question exceeds maximum length of {MAX_QUESTION_LENGTH} characters"
        
    # Sanitize inputs
    code = sanitize_input(code)
    question = sanitize_input(question)
    
    # Safety validation
    is_safe, error_msg = validate_code_safety(code)
    if not is_safe:
        return False, error_msg
    
    return True, ""

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    return render_template('error.html', error="CSRF token validation failed"), 400

@app.errorhandler(RequestEntityTooLarge)
def handle_request_too_large(e):
    return render_template('error.html', error="File too large"), 413

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            code = request.form.get('code', '').strip()
            # question = request.form.get('question', '').strip()
            question = "As the worlds greatest developer what reliability concerns to you see in the code provided?"
            # Validate input
            is_valid, error_message = validate_input(code, question)
            if not is_valid:
                return render_template('error.html', error=error_message), 400
            
            # Initialize Agent with the appropriate config file
            config_path = get_config_path()
            config = Config(config_path)
            agent = Agent(config)
            
            # Get response and escape any HTML
            response = agent.interrogate_code(code, question)
            safe_response = html.escape(response)
            
            # Only show question if not running in Docker
            template_params = {
                'response': safe_response,
                'code': html.escape(code)  # Escape the code as well
            }
            if not os.environ.get('DOCKER_ENV'):
                template_params['question'] = html.escape(question)
            
            return render_template('result.html', **template_params)
            
        except Exception as e:
            app.logger.error(f"Error processing request: {str(e)}")
            error_message = "An unexpected error occurred"
            status_code = 500
            
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
                
            app.logger.error(f"Error processing request: {str(e)}")
            return render_template('error.html', error=error_message), status_code
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8080)  # Set debug=False in production
