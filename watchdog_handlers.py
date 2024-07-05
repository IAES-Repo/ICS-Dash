"""
This module sets up a file system watcher using the watchdog library to 
monitor changes in a directory. It logs events such as file 
creation and modification, ensuring that events are not processed too 
frequently to avoid looping. The watcher runs in a separate thread, 
allowing it to monitor the directory in the background while the main
program continues to execute.

Note: This will most likely be removed due to our new collector.py module
which takes care of tracking and processing new changes.
"""

import logging
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import threading

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define a handler for file system events
class Handler(FileSystemEventHandler):
    def __init__(self):
        self.last_event_time = time.time()
        self.min_interval = 2  # Minimum interval between events to avoid looping

    def on_any_event(self, event):
        current_time = time.time()
        if current_time - self.last_event_time < self.min_interval:
            return

        self.last_event_time = current_time

        if event.is_directory:
            return None
        elif event.event_type in ("created", "modified"):
            logger.info(f"Event type: {event.event_type} - Path: {event.src_path}")

# Watchdog class to monitor a directory
class Watcher:
    def __init__(self, directory_to_watch):
        if not os.path.exists(directory_to_watch):
            raise FileNotFoundError(f"Directory {directory_to_watch} does not exist.")
        self.observer = Observer()
        self.directory_to_watch = directory_to_watch

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.directory_to_watch, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()

# Function to start the watcher
def start_watcher(directory):
    watcher = Watcher(directory)
    watcher_thread = threading.Thread(target=watcher.run)
    watcher_thread.daemon = True
    watcher_thread.start()
    return watcher_thread
