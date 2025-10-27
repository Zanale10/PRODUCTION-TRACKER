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

# ------------------- RESTORE PREVIOUS FILE -------------------
if st.session_state.uploaded_file is None and os.path.exists(UPLOAD_PATH):
    st.session_state.uploaded_file = UPLOAD_PATH
    if st.session_state.upload_time == 0:
        st.session_state.upload_time = os.path.getmtime(UPLOAD_PATH)

# ------------------- FILE UPLOAD -------------------
if st.session_state.uploaded_file is None:
    uploaded_file = st.file_uploader("📁 Upload Excel File", type=["xlsx"])
    if uploaded_file is not None:
        with open(UPLOAD_PATH, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.session_state.uploaded_file = UPLOAD_PATH
        st.session_state.upload_time = time.time()
        st.success("✅ File uploaded successfully! Dashboard will now load.")
        st.rerun()

else:
    # ------------------- FILE EXPIRY CHECK -------------------
    upload_time = st.session_state.get("upload_time", 0) or (os.path.getmtime(UPLOAD_PATH) if os.path.exists(UPLOAD_PATH) else 0)
    upload_age = time.time() - upload_time
    if upload_age > EXPIRY_HOURS * 3600:
        st.error(f"⚠️ File access expired ({EXPIRY_HOURS}-hour limit reached). Please re-upload a new file.")
        st.session_state.uploaded_file = None
        st.stop()
    else:
        remaining_hours = round((EXPIRY_HOURS * 3600 - upload_age) / 3600, 1)
        st.info(f"🕓 File valid for approximately {remaining_hours} more hour(s).")

    # ------------------- READ DATA -------------------
    try:
        try:
            df = pd.read_excel(UPLOAD_PATH, sheet_name="POWERBI SUMMARY")
        except ValueError:
            st.warning("Sheet 'POWERBI SUMMARY' not found; loading first sheet instead.")
            df = pd.read_excel(UPLOAD_PATH, sheet_name=0)
    except Exception as e:
        st.error(f"Failed to read the uploaded Excel file: {e}")
        st.stop()

    # ------------------- LAST UPDATED -------------------
    if os.path.exists(UPLOAD_PATH):
        last_modified = os.path.getmtime(UPLOAD_PATH)
        last_modified_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last_modified))
        time_diff = time.time() - last_modified
        hours_ago = int(time_diff // 3600)
        minutes_ago = int((time_diff % 3600) // 60)
        if hours_ago > 0:
            ago_text = f"{hours_ago} hour{'s' if hours_ago > 1 else ''} ago"
        elif minutes_ago > 0:
            ago_text = f"{minutes_ago} minute{'s' if minutes_ago > 1 else ''} ago"
        else:
            ago_text = "just now"
        st.caption(f"🕒 Last updated: {last_modified_time} ({ago_text})")

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
        machine_list = sorted(df['MACHINE'].dropna().unique())
        selected_machines = st.sidebar.multiselect("🧰 Select Machine(s)", machine_list, default=machine_list)
        filtered_df = df[df['MACHINE'].isin(selected_machines)]
    else:
        st.error("Column 'MACHINE' not found.")
        st.stop()

    if 'PIPE' in df.columns:
        size_list = sorted(df['PIPE'].dropna().unique())
        selected_sizes = st.sidebar.multiselect("📏 Select Sizes", size_list, default=size_list)
        filtered_df = filtered_df[filtered_df['PIPE'].isin(selected_sizes)]
    else:
        st.error("Column 'PIPE' not found.")
        st.stop()

    # ------------------- KPIs -------------------
    avg_expected = round(filtered_df['EXPECTED'].mean(), 2)
    avg_recorded = round(filtered_df['RECORDED'].mean(), 2)
    avg_expected_wt = round(filtered_df['EXPECTED WEIGHT'].mean(), 2) if 'EXPECTED WEIGHT' in filtered_df.columns else 0
    avg_achieved_wt = round(filtered_df['ACHIEVED TOTAL WEIGHT'].mean(), 2) if 'ACHIEVED TOTAL WEIGHT' in filtered_df.columns else 0
    ach_percent = round((avg_achieved_wt / avg_expected_wt * 100), 2) if avg_expected_wt != 0 else 0
    percent_change = round(((avg_recorded - avg_expected) / avg_expected) * 100, 2) if avg_expected != 0 else 0

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    kpi1.metric("Avg Expected Output", avg_expected)
    kpi2.metric("Avg Recorded Output", avg_recorded)
    kpi3.metric("Expected Weight", avg_expected_wt)
    kpi4.metric("Achieved Weight", avg_achieved_wt)
    kpi5.metric("🎯 Achievement %", f"{ach_percent}%")

    # ------------------- BAR CHART -------------------
    melted_df = filtered_df.melt(
        id_vars=['PIPE', 'MACHINE'],
        value_vars=['EXPECTED', 'RECORDED'],
        var_name='Type',
        value_name='Output'
    )

    fig = px.bar(
        melted_df,
        x='PIPE',
        y='Output',
        color='MACHINE',
        barmode='group',
        facet_col='Type',
        title="📊 Size-wise Output Across Machines",
        labels={'PIPE': 'Size', 'Output': 'Output'},
    )

    fig.update_traces(texttemplate='%{y:.0f}', textposition='outside')
    fig.update_layout(
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        yaxis_title="Output",
        bargap=0.15,
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig, use_container_width=True)

    # ------------------- DATA TABLE -------------------
    with st.expander("🔍 View Raw Data"):
        columns_to_show = [col for col in ['MONTH', 'MACHINE', 'PIPE', 'EXPECTED', 'RECORDED', 'EXPECTED WEIGHT', 'ACHIEVED TOTAL WEIGHT', '% CHANGE'] if col in filtered_df.columns]
        st.dataframe(filtered_df[columns_to_show])

    # ------------------- RESET BUTTON -------------------
    if st.button("🔄 Upload a New File"):
        st.session_state.uploaded_file = None
        st.session_state.upload_time = 0.0
        st.experimental_rerun()
