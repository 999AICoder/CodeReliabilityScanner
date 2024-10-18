"""
This module provides the LinterRunner class for running various linters on Python files.
It supports pylint, flake8, and ruff linters, and logs the results.
"""

from pathlib import Path
from typing import List
import subprocess
from pylint import lint
from pylint.reporters.text import TextReporter
from config import Config
from logger import Logger
from command_runner import CommandRunner

class LinterRunner:
    """
    A class responsible for running linters on Python files.
    """

    def __init__(self, config: Config, logger: Logger):
        """
        Initialize the LinterRunner.

        Args:
            config (Config): Configuration object.
            logger (Logger): Logging utility.
        """
        self.config = config
        self.logger = logger
        self.command_runner = CommandRunner(config, logger)

    def run_linter(self, file_path: Path) -> List[str]:
        """
        Run the configured linter on a file.

        Args:
            file_path (Path): Path to the file to be linted.

        Returns:
            List[str]: A list of linting issues found in the file.
        """
        if self.config.linter == "pylint":
            return self.run_pylint(file_path)
        if self.config.linter == "flake8":
            return self.run_flake8(file_path)
        if self.config.linter == "ruff":
            return self.run_ruff(file_path)
        self.logger.error(f"Unsupported linter: {self.config.linter}")
        return []

    def run_pylint(self, file_path: Path) -> List[str]:
        """
        Run pylint on a file to check for formatting issues.

        Args:
            file_path (Path): Path to the file to be linted.

        Returns:
            List[str]: A list of pylint issues found in the file.
        """
        pylint_output = WritableObject()
        issues = []
        args = ["--max-line-length", str(self.config.max_line_length)]
        lint.Run([str(file_path)] + args, reporter=TextReporter(pylint_output), exit=False)
        for line in pylint_output.read():
            self.logger.info(line)
            issues.append(line)
        if not any("***" in issue for issue in issues):
            return []
        return issues

    def run_flake8(self, file_path: Path) -> List[str]:
        """
        Run flake8 on a file to check for formatting issues.

        Args:
            file_path (Path): Path to the file to be linted.

        Returns:
            List[str]: A list of flake8 issues found in the file.
        """
        self.logger.info(f"Running flake8 on {file_path}")
        command = ["flake8", "--max-line-length", str(self.config.max_line_length), str(file_path)]
        results = self.command_runner.run_command(command)
        if results.stdout:
            self.logger.info("returning flake8 results")
            return results.stdout.splitlines()
        return []

    def run_ruff(self, file_path: Path) -> List[str]:
        """
        Run Ruff on a file to check for formatting issues.

        Args:
            file_path (Path): Path to the file to be linted.

        Returns:
            List[str]: A list of Ruff issues found in the file.
        """
        try:
            results = self.command_runner.run_command(["ruff", "check", str(file_path)])
            if results.stdout and "All checks passed!" not in results.stdout:
                self.logger.info("returning ruff results")
                return results.stdout.splitlines()
            return []
        except (subprocess.CalledProcessError, RuntimeError) as e:
            self.logger.error(f"Unexpected error while formatting {file_path} with Ruff: {e}")
        return []

class WritableObject:
    """A simple class to capture pylint output."""
    def __init__(self):
        self.content = []
    def write(self, st: str) -> None:
        """Write a string to the content list."""
        self.content.append(st)
    def read(self) -> List[str]:
        """Read the content list."""
        return self.content
