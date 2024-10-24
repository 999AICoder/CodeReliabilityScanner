import pytest

@pytest.fixture(autouse=True)
def setup_test_config(tmp_path, monkeypatch):
    """Setup test configuration before any tests run"""
    config_path = tmp_path / "config_local.yaml"
    with open(config_path, 'w') as f:
        f.write("""
REPO_PATH: '.'
VENV_PATH: ''
VENV_DIR: ''
TEST_COMMAND: ''
AIDER_PATH: ''
MAX_LINE_LENGTH: 100
AUTOPEP8_FIX: false
AIDER_MODEL: 'openrouter/anthropic/claude-3.5-sonnet:beta'
AIDER_WEAK_MODEL: 'openrouter/anthropic/claude-3-haiku-20240307'
LINTER: 'pylint'
LINE_COUNT_MAX: 200
LINE_COUNT_MIN: 10
ENABLE_BLACK: false
MAX_CODE_LENGTH: 50000
MAX_QUESTION_LENGTH: 1000
MAX_MEMORY_MB: 1000
API_RATE_LIMIT: 5

LANGUAGE_MAX_LENGTHS:
    default: 50000
    python: 50000

DANGEROUS_PATTERNS:
    default: ['rm -rf', 'sudo', 'chmod']
    python: ['os.system', 'subprocess']
""")
    monkeypatch.setenv('PYTEST_CURRENT_TEST', 'True')
    # Set config path before any imports
    monkeypatch.setattr('blueprints.analyzer.get_config_path', lambda: str(config_path))
    return config_path
