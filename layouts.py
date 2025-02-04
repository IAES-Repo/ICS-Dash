# layouts.py

from dash import dcc, html
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging
from colorlog import ColoredFormatter

formatter = ColoredFormatter(
    "%(log_color)s%(levelname)s:%(name)s:%(message)s",
    datefmt=None,
    reset=True,
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'blue',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    }
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)
logging.basicConfig(level=logging.INFO, handlers=[handler])
logger = logging.getLogger(__name__)

# ---- OVERVIEW (7 DAYS) LAYOUT ----
overview_layout = html.Div([
    # interval + store for overview
    dcc.Interval(id='overview-interval', interval=600*1000, n_intervals=0),
    dcc.Store(id='overview-figs-store', data={}),
    
    html.Div(
        [
            dcc.Link("Last Hour", href="/1_hour_data"),
            dcc.Link("Last 24 Hours", href="/24_hours_data"),
            dcc.Link("Custom Search", href="/custom_data"),
        ],
        className="header-links"
    ),
    html.H1("Overview (Last 7 Days)", style={"color": "white", "margin": "16px 0"}),

    html.Div(className="row", children=[
        html.Div(className="col-md-4", children=[
            dcc.Graph(id="overview-indicator-packets", figure=go.Figure(), className="card")
        ]),
        html.Div(className="col-md-4", children=[
            dcc.Graph(id="overview-indicator-data-points", figure=go.Figure(), className="card")
        ]),
        html.Div(className="col-md-4", children=[
            dcc.Graph(id="overview-indicator-cyber-reports", figure=go.Figure(), className="card")
        ]),
    ]),
    html.Div(className="row", children=[
        html.Div(className="col-md-12", children=[
            dcc.Graph(id="overview-treemap", figure=go.Figure(), className="card")
        ]),
    ]),
    html.Div(className="row", children=[
        html.Div(className="col-md-6", children=[
            dcc.Graph(id="overview-pie-chart", figure=go.Figure(), className="card")
        ]),
        html.Div(className="col-md-6", children=[
            dcc.Graph(id="overview-hourly-heatmap", figure=go.Figure(), className="card")
        ]),
    ]),
    html.Div(className="row", children=[
        html.Div(className="col-md-6", children=[
            dcc.Graph(id="overview-daily-heatmap", figure=go.Figure(), className="card")
        ]),
        html.Div(className="col-md-6", children=[
            dcc.Graph(id="overview-sankey-diagram", figure=go.Figure(), className="card")
        ]),
    ]),
    html.Div(className="row", children=[
        html.Div(className="col-md-6", children=[
            dcc.Graph(id="overview-sankey-heatmap-diagram", figure=go.Figure(), className="card")
        ]),
        html.Div(className="col-md-6", children=[
            dcc.Graph(id="overview-protocol-pie-chart", figure=go.Figure(), className="card")
        ]),
    ]),
    html.Div(className="row", children=[
        html.Div(className="col-md-6", children=[
            dcc.Graph(id="overview-parallel-categories", figure=go.Figure(), className="card")
        ]),
    ]),
    html.Div(className="row", children=[
        html.Div(className="col-md-12", children=[
            dcc.Graph(id="overview-stacked-area", figure=go.Figure(), className="card")
        ]),
    ]),
    html.Div(className="row", children=[
        html.Div(className="col-md-12", children=[
            dcc.Graph(id="overview-anomalies-scatter", figure=go.Figure(), className="card")
        ]),
    ]),
])

# ---- 1-HOUR LAYOUT ----
one_hour_layout = html.Div([
    # interval + store for 1 hour data
    dcc.Interval(id='1h-interval', interval=600*1000, n_intervals=0),
    dcc.Store(id='1h-figs-store', data={}),
    
    html.Div(
        [
            dcc.Link("Overview", href="/"),
            dcc.Link("Last 24 Hours", href="/24_hours_data"),
            dcc.Link("Custom Search", href="/custom_data"),
        ],
        className="header-links"
    ),
    html.H1("Last Hour", style={"color": "white", "margin": "16px 0"}),

    html.Div(className="row", children=[
        html.Div(className="col-md-4", children=[
            dcc.Graph(id="1h-indicator-packets", figure=go.Figure(), className="card")
        ]),
        html.Div(className="col-md-4", children=[
            dcc.Graph(id="1h-indicator-data-points", figure=go.Figure(), className="card")
        ]),
        html.Div(className="col-md-4", children=[
            dcc.Graph(id="1h-indicator-cyber-reports", figure=go.Figure(), className="card")
        ]),
    ]),
    html.Div(className="row", children=[
        html.Div(className="col-md-12", children=[
            dcc.Graph(id="1h-treemap", figure=go.Figure(), className="card")
        ]),
    ]),
    html.Div(className="row", children=[
        html.Div(className="col-md-6", children=[
            dcc.Graph(id="1h-pie-chart", figure=go.Figure(), className="card")
        ]),
        html.Div(className="col-md-6", children=[
            dcc.Graph(id="1h-hourly-heatmap", figure=go.Figure(), className="card")
        ]),
    ]),
    html.Div(className="row", children=[
        html.Div(className="col-md-6", children=[
            dcc.Graph(id="1h-daily-heatmap", figure=go.Figure(), className="card")
        ]),
        html.Div(className="col-md-6", children=[
            dcc.Graph(id="1h-sankey-diagram", figure=go.Figure(), className="card")
        ]),
    ]),
    html.Div(className="row", children=[
        html.Div(className="col-md-6", children=[
            dcc.Graph(id="1h-sankey-heatmap-diagram", figure=go.Figure(), className="card")
        ]),
        html.Div(className="col-md-6", children=[
            dcc.Graph(id="1h-protocol-pie-chart", figure=go.Figure(), className="card")
        ]),
    ]),
    html.Div(className="row", children=[
        html.Div(className="col-md-6", children=[
            dcc.Graph(id="1h-parallel-categories", figure=go.Figure(), className="card")
        ]),
    ]),
    html.Div(className="row", children=[
        html.Div(className="col-md-12", children=[
            dcc.Graph(id="1h-stacked-area", figure=go.Figure(), className="card")
        ]),
    ]),
    html.Div(className="row", children=[
        html.Div(className="col-md-12", children=[
            dcc.Graph(id="1h-anomalies-scatter", figure=go.Figure(), className="card")
        ]),
    ]),
])

