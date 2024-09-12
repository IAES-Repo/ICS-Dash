from dash.dependencies import Input, Output
from cache_config import get_visualizations
import dash
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
        [Input("interval-component", "n_intervals")]
    )
    def update_graphs(n_intervals):
        logger.info(f"Update graphs called with n_intervals: {n_intervals}")
        figs = get_visualizations()
        logger.info(f"Figures obtained")
        return figs
