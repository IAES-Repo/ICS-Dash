# callbacks.py
import time
from dash.dependencies import Input, Output, State
from dash import no_update, callback, ctx
from flask_caching import logger
import plotly.graph_objects as go
from cache_config import get_visualizations, update_cache_for_file, cache
from datetime import datetime, timedelta
import os
from data_processing import read_data, create_visualizations, count_files_in_directory
import hashlib
import json
from collector import NetworkDataHandler  
import dash_bootstrap_components as dbc
from dash import dcc, html


def register_callbacks(app, handler):

    # Overview callbacks
    @app.callback(
        Output('overview-figs-store', 'data'),
        Input('overview-interval', 'n_intervals')
    )
    def update_overview_figs(n):
        figs = get_visualizations('all_data.json') or []
        if len(figs) < 13:
            figs = [go.Figure()] * 13
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
        return [go.Figure(f) for f in data['figs']]

    # 1-hour callbacks
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
        return [go.Figure(f) for f in data['figs']]

    # 24-hour callbacks
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
        return [go.Figure(f) for f in data['figs']]

    # Custom timeframe callbacks
    @app.callback(
        Output('custom-figs-store', 'data'),
        Input('search-button', 'n_clicks'),
        Input('custom-status-check', 'n_intervals'),
        [
            State('start-date-picker', 'date'),
            State('start-time-input', 'value'),
            State('end-date-picker', 'date'),
            State('end-time-input', 'value'),
            State('custom-figs-store', 'data'),
            State('filter-protocol', 'value'),
            State('filter-dstip', 'value'),
            State('filter-srcip', 'value'),
            State('filter-srcport', 'value'),
            State('filter-dstport', 'value')
        ]
    )
    def update_custom_figs(n_clicks, n_intervals, start_date, start_time, end_date, end_time, store_data, filter_protocol, filter_dstip, filter_srcip, filter_srcport, filter_dstport):

        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if triggered_id == 'search-button':
            if not n_clicks:
                return no_update

            # parse dates
            try:
                start_str = f"{start_date} {start_time or '00:00:00'}"
                end_str = f"{end_date} {end_time or '23:59:59'}"
                start_dt = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
                end_dt = datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")
                if start_dt >= end_dt:
                    raise ValueError("end time must be after start time")
            except ValueError as e:
                return {'status': 'error', 'message': str(e)}

            # build filter dict, ignore blanks
            filters = {
                'PROTOCOL': filter_protocol.strip() if filter_protocol else None,
                'DSTIP': filter_dstip.strip() if filter_dstip else None,
                'SRCIP': filter_srcip.strip() if filter_srcip else None,
                'SRCPORT': filter_srcport.strip() if filter_srcport else None,
                'DSTPORT': filter_dstport.strip() if filter_dstport else None,
            }

            # pass filters to task scheduler (assume you update your handler accordingly)
            task_id = handler.add_custom_task(start_dt, end_dt, filters=filters)
            return {
                'status': 'processing',
                'task_id': task_id,
                'filename': None,
                'message': 'processing request...',
                'timestamp': time.time()
            }
        
        elif triggered_id == 'custom-status-check':
            current_data = store_data or {}
            if current_data.get('status') == 'processing':
                task_id = current_data.get('task_id')
                with handler.lock:
                    task = handler.active_tasks.get(task_id, {})
                
                if task.get('status') == 'complete':
                    return {
                        'status': 'ready',
                        'task_id': task_id,
                        'filename': task.get('filename'),
                        'message': None,
                        'timestamp': time.time()  # Force refresh
                    }
                elif task.get('status') == 'failed':
                    return {
                        'status': 'error',
                        'task_id': task_id,
                        'filename': None,
                        'message': task.get('message', 'Failed to generate dataset'),
                        'timestamp': time.time()
                    }
            
            return no_update
        
        return store_data or {}

    @app.callback(
    [
        Output('custom-visuals-container', 'children'),
        Output('custom-status-alert', 'children'),
        Output('custom-status-check', 'interval')
    ],
    Input('custom-figs-store', 'data'),
    prevent_initial_call=True
)
    def display_custom_figs(data):
        if not data or 'status' not in data:
            return no_update, no_update, no_update
            
        if data['status'] == 'processing':
            return (
                no_update,
                dbc.Alert("Generating dataset... This may take a few minutes.", color="info"),
                1000
            )
        
        if data['status'] == 'ready':
            try:
                filename = data['filename']
                filepath = os.path.join("/home/iaes/DiodeSensor/FM1/output", filename)
                
                if not os.path.exists(filepath):
                    raise FileNotFoundError("Dataset file not found")

                # Get fresh figures and ensure proper conversion
                figs = get_visualizations(filename, force_refresh=True)
                visuals = [go.Figure(fig) if isinstance(fig, dict) else fig for fig in figs]

                # Create components in EXACT layout order
                components = [
                    dcc.Graph(figure=visuals[0], id='custom-indicator-packets', className="card"),
                    dcc.Graph(figure=visuals[1], id='custom-indicator-data-points', className="card"),
                    dcc.Graph(figure=visuals[2], id='custom-indicator-cyber-reports', className="card"),
                    dcc.Graph(figure=visuals[3], id='custom-treemap', className="card"),
                    dcc.Graph(figure=visuals[4], id='custom-pie-chart', className="card"),
                    dcc.Graph(figure=visuals[5], id='custom-hourly-heatmap', className="card"),
                    dcc.Graph(figure=visuals[6], id='custom-daily-heatmap', className="card"),
                    dcc.Graph(figure=visuals[7], id='custom-sankey-diagram', className="card"),
                    dcc.Graph(figure=visuals[8], id='custom-sankey-heatmap-diagram', className="card"),
                    dcc.Graph(figure=visuals[9], id='custom-protocol-pie-chart', className="card"),
                    dcc.Graph(figure=visuals[10], id='custom-parallel-categories', className="card"),
                    dcc.Graph(figure=visuals[11], id='custom-stacked-area', className="card"),
                    dcc.Graph(figure=visuals[12], id='custom-anomalies-scatter', className="card")
                ]

                return (
                    components,
                    dbc.Alert("Data loaded successfully!", color="success", duration=4000),
                    no_update
                )
                
            except Exception as e:
                logger.error(f"Display error: {str(e)}", exc_info=True)
                return (
                    [dcc.Graph(className="card") for _ in range(13)],
                    dbc.Alert(f"Display error: {str(e)}", color="danger"),
                    no_update
                )
        
        if data['status'] == 'error':
            return (
                no_update,
                dbc.Alert(data.get('message', 'Unknown error occurred'), color="danger"),
                no_update
            )
        
        return no_update, no_update, no_update

    @app.callback(
        Output('cleanup-dummy', 'data'),
        Input('cleanup-interval', 'n_intervals')
    )
    def trigger_cleanup(n):
        clean_old_custom_files()
        return no_update

def clean_old_custom_files():
    """Remove custom JSON files older than 1 hour"""
    output_dir = "/home/iaes/DiodeSensor/FM1/output"
    now = datetime.now()
    
    for entry in os.scandir(output_dir):
        if entry.name.startswith("custom_") and entry.name.endswith(".json"):
            try:
                # Clear associated cache entries
                cache.delete(f'cached_data_{entry.name}')
                cache.delete(f'visualizations_{entry.name}')
                file_time = datetime.fromtimestamp(entry.stat().st_mtime)
                if (now - file_time) > timedelta(hours=1):
                    os.remove(entry.path)
                    print(f"Cleaned up old custom file: {entry.name}")
            except Exception as e:
                print(f"Error cleaning file {entry.name}: {e}")