# ---- 24-HOURS LAYOUT ----
twenty_four_hour_layout = html.Div([
    # interval + store for 24 hour data
    dcc.Interval(id='24h-interval', interval=600*1000, n_intervals=0),
    dcc.Store(id='24h-figs-store', data={}),
    
    html.Div(
        [
            dcc.Link("Overview", href="/"),
            dcc.Link("Last Hour", href="/1_hour_data"),
            dcc.Link("Custom Search", href="/custom_data"),
        ],
        className="header-links"
    ),
    html.H1("Last 24 Hours", style={"color": "white", "margin": "16px 0"}),

    html.Div(className="row", children=[
        html.Div(className="col-md-4", children=[
            dcc.Graph(id="24h-indicator-packets", figure=go.Figure(), className="card")
        ]),
        html.Div(className="col-md-4", children=[
            dcc.Graph(id="24h-indicator-data-points", figure=go.Figure(), className="card")
        ]),
        html.Div(className="col-md-4", children=[
            dcc.Graph(id="24h-indicator-cyber-reports", figure=go.Figure(), className="card")
        ]),
    ]),
    html.Div(className="row", children=[
        html.Div(className="col-md-12", children=[
            dcc.Graph(id="24h-treemap", figure=go.Figure(), className="card")
        ]),
    ]),
    html.Div(className="row", children=[
        html.Div(className="col-md-6", children=[
            dcc.Graph(id="24h-pie-chart", figure=go.Figure(), className="card")
        ]),
        html.Div(className="col-md-6", children=[
            dcc.Graph(id="24h-hourly-heatmap", figure=go.Figure(), className="card")
        ]),
    ]),
    html.Div(className="row", children=[
        html.Div(className="col-md-6", children=[
            dcc.Graph(id="24h-daily-heatmap", figure=go.Figure(), className="card")
        ]),
        html.Div(className="col-md-6", children=[
            dcc.Graph(id="24h-sankey-diagram", figure=go.Figure(), className="card")
        ]),
    ]),
    html.Div(className="row", children=[
        html.Div(className="col-md-6", children=[
            dcc.Graph(id="24h-sankey-heatmap-diagram", figure=go.Figure(), className="card")
        ]),
        html.Div(className="col-md-6", children=[
            dcc.Graph(id="24h-protocol-pie-chart", figure=go.Figure(), className="card")
        ]),
    ]),
    html.Div(className="row", children=[
        html.Div(className="col-md-6", children=[
            dcc.Graph(id="24h-parallel-categories", figure=go.Figure(), className="card")
        ]),
    ]),
    html.Div(className="row", children=[
        html.Div(className="col-md-12", children=[
            dcc.Graph(id="24h-stacked-area", figure=go.Figure(), className="card")
        ]),
    ]),
    html.Div(className="row", children=[
        html.Div(className="col-md-12", children=[
            dcc.Graph(id="24h-anomalies-scatter", figure=go.Figure(), className="card")
        ]),
    ]),
])

