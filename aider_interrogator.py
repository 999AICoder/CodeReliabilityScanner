"""
This module defines the Agent and AgentComponents classes, which are responsible
for managing and interrogating Python code using Aider.
"""

import subprocess
import os
import signal
import time
from pathlib import Path
import tempfile
from typing import List, Dict
from tenacity import retry, stop_after_attempt, wait_exponential

from exceptions import AiderTimeoutError, AiderProcessError, MaxRetriesExceededError

from config import Config
from logger import Logger
from command_runner import CommandRunner
from aider_runner import AiderRunner
from suggestion_db import SuggestionDB
from resource_manager import ResourceManager


class AiderInterrogator(AiderRunner):
    """
    A class responsible for interrogating code using Aider.
    """

    def __init__(self, config: Config, command_runner: CommandRunner, logger: Logger):
        super().__init__(config, command_runner, logger)
        self.db = SuggestionDB()
        self.resource_manager = ResourceManager(config)
        self.resource_manager.start_monitoring()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    def ask_question(self, code: str, question: str) -> str:
        """
        Ask Aider a question about the given code.

        Args:
            code (str): The Python code to be interrogated.
            question (str): The question to ask about the code.

        Returns:
            str: Aider's response to the question.
        """
        self._check_rate_limit()
        self.logger.info(f"Asking Aider: {question}")
        
        temp_file_path = self._create_temp_file(code)
        
        try:
            aider_command = self._build_aider_command(temp_file_path, question)
            response = self._run_aider_process(aider_command)
            self._store_response(question, response)
            return response.strip()
        except (subprocess.CalledProcessError, AiderTimeoutError) as e:
            self._handle_aider_error(e)
        except MaxRetriesExceededError:
            self._handle_max_retries()
        finally:
            self._cleanup_resources(temp_file_path)

    def _check_rate_limit(self):
        if not self.resource_manager.check_rate_limit():
            raise AiderProcessError("API rate limit exceeded. Please try again later.")

    def _create_temp_file(self, code: str) -> Path:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as temp_file:
            temp_file.write(code)
            return Path(temp_file.name)

    def _build_aider_command(self, temp_file_path: Path, question: str) -> List[str]:
        return [
            "aider",
            "--chat-mode",
            "ask",
            "--no-check-update",
            "--message",
            question,
            "--model",
            self.config.aider_model,
            "--weak-model",
            self.config.aider_weak_model,
            "--cache-prompts",
            str(temp_file_path),
        ]

    def _run_aider_process(self, aider_command: List[str]) -> str:
        env = self._prepare_environment()
        timeout = 300  # 5 minutes

        with subprocess.Popen(
            aider_command,
            cwd=self.config.repo_path,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True,
            env=env,
            start_new_session=True,  # Safer alternative to preexec_fn
        ) as process:
            return self._process_aider_output(process, timeout)

    def _prepare_environment(self) -> Dict[str, str]:
        env = self.command_runner.activate_virtualenv()
        env["COLUMNS"] = "100"
        return env

    def _process_aider_output(self, process: subprocess.Popen, timeout: int) -> str:
        response = ""
        capture_output = False
        start_time = time.time()

        while True:
            if time.time() - start_time > timeout:
                process.terminate()
                process.wait(timeout=5)  # Wait for up to 5 seconds for the process to terminate
                if process.poll() is None:
                    process.kill()  # Force kill if it doesn't terminate
                raise AiderTimeoutError(f"Aider process timed out after {timeout} seconds")

            try:
                output = process.stdout.readline()
                if output == "" and process.poll() is not None:
                    break
            except (IOError, OSError) as e:
                self.logger.error(f"Error reading from Aider process: {e}")
                raise AiderProcessError(f"Failed to read Aider output: {e}") from e

            if output:
                self.logger.info(output.strip())
                if "Use /help" in output:
                    capture_output = True
                    continue
                if capture_output:
                    response += output
                if "?" in output:
                    process.stdin.write("No\n")
                    process.stdin.flush()

        stderr = process.stderr.read()
        if stderr:
            self.logger.error(f"Aider errors: {stderr}")

        return response

    def _store_response(self, question: str, response: str):
        self.db.add_suggestion(
            "in_memory_code",
            question,
            {"response": response.strip()},
            self.config.aider_model,
        )

    def _handle_aider_error(self, error: Exception):
        self.logger.error(f"Failed to get response from Aider: {error}")
        raise AiderProcessError(f"Failed to get response from Aider: {error}") from error

    def _handle_max_retries(self):
        self.logger.error("Maximum retries exceeded for Aider process")
        raise MaxRetriesExceededError("Maximum retries exceeded for Aider process")

    def _cleanup_resources(self, temp_file_path: Path):
        if temp_file_path:
            self.resource_manager.register_temp_file(temp_file_path)
            self.resource_manager.cleanup_resources()


class AgentComponents:
    """A class that initializes and holds various components used by the Agent."""

    def __init__(self, config: Config, logger: Logger):
        self.command_runner = CommandRunner(config, logger)
        self.aider_interrogator = AiderInterrogator(config, self.command_runner, logger)
        self.logger = logger

    def get_component(self, component_name: str):
        """
        Get a component by name.

        Args:
            component_name (str): The name of the component to retrieve.

        Returns:
            The requested component.

        Raises:
            AttributeError: If the component doesn't exist.
        """
        if hasattr(self, component_name):
            return getattr(self, component_name)
        raise AttributeError(f"Component '{component_name}' not found")


class Agent:
    """Manages the interrogation of Python code using Aider."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = Logger()
        self.components = AgentComponents(self.config, self.logger)

    def interrogate_code(self, code: str, question: str) -> str:
        """
        Interrogate the given code using Aider and return the response.

        Args:
            code (str): The Python code to be interrogated.
            question (str): The question to ask about the code.

        Returns:
            str: Aider's response to the question.
        """
        self.logger.info("Interrogating code")
        return self.components.aider_interrogator.ask_question(code, question)
