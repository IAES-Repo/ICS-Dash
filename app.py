"""
This Dash application creates an interactive web dashboard for monitoring 
and analyzing ICS (Industrial Control Systems) network data. The dashboard
includes various visualizations such as top 10 lists, traffic analysis, 
activity patterns,protocol analysis, and data flow. The application 
monitors a specified directory for changes in JSON files, processes the 
data, updates the visualizations in real-time, and caches data for 
efficient retrieval. It uses the watchdog library to handle file system 
events and threads to run the file watcher in the background.
"""
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output
import logging
import threading
from cache_config import cache
from callbacks import update_graphs, get_cached_data, get_visualizations
from layouts import (
    overview_layout,
    top10_layout,
    traffic_analysis_layout,
    activity_patterns_layout,
    protocol_analysis_layout,
    data_flow_layout
)

# Attempt to use orjson if available
try:
    import orjson
    import dash.dash
    dash.dash._json = orjson
except ImportError:
    pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

# Initialize cache with the server
cache.init_app(app.server)

# Path to the directory containing JSON files
input_directory = "/home/iaes/iaesDash/source/jsondata/fm1"
# Path to the output combined JSON file
output_file = "/home/iaes/iaesDash/source/jsondata/fm1/output/data.json"

# Call the cached functions once to populate the cache
data, total_cyber9_reports = get_cached_data()
figs = get_visualizations()

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
        
    ],
    [Input("interval-component", "n_intervals")]
)(update_graphs)

# Function to invalidate cache
def invalidate_cache():
    cache.delete_memoized(get_cached_data)
    cache.delete_memoized(get_visualizations)

# Run the app
if __name__ == "__main__":
    try:
        logger.info("Running the server")
        app.run_server(host="127.0.0.1", port=8050, debug=True)
    except Exception as e:
        logger.error(f"Error running the server: {e}")