# Custom search layout
custom_layout = html.Div([
    dcc.Interval(id='custom-interval', interval=600*1000, n_intervals=0),
    dcc.Interval(id='cleanup-interval', interval=3600*1000),  # 1 hour
    dcc.Interval(id='custom-status-check', interval=1000),
    html.Div(id='custom-status-alert'),
    dcc.Store(id='cleanup-dummy'),
    dcc.Store(id='custom-figs-store', data={}),
    
    html.Div(
        [
            dcc.Link("Overview", href="/"),
            dcc.Link("Last Hour", href="/1_hour_data"),
            dcc.Link("Last 24 Hours", href="/24_hours_data"),
            dcc.Link("Custom Search", href="/custom_data"),
        ],
        className="header-links"
    ),
    html.H1("Custom Timeframe", style={"color": "white", "margin": "16px 0"}),
    
    html.Div(
        [
        html.Label("Start", style={  # Label for "Start"
                    'color': 'white',
                    'font-weight': 'light',
                    'margin-bottom': '0px',
                    'text-align': 'center',
                }),
            html.Div(
                [
                    dcc.DatePickerSingle(
                        id='start-date-picker',
                        min_date_allowed=datetime(2000, 1, 1),
                        max_date_allowed=datetime(2100, 12, 31),
                        initial_visible_month=datetime.now(),
                        date=datetime.now() - timedelta(days=1),
                        style={
                        'outline': 'none',
                        

                    }
                    ),
                    dcc.Input(
                        id='start-time-input',
                        type='text',
                        placeholder='HH:MM:SS',
                        value='00:00:00',
                        pattern="^([0-1][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$",
                        style={
                        'margin-left': '10px',  # Add spacing between date picker and input
                        'width': '70px',
        

                    }
                    ),
                ],
                className="date-time-group"
            ),
            html.Label("End", style={
            'color': 'white',
            'font-weight': 'light',
            'margin-bottom': '0px',
            'text-align': 'center',
            'margin-left': '15px',
            }),
            html.Div(
                [
                    dcc.DatePickerSingle(
                        id='end-date-picker',
                        min_date_allowed=datetime(2000, 1, 1),
                        max_date_allowed=datetime(2100, 12, 31),
                        initial_visible_month=datetime.now(),
                        date=datetime.now(),
                        style={
                        'outline': 'none',
                    }
                    ),
                    dcc.Input(
                        id='end-time-input',
                        type='text',
                        placeholder='HH:MM:SS',
                        value='23:59:59',
                        style={
                        'margin-left': '10px',  # Add spacing between date picker and input
                        'width': '70px',
                    }
                    ),
                ],
                className="date-time-group"
            ),
            html.Button(
                'Search',
                id='search-button',
                n_clicks=0,
                style={
                    'background-color': '#5d0000',
                    'color': 'white',
                    'border': 'none',
                    'border-radius': '5px',
                    'padding': '10px 20px',
                    'cursor': 'pointer',
                    'margin-left': '10px',
                }
            ),
        ],
        id='custom-search-container'
    ),
    
    # Add the missing container with the correct ID
    html.Div(
        id='custom-visuals-container',
        children=[
            html.Div(className="row", children=[
                html.Div(className="col-md-4", children=[
                    dcc.Graph(id="custom-indicator-packets", figure=go.Figure(), className="card")
                ]),
                html.Div(className="col-md-4", children=[
                    dcc.Graph(id="custom-indicator-data-points", figure=go.Figure(), className="card")
                ]),
                html.Div(className="col-md-4", children=[
                    dcc.Graph(id="custom-indicator-cyber-reports", figure=go.Figure(), className="card")
                ]),
            ]),
            html.Div(className="row", children=[
                html.Div(className="col-md-12", children=[
                    dcc.Graph(id="custom-treemap", figure=go.Figure(), className="card")
                ]),
            ]),
            html.Div(className="row", children=[
                html.Div(className="col-md-6", children=[
                    dcc.Graph(id="custom-pie-chart", figure=go.Figure(), className="card")
                ]),
                html.Div(className="col-md-6", children=[
                    dcc.Graph(id="custom-hourly-heatmap", figure=go.Figure(), className="card")
                ]),
            ]),
            html.Div(className="row", children=[
                html.Div(className="col-md-6", children=[
                    dcc.Graph(id="custom-daily-heatmap", figure=go.Figure(), className="card")
                ]),
                html.Div(className="col-md-6", children=[
                    dcc.Graph(id="custom-sankey-diagram", figure=go.Figure(), className="card")
                ]),
            ]),
            html.Div(className="row", children=[
                html.Div(className="col-md-6", children=[
                    dcc.Graph(id="custom-sankey-heatmap-diagram", figure=go.Figure(), className="card")
                ]),
                html.Div(className="col-md-6", children=[
                    dcc.Graph(id="custom-protocol-pie-chart", figure=go.Figure(), className="card")
                ]),
            ]),
            html.Div(className="row", children=[
                html.Div(className="col-md-6", children=[
                    dcc.Graph(id="custom-parallel-categories", figure=go.Figure(), className="card")
                ]),
            ]),
            html.Div(className="row", children=[
                html.Div(className="col-md-12", children=[
                    dcc.Graph(id="custom-stacked-area", figure=go.Figure(), className="card")
                ]),
            ]),
            html.Div(className="row", children=[
                html.Div(className="col-md-12", children=[
                    dcc.Graph(id="custom-anomalies-scatter", figure=go.Figure(), className="card")
                ]),
            ]),
        ]
    )
])