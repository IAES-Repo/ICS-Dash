# callbacks.py
import dash
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from dash import callback_context
import plotly.graph_objects as go
import logging
from colorlog import ColoredFormatter

from cache_config import get_visualizations, cache

formatter_callbacks = ColoredFormatter(
    "%(log_color)s%(levelname)s:%(name)s:%(message)s",
    datefmt=None,
    reset=True,
    log_colors={
        'debug': 'cyan',
        'info': 'magenta',
        'warning': 'yellow',
        'error': 'red',
        'critical': 'red,bg_white',
    }
)
handler_callbacks = logging.StreamHandler()
handler_callbacks.setFormatter(formatter_callbacks)
logging.basicConfig(level=logging.info, handlers=[handler_callbacks])
logger = logging.getLogger(__name__)

def register_callbacks(app):

    # update figs-store periodically
    @app.callback(
        Output('figs-store', 'data'),
        [
            Input('interval-component', 'n_intervals'),
            Input('url', 'pathname')
        ],
        State('figs-store', 'data')
    )
    def update_figs(n_intervals, pathname, figs_store):
        logger.info(f"update_figs called with n_intervals={n_intervals}")

        path_map = {
            "/": 'all_data.json',
            "/1_hour_data": '1_hour_data.json',
            "/24_hours_data": '24_hours_data.json',
            "/7_days_data": '7_days_data.json'
        }
        datafile = path_map.get(pathname, 'all_data.json')
        logger.info(f"target datafile: {datafile}")

        # see what we stored last time
        old_timestamp = 0
        if figs_store and isinstance(figs_store, dict):
            old_timestamp = figs_store.get('timestamp', 0)

        # get the new timestamp from the cache
        new_timestamp = cache.get(f'last_update_timestamp_{datafile}')
        if not new_timestamp:
            logger.info(f"cache has no timestamp for {datafile}, forcing new figs")
            # try forcing a get to fill the cache if it’s missing
            figs = get_visualizations(datafile)
            # store in figs-store
            return {
                'timestamp': 0,
                'figs': [fig.to_dict() for fig in figs]
            }

        if new_timestamp > old_timestamp:
            logger.info("detected updated file -> fetching new figs from cache")
            figs = get_visualizations(datafile)
            if not figs or len(figs) < 13:
                figs = [go.Figure()] * 13
            return {
                'timestamp': new_timestamp,
                'figs': [fig.to_dict() for fig in figs]
            }
        else:
            logger.info("no change detected in file -> prevent update")
            raise PreventUpdate

    # read figs-store data to display
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
        Input('figs-store', 'data')
    )
    def display_figs(figs_store):
        logger.info("display_figs callback triggered")

        if not figs_store or 'figs' not in figs_store:
            logger.warning("no figs in store, returning empty placeholders")
            return [go.Figure()] * 13

        try:
            figs = [go.Figure(fig_dict) for fig_dict in figs_store['figs']]
            return figs
        except Exception as e:
            logger.error(f"error rehydrating figs: {e}")
            return [go.Figure()] * 13
