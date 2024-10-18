"""
This module defines the FileProcessor class, which is responsible for processing
individual files in the repository. It handles operations such as running linters,
applying fixes, and managing Git operations related to file changes.
"""

from pathlib import Path
from typing import Dict, List
import subprocess


class ComponentManager(dict):
    """
    A class to manage and provide access to various components used in file processing.
    """

    def __init__(self, components: Dict[str, object]):
        """
        Initialize the ComponentManager with necessary components.

        Args:
            components (Dict[str, object]): A dictionary containing all necessary components.
        """
        super().__init__(components)

    def __getattr__(self, name):
        """
        Provide attribute-style access to components.

        Args:
            name (str): The name of the component to access.

        Returns:
            object: The requested component.

        Raises:
            AttributeError: If the requested component doesn't exist.
        """
        if name in self:
            return self[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")


class FileProcessor:
    """
    A class responsible for processing individual files in the repository.
    
    This class handles various operations on files, including running linters,
    applying fixes, and managing Git operations related to file changes.
    """

    def __init__(self, components: Dict[str, object]):
        """
        Initialize the FileProcessor with necessary components.

        Args:
            components (Dict[str, object]): A dictionary containing all necessary
                components.
        """
        self.components = ComponentManager(components)

    def process_file(self, file_path: Path) -> None:
        """
        Process a single file for linting, fixing issues, and running tests.

        Args:
            file_path (Path): Path to the file to be processed.
        """
        self.components.logger.info(f"Processing {file_path}...")

        env = self.components.command_runner.activate_virtualenv()
        try:
            self._run_code_formatters(file_path, env)
            issues = self._run_linter(file_path)
            if issues:
                self.components.logger.info("Running aider on file")
                self._process_issues(file_path, issues, env)

            self._run_tests_and_commit(file_path)
        except subprocess.CalledProcessError as e:
            self.components.logger.error(f"Error processing {file_path}: {e}")
        except RuntimeError as e:
            self.components.logger.error(
                f"Unexpected runtime error while processing {file_path}: {e}",
                exc_info=True
            )
        finally:
            self.components.logger.info(f"Finished processing {file_path}")

    def _run_code_formatters(self, file_path: Path, env: Dict[str, str]) -> None:
        if self.components.config.autopep8_fix:
            self.run_autopep8(file_path, env)
        if self.components.config.enable_black:
            self.run_black(file_path, env)

    def _run_linter(self, file_path: Path) -> List[str]:
        self.components.logger.info(f"Attempting to run {self.components.config.linter} on {file_path}")
        issues = self.components.linter_runner.run_linter(file_path)
        self.components.logger.info(f"Found {len(issues)} issues in {file_path}")
        return issues

    def _process_issues(self, file_path: Path, issues: List[str], env: Dict[str, str]) -> None:
        if len(issues) > 10:
            self.components.issue_processor.process_issues(file_path, issues)
        elif len(issues) > 5:
            self.components.issue_processor.process_issues_by_function(file_path, issues)
        else:
            issues_description = (
                "Address the following issues: " + "\n".join(issues)
            )
            self.components.aider_runner.run_aider(file_path, issues_description)
        if self.components.config.enable_black:
            self.run_black(file_path, env)

    def _run_tests_and_commit(self, file_path: Path) -> None:
        if not self.components.test_runner.run_tests(self.components.config, self.components.command_runner, self.components.logger):
            self.components.logger.error(f"Tests failed after applying fixes for {file_path}")
        else:
            commit_message = f'"Refactor {file_path.name} for code quality"'
            self.components.git_manager.commit_changes(file_path, commit_message)
            commit_sha = self.components.git_manager.get_current_commit_sha()
            self.components.logger.info(f"Committed {commit_sha}")

            if not self.components.test_runner.run_tests():
                self.components.git_manager.revert_last_commit()
                self.components.logger.info(f"Reverted changes in {file_path}")
            else:
                self.components.logger.info(f"Changes to {file_path} passed tests.")

    def run_autopep8(self, file_path: Path, env: Dict[str, str]) -> None:
        """
        Run autopep8 on the specified file.

        Args:
            file_path (Path): Path to the file to be processed.
            env (Dict[str, str]): Environment variables for the subprocess.
        """
        try:
            self.components.logger.info(
                f"Attempting to fix issues with autopep8 in {file_path}"
            )
            result = self.components.command_runner.run_command([
                "autopep8",
                f"--max-line-length={self.components.config.max_line_length}", "--in-place",
                "--aggressive", "--aggressive", str(file_path)
            ], env=env)
            if result.returncode == 0:
                self.components.logger.info(f"Autopep8 successfully fixed issues in {file_path}")
                self.components.git_manager.commit_changes(
                    file_path, f'"formatting: ran autopep8 on {file_path.name}"'
                )
            else:
                self.components.logger.error(f"Autopep8 failed to fix issues in {file_path}")
        except subprocess.CalledProcessError as e:
            self.components.logger.error(f"Error running autopep8 on {file_path}: {e}")
        except RuntimeError as e:
            self.components.logger.error(
                f"Unexpected runtime error while running autopep8 on {file_path}: {e}",
                exc_info=True
            )

    def run_black(self, file_path: Path, env: Dict[str, str]) -> None:
        """
        Run black on the specified file.

        Args:
            file_path (Path): Path to the file to be processed.
            env (Dict[str, str]): Environment variables for the subprocess.
        """
        try:
            self.components.logger.info(f"Attempting to format {file_path} with Black")
            self.components.command_runner.run_command(
                [
                    "black", "--line-length",
                    str(self.components.config.max_line_length), str(file_path)
                ],
                env=env
            )
            self.components.logger.info(f"Black successfully formatted {file_path}")
            self.components.git_manager.commit_changes(
                file_path, f'"formatting: ran black on {file_path.name}"'
            )
        except subprocess.CalledProcessError as e:
            self.components.logger.error(f"Failed to format {file_path} with Black: {e}")
        except RuntimeError as e:
            self.components.logger.error(
                f"Unexpected runtime error while formatting {file_path} with Black: {e}",
                exc_info=True
            )
