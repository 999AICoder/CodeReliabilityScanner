import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from google.cloud import secretmanager
from config_schema import ConfigSchema

class Config:
    """Configuration management class with schema validation and resource limits."""
    
    def __init__(self, config_path: Path):
        """Initialize configuration with schema validation."""
        try:
            with open(config_path, 'r') as config_file:
                config = yaml.safe_load(config_file)
        except FileNotFoundError:
            config = {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file {config_path}: {e}")
            
        if not isinstance(config, dict):
            raise ValueError(f"Invalid configuration format in {config_path}. Expected a YAML dictionary.")
            
        # Initialize Secret Manager client if running in GCP
        self.secret_client = None
        if os.environ.get('GOOGLE_CLOUD_PROJECT'):
            self.secret_client = secretmanager.SecretManagerServiceClient()
            self.project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
            
        # Get secrets first
        config['AIDER_MODEL'] = self._get_secret('AIDER_MODEL') or config.get('AIDER_MODEL')
        config['AIDER_WEAK_MODEL'] = self._get_secret('AIDER_WEAK_MODEL') or config.get('AIDER_WEAK_MODEL')
        config['AIDER_API_KEY'] = self._get_secret('AIDER_API_KEY')
        
        # Validate configuration against schema
        validated_config = ConfigSchema.validate(config)
        
        # Set all attributes from validated config
        for key, value in validated_config.items():
            setattr(self, key.lower(), value)
            
        # Convert paths to Path objects
        self.repo_path = Path(self.repo_path)
        self.venv_path = Path(self.venv_path)

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
