import os
import yaml
from pathlib import Path
from google.cloud import secretmanager

class Config:
    def __init__(self, config_path: Path):
        try:
            with open(config_path, 'r') as config_file:
                config = yaml.safe_load(config_file)
        except FileNotFoundError:
            config = {}
        
        if not isinstance(config, dict):
            raise ValueError(f"Invalid configuration format in {config_path}. Expected a YAML dictionary.")

        # Initialize Secret Manager client if running in GCP
        self.secret_client = None
        if os.environ.get('GOOGLE_CLOUD_PROJECT'):
            self.secret_client = secretmanager.SecretManagerServiceClient()
            self.project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')

        self.repo_path = Path(config.get('REPO_PATH', '.'))
        self.venv_path = Path(config.get('VENV_PATH', ''))
        self.venv_dir = config.get('VENV_DIR', '')
        self.test_command = config.get('TEST_COMMAND', '')
        self.aider_path = config.get('AIDER_PATH', '')
        self.max_line_length = config.get('MAX_LINE_LENGTH', 100)
        self.autopep8_fix = config.get('AUTOPEP8_FIX', False)
        
        # Get model configurations from Secret Manager if available, otherwise from config
        self.aider_model = self._get_secret('AIDER_MODEL') or config.get('AIDER_MODEL', 'openrouter/anthropic/claude-3.5-sonnet:beta')
        self.aider_weak_model = self._get_secret('AIDER_WEAK_MODEL') or config.get('AIDER_WEAK_MODEL', 'openrouter/anthropic/claude-3-haiku-20240307')
        self.aider_api_key = self._get_secret('AIDER_API_KEY')
        
        self.linter = config.get('LINTER', 'pylint')
        self.line_count_max = config.get('LINE_COUNT_MAX', 200)
        self.line_count_min = config.get('LINE_COUNT_MIN', 10)
        self.enable_black = config.get('ENABLE_BLACK', False)

    def _get_secret(self, secret_id: str) -> str:
        """
        Retrieve a secret from Google Cloud Secret Manager.
        Returns None if Secret Manager is not available or secret is not found.
        """
        if not self.secret_client:
            return None
            
        try:
            name = f"projects/{self.project_id}/secrets/{secret_id}/versions/latest"
            response = self.secret_client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            print(f"Warning: Could not retrieve secret {secret_id}: {e}")
            return None
