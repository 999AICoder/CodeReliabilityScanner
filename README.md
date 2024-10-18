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

## Components
- `agent_v2.py`: Main agent for processing Python files
- `aider_runner.py`: Runs Aider to fix code issues
- `linter_runner.py`: Executes various linters on Python files
- `issue_processor.py`: Processes and groups identified issues
- `suggestion_api.py`: API for managing suggestions
- `suggestion_cli.py`: CLI for interacting with suggestions
- `suggestion_web.py`: Web interface for managing suggestions

## How to Use

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the main agent:
   ```
   python agent_v2.py /path/to/your/repo
   ```

3. Use the CLI or web interface to manage and apply suggestions:
   ```
   python suggestion_cli.py
   ```
   or
   ```
   python suggestion_web.py
   ```

## Customization
You can extend the various components (e.g., `LinterRunner`, `IssueProcessor`) to add more checks or modify the processing logic according to your project's needs.

## Note
This tool is under active development. Please refer to individual component documentation for more detailed usage instructions.
