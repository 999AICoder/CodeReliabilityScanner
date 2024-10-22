from flask import Flask, request, render_template
import tempfile
from pathlib import Path
from aider_interrogator import Agent, Config

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        code = request.form['code']
        question = request.form['question']
        
        # Save code to a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(code)
            temp_file_path = Path(temp_file.name)
        
        # Initialize Agent and interrogate the file
        config = Config('config.yaml')
        agent = Agent(config)
        response = agent.interrogate_file(temp_file_path, question)
        
        # Clean up the temporary file
        temp_file_path.unlink()
        
        return render_template('result.html', response=response)
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
