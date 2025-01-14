# watchdog_handler.py

import os
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from cache_config import update_cache_for_file

logger = logging.getLogger(__name__)

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, server, directory_to_watch):
        super().__init__()
        self.server = server
        self.directory_to_watch = directory_to_watch

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.json'):
            logger.info(f"File created: {event.src_path}")
            self.handle_change(event.src_path)

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.json'):
            logger.info(f"File modified: {event.src_path}")
            self.handle_change(event.src_path)

    def on_moved(self, event):
        if not event.is_directory and event.dest_path.endswith('.json'):
            logger.info(f"File moved from {event.src_path} to {event.dest_path}")
            self.handle_change(event.dest_path)

    def handle_change(self, file_path):
        # just call our update func directly
        filename = os.path.basename(file_path)
        update_cache_for_file(filename)

def start_watchdog(directory_to_watch, server):
    event_handler = FileChangeHandler(server, directory_to_watch)
    observer = Observer()
    observer.schedule(event_handler, path=directory_to_watch, recursive=False)
    observer.start()
    logger.info(f"Watching {directory_to_watch} for .json changes...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
