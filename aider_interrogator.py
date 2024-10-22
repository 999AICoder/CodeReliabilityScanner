"""
This module defines the Agent and AgentComponents classes, which are responsible
for managing and interrogating Python code using Aider.
"""

import subprocess
from pathlib import Path
import tempfile

from config import Config
from logger import Logger
from command_runner import CommandRunner
from aider_runner import AiderRunner
from suggestion_db import SuggestionDB

class AiderInterrogator(AiderRunner):
    """
    A class responsible for interrogating code using Aider.
    """

    def __init__(self, config: Config, command_runner: CommandRunner, logger: Logger):
        super().__init__(config, command_runner, logger)
        self.db = SuggestionDB()

    def ask_question(self, code: str, question: str) -> str:
        """
        Ask Aider a question about the given code.

        Args:
            code (str): The Python code to be interrogated.
            question (str): The question to ask about the code.

        Returns:
            str: Aider's response to the question.
        """
        self.logger.info(f"Asking Aider: {question}")
        env = self.command_runner.activate_virtualenv()
        env['COLUMNS'] = '100'

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(code)
            temp_file_path = Path(temp_file.name)

        aider_command = [
            "aider" if not self.config.aider_path else self.config.aider_path,
            "--chat-mode", "ask",
            "--message", question,
            "--model", self.config.aider_model,
            "--weak-model", self.config.aider_weak_model,
            "--cache-prompts",
            str(temp_file_path),
        ]
        
        try:
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
            ) as process:
                response = ""
                while True:
                    output = process.stdout.readline()
                    if output == "" and process.poll() is not None:
                        break
                    if output:
                        self.logger.info(output.strip())
                        response += output
                        if "?" in output:  # This is likely a question
                            process.stdin.write("No\n")
                            process.stdin.flush()

                stderr = process.stderr.read()
                if stderr:
                    self.logger.error(f"Aider errors: {stderr}")

                # Store the response in the database
                self.db.add_suggestion("in_memory_code", question, {"response": response.strip()}, self.config.aider_model)

                # Clean up the temporary file
                temp_file_path.unlink()

                return response.strip()
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to get response from Aider: {e}")
            return f"Error: {e}"

class AgentComponents:
    """A class that initializes and holds various components used by the Agent."""

    def __init__(self, config: Config, logger: Logger):
        self.command_runner = CommandRunner(config, logger)
        self.aider_interrogator = AiderInterrogator(config, self.command_runner, logger)
        self.logger = logger

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
