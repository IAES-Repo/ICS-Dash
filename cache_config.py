from flask_caching import Cache
from data_processing import read_and_process_file
import logging
import plotly.graph_objects as go
from colorlog import ColoredFormatter
from collections import deque
import threading
import time
import os

# configure colorlog
formatter_cache = ColoredFormatter(
    "%(log_color)s%(levelname)s:%(name)s:%(message)s",
    datefmt=None,
    reset=True,
    log_colors={
        'DEBUG': 'purple',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    }
)

handler_cache = logging.StreamHandler()
handler_cache.setFormatter(formatter_cache)

logging.basicConfig(level=logging.INFO, handlers=[handler_cache])
logger = logging.getLogger(__name__)

cache = Cache(config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory',
    'CACHE_DEFAULT_TIMEOUT': 3600
})

processing_queue = deque()
queue_lock = threading.Lock()
is_first_run = True
data_folder = "/home/iaes/DiodeSensor/FM1/output/"

def initialize_cache():
    global is_first_run
    if is_first_run:
        logger.info("First run detected. Initializing cache with fresh data...")
        enqueue_existing_files()
        start_processing_thread()
        is_first_run = False
        logger.info("Cache initialized with fresh data.")
    else:
        logger.info("Not first run. Using existing cache if available.")

def enqueue_existing_files():
    files = []
    for file in os.listdir(data_folder):
        if file.endswith('.json'):
            file_path = os.path.join(data_folder, file)
            file_size = os.path.getsize(file_path)
            files.append((file_path, file_size))

    files.sort(key=lambda x: x[1], reverse=False) # emallest file to largest

    with queue_lock:
        for file_path, sz in files:
            processing_queue.append(file_path)
            logger.info(f"Queued file for processing: {file_path} (size: {sz} bytes)")

def process_queue():
    while True:
        with queue_lock:
            if not processing_queue:
                time.sleep(5)
                continue
            file_path = processing_queue.popleft()

        try:
            logger.info(f"Processing file: {file_path}")
            data, figs, total_reports = read_and_process_file(file_path)
            cache.set(f'cached_data_{os.path.basename(file_path)}', {
                'data': data,
                'total_reports': total_reports,
                'timestamp': time.time()
            })
            cache.set(f'visualizations_{os.path.basename(file_path)}', figs)
            logger.info(f"File processed and cached: {file_path}")
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}", exc_info=True)

def start_processing_thread():
    processing_thread = threading.Thread(target=process_queue)
    processing_thread.daemon = True
    processing_thread.start()

def invalidate_cache():
    logger.info("Invalidating entire cache...")
    cache.clear()
    logger.info("Cache invalidated.")

def get_cached_data(filename):
    try:
        cache_key = f'cached_data_{filename}'
        cached_data = cache.get(cache_key)
        if cached_data is None:
            logger.info(f"Cached data not found for {filename}, queuing for processing...")
            with queue_lock:
                processing_queue.append(os.path.join(data_folder, filename))
            return None, 0
        return cached_data['data'], cached_data['total_reports']
    except Exception as e:
        logger.error(f"Error getting cached data for {filename}: {e}", exc_info=True)
        return None, 0

def get_visualizations(filename=None):
    try:
        if filename:
            cache_key = f'visualizations_{filename}'
            figs = cache.get(cache_key)
            if figs is None:
                logger.info(f"Visualizations not found in cache for {filename}, queuing for processing...")
                with queue_lock:
                    processing_queue.append(os.path.join(data_folder, filename))
                return [go.Figure()] * 13
            return figs
        else:
            logger.error("Filename must be provided to get visualizations.")
            return [go.Figure()] * 13
    except Exception as e:
        logger.error(f"Error getting visualizations for {filename}: {e}", exc_info=True)
        return [go.Figure()] * 13

def force_cache_update(changed_file=None):
    if changed_file:
        logger.info(f"Processing updated file: {changed_file}")
        with queue_lock:
            processing_queue.append(changed_file)
    else:
        logger.info("Forcing cache update for all files...")
        invalidate_cache()
        enqueue_existing_files()
    logger.info("Cache update completed.")
