"""Resource management module for monitoring and controlling system resources."""
import psutil
import threading
import time
from pathlib import Path
import logging
from datetime import datetime, timedelta

class ResourceManager:
    """Manages system resources and enforces limits."""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.process = psutil.Process()
        self.temp_files = set()
        self.api_calls = []
        self.monitoring = False
        self.monitor_thread = None
        
    def start_monitoring(self):
        """Start the resource monitoring thread."""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_resources)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        """Stop the resource monitoring thread."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
            
    def _monitor_resources(self):
        """Monitor system resources in a separate thread."""
        while self.monitoring:
            try:
                memory_percent = self.process.memory_percent()
                cpu_percent = self.process.cpu_percent()
                
                # Only warn if memory usage exceeds 80% of max_memory_mb
                max_memory_percent = (self.process.memory_info().rss / (self.config.max_memory_mb * 1024 * 1024)) * 100
                if max_memory_percent > 80:
                    self.logger.warning(f"Memory usage too high: {memory_percent:.1f}%")
                    self.cleanup_resources()
                    
                if cpu_percent > self.config.max_cpu_percent:
                    self.logger.warning(f"CPU usage too high: {cpu_percent:.1f}%")
                    
            except Exception as e:
                self.logger.error(f"Error monitoring resources: {e}")
                
            time.sleep(1)
            
    def cleanup_resources(self):
        """Clean up temporary files and other resources."""
        current_time = datetime.now()
        
        # Clean up old temporary files
        for temp_file in list(self.temp_files):
            try:
                if not temp_file.exists():
                    self.temp_files.remove(temp_file)
                    continue
                    
                # Remove files older than 1 hour
                if current_time - datetime.fromtimestamp(temp_file.stat().st_mtime) > timedelta(hours=1):
                    temp_file.unlink()
                    self.temp_files.remove(temp_file)
            except Exception as e:
                self.logger.error(f"Error cleaning up temp file {temp_file}: {e}")
                
        # Clean up old API call records
        self.api_calls = [
            call_time for call_time in self.api_calls 
            if current_time - call_time < timedelta(minutes=1)
        ]
        
    def register_temp_file(self, file_path: Path):
        """Register a temporary file for cleanup."""
        self.temp_files.add(Path(file_path))
        
    def check_rate_limit(self) -> bool:
        """Check if API rate limit has been exceeded."""
        current_time = datetime.now()
        self.api_calls = [
            call_time for call_time in self.api_calls 
            if current_time - call_time < timedelta(minutes=1)
        ]
        
        if len(self.api_calls) >= self.config.api_rate_limit:
            return False
            
        self.api_calls.append(current_time)
        return True
        
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / 1024 / 1024
        
    def get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        return self.process.cpu_percent()
