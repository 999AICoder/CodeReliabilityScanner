import pytest
import json
from datetime import datetime
from pathlib import Path
from suggestion_db import SuggestionDB

@pytest.fixture
def db():
    """Create a fresh in-memory database for each test."""
    return SuggestionDB()

def test_table_creation(db):
    """Test that the suggestions table is created correctly."""
    # Add a suggestion to verify table exists and has correct schema
    db.add_suggestion(
        file="test.py",
        question="test question",
        response={"response": "test response"},
        model="test-model"
    )
    
    suggestions = db.get_suggestions()
    assert len(suggestions) == 1
    assert suggestions[0]['file'] == "test.py"
    assert suggestions[0]['question'] == "test question"
    assert suggestions[0]['response'] == {"response": "test response"}
    assert suggestions[0]['model'] == "test-model"
    assert 'timestamp' in suggestions[0]

def test_add_and_get_suggestion(db):
    """Test adding and retrieving a suggestion."""
    db.add_suggestion(
        file="test.py",
        question="What does this do?",
        response={"response": "It does something"},
        model="test-model"
    )
    
    suggestions = db.get_suggestions("test.py")
    assert len(suggestions) == 1
    suggestion = suggestions[0]
    assert suggestion['file'] == "test.py"
    assert suggestion['question'] == "What does this do?"
    assert suggestion['response'] == {"response": "It does something"}
    assert suggestion['model'] == "test-model"

def test_get_suggestion_by_id(db):
    """Test retrieving a specific suggestion by ID."""
    db.add_suggestion(
        file="test.py",
        question="question",
        response={"response": "answer"},
        model="test-model"
    )
    
    suggestions = db.get_suggestions()
    suggestion_id = suggestions[0]['id']
    
    suggestion = db.get_suggestion(suggestion_id)
    assert suggestion['id'] == suggestion_id
    assert suggestion['file'] == "test.py"
    assert suggestion['response'] == {"response": "answer"}

def test_update_suggestion(db):
    """Test updating an existing suggestion."""
    db.add_suggestion(
        file="test.py",
        question="question",
        response={"response": "old answer"},
        model="test-model"
    )
    
    suggestions = db.get_suggestions()
    suggestion_id = suggestions[0]['id']
    
    new_response = {"response": "new answer"}
    db.update_suggestion(suggestion_id, new_response)
    
    updated = db.get_suggestion(suggestion_id)
    assert updated['response'] == new_response

def test_delete_suggestion(db):
    """Test deleting a suggestion."""
    db.add_suggestion(
        file="test.py",
        question="question",
        response={"response": "answer"},
        model="test-model"
    )
    
    suggestions = db.get_suggestions()
    suggestion_id = suggestions[0]['id']
    
    db.delete_suggestion(suggestion_id)
    assert db.get_suggestion(suggestion_id) is None
    assert len(db.get_suggestions()) == 0

def test_get_suggestions_filtering(db):
    """Test filtering suggestions by file."""
    db.add_suggestion(
        file="test1.py",
        question="q1",
        response={"response": "a1"},
        model="test-model"
    )
    db.add_suggestion(
        file="test2.py",
        question="q2",
        response={"response": "a2"},
        model="test-model"
    )
    
    suggestions = db.get_suggestions("test1.py")
    assert len(suggestions) == 1
    assert suggestions[0]['file'] == "test1.py"

def test_json_serialization(db):
    """Test that JSON serialization/deserialization works correctly."""
    complex_response = {
        "response": "test",
        "metadata": {
            "confidence": 0.95,
            "timestamp": datetime.now().isoformat()
        }
    }
    
    db.add_suggestion(
        file="test.py",
        question="question",
        response=complex_response,
        model="test-model"
    )
    
    suggestion = db.get_suggestions()[0]
    assert suggestion['response'] == complex_response

def test_file_based_db():
    """Test that file-based database works correctly."""
    # Use a temporary file path
    db_path = "test_suggestions.db"
    try:
        db = SuggestionDB(db_path)
        db.add_suggestion(
            file="test.py",
            question="question",
            response={"response": "answer"},
            model="test-model"
        )
        
        # Create a new connection to verify persistence
        db2 = SuggestionDB(db_path)
        suggestions = db2.get_suggestions()
        assert len(suggestions) == 1
        assert suggestions[0]['file'] == "test.py"
    finally:
        # Cleanup
        if Path(db_path).exists():
            Path(db_path).unlink()
