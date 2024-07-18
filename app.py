import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output
import logging
from cache_config import cache, update_cache
from callbacks import update_graphs, get_cached_data, get_visualizations
from layouts import (
    overview_layout,
    top10_layout,
    traffic_analysis_layout,
    activity_patterns_layout,
    protocol_analysis_layout,
    data_flow_layout
)
from watchdog_handler import start_watchdog  # Import the watchdog handler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress Werkzeug logs
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

# Initialize cache with the server
cache.init_app(app.server)

def initialize_cache():
    logger.info("Populating cache with initial data...")
    data, total_cyber9_reports = get_cached_data()
    figs = get_visualizations()
    logger.info("Cache initialized successfully.")

# Define the app layout
app.layout = html.Div(
    [
        dcc.Location(id='url', refresh=False),
        html.Div(
            [
                html.Nav(
                    className="navbar navbar-dark sticky-top flex-md-nowrap p-0",
                    children=[
                        html.A(
                            "⠀⠀IAES ICS Dashboard",
                            className="navbar-brand col-sm-3 col-md-2 mr-0",
                            href="#",
                        ),
                        html.Ul(
                            className="navbar-nav px-3",
                            children=[
                                html.Li(className="nav-item text-nowrap", children=[])
                            ],
                        ),
                    ],
                ),
                html.Div(
                    className="container-fluid",
                    children=[
                        html.Div(
                            className="row",
                            children=[
                                html.Nav(
                                    className="col-md-2 d-none d-md-block sidebar",
                                    children=[
                                        html.Div(
                                            className="sidebar-sticky",
                                            children=[
                                                html.Ul(
                                                    className="nav flex-column",
                                                    children=[
                                                        html.Li(
                                                            className="nav-item",
                                                            children=[
                                                                html.A(
                                                                    "Overview",
                                                                    className="nav-link active",
                                                                    href="/",
                                                                )
                                                            ],
                                                        ),
                                                        html.Li(
                                                            className="nav-item",
                                                            children=[
                                                                html.A(
                                                                    "Top 10s",
                                                                    className="nav-link",
                                                                    href="/top10s",
                                                                )
                                                            ],
                                                        ),
                                                        html.Li(
                                                            className="nav-item",
                                                            children=[
                                                                html.A(
                                                                    "Traffic Analysis",
                                                                    className="nav-link",
                                                                    href="/traffic-analysis",
                                                                )
                                                            ],
                                                        ),
                                                        html.Li(
                                                            className="nav-item",
                                                            children=[
                                                                html.A(
                                                                    "Activity Patterns",
                                                                    className="nav-link",
                                                                    href="/activity-patterns",
                                                                )
                                                            ],
                                                        ),
                                                        html.Li(
                                                            className="nav-item",
                                                            children=[
                                                                html.A(
                                                                    "Protocol Analysis",
                                                                    className="nav-link",
                                                                    href="/protocol-analysis",
                                                                )
                                                            ],
                                                        ),
                                                        html.Li(
                                                            className="nav-item",
                                                            children=[
                                                                html.A(
                                                                    "Data Flow",
                                                                    className="nav-link",
                                                                    href="/data-flow",
                                                                )
                                                            ],
                                                        ),
                                                    ],
                                                )
                                            ],
                                        )
                                    ],
                                ),
                                html.Main(
                                    className="col-md-9 ml-sm-auto col-lg-10 my-3",
                                    children=[
                                        html.Div(id='page-content')
                                    ],
                                ),
                            ],
                        )
                    ],
                ),
            ],
        ),
    ]
)

# Callback to update the page content based on the URL
@app.callback(Output('page-content', 'children'), [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/top10s':
        return top10_layout
    elif pathname == '/traffic-analysis':
        return traffic_analysis_layout
    elif pathname == '/activity-patterns':
        return activity_patterns_layout
    elif pathname == '/protocol-analysis':
        return protocol_analysis_layout
    elif pathname == '/data-flow':
        return data_flow_layout
    else:
        return overview_layout

# Register the callback function for updating the graphs
app.callback(
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
    ],
    [Input("interval-component", "n_intervals")]
)(update_graphs)

# Start the watchdog only once in the main process
if __name__ == "__main__":
    try:
        logger.info("Starting the application...")

        logger.info("Running cache initialization and watchdog setup...")
        initialize_cache()
        directory_to_watch = "/home/iaes/iaesDash/source/jsondata/fm1/output"
        start_watchdog(directory_to_watch, app.server)
        #logger.info(f"Started watching directory: {directory_to_watch}")

        logger.info("Running the server")
        app.run_server(host="0.0.0.0", port=8050, debug=False)  # Set debug to False
    except Exception as e:
        logger.error(f"Error running the server: {e}")