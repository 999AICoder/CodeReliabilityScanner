from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from suggestion_db import SuggestionDB
from datetime import datetime

app = FastAPI()
db = SuggestionDB()

class Suggestion(BaseModel):
    file: str
    question: str
    response: Dict
    model: str

class SuggestionResponse(BaseModel):
    id: int
    file: str
    question: str
    response: Dict
    model: str
    timestamp: str

@app.post("/suggestions/", response_model=SuggestionResponse)
def create_suggestion(suggestion: Suggestion):
    db.add_suggestion(suggestion.file, suggestion.question, suggestion.response, suggestion.model)
    return db.get_suggestions(suggestion.file)[0]

@app.get("/suggestions/", response_model=List[SuggestionResponse])
def read_suggestions(file: str = None):
    return db.get_suggestions(file)

@app.get("/suggestions/{suggestion_id}", response_model=SuggestionResponse)
def read_suggestion(suggestion_id: int):
    suggestion = db.get_suggestion(suggestion_id)
    if suggestion is None:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    return suggestion

@app.put("/suggestions/{suggestion_id}", response_model=SuggestionResponse)
def update_suggestion(suggestion_id: int, response: Dict):
    suggestion = db.get_suggestion(suggestion_id)
    if suggestion is None:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    db.update_suggestion(suggestion_id, response)
    return db.get_suggestion(suggestion_id)

@app.delete("/suggestions/{suggestion_id}", response_model=Dict)
def delete_suggestion(suggestion_id: int):
    suggestion = db.get_suggestion(suggestion_id)
    if suggestion is None:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    return suggestion

@app.post("/suggestions/{suggestion_id}/confirm_delete", response_model=Dict)
def confirm_delete_suggestion(suggestion_id: int):
    suggestion = db.get_suggestion(suggestion_id)
    if suggestion is None:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    db.delete_suggestion(suggestion_id)
    return {"message": "Suggestion deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
