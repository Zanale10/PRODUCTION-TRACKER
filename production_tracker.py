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
    st.image("logo.jpg", width=120)
with col2:
    st.title("Production Output Tracker")

# ------------------- PASSWORD PROTECTION -------------------
password = st.sidebar.text_input("🔐 Enter Admin Password", type="password")

if password != "PRD2025":
    st.warning("View-only mode. Enter admin password to upload or modify data.")
    st.stop()

# ------------------- SESSION STATE -------------------
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None

# ------------------- FILE UPLOAD -------------------
if st.session_state.uploaded_file is None:
    uploaded_file = st.file_uploader("📁 Upload Excel File", type=["xlsx"])

    if uploaded_file is not None:
        st.session_state.uploaded_file = uploaded_file
        # Save locally for tracking and time display
        with open("uploaded_data.xlsx", "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.session_state.upload_time = time.time()  # Store upload timestamp
        st.success("✅ File uploaded successfully! Dashboard will now load.")
        st.rerun()
else:
    # ------------------- READ DATA -------------------
    df = pd.read_excel("uploaded_data.xlsx", sheet_name="POWERBI SUMMARY")

    # ------------------- LAST UPDATED -------------------
    file_path = "uploaded_data.xlsx"
    if os.path.exists(file_path):
        last_modified = os.path.getmtime(file_path)
        last_modified_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last_modified))

        # Calculate time difference
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

    df['PERFORMANCE (%)'] = (df['RECORDED'] / df['EXPECTED']) * 100

    # ------------------- SIDEBAR FILTERS -------------------
    # MONTH FILTER (now multi-select)
    if 'MONTH' in df.columns:
        month_list = sorted(df['MONTH'].dropna().unique())
        selected_months = st.sidebar.multiselect("🗓️ Select Month(s)", month_list, default=month_list)
        df = df[df['MONTH'].isin(selected_months)]

    # MACHINE FILTER
    machine_list = df['MACHINE'].dropna().unique()
    selected_machine = st.sidebar.selectbox("🧰 Select Machine", machine_list)
    filtered_df = df[df['MACHINE'] == selected_machine]

    # SIZE FILTER
    size_list = df['PIPE'].dropna().unique()
    selected_sizes = st.sidebar.multiselect("📏 Select Sizes", size_list, default=size_list)
    filtered_df = filtered_df[filtered_df['PIPE'].isin(selected_sizes)]

    # ------------------- KPIs -------------------
    avg_expected = round(filtered_df['EXPECTED'].mean(), 2)
    avg_recorded = round(filtered_df['RECORDED'].mean(), 2)
    performance = round((avg_recorded / avg_expected) * 100, 2) if avg_expected != 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Avg Expected Output", avg_expected)
    col2.metric("Avg Recorded Output", avg_recorded)
    col3.metric("✅ Performance (%)", f"{performance}%")

    # ------------------- BAR CHART -------------------
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
        title=f"Size-wise Expected vs Recorded Output - Machine {selected_machine}",
        labels={'PIPE': 'Size', 'Output': 'Output'},
        color_discrete_map={'EXPECTED': 'grey', 'RECORDED': 'orange'}
    )

    fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
    fig.update_layout(
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        yaxis_title="Output",
        xaxis_title="Size",
        bargap=0.2,
        plot_bgcolor='rgba(0,0,0,0)'
    )

    st.plotly_chart(fig, use_container_width=True)

    # ------------------- DATA TABLE -------------------
    with st.expander("🔍 View Raw Data"):
        columns_to_show = [col for col in ['MONTH', 'MACHINE', 'PIPE', 'EXPECTED', 'RECORDED', 'PERFORMANCE (%)'] if col in filtered_df.columns]
        st.dataframe(filtered_df[columns_to_show])

    # ------------------- RESET BUTTON -------------------
    if st.button("🔄 Upload a New File"):
        st.session_state.uploaded_file = None
        st.experimental_rerun()
