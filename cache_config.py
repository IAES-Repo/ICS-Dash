from flask_caching import Cache
from data_processing import read_data, create_visualizations
import logging
import plotly.graph_objects as go
from colorlog import ColoredFormatter

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

def invalidate_cache():
    logger.info("Invalidating cache...")
    cache.clear()
    logger.info("Cache invalidated.")

def update_cache():
    logger.info("Updating cache...")
    try:
        data, total_cyber9_reports = read_data()
        cache.set('cached_data', data)
        cache.set('total_cyber9_reports', total_cyber9_reports)
        figs = create_visualizations(data, total_cyber9_reports)
        cache.set('visualizations', figs)
        logger.info("Cache updated successfully.")
    except Exception as e:
        logger.error(f"Error updating cache: {e}", exc_info=True)

def get_cached_data():
    try:
        data = cache.get('cached_data')
        total_cyber9_reports = cache.get('total_cyber9_reports')
        if data is None or total_cyber9_reports is None:
            logger.info("Cached data not found, reading data...")
            data, total_cyber9_reports = read_data()
            cache.set('cached_data', data)
            cache.set('total_cyber9_reports', total_cyber9_reports)
        return data, total_cyber9_reports
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
