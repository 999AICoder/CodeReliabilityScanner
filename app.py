import os
from flask import Flask, request, render_template, abort
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFError
from flask_talisman import Talisman
from pathlib import Path
from aider_interrogator import Agent
from config import Config
import html
from werkzeug.exceptions import RequestEntityTooLarge

# Load config for validation limits
config = Config(get_config_path())
MAX_CODE_LENGTH = config.max_code_length
MAX_QUESTION_LENGTH = config.max_question_length

app = Flask(__name__)
# Set a secret key for CSRF protection - in production this should come from environment/config
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-here')
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024  # 1MB max-limit

# Initialize security extensions
csrf = CSRFProtect(app)
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
         force_https=not app.debug)

def get_config_path():
    """Get the appropriate config file path based on environment."""
    if os.environ.get('DOCKER_ENV'):
        return 'config_docker.yaml'
    return 'config_local.yaml'

def validate_input(code: str, question: str) -> tuple[bool, str]:
    """Validate the input data."""
    if not code or not code.strip():
        return False, "Code cannot be empty"
    if not question or not question.strip():
        return False, "Question cannot be empty"
    if len(code) > MAX_CODE_LENGTH:
        return False, f"Code exceeds maximum length of {MAX_CODE_LENGTH} characters"
    if len(question) > MAX_QUESTION_LENGTH:
        return False, f"Question exceeds maximum length of {MAX_QUESTION_LENGTH} characters"
    
    # Basic Python syntax check
    try:
        compile(code, '<string>', 'exec')
    except SyntaxError:
        return False, "Invalid Python syntax in code"
    
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
            question = request.form.get('question', '').strip()
            
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
            return render_template('error.html', 
                                error="An error occurred while processing your request"), 500
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8080)  # Set debug=False in production
