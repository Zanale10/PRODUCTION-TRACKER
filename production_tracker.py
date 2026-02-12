import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
import time
import os

# ------------------- PAGE CONFIG -------------------
st.set_page_config(page_title="Production Tracker", layout="wide")
st_autorefresh(interval=5 * 60 * 1000, key="refresh")  # auto-refresh every 5 min

# ------------------- LOGO AND TITLE -------------------
col1, col2 = st.columns([0.2, 0.8])
with col1:
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", width=120)
with col2:
    st.title("Production Output Tracker")

# ------------------- FILE SETTINGS -------------------
UPLOAD_PATH = "uploaded_data.xlsx"
EXPIRY_HOURS = 16

# ------------------- FILE UPLOAD FUNCTION -------------------
def upload_file():
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
    if uploaded_file is not None:
        with open(UPLOAD_PATH, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success("File uploaded successfully!")
        st.experimental_rerun()
    else:
        st.stop()

# ------------------- FILE CHECK -------------------
if os.path.exists(UPLOAD_PATH):
    file_mtime = os.path.getmtime(UPLOAD_PATH)
    age_seconds = time.time() - file_mtime
    if age_seconds > EXPIRY_HOURS * 3600:
        st.warning(f"File expired (>{EXPIRY_HOURS} hours). Please upload a new file.")
        upload_file()
else:
    upload_file()

# ------------------- READ DATA -------------------
try:
    try:
        df = pd.read_excel(UPLOAD_PATH, sheet_name="POWERBI SUMMARY")
    except:
        df = pd.read_excel(UPLOAD_PATH)
except Exception as e:
    st.error(f"Failed to read file: {e}")
    st.stop()

# ------------------- CLEAN NUMERIC COLUMNS -------------------
numeric_columns = ['EXPECTED', 'RECORDED', 'EXPECTED WEIGHT', 
                   'ACHIEVED TOTAL WEIGHT', 'TOTAL HOURS']

for col in numeric_columns:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

# ------------------- CALCULATE % CHANGE -------------------
if 'EXPECTED WEIGHT' in df.columns and 'ACHIEVED TOTAL WEIGHT' in df.columns:
    df['% CHANGE'] = ((df['ACHIEVED TOTAL WEIGHT'] - df['EXPECTED WEIGHT']) 
                      / df['EXPECTED WEIGHT']) * 100

# ------------------- SIDEBAR FILTERS -------------------

# MONTH
if 'MONTH' in df.columns:
    month_list = sorted(df['MONTH'].dropna().unique())
    selected_months = st.sidebar.multiselect(
        "Select Month(s)", month_list, default=month_list)
    df = df[df['MONTH'].isin(selected_months)]

# MATERIAL (NEW: predefined list)
material_list = ['HDPE', 'PPR', 'PP']
if 'MATERIAL' in df.columns:
    selected_materials = st.sidebar.multiselect(
        "Select Material(s)", material_list, default=material_list)
    df = df[df['MATERIAL'].isin(selected_materials)]

# MACHINE
if 'MACHINE' in df.columns:
    machine_list = df['MACHINE'].dropna().unique()
    selected_machines = st.sidebar.multiselect(
        "Select Machine(s)", machine_list, default=machine_list)
    filtered_df = df[df['MACHINE'].isin(selected_machines)]
else:
    st.error("MACHINE column missing")
    st.stop()

# PIPE
if 'PIPE' in filtered_df.columns:
    size_list = filtered_df['PIPE'].dropna().unique()
    selected_sizes = st.sidebar.multiselect(
        "Select Sizes", size_list, default=size_list)
    filtered_df = filtered_df[filtered_df['PIPE'].isin(selected_sizes)]
else:
    st.error("PIPE column missing")
    st.stop()

# ------------------- KPIs -------------------
avg_expected = round(filtered_df['EXPECTED'].mean(), 2) if 'EXPECTED' in filtered_df.columns else 0
avg_recorded = round(filtered_df['RECORDED'].mean(), 2) if 'RECORDED' in filtered_df.columns else 0

total_expected_weight = round(filtered_df['EXPECTED WEIGHT'].sum(), 2) if 'EXPECTED WEIGHT' in filtered_df.columns else 0
total_achieved_weight = round(filtered_df['ACHIEVED TOTAL WEIGHT'].sum(), 2) if 'ACHIEVED TOTAL WEIGHT' in filtered_df.columns else 0

# Calculate percent change based on total weights
percent_change = round(((total_achieved_weight - total_expected_weight) / total_expected_weight) * 100, 2) if total_expected_weight != 0 else 0

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

# ------------------- BAR CHARTS -------------------
if len(selected_machines) == 1:
    # Single machine = large horizontal bar chart
    chart_height = 500
    melted_df = filtered_df.melt(
        id_vars=['PIPE'],
        value_vars=['EXPECTED', 'RECORDED'],
        var_name='Type',
        value_name='Output'
    )
    fig = px.bar(
        melted_df,
        y='PIPE',  # horizontal
        x='Output',
        color='Type',
        barmode='group',
        text='Output',
        orientation='h',
        title=f"Size-wise Expected vs Recorded Output - Machine {selected_machines[0]}",
        labels={'PIPE': 'Size', 'Output': 'Output'},
        color_discrete_map={'EXPECTED': 'grey', 'RECORDED': 'orange'},
        height=chart_height
    )
    fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
    fig.update_layout(
        uniformtext_minsize=8,
        uniformtext_mode='show',
        xaxis_title="Output",
        yaxis_title="Size",
        bargap=0.3,
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis={'categoryorder':'total ascending'}
    )
    st.plotly_chart(fig, use_container_width=True)

else:
    # Multiple machines = smaller horizontal bar charts in 2x2 layout
    chart_height = 350
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
                y='PIPE',
                x='Output',
                color='Type',
                barmode='group',
                text='Output',
                orientation='h',
                title=f"Machine {machine}",
                labels={'PIPE': 'Size', 'Output': 'Output'},
                color_discrete_map={'EXPECTED': 'grey', 'RECORDED': 'orange'},
                height=chart_height
            )
            fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
            fig.update_layout(
                uniformtext_minsize=8,
                uniformtext_mode='show',
                xaxis_title="Output",
                yaxis_title="Size",
                bargap=0.3,
                plot_bgcolor='rgba(0,0,0,0)',
                yaxis={'categoryorder':'total ascending'}
            )
            cols[i].plotly_chart(fig, use_container_width=True)

# ------------------- RAW DATA -------------------
with st.expander("View Raw Data"):
    columns_to_show = [col for col in [
        'MONTH','MATERIAL','MACHINE','PIPE',
        'EXPECTED','RECORDED',
        'EXPECTED WEIGHT','ACHIEVED TOTAL WEIGHT',
        '% CHANGE'
    ] if col in filtered_df.columns]

    st.dataframe(filtered_df[columns_to_show])

# ------------------- RESET BUTTON -------------------
if st.button("🔄 Upload a New File"):
    if os.path.exists(UPLOAD_PATH):
        os.remove(UPLOAD_PATH)
    st.success("File cleared. Please upload a new file.")
    st.stop()
