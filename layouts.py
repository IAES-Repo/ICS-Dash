# layouts.py

from dash import dcc, html
import plotly.graph_objects as go

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
