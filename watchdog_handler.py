import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from cache_config import update_cache, invalidate_cache
import time
import os
from threading import Timer, Lock
from colorlog import ColoredFormatter

# Configure colorlog
formatter = ColoredFormatter(
    "%(log_color)s%(levelname)s:%(name)s:%(message)s",
    datefmt=None,
    reset=True,
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    }
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)

# Configure logging
logging.basicConfig(level=logging.INFO, handlers=[handler])
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
            if self.processing:
                logger.info("Debounce skipped: Already processing")
                return

            self.processing = True
            logger.info(f"Debounce processing started for file: {event.src_path}")

        time.sleep(30)  # Sleep outside the lock to avoid holding the lock for too long

        with self.app.app_context():
            try:
                with self.lock:
                    if os.path.getsize(event.src_path) > 0:
                        logger.info("Valid file size detected, updating cache...")
                        invalidate_cache()
                        update_cache()
                    else:
                        logger.warning(f"File {event.src_path} is empty, retrying in 1 second...")
                        time.sleep(1)
                        if os.path.getsize(event.src_path) > 0:
                            invalidate_cache()
                            update_cache()
                        else:
                            logger.error(f"File {event.src_path} is still empty after retry.")
            except Exception as e:
                logger.error(f"Error updating cache on file modification: {e}")
            finally:
                with self.lock:
                    self.processing = False

    def on_modified(self, event):
        if not event.is_directory and event.src_path == self.output_file:
            logger.info(f"File modified: {event.src_path}")
            with self.lock:
                if self.debounce_timer:
                    self.debounce_timer.cancel()
                self.debounce_timer = Timer(2, self.debounce, [event])
                self.debounce_timer.start()
                logger.info(f"Debounce timer started for {event.src_path}")

def start_watchdog(directory_to_watch, app, output_file):
    event_handler = WatchdogHandler(app, output_file)
    observer = Observer()
    observer.schedule(event_handler, directory_to_watch, recursive=True)
    observer.start()
    logger.info(f"Started watching directory: {directory_to_watch}")
