from dash.dependencies import Input, Output, State
from cache_config import get_visualizations
import dash
import logging

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
            Output("anomalies-scatter", "figure"),
            Output('new-data-available', 'data')
        ],
        [Input("interval-component", "n_intervals"),
         Input('new-data-available', 'data')]
    )
    def update_graphs(n_intervals, new_data_available):
        logger.info(f"Update graphs called with n_intervals: {n_intervals}, new_data_available: {new_data_available}")
        if new_data_available:
            logger.info("Processing new data...")
            figs = get_visualizations()
            logger.info(f"Figures obtained: {figs}")
            with app.server.app_context():
                app.server.config['NEW_DATA_AVAILABLE'] = False  # Reset the flag to False
            return figs + [False]  # Reset the new data flag to False
        else:
            logger.info("No new data available to process.")
        return dash.no_update

