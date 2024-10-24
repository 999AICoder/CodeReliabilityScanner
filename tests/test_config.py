import pytest
import tempfile
from pathlib import Path
from config import Config
import yaml

@pytest.fixture
def valid_config_file():
    config_data = {
        'REPO_PATH': '.',
        'VENV_PATH': 'venv',
        'VENV_DIR': 'venv',
        'TEST_COMMAND': 'pytest',
        'AIDER_PATH': 'aider',
        'MAX_LINE_LENGTH': 100,
        'AUTOPEP8_FIX': True,
        'AIDER_MODEL': 'test-model',
        'AIDER_WEAK_MODEL': 'test-weak-model',
        'LINTER': 'pylint',
        'LINE_COUNT_MAX': 200,
        'LINE_COUNT_MIN': 10,
        'ENABLE_BLACK': False,
        'MAX_CODE_LENGTH': 50000,
        'MAX_QUESTION_LENGTH': 1000,
        'MAX_MEMORY_MB': 512,
        'MAX_CPU_PERCENT': 80.0,
        'DB_CONNECTION_TIMEOUT': 30,
        'DB_CONNECTION_RETRIES': 3,
        'API_RATE_LIMIT': 60,
        'CLEANUP_THRESHOLD_MB': 400,
        'LOG_DIR': 'logs',
        'LOG_MAX_BYTES': 10485760,
        'LOG_BACKUP_COUNT': 5,
        'LOG_MAX_AGE_DAYS': 30
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        yaml.dump(config_data, f)
        return Path(f.name)

def test_config_validation(valid_config_file):
    config = Config(valid_config_file)
    assert config.repo_path == Path('.')
    assert config.max_memory_mb == 512
    assert config.aider_model == 'test-model'
    assert config.log_dir == 'logs'

def test_config_invalid_yaml():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write("invalid: yaml: :")
        invalid_file = Path(f.name)
    
    with pytest.raises(ValueError, match="Invalid YAML"):
        Config(invalid_file)

def test_config_missing_required():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        yaml.dump({}, f)
        empty_file = Path(f.name)
    
    with pytest.raises(ValueError, match="Missing required configuration"):
        Config(empty_file)

def test_config_type_validation():
    invalid_config = {
        'MAX_MEMORY_MB': 'not_an_integer',
        'MAX_CPU_PERCENT': 'not_a_float'
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        yaml.dump(invalid_config, f)
        invalid_file = Path(f.name)
    
    with pytest.raises(ValueError, match="Invalid configuration"):
        Config(invalid_file)

@pytest.fixture(autouse=True)
def cleanup():
    yield
    # Cleanup any temporary files after each test
