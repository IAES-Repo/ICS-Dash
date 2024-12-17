# watchdog_handler.py

import time
import os
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from cache_config import force_cache_update
from threading import Lock, Timer

logger = logging.getLogger(__name__)

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, app, directory_to_watch):
        super().__init__()
        self.app = app
        self.directory_to_watch = directory_to_watch
        self.file_states = {}  # track size and mtime for each file
        self.processing = False
        self.lock = Lock()
        self.timer = None
        self.scan_files()

    def scan_files(self):
        """Initialize file states for all files in the directory."""
        for filename in os.listdir(self.directory_to_watch):
            file_path = os.path.join(self.directory_to_watch, filename)
            if os.path.isfile(file_path) and filename.endswith('.json'):
                self.file_states[file_path] = {
                    "size": os.path.getsize(file_path),
                    "mtime": os.path.getmtime(file_path),
                }

    def on_modified(self, event):
        """Handle modified files."""
        if event.is_directory:
            return

        file_path = event.src_path
        filename = os.path.basename(file_path)

        # Skip non-json files
        if not filename.endswith('.json'):
            return

        current_size = os.path.getsize(file_path)
        current_mtime = os.path.getmtime(file_path)

        if (file_path not in self.file_states or
            current_size != self.file_states[file_path]["size"] or
            current_mtime != self.file_states[file_path]["mtime"]):
            logger.info(f"Change detected in {file_path}")
            logger.info(f"Size changed: {self.file_states.get(file_path, {}).get('size', 0)} -> {current_size}")
            logger.info(f"Modification time changed: {self.file_states.get(file_path, {}).get('mtime', 0)} -> {current_mtime}")
            self.file_states[file_path] = {"size": current_size, "mtime": current_mtime}

            # Cancel any existing timer
            if self.timer:
                self.timer.cancel()

            # Process changes after a delay
            logger.info("Starting 30-second wait before processing...")
            self.timer = Timer(30, self.process_changes, args=(file_path,))
            self.timer.start()

    def process_changes(self, changed_file):
        """Process the changed file."""
        try:
            logger.info("30-second wait completed. Processing changes...")
            with self.app.app_context():
                logger.info(f"Processing file: {changed_file}")
                force_cache_update(changed_file)
            logger.info("File processing and cache update completed")
        except Exception as e:
            logger.error(f"Error processing file changes: {e}", exc_info=True)
        finally:
            with self.lock:
                self.processing = False

def start_watchdog(directory_to_watch, app):
    event_handler = FileChangeHandler(app, directory_to_watch)
    observer = Observer()
    observer.schedule(event_handler, path=directory_to_watch, recursive=False)
    observer.start()
    logger.info(f"Started watching directory: {directory_to_watch}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("Watchdog stopped by user.")
    observer.join()
