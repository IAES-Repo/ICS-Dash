import logging
from data_processing import read_data, create_visualizations
from cache_config import cache
import plotly.graph_objects as go

# Set up logger
logger = logging.getLogger(__name__)

# Cache the result of this function
@cache.memoize(timeout=3600)  # Cache timeout in seconds, adjust as needed
def get_cached_data():
    try:
        data, total_cyber9_reports = read_data()  # Read the data from the source
        return data, total_cyber9_reports
    except Exception as e:
        logger.error(f"Error getting cached data: {e}")  # Log any errors encountered
        return None, 0  # Return default values in case of error

# Cache the result of this function
@cache.memoize(timeout=3600)  # Cache timeout in seconds, adjust as needed
def get_visualizations():
    try:
        data, total_cyber9_reports = get_cached_data()  # Get cached data
        return create_visualizations(data, total_cyber9_reports)  # Create visualizations
    except Exception as e:
        logger.error(f"Error getting visualizations: {e}")  # Log any errors encountered
        return [go.Figure()] * 13  # Return a list of empty figures in case of error

# Function to update graphs periodically, intended to be used as a callback
def update_graphs(n_intervals):
    logger.debug(f"update_graphs called with n_intervals={n_intervals}")  # Debug log for function call
    try:
        figs = get_visualizations()  # Get cached visualizations
        return figs
    except Exception as e:
        logger.error(f"Error updating graphs: {e}")  # Log any errors encountered
        return [go.Figure()] * 13  # Return a list of empty figures in case of error