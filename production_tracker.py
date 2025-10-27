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

# ------------------- FILE SETTINGS -------------------
UPLOAD_PATH = "uploaded_data.xlsx"
EXPIRY_HOURS = 16

# ------------------- FILE UPLOAD -------------------
def upload_file():
    uploaded_file = st.file_uploader("📁 Upload Excel File", type=["xlsx"])
    if uploaded_file is not None:
        with open(UPLOAD_PATH, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success("✅ File uploaded successfully! Refresh the page to load the dashboard.")
        st.stop()
    else:
        st.stop()

# Check if file exists and age
if os.path.exists(UPLOAD_PATH):
    file_mtime = os.path.getmtime(UPLOAD_PATH)
    age_seconds = time.time() - file_mtime
    if age_seconds > EXPIRY_HOURS * 3600:
        st.warning(f"⚠️ File expired (>{EXPIRY_HOURS} hours). Please upload a new file.")
        upload_file()
else:
    upload_file()

# ------------------- READ DATA -------------------
try:
    try:
        df = pd.read_excel(UPLOAD_PATH, sheet_name="POWERBI SUMMARY")
    except ValueError:
        st.warning("Sheet 'POWERBI SUMMARY' not found; loading first sheet instead.")
        df = pd.read_excel(UPLOAD_PATH, sheet_name=0)
except Exception as e:
    st.error(f"Failed to read the Excel file: {e}")
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
    selected_machines =_
