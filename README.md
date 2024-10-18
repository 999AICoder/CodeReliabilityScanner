# Code Quality Improvement Tool

## Overview
This tool is designed to analyze and improve the quality of Python code repositories. It uses various linters, static code analysis tools, and AI-powered suggestions to identify and fix potential issues in your codebase.

## Features
- Scans Python files in a git repository
- Runs multiple linters (Pylint, Flake8, Ruff)
- Processes and groups issues by type and function
- Uses AI (via Aider) to suggest and apply fixes
- Provides a web interface and CLI for managing suggestions
- Supports running tests to validate fixes
- Allows interrogation of specific files using AI

## Components
- `agent_v2.py`: Main agent for processing Python files
- `aider_runner.py`: Runs Aider to fix code issues
- `linter_runner.py`: Executes various linters on Python files
- `issue_processor.py`: Processes and groups identified issues
- `suggestion_api.py`: API for managing suggestions
- `suggestion_cli.py`: CLI for interacting with suggestions
- `suggestion_web.py`: Web interface for managing suggestions
- `aider_interrogator.py`: Script for interrogating specific files using AI

## How to Use

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Copy the configuration file and update the variables:
   ```
   cp config_example.yaml config.yaml
   ```
   Open `config.yaml` in a text editor and update the variables according to your setup.

3. Run the main agent:
   ```
   python agent_v2.py /path/to/your/repo
   ```

4. Use the CLI or web interface to manage and apply suggestions:
   ```
   python suggestion_cli.py
   ```
   or
   ```
   python suggestion_web.py
   ```

5. To interrogate a specific file using AI:
   ```
   python aider_interrogator.py --file /path/to/file.py --question "Your question about the file"
   ```

## Aider Interrogator
The `aider_interrogator.py` script allows you to ask questions about specific files in your repository using AI. It uses the Aider tool to analyze the file and provide insights based on your questions. This can be useful for understanding complex code, identifying potential issues, or getting suggestions for improvements.

To use the Aider Interrogator:
1. Ensure you have set up the `config.yaml` file correctly, especially the Aider-related settings.
2. Run the script with the `--file` argument pointing to the file you want to interrogate, and the `--question` argument containing your question about the file.
3. The script will use Aider to analyze the file and provide a response to your question.
4. The question and response will be stored in a local database for future reference.

## Customization
You can extend the various components (e.g., `LinterRunner`, `IssueProcessor`) to add more checks or modify the processing logic according to your project's needs.

## Note
This tool is under active development. Please refer to individual component documentation for more detailed usage instructions.
