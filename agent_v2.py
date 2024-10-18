"""
This module defines the Agent and AgentComponents classes, which are responsible
for managing and processing Python files in a repository for code quality improvements.
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import List

import git

from issue_processor import IssueProcessor, IssueProcessorConfig
from config import Config
from logger import Logger
from command_runner import CommandRunner
from file_processor import FileProcessor, ComponentManager
from git_manager import GitManager
from aider_runner import AiderRunner
from test_runner import TestRunner
from linter_runner import LinterRunner


class AgentComponents:
    """A class that initializes and holds various components used by the Agent."""

    def __init__(self, config: Config, logger: Logger):
        self.command_runner = CommandRunner(config, logger)
        self.git_manager = GitManager(config, self.command_runner, logger)
        self.test_runner = TestRunner
        self.aider_runner = AiderRunner(config, self.command_runner, logger)
        self.linter_runner = LinterRunner(config, logger)

        issue_processor_config = IssueProcessorConfig()
        issue_processor_config.set_components({
            'config': config,
            'command_runner': self.command_runner,
            'git_manager': self.git_manager,
            'aider_runner': self.aider_runner,
            'test_runner': self.test_runner,
            'logger': logger
        })
        self.issue_processor = IssueProcessor(issue_processor_config)

        file_processor_config = ComponentManager({
            'config': config,
            'command_runner': self.command_runner,
            'git_manager': self.git_manager,
            'aider_runner': self.aider_runner,
            'test_runner': self.test_runner,
            'linter_runner': self.linter_runner,
            'issue_processor': self.issue_processor,
            'logger': logger
        })
        self.file_processor = FileProcessor(file_processor_config)

    def get_component_names(self) -> List[str]:
        """Return a list of component names."""
        return [
            "CommandRunner",
            "GitManager",
            "TestRunner",
            "AiderRunner",
            "LinterRunner",
            "IssueProcessor",
            "FileProcessor"
        ]

    def get_component_summary(self) -> str:
        """Return a summary of the initialized components."""
        return (
            f"CommandRunner: {self.command_runner}, "
            f"GitManager: {self.git_manager}, "
            f"TestRunner: {self.test_runner}, "
            f"AiderRunner: {self.aider_runner}, "
            f"LinterRunner: {self.linter_runner}, "
            f"IssueProcessor: {self.issue_processor}, "
            f"FileProcessor: {self.file_processor}"
        )


class Agent:
    """Manages the processing of Python files for code quality improvements."""

    def __init__(self, config_path: Path):
        self.config = Config(config_path)
        self.logger = Logger()
        self.components = AgentComponents(self.config, self.logger)
        self.file_processor = self.components.file_processor

        # Add this check
        if not self.verify_repo_path():
            self.logger.error(
                f"The specified REPO_PATH ({self.config.repo_path}) is not a git repository or is not the top-level directory.")
            sys.exit(1)

    def verify_repo_path(self) -> bool:
        """
        Verify that the REPO_PATH is under git control and is the top-level directory.

        Returns:
            bool: True if the REPO_PATH is valid, False otherwise.
        """
        return self.components.git_manager.is_git_repo(self.config.repo_path)

    def get_tracked_files(self) -> List[str]:
        """Retrieve a list of tracked files in the repository."""
        repo = git.Repo(self.config.repo_path)
        tracked_files = repo.git.ls_files().splitlines()
        return [os.path.join(repo.working_dir, file) for file in tracked_files]

    def display_config_summary(self):
        """Display a summary of the current configuration settings."""
        print("Configuration Summary:")
        print(f"Repository Path: {self.config.repo_path}")
        print(f"Virtual Environment Path: {self.config.venv_path}")
        print(f"Virtual Environment Directory: {self.config.venv_dir}")
        print(f"Test Command: {self.config.test_command}")
        print(f"Aider Path: {self.config.aider_path}")
        print(f"Max Line Length: {self.config.max_line_length}")
        print(f"Autopep8 Fix: {self.config.autopep8_fix}")
        print(f"Aider Model: {self.config.aider_model}")
        print(f"Aider Weak Model: {self.config.aider_weak_model}")
        print(f"Linter: {self.config.linter}")
        print(f"Line Count Max: {self.config.line_count_max}")
        print(f"Line Count Min: {self.config.line_count_min}")
        print(f"Enable Black: {self.config.enable_black}")

    def check_pylintrc(self):
        """Check for the presence of a .pylintrc file and warn if it is missing."""
        pylintrc_path = os.path.join(self.config.repo_path, '.pylintrc')
        if self.config.linter == 'pylint' and not os.path.exists(pylintrc_path):
            print("\nWARNING: No .pylintrc file found in the repository directory.")
            print("While it is not mandatory, it is recommended to have a .pylintrc file "
                  "in the repository directory.")
            print("To learn more about .pylintrc file, visit:")
            print("https://pylint.readthedocs.io/en/stable/user_guide/usage/run.html")
            print("You have 10 seconds to exit if you want to end the run.")
            print("Press Ctrl+C to exit.")
            try:
                time.sleep(10)
            except KeyboardInterrupt:
                print("\nExiting as per user request.")
                sys.exit(0)
            print("\nContinuing with the execution...\n")

    def run(self, debug: bool, filename: str = None) -> None:
        """
        Execute the agent's main functionality, processing Python files for code quality.

        :param debug: Enable debug logging if True.
        :param filename: Specific Python file to process, if provided.
        """
        self.display_config_summary()
        print("\nYou have 10 seconds to review the configuration.")
        print("Press Ctrl+C to exit if you disagree with the configuration.")
        try:
            time.sleep(10)
        except KeyboardInterrupt:
            print("\nExiting as per user request.")
            sys.exit(0)
        print("\nProceeding with the execution...\n")

        self.check_pylintrc()
        if debug:
            self.logger.logger.setLevel(logging.DEBUG)

        # Add this check
        if not self.verify_repo_path():
            self.logger.error(
                f"The specified REPO_PATH ({self.config.repo_path}) is not a git repository or is not the top-level directory.")
            sys.exit(1)

        os.chdir(self.config.repo_path)

        if filename:
            python_files = [Path(filename)]
        else:
            tracked_files = self.get_tracked_files()
            python_files = [Path(file) for file in tracked_files if str(file).endswith('.py')]

        excluded_dirs = {self.config.venv_dir, ".git", "benchmark", "tests"}
        python_files = [
            file for file in python_files
            if not any(excluded_dir in file.parts for excluded_dir in excluded_dirs)
        ]
        for file in python_files:
            if file.name.startswith("test_"):
                self.logger.info(f"Skipping test file: {file}")
                continue
            if "__" in file.name:
                self.logger.info(f"Skipping __<file>: {file}")
                continue
            line_count = self.rawgencount(file)
            if line_count > self.config.line_count_max:
                self.logger.info(
                    f"Skipping file with more than {self.config.line_count_max} "
                    f"lines: {file}"
                )
                time.sleep(.25)
                continue
            if line_count == 0:
                self.logger.info(f"Skipping empty file: {file}")
                continue
            if line_count < self.config.line_count_min:
                self.logger.info(
                    f"Skipping file with less than {self.config.line_count_min} "
                    f"lines: {file}"
                )
                continue

            self.logger.info("Attempting to process Python file: {}".format(file))
            self.file_processor.process_file(file)

    @staticmethod
    def rawgencount(filename):
        """Count the number of lines in a file using a generator."""
        with open(filename, 'r') as f:
            return sum(1 for _ in f)

    @staticmethod
    def _make_gen(reader):
        chunk = reader(1024 * 1024)
        while chunk:
            yield chunk
            chunk = reader(1024 * 1024)


class WritableObject:
    """A simple class to capture and read written content."""

    def __init__(self):
        self.content = []

    def write(self, st):
        """Write a string to the content list."""
        self.content.append(st)

    def read(self):
        """Read the content list."""
        return self.content


def main():
    """Parse command-line arguments and execute the agent."""
    parser = argparse.ArgumentParser(
        description="Process Python files for code quality improvements.")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--max-workers", type=int, default=1,
                        help="Maximum number of worker processes")
    parser.add_argument("--file", type=str, help="Specific Python file to process")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    config_path = script_dir / 'config.yaml'
    if not config_path.exists():
        print("Error: Configuration file 'config.yaml' not found in the script directory.")
        print("Please make sure the config file exists in:", script_dir)
        print("The config file should contain the following keys:")
        print("REPO_PATH, VENV_PATH, VENV_DIR, TEST_COMMAND, AIDER_PATH, MAX_LINE_LENGTH")
        sys.exit(1)

    agent = Agent(config_path)
    try:
        agent.run(args.debug, args.file)
    except KeyboardInterrupt:
        print("\nExecution interrupted by user. Exiting.")
        sys.exit(0)


if __name__ == "__main__":
    main()
