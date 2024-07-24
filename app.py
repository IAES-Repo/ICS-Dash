import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output
import logging
from cache_config import cache, update_cache, get_visualizations
from layouts import (
    overview_layout,
    top10_layout,
    traffic_analysis_layout,
    activity_patterns_layout,
    protocol_analysis_layout,
    data_flow_layout
)
from watchdog_handler import start_watchdog
from flask import Flask
from callbacks import register_callbacks  # Import the callback registration function

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress Werkzeug logs
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Initialize the Flask server
server = Flask(__name__)
server.config['NEW_DATA_AVAILABLE'] = False  # Define the new_data_available attribute

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], server=server, suppress_callback_exceptions=True)

# Initialize cache with the server
cache.init_app(app.server)

app.layout = html.Div(
    [
        dcc.Location(id='url', refresh=False),
        dcc.Interval(
            id='interval-component',
            interval=600*1000,  # Update every 10 minutes for faster debugging
            n_intervals=0
        ),
        dcc.Store(id='new-data-available', data=False),  # Hidden component to track new data
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

@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
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

# Register callbacks from callbacks.py
register_callbacks(app)

# Initialize the cache with the initial visualizations
update_cache()
logger.info("Initial cache update completed.")

watchdog_started = False

if __name__ == "__main__":
    if not watchdog_started:
        logger.info("Starting the application...")
        output_file = "/home/iaes/iaesDash/source/jsondata/fm1/output/data.json"
        directory_to_watch = "/home/iaes/iaesDash/source/jsondata/fm1/output"
        start_watchdog(directory_to_watch, app.server, output_file)
        logger.info("Initializing the server")
    app.run_server(host="0.0.0.0", port=8050, debug=False)
