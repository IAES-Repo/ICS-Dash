"""
This module processes data for the visualizations in a Dash application. 
It includes asynchronous functions to read JSON files, handle large data 
sets, and generate various visualizations such as indicators, heatmaps, 
pie charts, and Sankey diagrams. It uses orjson for fast JSON processing 
when available.
"""

import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.colors as colors
import logging
import asyncio
import aiofiles

# Attempt to use orjson if available for faster JSON operations
try:
    import orjson as json
except ImportError:
    import json

# FOLDER DIRECTORIES
DATA_FOLDER = "/home/iaes/iaesDash/source/jsondata/fm1/output"
C9REPORTS_FOLDER = "/home/iaes/iaesDash/source/c9reports"
MAX_ROWS = 1000000

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Required columns for data processing
required_columns = [
    "SRCIP", "DSTIP", "TOTPACKETS", "TOTDATA", "PROTOCOL",
    "12AM", "1AM", "2AM", "3AM", "4AM", "5AM", "6AM", "7AM",
    "8AM", "9AM", "10AM", "11AM", "12PM", "1PM", "2PM", "3PM",
    "4PM", "5PM", "6PM", "7PM", "8PM", "9PM", "10PM", "11PM",
    "MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"
]

# Required hourly columns
required_hourly_columns = [
    "12AM", "1AM", "2AM", "3AM", "4AM", "5AM", "6AM", "7AM",
    "8AM", "9AM", "10AM", "11AM", "12PM", "1PM", "2PM", "3PM",
    "4PM", "5PM", "6PM", "7PM", "8PM", "9PM", "10PM", "11PM",
]

# Required daily columns
required_daily_columns = [
    "MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"
]

# Asynchronous function to read a single JSON file
async def read_json_file(filepath):
    async with aiofiles.open(filepath, mode='rb') as f:
        content = await f.read()
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Error reading {filepath}: {e}")
            return None

# Asynchronous function to read all JSON files in the data folder
async def read_all_files():
    all_data = []
    tasks = []
    for filename in os.listdir(DATA_FOLDER):
        if filename.endswith(".json"):
            filepath = os.path.join(DATA_FOLDER, filename)
            tasks.append(read_json_file(filepath))
    results = await asyncio.gather(*tasks)
    for result in results:
        if result and isinstance(result, list) and len(result) > 1:
            all_data.extend(result[1:])
    logger.info(f"Total records loaded: {len(all_data)}")
    return all_data

# Function to read data asynchronously
async def async_read_data():
    all_data = await read_all_files()
    total_cyber9_reports = count_files_in_directory(C9REPORTS_FOLDER)
    return all_data, total_cyber9_reports

# Synchronous function to read data, compatible with async event loops
def read_data():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:  # No event loop running
        loop = None

    if loop and loop.is_running():
        future = asyncio.run_coroutine_threadsafe(async_read_data(), loop)
        all_data, total_cyber9_reports = future.result()
    else:
        all_data, total_cyber9_reports = asyncio.run(async_read_data())

    return all_data, total_cyber9_reports

# Function to count files in a directory
def count_files_in_directory(directory):
    try:
        items = os.listdir(directory)
        files = [item for item in items if os.path.isfile(os.path.join(directory, item))]
        total_cyber9_reports = len(files)
        return total_cyber9_reports
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return None

