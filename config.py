import yaml
from pathlib import Path

class Config:
    def __init__(self, config_path: Path):
        try:
            with open(config_path, 'r') as config_file:
                config = yaml.safe_load(config_file)
        except FileNotFoundError:
            config = {}
        
        if not isinstance(config, dict):
            raise ValueError(f"Invalid configuration format in {config_path}. Expected a YAML dictionary.")

        self.repo_path = Path(config.get('REPO_PATH', '.'))
        self.venv_path = Path(config.get('VENV_PATH', ''))
        self.venv_dir = config.get('VENV_DIR', '')
        self.test_command = config.get('TEST_COMMAND', '')
        self.aider_path = config.get('AIDER_PATH', '')
        self.max_line_length = config.get('MAX_LINE_LENGTH', 100)
        self.autopep8_fix = config.get('AUTOPEP8_FIX', False)
        self.aider_model = config.get('AIDER_MODEL', 'openrouter/anthropic/claude-3.5-sonnet:beta')
        self.aider_weak_model = config.get('AIDER_WEAK_MODEL', 'openrouter/anthropic/claude-3-haiku-20240307')
        self.linter = config.get('LINTER', 'pylint')
        self.line_count_max = config.get('LINE_COUNT_MAX', 200)
        self.line_count_min = config.get('LINE_COUNT_MIN', 10)
        self.enable_black = config.get('ENABLE_BLACK', False)
