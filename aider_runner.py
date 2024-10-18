"""
AiderRunner module for running Aider to fix code issues.

This module provides the AiderRunner class which utilizes a command runner
and logger to execute Aider commands for code issue resolution.
"""

import time
import subprocess
from pathlib import Path
from config import Config
from command_runner import CommandRunner
from logger import Logger

class AiderRunner:
    """
    A class responsible for running Aider to fix code issues.
    """

    def __init__(self, config: Config, command_runner: CommandRunner, logger: Logger):
        """
        Initialize the AiderRunner.

        Args:
            config (Config): Configuration object.
            command_runner (CommandRunner): Command execution utility.
            logger (Logger): Logging utility.
        """
        self.config = config
        self.command_runner = command_runner
        self.logger = logger

    def get_status(self) -> str:
        """
        Get the current status of the AiderRunner.

        Returns:
            str: A status message.
        """
        return "AiderRunner is ready to run Aider."

    def run_aider(self, file_path: Path, fix_request: str) -> int:
        """
        Run Aider on a specific file with a fix request.

        Args:
            file_path (Path): Path to the file to be processed.
            fix_request (str): The fix request to be sent to Aider.

        Returns:
            int: The return code from the Aider process.
        """
        self.logger.info(f"Running aider on {file_path} with fix request: {fix_request}")
        env = self.command_runner.activate_virtualenv()
        aider_command = [
            self.config.aider_path,
            "--message",
            (
                "Thinking like the worlds greatest programmer, "
                f"resolve these pylint warnings: {fix_request}"
            ),
            "--model", self.config.aider_model,
            "--weak-model", self.config.aider_weak_model,
            "--cache-prompts",
            str(file_path),
        ]
        time.sleep(5)
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
                while True:
                    output = process.stdout.readline()
                    if output == "" and process.poll() is not None:
                        break
                    if output:
                        self.logger.info(output.strip())
                        if "?" in output:  # This is likely a question
                            if "Attempt to fix lint errors?" in output:
                                process.stdin.write("Yes\n")
                            elif "Allow creation of new file?" in output:
                                process.stdin.write("Yes\n")
                            elif "to the chat?" in output and "Add" in output:
                                process.stdin.write("Yes\n")
                            elif "Allow edits to file that has not been added to the chat?" in output:
                                process.stdin.write("Yes\n")
                            else:
                                process.stdin.write("No\n")
                            process.stdin.flush()

                stderr = process.stderr.read()
                if stderr:
                    self.logger.error(f"Aider errors: {stderr}")

            return process.returncode
        except FileNotFoundError as e:
            self.logger.error(f"Aider executable not found: {e}")
            return 1
        except subprocess.SubprocessError as e:
            self.logger.error(f"Subprocess error: {e}")
            return 1
        except OSError as e:
            self.logger.error(f"OS error: {e}")
            return 1
