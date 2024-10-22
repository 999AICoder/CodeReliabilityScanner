from flask import Flask, request, render_template
import tempfile
from pathlib import Path
from aider_interrogator import Agent
from config import Config

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        code = request.form['code']
        question = request.form['question']
        
        # Initialize Agent and interrogate the code
        config = Config('config.yaml')
        agent = Agent(config)
        response = agent.interrogate_code(code, question)
        
        return render_template('result.html', response=response)
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
