"""
This module handles data processing and visualization for a Dash 
application. It includes functions to read data, generate visualizations, 
and update graphs. The functions are designed to work with cached data 
and handle errors gracefully, logging any issues that occur during execution.
"""

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
        data, total_cyber9_reports = read_data()  # Read the data from the source
        return create_visualizations(total_cyber9_reports)  # Create visualizations
    except Exception as e:
        logger.error(f"Error getting visualizations: {e}")  # Log any errors encountered
        return [go.Figure()] * 12  # Return a list of empty figures in case of error

# Function to update graphs periodically, intended to be used as a callback
def update_graphs(n_intervals):
    logger.debug(f"update_graphs called with n_intervals={n_intervals}")  # Debug log for function call
    try:
        data, total_cyber9_reports = read_data()  # Read the data from the source
        (
            fig_indicator_packets,
            fig_indicator_data_points, 
            fig_indicator_cyber_reports,
            fig_treemap_src_dst_protocol,
            fig3, 
            fig4, 
            fig5, 
            fig_sankey, 
            fig_sankey_heatmap, 
            fig_protocol_pie, 
            fig_parallel, 
            fig_stacked_area, 
        ) = create_visualizations(total_cyber9_reports)  # Create visualizations

        return (
            fig_indicator_packets,
            fig_indicator_data_points,
            fig_indicator_cyber_reports,
            fig_treemap_src_dst_protocol,
            fig3,
            fig4,
            fig5,
            fig_sankey,
            fig_sankey_heatmap,
            fig_protocol_pie,
            fig_parallel,
            fig_stacked_area,
        )
    except Exception as e:
        logger.error(f"Error updating graphs: {e}")  # Log any errors encountered
        return [go.Figure()] * 12  # Return a list of empty figures in case of error
