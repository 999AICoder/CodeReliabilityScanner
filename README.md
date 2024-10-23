# Code Quality Improvement Tool

## Overview
This tool is designed to analyze and improve the quality of Python code repositories. It uses various linters, static code analysis tools, and AI-powered suggestions to identify and fix potential issues in your codebase.

This code is considered alpha as of 2024-10-23

98% of this code was written by [aider](https://github.com/Aider-AI/aider) 

## Requirements
- Python 3.12 or higher
- Git
- Virtual environment (recommended)
- SQLite3

## Core Components
- `agent_v2.py`: Main agent for processing Python files
- `aider_runner.py`: Runs Aider to fix code issues
- `command_runner.py`: Executes system commands securely
- `config.py`: Configuration management with validation
- `file_processor.py`: Processes individual files
- `git_manager.py`: Handles Git operations
- `issue_processor.py`: Analyzes and groups code issues
- `linter_runner.py`: Runs various code linters
- `logger.py`: Centralized logging system
- `resource_manager.py`: Manages system resources
- `suggestion_db.py`: SQLite database management
- `suggestion_api.py`: FastAPI-based suggestion API
- `suggestion_cli.py`: CLI interface
- `suggestion_web.py`: Flask web interface

## Features
- Scans Python files in a git repository
- Runs multiple linters (Pylint, Flake8, Ruff)
- Processes and groups issues by type and function
- Uses AI (via Aider) to suggest and apply fixes
- Provides secure web and CLI interfaces
- Supports running tests to validate fixes
- Allows interrogation of specific files using AI
- Resource monitoring and management
- Rate limiting and error handling
- Secure input validation and sanitization

## Installation

1. Install aider-chat:
   ```bash
   pip install aider-chat==0.60.0
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   - For local development:
     ```bash
     pip install -r requirements.txt
     ```
   - For Docker deployment:
     ```bash
     pip install -r requirements.docker.txt
     ```

## Configuration

### Local Development
```bash
cp config_example.yaml config_local.yaml
```

### Docker Deployment
```bash
cp config_example.yaml config_docker.yaml
```

### Key Configuration Options
- `REPO_PATH`: Path to Git repository
- `VENV_PATH`: Virtual environment path
- `TEST_COMMAND`: Command to run tests
- `MAX_LINE_LENGTH`: Maximum line length for code
- `LINTER`: Choice of linter (pylint/flake8/ruff)
- `AIDER_MODEL`: AI model selection
- `MAX_CODE_LENGTH`: Maximum code size
- `MAX_MEMORY_MB`: Memory limit
- `API_RATE_LIMIT`: API call limit

## Resource Management
- Memory limit: Configurable via MAX_MEMORY_MB
- CPU usage monitoring
- Automatic temp file cleanup
- API rate limiting
- Database connection management
- Request size limits

## Security Features
- Input validation and sanitization
- CSRF protection
- Content Security Policy
- Request size limits
- Secure cookie handling
- XSS protection
- Rate limiting
- Resource monitoring

## Database
The application uses SQLite3 for storing:
- Code analysis suggestions
- AI responses
- File metadata
- Timestamps

Database file: `suggestions.db`
Maintenance: Automatic cleanup based on configured thresholds

## Web Interface
Start the web server:
```bash
python app.py
```
Access at http://localhost:8080

Available pages:
- `/`: Code analysis input
- `/suggestions`: Previous analyses
- `/suggestion/<id>`: Detailed view
- `/analyze`: New analysis

## API Server
Start the API:
```bash
uvicorn suggestion_api:app --host 0.0.0.0 --port 8000
```

## Command Line Tools

### Aider Interrogator
```bash
python aider_interrogator.py --file /path/to/file.py --question "Your question"
```

### Suggestion Management
```bash
python suggestion_cli.py [--id <id>] [--delete <id>] [--highlight]
```

### Automated Agent
```bash
python agent_v2.py [--debug] [--max-workers <n>] [--file <path>]
```

## Environment Variables
- `DOCKER_ENV`: Set to 1 for Docker
- `FLASK_SECRET_KEY`: Flask security key
- `FLASK_ENV`: development/production
- `AIDER_API_KEY`: Aider API key
- `GOOGLE_CLOUD_PROJECT`: GCP project ID

## Error Handling
Common errors and solutions:
- Timeout: Reduce code size or increase timeout
- Rate limit: Wait and retry
- Resource limit: Increase limits or reduce load
- Validation: Check input requirements
- Database: Check permissions and space

Automatic retries implemented for:
- API calls
- Database operations
- Command execution

## Logging
Logs include:
- Timestamp
- Log level
- File and line number
- Message

Log levels:
- INFO: Normal operations
- ERROR: Failures and exceptions
- DEBUG: Detailed debugging (when enabled)

## Testing
Run tests:
```bash
python -m pytest
```

Test coverage includes:
- Unit tests
- Integration tests
- Resource management tests
- Security tests

## Docker Deployment
```bash
docker build -t code-quality-tool .
docker run -p 8080:8080 -p 8000:8000 code-quality-tool
```

## Development
This tool is under active development. Contributions welcome!

### Best Practices
- Run tests before commits
- Check resource usage
- Monitor logs
- Review security settings
- Keep dependencies updated

## Support
For issues and questions:
- Check logs
- Review configuration
- Verify dependencies
- Check resource usage
- Review documentation
