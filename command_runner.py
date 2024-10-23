"""
This module provides the CommandRunner class, which is responsible for
executing shell commands and managing virtual environments.
"""

import os
import subprocess
from pathlib import Path
from typing import List, Dict
from config import Config
from logger import Logger


class CommandRunner:
    """Handles execution of shell commands and virtual environment management."""
    def __init__(self, config: Config, logger: Logger):
        self.config = config
        self.logger = logger

    def run_command(
        self,
        command: List[str],
        cwd: Path = None,
        env: Dict[str, str] = None
    ) -> subprocess.CompletedProcess:
        """Executes a shell command in the specified directory with the given environment.

        Args:
            command (List[str]): The command to run as a list of strings.
            cwd (Path, optional): The directory to run the command in. Defaults to None.
            env (Dict[str, str], optional): The environment variables to use. Defaults to None.

        Returns:
            subprocess.CompletedProcess: The result of the executed command.
        """
        if cwd is None:
            cwd = self.config.repo_path
        if env is None:
            env = os.environ.copy()

        check_boolean = True
        if "ruff" in command[0]:
            check_boolean = False

        if "git" not in command[0]:
            if isinstance(command, str):
                command = command.split()
            command = ["source", f"{self.config.venv_dir}/bin/activate", "&&"] + command

        command_str = " ".join(command)
        self.logger.info(f'Running {command_str}')

        try:
            result = subprocess.run(
                command_str,
                cwd=cwd,
                capture_output=True,
                text=True,
                env=env,
                check=check_boolean,
                shell=True
            )
            self.logger.info(f"Command output: {result.stdout}")
            return result
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed with return code {e.returncode}: {e}")
            self.logger.error(f"Command output: {e.output}")
            raise
        except FileNotFoundError as e:
            self.logger.error(f"Command not found: {e}")
            raise
        except subprocess.SubprocessError as e:
            self.logger.error(f"Subprocess error: {e}")
            raise

    def activate_virtualenv(self) -> Dict[str, str]:
        """Activates the virtual environment and returns the updated environment variables.

        Returns:
            Dict[str, str]: The environment variables with the virtual environment activated.
        """
        env = os.environ.copy()
        bin_path = self.config.venv_path / ("Scripts" if os.name == "nt" else "bin")
        env["PATH"] = f"{bin_path}{os.pathsep}{env.get('PATH', '')}"
        self.logger.info(f"Activating virtual environment: {self.config.venv_path}")
        env["VIRTUAL_ENV"] = str(self.config.venv_path)
        return env
