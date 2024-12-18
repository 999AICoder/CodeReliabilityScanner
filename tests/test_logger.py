import os
import pytest
import logging
import logging.handlers
import time
import sys
from pathlib import Path
# Add the directory containing agent_v2.py to the PYTHONPATH
sys.path.append(str(Path(__file__).resolve().parent.parent))
from logger import Logger

def test_logger_initialization():
    logger = Logger()
    assert logger.logger.level == logging.INFO
    assert any(isinstance(h, logging.StreamHandler) for h in logger.logger.handlers)

def test_logger_with_file_handler():
    test_log_dir = "test_logs"
    logger = Logger(log_dir=test_log_dir, max_bytes=100)
    assert Path(test_log_dir).exists()
    assert any(isinstance(h, logging.handlers.RotatingFileHandler) 
              for h in logger.logger.handlers)
    assert len(logger.logger.handlers) == 2  # Stream handler and file handler

def test_log_rotation():
    test_log_dir = "test_logs"
    max_bytes = 100
    logger = Logger(log_dir=test_log_dir, max_bytes=max_bytes)
    
    # Write enough logs to trigger rotation
    for i in range(20):
        logger.info("x" * 10)
    
    log_files = list(Path(test_log_dir).glob("*.log*"))
    assert len(log_files) > 1

def test_log_cleanup():
    test_log_dir = "test_logs"
    logger = Logger(log_dir=test_log_dir)

    # Create some test log files with old timestamps
    log_path = Path(test_log_dir)
    test_files = ["test1.log", "test2.log"]
    for file in test_files:
        file_path = log_path / file
        file_path.touch()
        # Set access and modified times to 31 days ago
        old_time = time.time() - (31 * 24 * 3600)
        os.utime(file_path, (old_time, old_time))
            
    # Also set the app.log file to be old
    app_log = log_path / "app.log"
    os.utime(app_log, (old_time, old_time))

    Logger.cleanup_old_logs(test_log_dir, max_age_days=30)
    remaining_files = list(log_path.glob("*.log*"))
    assert len(remaining_files) == 0

@pytest.fixture(autouse=True)
def cleanup():
    yield
    import shutil
    if Path("test_logs").exists():
        shutil.rmtree("test_logs")
