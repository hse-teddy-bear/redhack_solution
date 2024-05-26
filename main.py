import streamlit as st
import datetime
from datetime import timedelta
import pandas as pd
import numpy as np

import plotly
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots

st.set_page_config(
    layout="wide",
)

# Вводим все для sidebar
st.sidebar.subheader("Set up the parameters")
datemin = st.sidebar.text_input(label="Choose datemin", value="2024-05-14 0:0:0")
datemax = st.sidebar.text_input(label="Choose datemax", value="2024-05-14 23:59:59")

perc_lvl_wre=st.sidebar.slider(label="Choose perc_lvl_wre", min_value=90.0, max_value=100.0, value=96.0, step=0.5)
perc_lvl_thr=st.sidebar.slider(label="Choose perc_lvl_thr", min_value=90.0, max_value=100.0, value=96.0, step=0.5)

perc_lvl_apdex=st.sidebar.slider(label="Choose perc_lvl_apdex", min_value=95.0, max_value=100.0, value=99.0, step=0.1)
perc_lvl_error=st.sidebar.slider(label="Choose perc_lvl_error", min_value=95.0, max_value=100.0, value=99.0, step=0.1)

minutes_range=st.sidebar.slider(label="Choose minutes_range", min_value=5, max_value=25, value=20, step=1)

minutes_safe_delta=st.sidebar.slider(label="Choose minutes_safe_delta", min_value=0, max_value=5, value=2, step=1)


def find_clusters(anomalies:pd.DataFrame, minutes_range:int, minutes_safe_delta=1) -> list:
    # Initialize variables
    clusters = []
    current_cluster = []
    cluster_start_time = anomalies.iloc[0]['point']

    # Iterate through rows
    for idx, row in anomalies.iterrows():
        if row['point'] <= cluster_start_time + timedelta(minutes=minutes_range):
            current_cluster.append(row)
        else:
            clusters.append(current_cluster)
            current_cluster = [row]
            cluster_start_time = row['point']

    # Append the last cluster
    if current_cluster:
        clusters.append(current_cluster)

    # Find minimum and maximum for each cluster
    min_max_list = []
    for cluster in clusters:
        cluster_df = pd.DataFrame(cluster)
        min_point = cluster_df['point'].min() - timedelta(minutes=minutes_safe_delta)
        max_point = cluster_df['point'].max() + timedelta(minutes=minutes_safe_delta)
        min_max_list.append([min_point, max_point])

    return min_max_list

#load data
ts_tsr = pd.read_csv('result_dataframe.csv')
ts_tsr['point'] = pd.to_datetime(ts_tsr['point'])

#selecting data
dfplot = ts_tsr.loc[(ts_tsr.point >= datemin) & (ts_tsr.point <= datemax)] #data

#displaying graphs
fig = plotly.tools.make_subplots(rows=4, cols=1,
                                 subplot_titles=("Graph for apdex", "Graph for error", "Graph for web_response", "Graph for throughput"))

for i, metric in enumerate(['web_response', 'throughput', 'apdex', 'error']):
    if metric == 'apdex':
        user_perc = perc_lvl_apdex
    elif metric == 'error':
        user_perc = perc_lvl_error
    elif metric == 'web_response':
        user_perc = perc_lvl_wre
    elif metric == 'throughput':
        user_perc = perc_lvl_thr
    
    anomalies = dfplot[dfplot[f'diff_{metric}'] >= np.percentile(dfplot[f'diff_{metric}'], user_perc)]
    anomalies.reset_index(drop=True, inplace=True)
    datetimes_list = find_clusters(anomalies=anomalies, minutes_range=minutes_range, minutes_safe_delta=minutes_safe_delta)

    fig.add_trace(go.Scatter(x=dfplot['point'], y=dfplot[metric], name=metric, legendgroup = str(i)), i + 1, 1)
    fig.add_trace(go.Scatter(x=anomalies['point'], y=anomalies[metric], mode='markers', fillcolor='red', name='Anomalies', legendgroup = str(i)), i + 1, 1)
    for tuple in datetimes_list:
        fig.add_vrect(tuple[0], tuple[1], fillcolor="red", opacity=0.5, line_width=0, row=i+1, col=1, legendgroup = str(i))
    fig.update_yaxes(title='metric value', col=1, row=i+1)

fig.update_xaxes(title='timestamp', col=1, row=i+1)
fig.update_layout(legend_orientation="h",
                      title='Anomaly detection graphs',
                      legend=dict(font=dict(size=10), orientation='h',
                                x=0.5, xanchor='center',
                                y=-0.2, yanchor='top',
                                bgcolor='rgba(0,0,0,0)'),
                      margin=dict(b=100),
                      hovermode="x",
                      width=1200,
                      height=800,
                      legend_tracegroupgap = 180)

custom_css = """
<style>
    .main .block-container {
        padding-top: 1rem;
        padding-right: 1rem;
        padding-left: 1rem;
        padding-bottom: 1rem;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)
st.plotly_chart(fig, theme="streamlit", use_container_width=True)