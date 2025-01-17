# cache_config.py

import threading
import time
import os
import logging
from flask_caching import Cache
from colorlog import ColoredFormatter
from data_processing import read_and_process_file
from collections import defaultdict

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
    'CACHE_TYPE': 'memcached',
    'CACHE_DIR': 'cache-directory',
    'CACHE_DEFAULT_TIMEOUT': 3600
})

# track last updated times so dash doesn't keep re-fetching
last_file_timestamp = {}
file_locks = defaultdict(threading.Lock)

def initialize_cache():
    # on startup, just load existing .json files if you want
    logger.info("Initializing cache fresh...")
    # if you prefer to skip reading them all at startup, remove this
    data_dir = "/home/iaes/DiodeSensor/FM1/output"
    for filename in os.listdir(data_dir):
        if filename.endswith('.json'):
            logger.info(f"Loading {filename} into cache once...")
            update_cache_for_file(filename)

def update_cache_for_file(filename):
    """ read data from changed file and store new figs in cache if updated """
    file_path = os.path.join("/home/iaes/DiodeSensor/FM1/output", filename)

    # do per-file locking so we don't process duplicates concurrently
    with file_locks[file_path]:
        mod_time = os.path.getmtime(file_path)
        prev_time = last_file_timestamp.get(filename, 0)
        if mod_time <= prev_time:
            logger.info(f"File {filename} didn't actually get newer. skipping.")
            return

        # read data, create figs
        logger.info(f"Generating figs for {filename}")
        try:
            data, figs, total_reports = read_and_process_file(file_path)
            # store in cache
            cache.set(f'cached_data_{filename}', {
                'data': data,
                'total_reports': total_reports,
                'timestamp': mod_time,
            })
            cache.set(f'visualizations_{filename}', figs)
            # update the time so your dash callbacks know it's fresh
            cache.set(f'last_update_timestamp_{filename}', mod_time)

            # remember it locally to skip re-process next time
            last_file_timestamp[filename] = mod_time
            logger.info(f"cache updated for {filename}")
        except Exception as e:
            logger.error(f"error reading and caching {filename}: {e}")

def get_cached_data(filename):
    stuff = cache.get(f'cached_data_{filename}')
    if not stuff:
        # maybe queue a re-load if not found
        logger.info(f"No cached data for {filename}. Forcing update...")
        update_cache_for_file(filename)
        stuff = cache.get(f'cached_data_{filename}')
    if stuff is None:
        return None, 0
    return stuff['data'], stuff['total_reports']

def get_visualizations(filename):
    figs = cache.get(f'visualizations_{filename}')
    if not figs:
        logger.info(f"No figs in cache for {filename}. forcing update...")
        update_cache_for_file(filename)
        figs = cache.get(f'visualizations_{filename}')
    if not figs:
        logger.warning(f"Still no figs for {filename} after update, returning empties.")
        return []
    return figs
