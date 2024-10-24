import sys
from pathlib import Path
from unittest.mock import patch, Mock, mock_open

# Add the directory containing agent_v2.py to the PYTHONPATH
sys.path.append(str(Path(__file__).resolve().parent.parent))

import tempfile

import os
import yaml
import pytest
import subprocess
from logger import Logger
from config import Config
from command_runner import CommandRunner
from agent_v2 import Agent, AgentComponents


def test_agent_initialization():
    config_path = Path("config.yaml")
    agent = Agent(config_path)
    assert isinstance(agent.config, Config)
    assert isinstance(agent.logger, Logger)
    assert isinstance(agent.components, AgentComponents)


@patch("agent_v2.git.Repo")
def test_get_tracked_files(mock_repo):
    config_path = Path("config.yaml")
    agent = Agent(config_path)
    mock_repo.return_value.git.ls_files.return_value = "file1.py\nfile2.py"
    mock_repo.return_value.working_dir = "/test/repo"

    tracked_files = agent.get_tracked_files()

    assert tracked_files == ["/test/repo/file1.py", "/test/repo/file2.py"]

@patch('builtins.open', new_callable=mock_open, read_data="dummy_config_data")
def test_run(mock_open):
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch("yaml.safe_load") as mock_yaml_load, patch(
            "agent_v2.FileProcessor.process_file"
        ) as mock_process_file, patch(
            "agent_v2.Agent.get_tracked_files"
        ) as mock_get_tracked_files, patch(
            "pathlib.Path.exists"
        ) as mock_path_exists, patch(
            "time.sleep"
        ), patch(
            "agent_v2.GitManager.is_git_repo"
        ) as mock_is_git_repo:

            mock_yaml_load.return_value = {
                "REPO_PATH": temp_dir,
                "VENV_PATH": os.path.join(temp_dir, "venv"),
                "VENV_DIR": "venv",
                "TEST_COMMAND": ["python", "-m", "pytest"],
                "AIDER_PATH": os.path.join(temp_dir, "aider"),
                "MAX_LINE_LENGTH": 100,
                "LANGUAGE_MAX_LENGTHS": {
                    "default": 50000,
                    "python": 50000
                },
                "DANGEROUS_PATTERNS": {
                    "default": ["rm -rf", "sudo", "chmod"],
                    "python": ["os.system", "subprocess"]
                }
            }
            mock_path_exists.return_value = True
            mock_is_git_repo.return_value = True

            config_path = Path(os.path.join(temp_dir, "config.yaml"))

            agent = Agent(config_path)

            mock_file1 = Path(os.path.join(temp_dir, "file1.py"))
            mock_file2 = Path(os.path.join(temp_dir, "file2.py"))
            mock_get_tracked_files.return_value = [mock_file1, mock_file2]

            mock_file_content = "\n".join(["line " + str(i) for i in range(20)])
            file_mock = mock_open(read_data=mock_file_content)
            file_mock.return_value.__iter__.return_value = mock_file_content.splitlines(True)
            with patch("builtins.open", file_mock), patch("pathlib.Path.exists", return_value=True), patch("agent_v2.Agent.rawgencount", return_value=20):
                agent.run(debug=True)

            mock_process_file.assert_any_call(mock_file1)
            mock_process_file.assert_any_call(mock_file2)

        mock_get_tracked_files.assert_called_once()
        assert mock_process_file.call_count == 2


def test_command_runner():
    config = Mock(spec=Config)
    logger = Mock(spec=Logger)
    command_runner = CommandRunner(config, logger)

    assert command_runner.config == config
    assert command_runner.logger == logger


def test_verify_repo_path():
    with patch("agent_v2.Config") as mock_config, patch("agent_v2.Logger"), patch("agent_v2.GitManager.is_git_repo") as mock_is_git_repo:
        mock_config.return_value.repo_path = Path("/test/repo")
        mock_is_git_repo.return_value = True
        
        agent = Agent(Path("config.yaml"))
        assert agent.verify_repo_path() == True

        mock_is_git_repo.return_value = False
        assert agent.verify_repo_path() == False


