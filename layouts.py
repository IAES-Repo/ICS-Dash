from dash import dcc, html
from cache_config import get_visualizations
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

def generate_layout_for_datafile(datafile_name, page_title, nav_links=None):
    """Generate a layout for the given datafile.

    datafile_name: str, e.g. 'all_data.json'
    page_title: str, title for the page
    nav_links: list of (text, href) tuples for navigation, e.g. [('1-Hour Data', '/1_hour_data'), ...]
    """
    figs = get_visualizations(datafile_name)
    if not figs or len(figs) < 13:
        figs = [go.Figure()] * 13

    (fig_indicator_packets,
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
     fig_anomalies) = figs

    # build navigation bar if provided
    nav_bar = html.Div(
        [dcc.Link(text, href=href) for text, href in (nav_links or [])],
        className="header-links"
    )
    return html.Div(
        [
            nav_bar,
            html.H1(page_title, style={"color": "white", "margin": "16px 0"}),
            html.Div(className="row", children=[
                html.Div(className="col-md-4", children=[dcc.Graph(figure=fig_indicator_packets, className="card")]),
                html.Div(className="col-md-4", children=[dcc.Graph(figure=fig_indicator_data_points, className="card")]),
                html.Div(className="col-md-4", children=[dcc.Graph(figure=fig_indicator_cyber_reports, className="card")]),
            ]),
            html.Div(className="row", children=[
                html.Div(className="col-md-12", children=[
                    dcc.Graph(figure=fig_treemap_src_dst_protocol, className="card")
                ]),
            ]),
            html.Div(className="row", children=[
                html.Div(className="col-md-6", children=[dcc.Graph(figure=fig3, className="card")]),
                html.Div(className="col-md-6", children=[dcc.Graph(figure=fig4, className="card")]),
            ]),
            html.Div(className="row", children=[
                html.Div(className="col-md-6", children=[dcc.Graph(figure=fig5, className="card")]),
                html.Div(className="col-md-6", children=[dcc.Graph(figure=fig_sankey, className="card")]),
            ]),
            html.Div(className="row", children=[
                html.Div(className="col-md-6", children=[dcc.Graph(figure=fig_sankey_heatmap, className="card")]),
                html.Div(className="col-md-6", children=[dcc.Graph(figure=fig_protocol_pie, className="card")]),
            ]),
            html.Div(className="row", children=[
                html.Div(className="col-md-6", children=[dcc.Graph(figure=fig_parallel, className="card")]),
            ]),
            html.Div(className="row", children=[
                html.Div(className="col-md-12", children=[dcc.Graph(figure=fig_stacked_area, className="card")]),
            ]),
            html.Div(className="row", children=[
                html.Div(className="col-md-12", children=[dcc.Graph(figure=fig_anomalies, className="card")]),
            ]),
        ]
    )

# now define specific layouts using this function
overview_layout = html.Div([
    dcc.Interval(id='interval-component', interval=600*1000, n_intervals=0),
    dcc.Store(id='new-data-available', data=False),
    generate_layout_for_datafile(
        'all_data.json',
        "Overview (all_data.json)",
        nav_links=[("1-Hour Data", "/1_hour_data"), ("24-Hours Data", "/24_hours_data"), ("7-Days Data", "/7_days_data")]
    )
])

one_hour_layout = generate_layout_for_datafile(
    '1_hour_data.json',
    "1 Hour Data",
    nav_links=[("Overview", "/"), ("24-Hours Data", "/24_hours_data"), ("7-Days Data", "/7_days_data")]
)

twenty_four_hour_layout = generate_layout_for_datafile(
    '24_hours_data.json',
    "24 Hours Data",
    nav_links=[("Overview", "/"), ("1-Hour Data", "/1_hour_data"), ("7-Days Data", "/7_days_data")]
)

seven_days_layout = generate_layout_for_datafile(
    '7_days_data.json',
    "7 Days Data",
    nav_links=[("Overview", "/"), ("1-Hour Data", "/1_hour_data"), ("24-Hours Data", "/24_hours_data")]
)
