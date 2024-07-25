from dash import dcc, html
from data_processing import create_visualizations, read_data
import plotly.graph_objects as go
import logging
from colorlog import ColoredFormatter

# Configure colorlog
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

# Configure logging
logging.basicConfig(level=logging.INFO, handlers=[handler])
logger = logging.getLogger(__name__)

try:
    data, total_cyber9_reports = read_data()
    (
        fig_indicator_packets,
        fig_indicator_data_points,
        fig_indicator_cyber_reports,
        fig_treemap_src_dst_protocol,
        fig3,
        fig4,
        fig5,
        fig_sankey,
        fig_sankey_heatmap,
        fig_protocol_pie,
        fig_parallel,
        fig_stacked_area,
        fig_anomalies
    ) = create_visualizations(data, total_cyber9_reports)
except Exception as e:
    logger.error(f"Error reading initial data or creating visualizations: {e}", exc_info=True)
    (
        fig_indicator_packets,
        fig_indicator_data_points,
        fig_indicator_cyber_reports,
        fig_treemap_src_dst_protocol,
        fig3,
        fig4,
        fig5,
        fig_sankey,
        fig_sankey_heatmap,
        fig_protocol_pie,
        fig_parallel,
        fig_stacked_area,
        fig_anomalies
    ) = [go.Figure()] * 13

overview_layout = html.Div(
    [
        dcc.Interval(
            id='interval-component',
            interval=600*1000, # update every 10 mintues
            n_intervals=0
        ),
        dcc.Store(id='new-data-available', data=False),  # Hidden component to track new data
        html.H1("Overview", style={"color": "white", "margin": "16px 0"}),
        html.Div(
            className="row",
            children=[
                html.Div(
                    className="col-md-4",
                    children=[
                        dcc.Graph(id="indicator-packets", figure=fig_indicator_packets, className="card")
                    ],
                ),
                html.Div(
                    className="col-md-4",
                    children=[
                        dcc.Graph(id="indicator-data-points", figure=fig_indicator_data_points, className="card")
                    ],
                ),
                html.Div(
                    className="col-md-4",
                    children=[
                        dcc.Graph(id="indicator-cyber-reports", figure=fig_indicator_cyber_reports, className="card")
                    ],
                ),
            ],
        ),
        html.Div(
            className="row",
            children=[
                html.Div(
                    className="col-md-12",
                    children=[
                        dcc.Graph(id="treemap_source_destination_protocol", figure=fig_treemap_src_dst_protocol, className="card")
                    ],
                ),
            ],
        ),
        html.Div(
            className="row",
            children=[
                html.Div(
                    className="col-md-6",
                    children=[
                        dcc.Graph(id="pie-chart", figure=fig3, className="card")
                    ],
                ),
                html.Div(
                    className="col-md-6",
                    children=[
                        dcc.Graph(id="hourly-heatmap", figure=fig4, className="card")
                    ],
                ),
            ],
        ),
        html.Div(
            className="row",
            children=[
                html.Div(
                    className="col-md-6",
                    children=[
                        dcc.Graph(id="daily-heatmap", figure=fig5, className="card")
                    ],
                ),
                html.Div(
                    className="col-md-6",
                    children=[
                        dcc.Graph(id="sankey-diagram", figure=fig_sankey, className="card")
                    ],
                ),
            ],
        ),
        html.Div(
            className="row",
            children=[
                html.Div(
                    className="col-md-6",
                    children=[
                        dcc.Graph(id="sankey-heatmap-diagram", figure=fig_sankey_heatmap, className="card")
                    ],
                ),
                html.Div(
                    className="col-md-6",
                    children=[
                        dcc.Graph(id="protocol-pie-chart", figure=fig_protocol_pie, className="card")
                    ],
                ),
            ],
        ),
        html.Div(
            className="row",
            children=[
                html.Div(
                    className="col-md-6",
                    children=[
                        dcc.Graph(id="parallel-categories", figure=fig_parallel, className="card")
                    ],
                ),
            ],
        ),
        html.Div(
            className="row",
            children=[
                html.Div(
                    className="col-md-12",
                    children=[
                        dcc.Graph(id="stacked-area", figure=fig_stacked_area, className="card")
                    ],
                ),
            ],
        ),
        html.Div(
            className="row",
            children=[
                html.Div(
                    className="col-md-12",
                    children=[
                        dcc.Graph(id="anomalies-scatter", figure=fig_anomalies, className="card")
                    ],
                ),
            ],
        ),
    ]
)

top10_layout = html.Div(
    [
        html.H1("Top 10s", style={"color": "white", "margin": "16px 0"}),
    ]
)

traffic_analysis_layout = html.Div(
    [
        html.H1("Traffic Analysis", style={"color": "white", "margin": "16px 0"}),
    ]
)

activity_patterns_layout = html.Div(
    [
        html.H1("Activity Patterns", style={"color": "white", "margin": "16px 0"}),
    ]
)

protocol_analysis_layout = html.Div(
    [
        html.H1("Protocol Analysis", style={"color": "white", "margin": "16px 0"}),
    ]
)

data_flow_layout = html.Div(
    [
        html.H1("Data Flow", style={"color": "white", "margin": "16px 0"}),
    ]
)