def test_display_config_summary(capsys):
    with patch("agent_v2.Config") as mock_config, patch("agent_v2.Logger"), \
         patch("agent_v2.GitManager.is_git_repo", return_value=True):
        mock_config.return_value.repo_path = Path("/test/repo")
        mock_config.return_value.venv_path = Path("/test/venv")
        mock_config.return_value.venv_dir = "venv"
        mock_config.return_value.test_command = ["pytest"]
        mock_config.return_value.aider_path = "/test/aider"
        mock_config.return_value.max_line_length = 100
        mock_config.return_value.autopep8_fix = True
        mock_config.return_value.aider_model = "test-model"
        mock_config.return_value.aider_weak_model = "test-weak-model"
        mock_config.return_value.linter = "pylint"
        mock_config.return_value.line_count_max = 1000
        mock_config.return_value.line_count_min = 10
        mock_config.return_value.enable_black = True
    
        agent = Agent(Path("/test/config.yaml"))
        agent.display_config_summary()

        captured = capsys.readouterr()
        assert "Configuration Summary:" in captured.out
        assert "Repository Path: /test/repo" in captured.out
        assert "Virtual Environment Path: /test/venv" in captured.out
        assert "Virtual Environment Directory: venv" in captured.out
        assert "Test Command: ['pytest']" in captured.out
        assert "Aider Path: /test/aider" in captured.out
        assert "Max Line Length: 100" in captured.out
        assert "Autopep8 Fix: True" in captured.out
        assert "Aider Model: test-model" in captured.out
        assert "Aider Weak Model: test-weak-model" in captured.out
        assert "Linter: pylint" in captured.out
        assert "Line Count Max: 1000" in captured.out
        assert "Line Count Min: 10" in captured.out
        assert "Enable Black: True" in captured.out


@pytest.mark.parametrize("file_count,line_count,expected_process_count", [
    (3, 15, 3),  # All files should be processed
    (3, 5, 0),   # No files should be processed (below min line count)
    (3, 25, 0),  # No files should be processed (above max line count)
])
def test_run_with_different_file_sizes(file_count, line_count, expected_process_count):
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=temp_dir, check=True)
            
        config_path = Path(os.path.join(temp_dir, "config.yaml"))
        config_data = {
            "REPO_PATH": temp_dir,
            "VENV_PATH": os.path.join(temp_dir, "venv"),
            "VENV_DIR": "venv",
            "TEST_COMMAND": ["pytest"],
            "AIDER_PATH": os.path.join(temp_dir, "aider"),
            "MAX_LINE_LENGTH": 100,
            "AUTOPEP8_FIX": True,
            "AIDER_MODEL": "test-model",
            "AIDER_WEAK_MODEL": "test-weak-model",
            "LINTER": "pylint",
            "LINE_COUNT_MAX": 20,
            "LINE_COUNT_MIN": 10,
            "ENABLE_BLACK": True,
            "LANGUAGE_MAX_LENGTHS": {
                "default": 50000,
                "python": 50000
            }
        }
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
    
        with patch(
            "agent_v2.FileProcessor.process_file"
        ) as mock_process_file, patch(
            "agent_v2.Agent.get_tracked_files"
        ) as mock_get_tracked_files, patch(
            "time.sleep"
        ):
            agent = Agent(config_path)
    
            # Mock configuration
            agent.config.line_count_min = 10
            agent.config.line_count_max = 20
            agent.config.venv_dir = "venv"
    
            # Create mock files
            mock_files = [Path(os.path.join(temp_dir, f"file{i}.py")) for i in range(file_count)]
            mock_get_tracked_files.return_value = mock_files
    
            # Mock rawgencount to return the specified line count
            with patch("agent_v2.Agent.rawgencount", return_value=line_count):
                agent.run(debug=True)
    
        assert mock_process_file.call_count == expected_process_count
