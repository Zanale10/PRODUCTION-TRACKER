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
        st.success("File uploaded successfully! Loading dashboard...")
        st.experimental_rerun()
    else:
        st.stop()

# ------------------- CHECK FILE EXISTENCE & EXPIRY -------------------
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

# ------------------- CLEAN COLUMN NAMES -------------------
df.columns = df.columns.str.strip()

# ------------------- CLEAN NUMERIC COLUMNS -------------------
numeric_cols = ['STANDARD OUTPUT(KG/HR)', 'EXPECTED OUTPUT(KG)', 
                'ACHIEVED TOTAL WEIGHT(KG)', 'TOTAL HOURS']
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# ------------------- CALCULATE RECORDED RATE & % CHANGE -------------------
df['RECORDED(KG/HR)'] = df.apply(
    lambda x: x['ACHIEVED TOTAL WEIGHT(KG)']/x['TOTAL HOURS'] if x['TOTAL HOURS'] != 0 else 0, axis=1
)
df['% CHANGE'] = ((df['ACHIEVED TOTAL WEIGHT(KG)'] - df['EXPECTED OUTPUT(KG)'])
                  / df['EXPECTED OUTPUT(KG)'].replace(0,1)) * 100  # prevent division by zero

# ------------------- EXTRACT YEAR, MONTH, WEEK -------------------
df['DATE'] = pd.to_datetime(df['DATE'])
df['YEAR'] = df['DATE'].dt.year
df['MONTH'] = df['DATE'].dt.month
df['WEEK'] = df['DATE'].dt.isocalendar().week

# ------------------- SIDEBAR FILTERS -------------------
selected_years = st.sidebar.multiselect("Year", sorted(df['YEAR'].unique()), default=sorted(df['YEAR'].unique()))
df = df[df['YEAR'].isin(selected_years)]

selected_months = st.sidebar.multiselect("Month", sorted(df['MONTH'].unique()), default=sorted(df['MONTH'].unique()))
df = df[df['MONTH'].isin(selected_months)]

selected_materials = st.sidebar.multiselect("Material", sorted(df['MATERIAL'].unique()), default=sorted(df['MATERIAL'].unique()))
df = df[df['MATERIAL'].isin(selected_materials)]

selected_machines = st.sidebar.multiselect("Machine", sorted(df['MACHINE'].unique()), default=sorted(df['MACHINE'].unique()))
df = df[df['MACHINE'].isin(selected_machines)]

selected_supervisors = st.sidebar.multiselect("Supervisor", sorted(df['SUPERVISOR'].unique()), default=sorted(df['SUPERVISOR'].unique()))
df = df[df['SUPERVISOR'].isin(selected_supervisors)]

selected_sizes = st.sidebar.multiselect("Pipe Size", sorted(df['PIPE size'].unique()), default=sorted(df['PIPE size'].unique()))
df = df[df['PIPE size'].isin(selected_sizes)]

# ------------------- HANDLE EMPTY FILTER RESULT -------------------
if df.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

# ------------------- KPIs -------------------
total_expected = df['EXPECTED OUTPUT(KG)'].sum()
total_achieved = df['ACHIEVED TOTAL WEIGHT(KG)'].sum()
avg_expected = df['EXPECTED OUTPUT(KG)'].mean()
avg_recorded = df['RECORDED(KG/HR)'].mean()
percent_change = ((total_achieved - total_expected) / total_expected) * 100 if total_expected != 0 else 0
change_color = "green" if -5 <= percent_change <= 5 else "red"

def kpi_box(label, value, color="black"):
    return f"""
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
        <div style='font-size:20px;color:{color};'>{value}</div>
    </div>
    """

col1, col2, col3, col4, col5 = st.columns(5)
col1.markdown(kpi_box("Achieved Weight", total_achieved), unsafe_allow_html=True)
col2.markdown(kpi_box("Expected Weight", total_expected), unsafe_allow_html=True)
col3.markdown(kpi_box("Avg Expected Output", round(avg_expected,2)), unsafe_allow_html=True)
col4.markdown(kpi_box("Avg Recorded Output", round(avg_recorded,2)), unsafe_allow_html=True)
col5.markdown(kpi_box("% Change", f"{round(percent_change,2)}%", color=change_color), unsafe_allow_html=True)

# ------------------- TREND ANALYSIS -------------------
st.subheader("Weekly Production Trend by Size")

weekly_df = df.groupby(['WEEK','PIPE size']).agg({
    'EXPECTED OUTPUT(KG)': 'sum',
    'ACHIEVED TOTAL WEIGHT(KG)': 'sum'
}).reset_index()

fig_trend = px.line(
    weekly_df,
    x='WEEK',
    y=['EXPECTED OUTPUT(KG)','ACHIEVED TOTAL WEIGHT(KG)'],
    color='PIPE size',
    markers=True,
    labels={'value':'Weight (KG)','variable':'Type'},
    title="Weekly Production Trend by Pipe Size"
)
st.plotly_chart(fig_trend, use_container_width=True)

# ------------------- RAW DATA -------------------
with st.expander("View Raw Data"):
    st.dataframe(df)

# ------------------- RESET BUTTON -------------------
if st.button("🔄 Upload a New File"):
    if os.path.exists(UPLOAD_PATH):
        os.remove(UPLOAD_PATH)
    st.success("File cleared. Please upload a new file.")
    st.stop()
