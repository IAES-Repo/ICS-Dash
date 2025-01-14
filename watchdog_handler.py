# watchdog_handler.py

import time
import os
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from watchdog.events import FileSystemEvent
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
        logger.info("Scanning existing files in the directory to initialize states.")
        for filename in os.listdir(self.directory_to_watch):
            file_path = os.path.join(self.directory_to_watch, filename)
            if os.path.isfile(file_path) and filename.endswith('.json'):
                self.file_states[file_path] = {
                    "size": os.path.getsize(file_path),
                    "mtime": os.path.getmtime(file_path),
                }
                logger.debug(f"Initialized state for {file_path}: size={self.file_states[file_path]['size']}, mtime={self.file_states[file_path]['mtime']}")


    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.json'):
            logger.info(f"File created: {event.src_path}")
            self.on_modified(event)

    def on_moved(self, event):
        if not event.is_directory and event.dest_path.endswith('.json'):
            logger.info(f"File moved: {event.dest_path}")
            # Treat the moved file as a modified file
            self.on_modified(FileSystemEvent(event.dest_path))

    def on_modified(self, event):
        """Handle modified files."""
        if event.is_directory:
            return

        file_path = event.src_path
        filename = os.path.basename(file_path)

        # Skip non-json files
        if not filename.endswith('.json'):
            logger.debug(f"Ignored modification for non-json file: {filename}")
            return

        current_size = os.path.getsize(file_path)
        current_mtime = os.path.getmtime(file_path)

        previous_state = self.file_states.get(file_path, {})
        previous_size = previous_state.get("size", 0)
        previous_mtime = previous_state.get("mtime", 0)

        if (current_size != previous_size) or (current_mtime != previous_mtime):
            logger.info(f"Change detected in {file_path}")
            logger.info(f"Size changed: {previous_size} -> {current_size}")
            logger.info(f"Modification time changed: {previous_mtime} -> {current_mtime}")
            self.file_states[file_path] = {"size": current_size, "mtime": current_mtime}

            # Cancel any existing timer
            if self.timer:
                logger.debug("Existing timer found. Canceling it.")
                self.timer.cancel()

            # Process changes after a short delay to ensure file write completion
            logger.info("Starting 5-second wait before processing changes...")
            self.timer = Timer(5, self.process_changes, args=(filename,))
            self.timer.start()
        else:
            logger.debug(f"No actual changes detected in {file_path}.")

    def process_changes(self, changed_filename):
        """Process the changed file."""
        try:
            logger.info(f"Processing changes for file: {changed_filename}")
            with self.app.app_context():
                logger.info(f"Calling force_cache_update for {changed_filename}")
                force_cache_update(changed_filename)
            logger.info(f"Completed processing changes for {changed_filename}")
        except Exception as e:
            logger.error(f"Error processing changes for {changed_filename}: {e}", exc_info=True)
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
