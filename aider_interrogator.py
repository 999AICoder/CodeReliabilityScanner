"""
This module defines the Agent and AgentComponents classes, which are responsible
for managing and interrogating Python files in a repository using Aider.
"""

import argparse
import subprocess
from pathlib import Path
import sys

from config import Config
from logger import Logger
from command_runner import CommandRunner
from aider_runner import AiderRunner
from suggestion_db import SuggestionDB

class AiderInterrogator(AiderRunner):
    """
    A class responsible for interrogating files using Aider.
    """

    def __init__(self, config: Config, command_runner: CommandRunner, logger: Logger):
        super().__init__(config, command_runner, logger)
        self.db = SuggestionDB()

    def ask_question(self, file_path: Path, question: str) -> str:
        """
        Ask Aider a question about a specific file.

        Args:
            file_path (Path): Path to the file to be interrogated.
            question (str): The question to ask about the file.

        Returns:
            str: Aider's response to the question.
        """
        self.logger.info(f"Asking Aider about {file_path}: {question}")
        env = self.command_runner.activate_virtualenv()
        env['COLUMNS'] = '100'
        aider_command = [
            self.config.aider_path,
            "--chat-mode", "ask",
            "--message", question,
            "--model", self.config.aider_model,
            "--weak-model", self.config.aider_weak_model,
            "--cache-prompts",
            str(file_path),
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
                self.db.add_suggestion(str(file_path), question, {"response": response.strip()}, self.config.aider_model)

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
    """Manages the interrogation of Python files using Aider."""

    def __init__(self, config_path: Path):
        self.config = Config(config_path)
        self.logger = Logger()
        self.components = AgentComponents(self.config, self.logger)

    def interrogate_file(self, file_path: Path, question: str) -> None:
        """
        Interrogate a specific file using Aider and store the response in the database.

        Args:
            file_path (Path): Path to the file to be interrogated.
            question (str): The question to ask about the file.
        """
        self.logger.info(f"Interrogating file: {file_path}")
        response = self.components.aider_interrogator.ask_question(file_path, question)
        print(f"Response for {file_path}:")
        print(response)

def main():
    """Parse command-line arguments and execute the agent."""
    parser = argparse.ArgumentParser(
        description="Interrogate Python files using Aider.")
    parser.add_argument("--file", type=str, required=True, help="Python file to interrogate")
    parser.add_argument("--question", type=str, required=True, help="Question to ask about the file")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    config_path = script_dir / 'config.yaml'
    if not config_path.exists():
        print("Error: Configuration file 'config.yaml' not found in the script directory.")
        sys.exit(1)

    agent = Agent(config_path)
    try:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File {file_path} does not exist.")
            sys.exit(1)
        agent.interrogate_file(file_path, args.question)
    except KeyboardInterrupt:
        print("\nExecution interrupted by user. Exiting.")
        sys.exit(0)

if __name__ == "__main__":
    main()