# Function to create visualizations from the data
def create_visualizations(total_cyber9_reports):
    try:
        all_data, total_cyber9_reports = read_data()
        if all_data is None:
            logger.error("No data available to create visualizations.")
            return (go.Figure(),) * 12

        df = pd.DataFrame(all_data).head(MAX_ROWS)
        if df.empty:
            logger.error("No valid data in DataFrame.")
            return (go.Figure(),) * 12

        logger.info(f"DataFrame head:\n{df.head()}")

        # Ensure all required columns are present
        for col in required_columns:
            if col not in df.columns:
                df[col] = 0
        logger.info(f"DataFrame with required columns:\n{df.head()}")

        # Convert TOTDATA to numeric
        df["TOTDATA_MB"] = pd.to_numeric(df["TOTDATA"].str.replace(" MB", ""), errors='coerce').fillna(0)

        custom_colorscale = [(0, "red"), (0.33, "yellow"), (0.67, "green"), (1, "blue")]

        # Create various visualizations
        total_packets = df["TOTPACKETS"].sum()
        fig_indicator_packets = go.Figure(
            go.Indicator(
                mode="number", value=total_packets, title={"text": "Total Packets"}
            )
        )
        fig_indicator_packets.update_layout(
            font=dict(color="white"), template="plotly_dark", height=250
        )

        total_data_points = len(df)
        fig_indicator_data_points = go.Figure(
            go.Indicator(
                mode="number",
                value=total_data_points,
                title={"text": "Total Connections"},
            )
        )
        fig_indicator_data_points.update_layout(
            font=dict(color="white"), template="plotly_dark", height=250
        )

        fig_indicator_cyber_reports = go.Figure(
            go.Indicator(
                mode="number",
                value=total_cyber9_reports,
                title={"text": "Total Cyber9 Line Reports"},
            )
        )
        fig_indicator_cyber_reports.update_layout(
            font=dict(color="white"), template="plotly_dark", height=250
        )

        fig_treemap_src_dst_protocol = px.treemap(df, path=['SRCIP', 'DSTIP', 'PROTOCOL'],template="plotly_dark", values='TOTPACKETS',height=600, title='Source, Destination IP and Protocol Distribution')

        df["TOTDATA"] = pd.to_numeric(df["TOTDATA_MB"], errors="coerce")
        total_data_by_srcip = df.groupby("SRCIP", as_index=False)["TOTDATA"].sum()
        top_10_data = total_data_by_srcip.nlargest(10, "TOTDATA")
        df["SRCIP_GROUPED"] = df["SRCIP"].where(df["SRCIP"].isin(top_10_data["SRCIP"]), "Others")
        grouped_data = df.groupby("SRCIP_GROUPED", as_index=False)["TOTDATA"].sum()
        fig3 = px.pie(
            grouped_data,
            names="SRCIP_GROUPED",
            values="TOTDATA",
            title="Total Data by Top 10 Source IP",
            color_discrete_sequence=[c[1] for c in custom_colorscale],
            template="plotly_dark",
        )

        hourly_activity = df[required_hourly_columns].sum().values.reshape(1, -1)
        logger.debug(f"Hourly Activity Data Shape: {hourly_activity.shape}")
        logger.debug(f"Hourly Activity Data:\n{hourly_activity}")

        fig4 = go.Figure(
            data=go.Heatmap(
                z=hourly_activity,
                x=required_hourly_columns,
                y=["Activity"],
                colorscale="jet",
                colorbar=dict(title="Number of Packets"),
            )
        )
        fig4.update_layout(
            title="Hourly Packet Activity Heatmap (with Overlay Line Plot)",
            xaxis_title="Hour",
            yaxis_title="Activity (log scale)",
            template="plotly_dark",
        )
        hourly_totals = df[required_hourly_columns].sum(axis=0)
        fig4.add_trace(
            go.Scatter(
                x=required_hourly_columns,
                y=hourly_totals,
                mode="lines+markers",
                line=dict(color="black"),
                name="Total Packets per Hour",
                yaxis="y2",
            )
        )
        fig4.update_layout(
            yaxis2=dict(title="", overlaying="y", side="right", showgrid=False),
            margin=dict(l=50, r=50, t=50, b=50),
        )

        daily_activity = df[required_daily_columns].sum().values.reshape(1, -1)
        logger.debug(f"Daily Activity Data Shape: {daily_activity.shape}")
        logger.debug(f"Daily Activity Data:\n{daily_activity}")

        fig5 = go.Figure(
            data=go.Heatmap(
                z=daily_activity,
                x=required_daily_columns,
                y=["Activity"],
                colorscale="jet",
                colorbar=dict(title="Number of Packets"),
            )
        )
        fig5.update_layout(
            title="Daily Activity Heatmap",
            xaxis_title="Day",
            yaxis_title="Activity",
            template="plotly_dark",
        )

        sankey_data = df.groupby(["SRCIP", "DSTIP"], as_index=False)["TOTDATA_MB"].sum()
        top_connections = sankey_data.nlargest(10, "TOTDATA_MB")
        all_nodes = list(set(top_connections["SRCIP"]).union(set(top_connections["DSTIP"])))
        node_map = {node: idx for idx, node in enumerate(all_nodes)}
        fig_sankey = go.Figure(
            data=[
                go.Sankey(
                    node=dict(
                        pad=15,
                        thickness=20,
                        line=dict(color="black", width=0.5),
                        label=all_nodes,
                        color="blue",
                    ),
                    link=dict(
                        source=[node_map[src] for src in top_connections["SRCIP"]],
                        target=[node_map[dst] for dst in top_connections["DSTIP"]],
                        value=top_connections["TOTDATA_MB"],
                    ),
                )
            ]
        )
        fig_sankey.update_layout(
            title_text="Top 10 IP Data Flows", font_size=10, template="plotly_dark"
        )

        top_connections["norm_data"] = (top_connections["TOTDATA_MB"] - top_connections["TOTDATA_MB"].min()) / (top_connections["TOTDATA_MB"].max() - top_connections["TOTDATA_MB"].min())
        colorscale = "jet"
        color_values = colors.sample_colorscale(colorscale, top_connections["norm_data"])
        fig_sankey_heatmap = go.Figure(
            data=[
                go.Sankey(
                    node=dict(
                        pad=15,
                        thickness=20,
                        line=dict(color="black", width=0.5),
                        label=all_nodes,
                        color="blue",
                    ),
                    link=dict(
                        source=[node_map[src] for src in top_connections["SRCIP"]],
                        target=[node_map[dst] for dst in top_connections["DSTIP"]],
                        value=top_connections["TOTDATA_MB"],
                        color=color_values,
                    ),
                )
            ]
        )
        fig_sankey_heatmap.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                marker=dict(
                    colorscale="jet",
                    cmin=top_connections["TOTDATA_MB"].min(),
                    cmax=top_connections["TOTDATA_MB"].max(),
                    colorbar=dict(
                        title="TOTDATA_MB",
                        titleside="right",
                        tickmode="array",
                        tickvals=[top_connections["TOTDATA_MB"].min(), top_connections["TOTDATA_MB"].max()],
                        ticktext=["Low", "High"],
                    ),
                ),
                hoverinfo="none",
            )
        )
        fig_sankey_heatmap.update_layout(
            title_text="Sankey Diagram with Heatmap",
            font_size=10,
            xaxis=dict(showgrid=False, zeroline=False, visible=False),
            yaxis=dict(showgrid=False, zeroline=False, visible=False),
            template="plotly_dark",
        )

        fig_protocol_pie = px.pie(
            df,
            names="PROTOCOL",
            title="Protocol Usage",
            hole=0.3,
            color_discrete_sequence=px.colors.sequential.RdBu,
            template="plotly_dark",
        )
        fig_protocol_pie.update_traces(textinfo="percent+label")

        top_10_connections = df.nlargest(10, "TOTPACKETS")
        fig_parallel = px.parallel_categories(
            top_10_connections,
            dimensions=["SRCIP", "DSTIP", "PROTOCOL"],
            color="TOTPACKETS",
            color_continuous_scale=px.colors.sequential.Jet,
            template="plotly_dark",
            labels={
                "SRCIP": "Source IP",
                "DSTIP": "Destination IP",
                "PROTOCOL": "Protocol",
                "TOTPACKETS": "Total Packets",
            },
            title="Top 10 Connections by Total Packets",
        )

        hourly_columns = required_hourly_columns
        protocol_agg = df.groupby("PROTOCOL", as_index=False)[hourly_columns].sum()
        protocol_agg_melted = protocol_agg.melt(id_vars=["PROTOCOL"], var_name="Hour", value_name="Total Packets")

        fig_stacked_area = px.area(
            protocol_agg_melted,
            x="Hour",
            y="Total Packets",
            color="PROTOCOL",
            title="Network Traffic by Protocol (Hourly)",
            template="plotly_dark",
        )
        fig_stacked_area.update_layout(
            xaxis_title="Hour",
            yaxis_title="Total Packets",
            legend_title="Protocol",
        )

        return (
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
        )
    except Exception as e:
        logger.error(f"Error creating visualizations: {e}")
        return (go.Figure(),) * 12
