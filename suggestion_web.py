from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests
import argparse
from datetime import datetime
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # In production, use a secure secret key
csrf = CSRFProtect(app)

@app.route('/')
def index():
    response = requests.get("http://localhost:8000/suggestions/")
    suggestions = response.json() if response.status_code == 200 else []
    return render_template('index.html', suggestions=suggestions)

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
