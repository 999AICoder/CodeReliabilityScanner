from flask import Blueprint, render_template, request, jsonify, redirect, url_for
import requests
from datetime import datetime

suggestions = Blueprint('suggestions', __name__)

@suggestions.route('/suggestions')
def list_suggestions():
    """Route for viewing previous suggestions"""
    response = requests.get("http://localhost:8000/suggestions/")
    suggestions = response.json() if response.status_code == 200 else []
    return render_template('suggestions.html', suggestions=suggestions)

@suggestions.route('/suggestion/<int:suggestion_id>')
def suggestion_detail(suggestion_id):
    response = requests.get(f"http://localhost:8000/suggestions/{suggestion_id}")
    suggestion = response.json() if response.status_code == 200 else None
    if suggestion:
        suggestion['timestamp'] = datetime.fromisoformat(suggestion['timestamp']).strftime('%Y-%m-%-d %H:%M:%S')
    return render_template('suggestion_detail.html', suggestion=suggestion)

@suggestions.route('/suggestion/<int:suggestion_id>/delete', methods=['POST'])
def delete_suggestion(suggestion_id):
    response = requests.post(f"http://localhost:8000/suggestions/{suggestion_id}/confirm_delete")
    if response.status_code == 200:
        return redirect(url_for('suggestions.list_suggestions'))
    else:
        return jsonify({"error": "Failed to delete suggestion"}), 500
