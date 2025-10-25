import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# ------------------- PAGE CONFIG -------------------
st.set_page_config(page_title="Production Tracker", layout="wide")

# ------------------- AUTO REFRESH -------------------
st_autorefresh(interval=5 * 60 * 1000, key="refresh")  # refresh every 5 minutes

# ------------------- LOGO AND TITLE -------------------
col1, col2 = st.columns([0.2, 0.8])
with col1:
    st.image("logo.jpg", width=120)  # ✅ ensure 'logo.jpg' is in the same folder
with col2:
    st.title("📊 Production Output Tracker")

# ------------------- PASSWORD PROTECTION -------------------
password = st.sidebar.text_input("🔐 Enter Admin Password", type="password")

if password != "mysecret":
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
        st.success("✅ File uploaded successfully! Dashboard will now load.")
        st.rerun()
else:
    # ------------------- READ DATA -------------------
    df = pd.read_excel(st.session_state.uploaded_file, sheet_name="POWERBI SUMMARY")

    # ------------------- CLEANUP -------------------
    df['EXPECTED'] = pd.to_numeric(df['EXPECTED'], errors='coerce')
    df['RECORDED'] = pd.to_numeric(df['RECORDED'], errors='coerce')
    df['EXPECTED WEIGHT'] = pd.to_numeric(df['EXPECTED WEIGHT'], errors='coerce')
    df['ACHIEVED TOTAL WEIGHT'] = pd.to_numeric(df['ACHIEVED TOTAL WEIGHT'], errors='coerce')
    df['TOTAL HOURS'] = pd.to_numeric(df['TOTAL HOURS'], errors='coerce')

    df['PERFORMANCE (%)'] = (df['RECORDED'] / df['EXPECTED']) * 100

    # ------------------- SIDEBAR FILTERS -------------------
    machine_list = df['MACHINE'].dropna().unique()
    selected_machine = st.sidebar.selectbox("🧰 Select Machine", machine_list)
    filtered_df = df[df['MACHINE'] == selected_machine]

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
        color_discrete_sequence=px.colors.qualitative.Set2,
        text='Output',
        title=f"Size-wise Expected vs Recorded Output - Machine {selected_machine}",
        labels={'PIPE': 'Size', 'Output': 'Output'},
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
        st.dataframe(filtered_df[['MACHINE', 'PIPE', 'EXPECTED', 'RECORDED', 'PERFORMANCE (%)']])

    # ------------------- RESET BUTTON -------------------
    if st.button("🔄 Upload a New File"):
        st.session_state.uploaded_file = None
        st.experimental_rerun()
