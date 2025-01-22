import os
import threading
import logging
from flask_caching import Cache
from colorlog import ColoredFormatter
from data_processing import read_and_process_file
from collections import defaultdict
import math
import pickle
import zlib

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

cache = Cache()

# track last update times so dash doesn't keep re-fetching
last_file_timestamp = {}
file_locks = defaultdict(threading.Lock)

# --- CHUNKED CACHE HELPERS --- #
def set_in_chunks(key, data, chunk_size=500*1024):
    """compress and split data into chunks and store each chunk separately."""
    comp = zlib.compress(data)
    nchunks = math.ceil(len(comp) / chunk_size)
    for i in range(nchunks):
        chunk = comp[i*chunk_size:(i+1)*chunk_size]
        cache.set(f"{key}:chunk:{i}", chunk)
    cache.set(f"{key}:nchunks", nchunks)

def get_from_chunks(key):
    """retrieve chunks, reassemble, and decompress."""
    nchunks = cache.get(f"{key}:nchunks")
    if not nchunks:
        return None
    comp = b"".join(cache.get(f"{key}:chunk:{i}") for i in range(int(nchunks)))
    try:
        return zlib.decompress(comp)
    except Exception as e:
        logger.error(f"decompress failed for {key}: {e}")
        return None
# --- END CHUNKED CACHE HELPERS --- #

def update_cache_for_file(filename):
    """read data from file and store processed figs into cache using chunked storage."""
    file_path = os.path.join("/home/iaes/DiodeSensor/FM1/output", filename)
    with file_locks[file_path]:
        mod_time = os.path.getmtime(file_path)
        prev_time = last_file_timestamp.get(filename, 0)
        if mod_time <= prev_time:
            logger.info(f"file {filename} didn't get newer. skipping.")
            return

        logger.info(f"generating figs for {filename}")
        try:
            data, figs, total_reports = read_and_process_file(file_path)
            payload = pickle.dumps({
                'data': data,
                'total_reports': total_reports,
                'timestamp': mod_time,
            })
            # use chunked set for the big payload
            set_in_chunks(f'cached_data_{filename}', payload)
            # similarly, for figs if they're large; adjust if figs are small
            figs_payload = pickle.dumps(figs)
            set_in_chunks(f'visualizations_{filename}', figs_payload)
            cache.set(f'last_update_timestamp_{filename}', mod_time)
            last_file_timestamp[filename] = mod_time
            logger.info(f"cache updated for {filename}")
        except Exception as e:
            logger.error(f"error reading and caching {filename}: {e}")

def get_cached_data(filename):
    payload = get_from_chunks(f'cached_data_{filename}')
    if not payload:
        logger.info(f"no cached data for {filename}. forcing update...")
        update_cache_for_file(filename)
        payload = get_from_chunks(f'cached_data_{filename}')
    if payload is None:
        return None, 0
    stored = pickle.loads(payload)
    return stored['data'], stored['total_reports']

def get_visualizations(filename):
    figs_payload = get_from_chunks(f'visualizations_{filename}')
    if not figs_payload:
        logger.info(f"no figs in cache for {filename}. forcing update...")
        update_cache_for_file(filename)
        figs_payload = get_from_chunks(f'visualizations_{filename}')
    if not figs_payload:
        logger.warning(f"still no figs for {filename} after update, returning empties.")
        return []
    figs = pickle.loads(figs_payload)
    return figs

def initialize_cache():
    logger.info("initializing cache fresh...")
    data_dir = "/home/iaes/DiodeSensor/FM1/output"
    for filename in os.listdir(data_dir):
        if filename.endswith('.json'):
            logger.info(f"loading {filename} into cache once...")
            update_cache_for_file(filename)
