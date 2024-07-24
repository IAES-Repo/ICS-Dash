import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from cache_config import update_cache, invalidate_cache
from flask import current_app
import time
import os
from threading import Timer, Lock

logger = logging.getLogger(__name__)

class WatchdogHandler(FileSystemEventHandler):
    def __init__(self, app, output_file):
        self.app = app
        self.output_file = output_file
        self.processing = False
        self.debounce_timer = None
        self.lock = Lock()
        super().__init__()

    def debounce(self, event):
        with self.lock:
            if not self.processing:
                self.processing = True
                logger.info(f"Modified file: {event.src_path}")
                logger.info("Sleeping for 30 seconds before processing the modified file...")
                time.sleep(30)
                with self.app.app_context():
                    try:
                        if os.path.getsize(event.src_path) > 0:
                            invalidate_cache()
                            update_cache()
                            current_app.config['NEW_DATA_AVAILABLE'] = True
                            logger.info("Set NEW_DATA_AVAILABLE to True")
                        else:
                            logger.warning(f"File {event.src_path} is empty, retrying in 1 second...")
                            time.sleep(1)
                            if os.path.getsize(event.src_path) > 0:
                                invalidate_cache()
                                update_cache()
                                current_app.config['NEW_DATA_AVAILABLE'] = True
                                logger.info("Set NEW_DATA_AVAILABLE to True after retry")
                            else:
                                logger.error(f"File {event.src_path} is still empty after retry.")
                    except Exception as e:
                        logger.error(f"Error updating cache on file modification: {e}")
                    finally:
                        self.processing = False
                        with self.app.app_context():
                            self.app.config['NEW_DATA_AVAILABLE'] = True
                            logger.info("Set NEW_DATA_AVAILABLE to True in debounce finally block")

    def on_modified(self, event):
        if not event.is_directory:
            with self.lock:
                if self.debounce_timer:
                    self.debounce_timer.cancel()
                self.debounce_timer = Timer(2, self.debounce, [event])
                self.debounce_timer.start()

def start_watchdog(directory_to_watch, app, output_file):
    event_handler = WatchdogHandler(app, output_file)
    observer = Observer()
    observer.schedule(event_handler, directory_to_watch, recursive=True)
    observer.start()
    logger.info(f"Started watching directory: {directory_to_watch}")
