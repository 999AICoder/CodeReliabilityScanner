from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests
import argparse
from datetime import datetime
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # In production, use a secure secret key
csrf = CSRFProtect(app)

@app.route('/')
def analyze():
    """Route for code analysis input"""
    return render_template('analyze.html')

@app.route('/suggestions')
def suggestions():
    """Route for viewing previous suggestions"""
    response = requests.get("http://localhost:8000/suggestions/")
    suggestions = response.json() if response.status_code == 200 else []
    return render_template('suggestions.html', suggestions=suggestions)

@app.route('/', methods=['POST'])
def analyze_code():
    """Handle code analysis submission"""
    try:
        code = request.form.get('code', '').strip()
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
        
        template_params = {
            'response': safe_response,
            'code': html.escape(code)
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
            
        return render_template('error.html', error=error_message), status_code

@app.route('/suggestion/<int:suggestion_id>')
def suggestion_detail(suggestion_id):
    response = requests.get(f"http://localhost:8000/suggestions/{suggestion_id}")
    suggestion = response.json() if response.status_code == 200 else None
    if suggestion:
        suggestion['timestamp'] = datetime.fromisoformat(suggestion['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
    return render_template('suggestion_detail.html', suggestion=suggestion, highlight=app.config['HIGHLIGHT'])

@app.route('/suggestion/<int:suggestion_id>/delete', methods=['POST'])
def delete_suggestion(suggestion_id):
    response = requests.post(f"http://localhost:8000/suggestions/{suggestion_id}/confirm_delete")
    if response.status_code == 200:
        return redirect(url_for('index'))
    else:
        return jsonify({"error": "Failed to delete suggestion"}), 500

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run the Aider Suggestions web interface")
    parser.add_argument("--highlight", action="store_true", help="Enable syntax highlighting")
    args = parser.parse_args()

    app.config['HIGHLIGHT'] = args.highlight
    app.run(debug=True, port=5000)
