# callbacks.py
import dash
from dash.dependencies import Input, Output, State
from cache_config import get_visualizations, cache
import plotly.graph_objects as go
import logging
from colorlog import ColoredFormatter
from dash import callback_context
from dash.exceptions import PreventUpdate

# Configure colorlog
formatter_callbacks = ColoredFormatter(
    "%(log_color)s%(levelname)s:%(name)s:%(message)s",
    datefmt=None,
    reset=True,
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'magenta',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    }
)

handler_callbacks = logging.StreamHandler()
handler_callbacks.setFormatter(formatter_callbacks)

# Configure logging
logging.basicConfig(level=logging.INFO, handlers=[handler_callbacks])
logger = logging.getLogger(__name__)

def register_callbacks(app):
    # Callback to update figs-store based on interval
    @app.callback(
        Output('figs-store', 'data'),
        [
            Input('interval-component', 'n_intervals'),
            Input('url', 'pathname')
        ],
        State('last-visual-update', 'data')
    )
    def update_figs(n_intervals, pathname, last_visual_update):
        logger.info(f"update_figs called with n_intervals: {n_intervals}")

        # Map pathname to datafile
        path_to_file = {
            "/": 'all_data.json',
            "/1_hour_data": '1_hour_data.json',
            "/24_hours_data": '24_hours_data.json',
            "/7_days_data": '7_days_data.json'
        }

        datafile = path_to_file.get(pathname, 'all_data.json')
        logger.info(f"Determined datafile: {datafile}")

        # Get last update timestamp from cache
        last_update_timestamp = cache.get(f'last_update_timestamp_{datafile}')
        if last_update_timestamp is None:
            logger.info(f"No update timestamp found for {datafile}. Fetching visualizations.")
            figs = get_visualizations(filename=datafile)
            return [fig.to_dict() for fig in figs]

        # Get the last visual update timestamp from State
        last_visual_time = last_visual_update.get(datafile, 0) if last_visual_update else 0

        logger.info(f"Last update timestamp for {datafile}: {last_update_timestamp}")
        logger.info(f"Last visual update timestamp for {datafile}: {last_visual_time}")

        if last_update_timestamp > last_visual_time:
            logger.info(f"{datafile} has been updated since the last visual update. Updating visuals.")
            figs = get_visualizations(filename=datafile)
            if not figs or len(figs) < 13:
                figs = [go.Figure()] * 13
            figs_dict = [fig.to_dict() for fig in figs]
            return figs_dict
        else:
            logger.info(f"No updates detected for {datafile} since the last visual update.")
            raise dash.expections.PreventUpdate

    # Callback to update the last visual update timestamp
    @app.callback(
        Output('last-visual-update', 'data'),
        [Input('figs-store', 'data')],
        [State('url', 'pathname')]
    )
    def set_last_visual_update(figs_data, pathname):
        logger.info("set_last_visual_update called.")
        path_to_file = {
            "/": 'all_data.json',
            "/1_hour_data": '1_hour_data.json',
            "/24_hours_data": '24_hours_data.json',
            "/7_days_data": '7_days_data.json'
        }

        datafile = path_to_file.get(pathname, 'all_data.json')
        last_update_timestamp = cache.get(f'last_update_timestamp_{datafile}')
        if last_update_timestamp is not None:
            return {datafile: last_update_timestamp}
        return {}

    # Callback to update graph figures from figs-store
    @app.callback(
        [
            Output("indicator-packets", "figure"),
            Output("indicator-data-points", "figure"),
            Output("indicator-cyber-reports", "figure"),
            Output("treemap_source_destination_protocol", "figure"),
            Output("pie-chart", "figure"),
            Output("hourly-heatmap", "figure"),
            Output("daily-heatmap", "figure"),
            Output("sankey-diagram", "figure"),
            Output("sankey-heatmap-diagram", "figure"),
            Output("protocol-pie-chart", "figure"),
            Output("parallel-categories", "figure"),
            Output("stacked-area", "figure"),
            Output("anomalies-scatter", "figure")
        ],
        [Input('figs-store', 'data')]
    )
    def display_figs(figs_data):
        logger.info("display_figs callback triggered.")

        if figs_data is None:
            logger.warning("No figs data in store. Returning empty figures.")
            return [go.Figure()] * 13

        # Convert dicts back to go.Figure
        try:
            figs = [go.Figure(fig_dict) for fig_dict in figs_data]
            logger.info("Figures deserialized successfully.")
            return figs
        except Exception as e:
            logger.error(f"Error deserializing figures: {e}")
            return [go.Figure()] * 13