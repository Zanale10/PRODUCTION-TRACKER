import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
import time
import os

# ------------------- PAGE CONFIG -------------------
st.set_page_config(page_title="Production Tracker", layout="wide")

# ------------------- AUTO REFRESH -------------------
st_autorefresh(interval=5 * 60 * 1000, key="refresh")  # refresh every 5 minutes

# ------------------- LOGO AND TITLE -------------------
col1, col2 = st.columns([0.2, 0.8])
with col1:
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", width=120)
with col2:
    st.title("Production Output Tracker")

# ------------------- SESSION STATE -------------------
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "upload_time" not in st.session_state:
    st.session_state.upload_time = 0.0

UPLOAD_PATH = "uploaded_data.xlsx"
EXPIRY_HOURS = 16

# ------------------- FILE UPLOAD -------------------
if st.session_state.uploaded_file is None:
    uploaded_file = st.file_uploader(" Upload Excel File", type=["xlsx"])
    if uploaded_file is not None:
        with open(UPLOAD_PATH, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.session_state.uploaded_file = UPLOAD_PATH
        st.session_state.upload_time = time.time()
        st.success(" File uploaded successfully! Dashboard will now load.")
        st.rerun()  # reload dashboard
    else:
        # No file uploaded yet, stop execution
        st.stop()

# ------------------- FILE EXPIRY CHECK -------------------
if os.path.exists(UPLOAD_PATH):
    upload_time = st.session_state.get("upload_time", os.path.getmtime(UPLOAD_PATH))
    upload_age = time.time() - upload_time

    if upload_age > EXPIRY_HOURS * 3600:
        st.warning(f" File expired (>{EXPIRY_HOURS} hours). Please upload a new file to continue.")
        st.session_state.uploaded_file = None
        st.stop()
    else:
        st.session_state.uploaded_file = UPLOAD_PATH
        st.session_state.upload_time = upload_time

# ------------------- READ DATA -------------------
try:
    try:
        df = pd.read_excel(st.session_state.uploaded_file, sheet_name="POWERBI SUMMARY")
    except ValueError:
        st.warning("Sheet 'POWERBI SUMMARY' not found; loading first sheet instead.")
        df = pd.read_excel(st.session_state.uploaded_file, sheet_name=0)
except Exception as e:
    st.error(f"Failed to read the uploaded Excel file: {e}")
    st.stop()

# ------------------- CLEANUP -------------------
numeric_columns = ['EXPECTED', 'RECORDED', 'EXPECTED WEIGHT', 'ACHIEVED TOTAL WEIGHT', 'TOTAL HOURS']
for col in numeric_columns:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

if 'EXPECTED' in df.columns and 'RECORDED' in df.columns:
    df['% CHANGE'] = df.apply(
        lambda r: ((r['RECORDED'] - r['EXPECTED']) / r['EXPECTED'] * 100)
        if pd.notnull(r['EXPECTED']) and r['EXPECTED'] != 0 else None,
        axis=1
    )

# ------------------- SIDEBAR FILTERS -------------------
if 'MONTH' in df.columns:
    month_list = sorted(df['MONTH'].dropna().unique())
    selected_months = st.sidebar.multiselect("🗓️ Select Month(s)", month_list, default=month_list)
    df = df[df['MONTH'].isin(selected_months)]

if 'MACHINE' in df.columns:
    machine_list = df['MACHINE'].dropna().unique()
    selected_machines = st.sidebar.multiselect(" Select Machine(s)", machine_list, default=machine_list)
    filtered_df = df[df['MACHINE'].isin(selected_machines)]
else:
    st.error("Column 'MACHINE' not found.")
    st.stop()

if 'PIPE' in df.columns:
    size_list = df['PIPE'].dropna().unique()
    selected_sizes = st.sidebar.multiselect(" Select Sizes", size_list, default=size_list)
    filtered_df = filtered_df[filtered_df['PIPE'].isin(selected_sizes)]
else:
    st.error("Column 'PIPE' not found.")
    st.stop()

# ------------------- KPIs -------------------
avg_expected = round(filtered_df['EXPECTED'].mean(), 2)
avg_recorded = round(filtered_df['RECORDED'].mean(), 2)
percent_change = round(((avg_recorded - avg_expected) / avg_expected) * 100, 2) if avg_expected != 0 else 0
total_expected_weight = round(filtered_df['EXPECTED WEIGHT'].sum(), 2) if 'EXPECTED WEIGHT' in filtered_df.columns else 0
total_achieved_weight = round(filtered_df['ACHIEVED TOTAL WEIGHT'].sum(), 2) if 'ACHIEVED TOTAL WEIGHT' in filtered_df.columns else 0

# ------------------- STYLED BOXED KPIs -------------------
kpi_style = """
<div style='
    background-color: #f0f2f6; 
    padding: 12px; 
    border-radius: 10px; 
    text-align: center; 
    font-size: 16px; 
    font-weight: bold;
    box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
'>
    <div style='font-size:12px;color:grey;'>{label}</div>
    <div style='font-size:20px;color:black;'>{value}</div>
</div>
"""

col1, col2, col3, col4, col5 = st.columns(5)
col1.markdown(kpi_style.format(label="Achieved Weight", value=total_achieved_weight), unsafe_allow_html=True)
col2.markdown(kpi_style.format(label="Expected Weight", value=total_expected_weight), unsafe_allow_html=True)
col3.markdown(kpi_style.format(label="Avg Expected Output", value=avg_expected), unsafe_allow_html=True)
col4.markdown(kpi_style.format(label="Avg Recorded Output", value=avg_recorded), unsafe_allow_html=True)
col5.markdown(kpi_style.format(label="% Change", value=f"{percent_change}%"), unsafe_allow_html=True)

# ------------------- BAR CHART -------------------
if len(selected_machines) == 1:
    chart_height = 500
    melted_df = filtered_df.melt(
        id_vars=['PIPE'],
        value_vars=['EXPECTED', 'RECORDED'],
        var_name='Type',
        value_name='Output'
    )
    fig = px.bar(
        melted_df,
        x='PIPE',
        y='Output',
        color='Type',
        barmode='group',
        text='Output',
        title=f"Size-wise Expected vs Recorded Output - Machine {selected_machines[0]}",
        labels={'PIPE': 'Size', 'Output': 'Output'},
        color_discrete_map={'EXPECTED': 'grey', 'RECORDED': 'orange'},
        height=chart_height
    )
    fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
    fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide', yaxis_title="Output", xaxis_title="Size", bargap=0.2, plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)
else:
    chart_height = 300
    machine_chunks = [selected_machines[i:i+2] for i in range(0, len(selected_machines), 2)]
    for chunk in machine_chunks:
        cols = st.columns(len(chunk))
        for i, machine in enumerate(chunk):
            machine_df = filtered_df[filtered_df['MACHINE'] == machine]
            melted_df = machine_df.melt(
                id_vars=['PIPE'],
                value_vars=['EXPECTED', 'RECORDED'],
                var_name='Type',
                value_name='Output'
            )
            fig = px.bar(
                melted_df,
                x='PIPE',
                y='Output',
                color='Type',
                barmode='group',
                text='Output',
                title=f"Machine {machine}",
                labels={'PIPE': 'Size', 'Output': 'Output'},
                color_discrete_map={'EXPECTED': 'grey', 'RECORDED': 'orange'},
                height=chart_height
            )
            fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
            fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide', yaxis_title="Output", xaxis_title="Size", bargap=0.2, plot_bgcolor='rgba(0,0,0,0)')
            cols[i].plotly_chart(fig, use_container_width=True)

# ------------------- DATA TABLE -------------------
with st.expander(" View Raw Data"):
    columns_to_show = [col for col in ['MONTH','MACHINE','PIPE','EXPECTED','RECORDED','EXPECTED WEIGHT','ACHIEVED TOTAL WEIGHT','% CHANGE'] if col in filtered_df.columns]
    st.dataframe(filtered_df[columns_to_show])

# ------------------- RESET BUTTON -------------------
if st.button("🔄 Upload a New File"):
    st.session_state.uploaded_file = None
    st.session_state.upload_time = 0.0
    st.success(" File reset. Please upload a new file to continue.")
    st.rerun()
