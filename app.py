import os
from flask import Flask, request, render_template
from pathlib import Path
from aider_interrogator import Agent
from config import Config

app = Flask(__name__)

def get_config_path():
    if os.environ.get('DOCKER_ENV'):
        return 'config_docker.yaml'
    return 'config_local.yaml'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        code = request.form['code']
        question = request.form['question']
        
        # Initialize Agent with the appropriate config file
        config_path = get_config_path()
        config = Config(config_path)
        agent = Agent(config)
        response = agent.interrogate_code(code, question)
        
        return render_template('result.html', response=response)
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
