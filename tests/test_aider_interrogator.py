import pytest
import time
from pathlib import Path
from unittest.mock import Mock, patch
from aider_interrogator import AiderInterrogator, Agent
from exceptions import AiderTimeoutError, AiderProcessError
from config import Config

@pytest.fixture
def mock_config(tmp_path):
    config = Mock(spec=Config)
    config.aider_model = "test-model"
    config.aider_weak_model = "test-weak-model"
    config.repo_path = Path(".")
    # Use a temporary directory for the database
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
    interrogator._cleanup_resources(temp_file)
    assert not temp_file.exists()

def test_agent_initialization(mock_config):
    agent = Agent(mock_config)
    assert agent.config == mock_config
    assert agent.logger is not None
    assert agent.components is not None
