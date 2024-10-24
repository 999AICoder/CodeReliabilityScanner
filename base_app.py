import os
from flask import Flask, render_template, request, jsonify
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_talisman import Talisman
from werkzeug.exceptions import RequestEntityTooLarge

def create_base_app():
    """Create and configure the base Flask application."""
    app = Flask(__name__)
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
                              "'unsafe-inline'"],
                 'style-src': ["'self'", 
                             'cdn.jsdelivr.net',
                             'cdnjs.cloudflare.com',
                             "'unsafe-inline'"],
                 'font-src': ["'self'"],
                 'img-src': ["'self'"],
             },
             force_https=False,
             force_file_save=False,
             strict_transport_security=False if is_development else True,
             session_cookie_secure=False if is_development else True)

    # Register error handlers
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        if request and request.content_type == 'application/json':
            return jsonify({'error': 'CSRF token validation failed'}), 400
        return render_template('error.html', error="CSRF token validation failed"), 400

    @app.errorhandler(RequestEntityTooLarge)
    def handle_request_too_large(e):
        return render_template('error.html', error="File too large"), 413

    return app
