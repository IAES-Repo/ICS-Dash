# callbacks.py

from dash.dependencies import Input, Output
from cache_config import get_visualizations
import plotly.graph_objects as go
import logging
from colorlog import ColoredFormatter

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
    # Callback to update figs-store based on interval and url
    @app.callback(
        Output('figs-store', 'data'),
        [Input('interval-component', 'n_intervals'),
         Input('url', 'pathname')]
    )
    def update_figs(n_intervals, pathname):
        logger.info(f"update_figs called with n_intervals: {n_intervals}, pathname: {pathname}")

        # Determine which datafile to use based on pathname
        if pathname == '/1_hour_data':
            datafile = '1_hour_data.json'
        elif pathname == '/24_hours_data':
            datafile = '24_hours_data.json'
        elif pathname == '/7_days_data':
            datafile = '7_days_data.json'
        else:
            datafile = 'all_data.json'

        figs = get_visualizations(filename=datafile)
        if not figs or len(figs) < 13:
            figs = [go.Figure()] * 13

        # Serialize figs to dicts (already done in cache_config.py)
        figs_dict = figs  # Assuming get_visualizations returns list of dicts
        logger.info(f"Figures fetched and serialized successfully for {datafile}.")
        return figs_dict

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
