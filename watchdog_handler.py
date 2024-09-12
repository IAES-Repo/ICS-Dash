import time
import os
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from cache_config import force_cache_update
from threading import Lock, Timer

logger = logging.getLogger(__name__)

class FileChangeHandler:
    def __init__(self, app, output_file):
        self.app = app
        self.output_file = output_file
        self.last_size = self.get_file_size()
        self.last_mtime = self.get_file_mtime()
        self.processing = False
        self.lock = Lock()
        self.timer = None

    def get_file_size(self):
        return os.path.getsize(self.output_file) if os.path.exists(self.output_file) else 0

    def get_file_mtime(self):
        return os.path.getmtime(self.output_file) if os.path.exists(self.output_file) else 0

    def check_file_changes(self):
        if not os.path.exists(self.output_file):
            logger.warning(f"File does not exist: {self.output_file}")
            return

        current_size = self.get_file_size()
        current_mtime = self.get_file_mtime()

        with self.lock:
            if self.processing:
                return

            if current_size != self.last_size or current_mtime != self.last_mtime:
                logger.info(f"Change detected in {self.output_file}")
                logger.info(f"Size changed: {self.last_size} -> {current_size}")
                logger.info(f"Modification time changed: {self.last_mtime} -> {current_mtime}")
                
                self.last_size = current_size
                self.last_mtime = current_mtime
                
                # Cancel any existing timer
                if self.timer:
                    self.timer.cancel()
                
                # Set a new timer for 30 seconds
                logger.info("Starting 30-second wait before processing...")
                self.processing = True
                self.timer = Timer(30, self.process_changes)
                self.timer.start()

    def process_changes(self):
        try:
            logger.info("30-second wait completed. Processing changes...")
            with self.app.app_context():
                logger.info("Forcing cache update")
                force_cache_update()
            
            logger.info("File processing and cache update completed")
        except Exception as e:
            logger.error(f"Error processing file changes: {e}", exc_info=True)
        finally:
            with self.lock:
                self.processing = False

def start_watchdog(directory_to_watch, app, output_file):
    handler = FileChangeHandler(app, output_file)
    logger.info(f"Started watching file: {output_file}")

    try:
        while True:
            handler.check_file_changes()
            time.sleep(10)  # Check every 10 seconds
    except KeyboardInterrupt:
        logger.info("Watchdog stopped")