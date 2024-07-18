from flask_caching import Cache
from data_processing import read_data, create_visualizations
import logging
import plotly.graph_objects as go

# Initialize Cache
cache = Cache(config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory',
    'CACHE_DEFAULT_TIMEOUT': 3600  # Set default timeout to 1 hour
})

logger = logging.getLogger(__name__)

def invalidate_cache():
    logger.info("Invalidating cache...")
    cache.clear()

def update_cache():
    logger.info("Updating cache...")
    try:
        invalidate_cache()
        # Calling the cached functions to repopulate the cache
        get_cached_data()
        get_visualizations()
        logger.info("Cache updated successfully.")
    except Exception as e:
        logger.error(f"Error updating cache: {e}")

@cache.memoize(timeout=3600)
def get_cached_data():
    try:
        data, total_cyber9_reports = read_data()
        return data, total_cyber9_reports
    except Exception as e:
        logger.error(f"Error getting cached data: {e}")
        return None, 0

@cache.memoize(timeout=3600)
def get_visualizations():
    try:
        data, total_cyber9_reports = get_cached_data()
        return create_visualizations(data, total_cyber9_reports)
    except Exception as e:
        logger.error(f"Error getting visualizations: {e}")
        return [go.Figure()] * 12
