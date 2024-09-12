from flask_caching import Cache
from data_processing import read_data, create_visualizations
import logging
import plotly.graph_objects as go
from colorlog import ColoredFormatter
import time

# Configure colorlog
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

# Configure logging
logging.basicConfig(level=logging.INFO, handlers=[handler_cache])
logger = logging.getLogger(__name__)

# Initialize Cache
cache = Cache(config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory',
    'CACHE_DEFAULT_TIMEOUT': 3600  # Set default timeout to 1 hour
})

is_first_run = True

def initialize_cache():
    global is_first_run
    if is_first_run:
        logger.info("First run detected. Initializing cache with fresh data...")
        update_cache()
        is_first_run = False
        logger.info("Cache initialized with fresh data.")
    else:
        logger.info("Not first run. Using existing cache if available.")

def invalidate_cache():
    logger.info("Invalidating cache...")
    cache.delete('cached_data')
    cache.delete('visualizations')
    logger.info("Cache invalidated.")

def update_cache():
    logger.info("Updating cache...")
    try:
        data, total_cyber9_reports = read_data()
        figs = create_visualizations(data, total_cyber9_reports)
        cache.set('cached_data', {'data': data, 'total_cyber9_reports': total_cyber9_reports, 'timestamp': time.time()})
        cache.set('visualizations', figs)
        logger.info("Cache updated successfully.")
    except Exception as e:
        logger.error(f"Error updating cache: {e}", exc_info=True)

def get_cached_data():
    try:
        cached_data = cache.get('cached_data')
        if cached_data is None:
            logger.info("Cached data not found, reading fresh data...")
            update_cache()
            cached_data = cache.get('cached_data')
        return cached_data['data'], cached_data['total_cyber9_reports']
    except Exception as e:
        logger.error(f"Error getting cached data: {e}", exc_info=True)
        return None, 0

def get_visualizations():
    try:
        figs = cache.get('visualizations')
        if figs is None:
            logger.info("Visualizations not found in cache, creating visualizations...")
            data, total_cyber9_reports = get_cached_data()
            figs = create_visualizations(data, total_cyber9_reports)
            cache.set('visualizations', figs)
        return figs
    except Exception as e:
        logger.error(f"Error getting visualizations: {e}", exc_info=True)
        return [go.Figure()] * 13

def force_cache_update():
    logger.info("Forcing cache update...")
    invalidate_cache()
    update_cache()
    logger.info("Cache update completed.")