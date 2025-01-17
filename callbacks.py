# callbacks.py
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
from cache_config import get_visualizations

def register_callbacks(app):

    @app.callback(
        Output('overview-figs-store', 'data'),
        Input('overview-interval', 'n_intervals')
    )
    def update_overview_figs(n):
        figs = get_visualizations('all_data.json') or []
        if len(figs) < 13:
            figs = [go.Figure()] * 13
        # convert figs to dict for JSON serializability
        return {'figs': [f.to_dict() for f in figs]}

    @app.callback(
        [
            Output('overview-indicator-packets', 'figure'),
            Output('overview-indicator-data-points', 'figure'),
            Output('overview-indicator-cyber-reports', 'figure'),
            Output('overview-treemap', 'figure'),
            Output('overview-pie-chart', 'figure'),
            Output('overview-hourly-heatmap', 'figure'),
            Output('overview-daily-heatmap', 'figure'),
            Output('overview-sankey-diagram', 'figure'),
            Output('overview-sankey-heatmap-diagram', 'figure'),
            Output('overview-protocol-pie-chart', 'figure'),
            Output('overview-parallel-categories', 'figure'),
            Output('overview-stacked-area', 'figure'),
            Output('overview-anomalies-scatter', 'figure'),
        ],
        Input('overview-figs-store', 'data')
    )
    def display_overview_figs(data):
        if not data or 'figs' not in data:
            return [go.Figure()] * 13
        figs = [go.Figure(f) for f in data['figs']]
        return figs

    # do the same pattern for 1h
    @app.callback(
        Output('1h-figs-store', 'data'),
        Input('1h-interval', 'n_intervals')
    )
    def update_1h_figs(n):
        figs = get_visualizations('1_hour_data.json') or []
        if len(figs) < 13:
            figs = [go.Figure()] * 13
        return {'figs': [f.to_dict() for f in figs]}

    @app.callback(
        [
            Output('1h-indicator-packets', 'figure'),
            Output('1h-indicator-data-points', 'figure'),
            Output('1h-indicator-cyber-reports', 'figure'),
            Output('1h-treemap', 'figure'),
            Output('1h-pie-chart', 'figure'),
            Output('1h-hourly-heatmap', 'figure'),
            Output('1h-daily-heatmap', 'figure'),
            Output('1h-sankey-diagram', 'figure'),
            Output('1h-sankey-heatmap-diagram', 'figure'),
            Output('1h-protocol-pie-chart', 'figure'),
            Output('1h-parallel-categories', 'figure'),
            Output('1h-stacked-area', 'figure'),
            Output('1h-anomalies-scatter', 'figure'),
        ],
        Input('1h-figs-store', 'data')
    )
    def display_1h_figs(data):
        if not data or 'figs' not in data:
            return [go.Figure()] * 13
        figs = [go.Figure(f) for f in data['figs']]
        return figs

    # do the same pattern for 24h
    @app.callback(
        Output('24h-figs-store', 'data'),
        Input('24h-interval', 'n_intervals')
    )
    def update_24h_figs(n):
        figs = get_visualizations('24_hours_data.json') or []
        if len(figs) < 13:
            figs = [go.Figure()] * 13
        return {'figs': [f.to_dict() for f in figs]}

    @app.callback(
        [
            Output('24h-indicator-packets', 'figure'),
            Output('24h-indicator-data-points', 'figure'),
            Output('24h-indicator-cyber-reports', 'figure'),
            Output('24h-treemap', 'figure'),
            Output('24h-pie-chart', 'figure'),
            Output('24h-hourly-heatmap', 'figure'),
            Output('24h-daily-heatmap', 'figure'),
            Output('24h-sankey-diagram', 'figure'),
            Output('24h-sankey-heatmap-diagram', 'figure'),
            Output('24h-protocol-pie-chart', 'figure'),
            Output('24h-parallel-categories', 'figure'),
            Output('24h-stacked-area', 'figure'),
            Output('24h-anomalies-scatter', 'figure'),
        ],
        Input('24h-figs-store', 'data')
    )
    def display_24h_figs(data):
        if not data or 'figs' not in data:
            return [go.Figure()] * 13
        figs = [go.Figure(f) for f in data['figs']]
        return figs
