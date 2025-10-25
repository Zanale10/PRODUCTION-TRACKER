import streamlit as st
import pandas as pd
import plotly.express as px

# ------------------- PAGE CONFIG -------------------
st.set_page_config(page_title="Production Output Tracker", layout="wide")

# ------------------- LOGO AND TITLE -------------------
col1, col2 = st.columns([0.2, 0.8])
with col1:
    st.image("logo.jpg", width=120)  # ✅ make sure your file is named 'logo.jpg' and in the same folder
with col2:
    st.title("📊 Production Output Tracker")

# ------------------- FILE UPLOAD -------------------
uploaded_file = st.file_uploader("📁 Upload Excel File", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name="POWERBI SUMMARY")

    # ------------------- DATA CLEANING -------------------
    df['EXPECTED'] = pd.to_numeric(df['EXPECTED'], errors='coerce')
    df['RECORDED'] = pd.to_numeric(df['RECORDED'], errors='coerce')
    df['EXPECTED WEIGHT'] = pd.to_numeric(df['EXPECTED WEIGHT'], errors='coerce')
    df['ACHIEVED TOTAL WEIGHT'] = pd.to_numeric(df['ACHIEVED TOTAL WEIGHT'], errors='coerce')
    df['TOTAL HOURS'] = pd.to_numeric(df['TOTAL HOURS'], errors='coerce')

    # Calculate performance vs expected
    df['PERFORMANCE (%)'] = (df['RECORDED'] / df['EXPECTED']) * 100

    # ------------------- FILTERS -------------------
    machine_list = df['MACHINE'].dropna().unique()
    selected_machine = st.sidebar.selectbox("Select Machine", machine_list)
    filtered_df = df[df['MACHINE'] == selected_machine]

    # ------------------- SIZE FILTER -------------------
    size_list = df['PIPE'].dropna().unique()
    selected_sizes = st.sidebar.multiselect("Select Sizes", size_list, default=size_list)
    filtered_df = filtered_df[filtered_df['PIPE'].isin(selected_sizes)]

    # ------------------- KPIs -------------------
    avg_expected = round(filtered_df['EXPECTED'].mean(), 2)
    avg_recorded = round(filtered_df['RECORDED'].mean(), 2)

    # ------------------- DISPLAY KPIs -------------------
    col1, col2, col3 = st.columns(3)
    col1.metric("Avg Expected Output", avg_expected)
    col2.metric("Avg Recorded Output", avg_recorded)
    col3.metric("✅ Performance (%)", f"{round((avg_recorded / avg_expected) * 100, 2)}%")

    # ------------------- SIZE-WISE OUTPUT CHART -------------------
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
        text='Output',  # ✅ Add data labels
        title=f"Size-wise Expected vs Recorded Output - Machine {selected_machine}",
        labels={'PIPE': 'Size', 'Output': 'Output'},
    )

    # Improve label visibility
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

    # ------------------- TABLE -------------------
    st.dataframe(filtered_df[['MACHINE', 'PIPE', 'EXPECTED', 'RECORDED', 'PERFORMANCE (%)']])
