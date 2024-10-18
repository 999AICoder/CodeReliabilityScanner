"""
This module provides the GitManager class, which handles Git operations
such as committing changes, retrieving the current commit SHA, and reverting
the last commit.
"""

import subprocess
from pathlib import Path
import sys
from config import Config
from command_runner import CommandRunner
from logger import Logger


class GitManager:
    """
    A class to manage Git operations for the project.
    """

    def __init__(self, config: Config, command_runner: CommandRunner, logger: Logger):
        """
        Initialize the GitManager.

        Args:
            config (Config): Configuration object.
            command_runner (CommandRunner): Command execution utility.
            logger (Logger): Logging utility.
        """
        self.config = config
        self.command_runner = command_runner
        self.logger = logger

    def is_git_repo(self, path: Path) -> bool:
        """
        Check if the given path is a git repository and is the top-level directory.

        Args:
            path (Path): The path to check.

        Returns:
            bool: True if the path is a git repository and is the top-level directory, False otherwise.
        """
        try:
            result = self.command_runner.run_command(['git', 'rev-parse', '--show-toplevel'], cwd=path)
            repo_root = Path(result.stdout.strip())
            return repo_root.resolve() == path.resolve()
        except subprocess.CalledProcessError:
            return False

    def commit_changes(self, file_path: Path, message: str) -> None:
        """
        Commit changes for a specific file.

        Args:
            file_path (Path): Path to the file to be committed.
            message (str): Commit message.
        """
        env = self.command_runner.activate_virtualenv()
        try:
            status = self.command_runner.run_command(
                ['git', 'status', '--porcelain', str(file_path)], env=env
            )
            if status.stdout.strip():
                self.command_runner.run_command(['git', 'add', str(file_path)], env=env)
                self.command_runner.run_command(
                    ['git', 'commit', '-m', message, str(file_path)], env=env
                )
                self.logger.info(f"Committed changes for {file_path}")
            else:
                self.logger.info(f"No changes to commit for {file_path}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to commit changes for {file_path}: {e}")

    def get_current_commit_sha(self) -> str:
        """
        Get the SHA of the current commit.

        Returns:
            str: The SHA of the current commit.
        """
        result = self.command_runner.run_command(["git", "rev-parse", "HEAD"])
        return result.stdout.strip()

    def revert_last_commit(self) -> None:
        """
        Revert the last commit and exit the program.
        """
        self.logger.info("Attempting to revert last commit...")
        self.command_runner.run_command(["git", "revert", "--no-edit", "HEAD"])
        self.logger.info("Exiting so you can verify before we proceed")
        sys.exit(1)
