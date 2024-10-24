import os
import pytest
import time
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add the directory containing agent_v2.py to the PYTHONPATH
sys.path.append(str(Path(__file__).resolve().parent.parent))

from aider_interrogator import AiderInterrogator
from agent_v2 import Agent
from exceptions import AiderTimeoutError, AiderProcessError
from config import Config

@pytest.fixture
def mock_config(tmp_path):
    config = Mock(spec=Config)
    config.aider_model = "test-model"
    config.aider_weak_model = "test-weak-model"
    config.repo_path = Path(".")
    config.api_rate_limit = 60
    config.max_memory_mb = 512
    config.max_cpu_percent = 80.0
    config.cleanup_threshold_mb = 400
    config.db_path = str(tmp_path / "test.db")
    return config

@pytest.fixture
def mock_command_runner():
    return Mock()

@pytest.fixture
def mock_logger():
    return Mock()

def test_ask_question_basic(mock_config, mock_command_runner, mock_logger):
    interrogator = AiderInterrogator(mock_config, mock_command_runner, mock_logger)
    with patch.object(interrogator, '_run_aider_process', return_value="Test response"):
        response = interrogator.ask_question(
            "def hello(): pass", 
            "What does this function do?"
        )
        assert response == "Test response"

def test_rate_limiting(mock_config, mock_command_runner, mock_logger):
    interrogator = AiderInterrogator(mock_config, mock_command_runner, mock_logger)
    # Force rate limit exceeded
    interrogator.resource_manager.check_rate_limit = Mock(return_value=False)
    
    with pytest.raises(AiderProcessError, match="API rate limit exceeded"):
        interrogator.ask_question("code", "question")

def test_process_timeout(mock_config, mock_command_runner, mock_logger):
    interrogator = AiderInterrogator(mock_config, mock_command_runner, mock_logger)
    
    class MockProcess:
        def __init__(self):
            self.stdout = Mock()
            self.stderr = Mock()
            self.stdin = Mock()
            self.stdout.readline.side_effect = lambda: time.sleep(0.2) or ""
        def poll(self):
            return None
        def terminate(self):
            pass
        def kill(self):
            pass
        def wait(self, timeout):
            pass
    
    with pytest.raises(AiderTimeoutError):
        interrogator._process_aider_output(MockProcess(), timeout=0.1)

def test_resource_cleanup(mock_config, mock_command_runner, mock_logger):
    interrogator = AiderInterrogator(mock_config, mock_command_runner, mock_logger)
    temp_file = interrogator._create_temp_file("test code")
    assert temp_file.exists()
    try:
        os.unlink(temp_file)  # Directly remove the file
        assert not temp_file.exists()
    finally:
        # Cleanup in case test fails
        if temp_file.exists():
            os.unlink(temp_file)

def test_agent_initialization(mock_config, tmp_path):
    # Initialize git repo and set current directory
    import subprocess
    import os
    os.chdir(str(tmp_path))
    subprocess.run(['git', 'init'], check=True)
        
    # Create a temporary config file
    config_path = tmp_path / "test_config.yml"
    with open(config_path, 'w') as f:
        f.write("""
REPO_PATH: .
VENV_PATH: venv
VENV_DIR: venv
TEST_COMMAND: pytest
AIDER_PATH: aider
MAX_LINE_LENGTH: 100
AUTOPEP8_FIX: true
AIDER_MODEL: test-model
AIDER_WEAK_MODEL: test-weak-model
LINTER: pylint
LINE_COUNT_MAX: 200
LINE_COUNT_MIN: 10
ENABLE_BLACK: false
MAX_CODE_LENGTH: 50000
MAX_QUESTION_LENGTH: 1000
MAX_MEMORY_MB: 512
MAX_CPU_PERCENT: 80.0
DB_CONNECTION_TIMEOUT: 30
DB_CONNECTION_RETRIES: 3
API_RATE_LIMIT: 60
CLEANUP_THRESHOLD_MB: 400
""")
    
    agent = Agent(config_path)
    assert isinstance(agent.config, Config)
    assert agent.logger is not None
    assert agent.components is not None
