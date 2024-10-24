import os
import subprocess
from pathlib import Path
import unittest
from config import Config
from command_runner import CommandRunner
from logger import Logger

class TestRunner:
    """
    A class responsible for running tests in the project.
    """

    @staticmethod
    def run_tests(config: Config, command_runner: CommandRunner, logger: Logger) -> bool:
        """
        Run the tests using the configured test command.

        Args:
            config (Config): The configuration object.
            command_runner (CommandRunner): The command runner object.
            logger (Logger): The logger object.

        Returns:
            bool: True if tests pass, False otherwise.
        """
        logger.info("Running tests...")
        env = command_runner.activate_virtualenv()
        env["PYTHONPATH"] = f"{config.repo_path}{os.pathsep}{env.get('PYTHONPATH', '')}"
        try:
            result = command_runner.run_command(config.test_command, env=env)
            logger.info(result.stdout)
            return result.returncode == 0
        except subprocess.CalledProcessError:
            logger.error("Tests failed")
            return False

def run_all_tests():
    """
    Run all test cases in the project.
    """
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(str(Path(__file__).parent), pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
