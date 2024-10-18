"""
This module provides classes and functions to process and group issues found in code.

It includes the IssueProcessorConfig and IssueProcessor classes, which handle the
grouping of issues by type and function, and the processing of these issues using
various strategies.
"""

from pathlib import Path
from typing import List, Dict
from config import Config
from command_runner import CommandRunner
from git_manager import GitManager
from aider_runner import AiderRunner
from test_runner import TestRunner
from logger import Logger

class IssueProcessorConfig:
    """
    Configuration class for setting up components required by the IssueProcessor.

    This class holds references to various components like command runner, git manager,
    aider runner, test runner, and logger, which are necessary for processing issues.
    """
    def __init__(self):
        """
        Initialize the IssueProcessorConfig with an empty components dictionary.
        """
        self.components = {}

    def set_components(self, components: Dict[str, object]):
        """
        Set all components at once using a dictionary.

        Args:
            components (Dict[str, object]): A dictionary of component names and their instances.
        """
        self.components = components

    def get_component(self, component_name: str):
        """
        Get a specific component by name.

        Args:
            component_name (str): The name of the component to retrieve.

        Returns:
            The requested component or None if not found.
        """
        return self.components.get(component_name)

class IssueProcessor:
    """
    A class responsible for processing and grouping issues found in the code.
    """

    def __init__(self, config: IssueProcessorConfig):
        """
        Initialize the IssueProcessor.

        Args:
            config (IssueProcessorConfig): An instance of IssueProcessorConfig containing all necessary components.
        """
        self.config = config.get_component('config')
        self.command_runner = config.get_component('command_runner')
        self.git_manager = config.get_component('git_manager')
        self.aider_runner = config.get_component('aider_runner')
        self.test_runner = config.get_component('test_runner')
        self.logger = config.get_component('logger')

    def group_issues_by_type(self, issues: List[str]) -> Dict[str, List[str]]:
        """
        Group issues by their type.

        Args:
            issues (List[str]): List of issues to group.

        Returns:
            Dict[str, List[str]]: Dictionary of grouped issues.
        """
        grouped: Dict[str, List[str]] = {
            "complexity": [],
            "style": [],
            "error_handling": [],
            "other": []
        }
        for issue in issues:
            if any(x in issue for x in ["too-many", "R09", "R10"]):
                grouped["complexity"].append(issue)
            elif any(x in issue for x in ["missing-", "unused-", "pointless-"]):
                grouped["style"].append(issue)
            elif "exception" in issue or "return" in issue:
                grouped["error_handling"].append(issue)
            else:
                grouped["other"].append(issue)
        return grouped

    def group_issues_by_function(self, issues: List[str]) -> Dict[str, List[str]]:
        """
        Group issues by the function they occur in.

        Args:
            issues (List[str]): List of issues to group.

        Returns:
            Dict[str, List[str]]: Dictionary of grouped issues.
        """
        grouped: Dict[str, List[str]] = {}
        for issue in issues:
            parts = issue.split(":")
            if len(parts) > 2:
                func_name = parts[2].strip()
                if func_name not in grouped:
                    grouped[func_name] = []
                grouped[func_name].append(issue)
        return grouped

    def process_issues(self, file_path: Path, issues: List[str]) -> None:
        """
        Process issues by grouping them by type and running Aider on each group.

        Args:
            file_path (Path): Path to the file being processed.
            issues (List[str]): List of issues to process.
        """
        grouped_by_type = self.group_issues_by_type(issues)

        for issue_type, issue_list in grouped_by_type.items():
            if issue_list:
                message = (
                    f"Refactor to address {issue_type} issues: " + "\n".join(issue_list)
                )
                self.aider_runner.run_aider(file_path, message)

    def process_issues_by_function(self, file_path: Path, issues: List[str]) -> None:
        """
        Process issues by grouping them by function and running Aider on each group.

        Args:
            file_path (Path): Path to the file being processed.
            issues (List[str]): List of issues to process.
        """
        grouped = self.group_issues_by_function(issues)
        for func, func_issues in grouped.items():
            message = (
                f"Refactor function {func} to address: " + "\n".join(func_issues)
            )
            self.aider_runner.run_aider(file_path, message)

    def process_issues_with_sliding_window(self, file_path: Path, issues: List[str], window_size: int = 5) -> None:
        """
        Process issues using a sliding window approach.

        Args:
            file_path (Path): Path to the file being processed.
            issues (List[str]): List of issues to process.
            window_size (int): Size of the sliding window. Defaults to 5.
        """
        for i in range(0, len(issues), window_size):
            window = issues[i : i + window_size]
            message = "Address the following issues:\n" + "\n".join(window)
            self.aider_runner.run_aider(file_path, message)
