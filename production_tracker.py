import streamlit as st
import pandas as pd
import plotly.express as px
import os
import time
from streamlit_autorefresh import st_autorefresh

# ------------------- PAGE CONFIG -------------------
st.set_page_config(page_title="Production Output Tracker", layout="wide")
st_autorefresh(interval=5 * 60 * 1000, key="refresh")  # refresh every 5 min

# ------------------- TITLE -------------------
st.title("Production Output Tracker")

# ------------------- FILE SETTINGS -------------------
UPLOAD_PATH = "uploaded_data.xlsx"
EXPIRY_HOURS = 16

# ------------------- FILE UPLOAD -------------------
def upload_file():
    uploaded_file = st.file_uploader("Upload Production Excel File", type=["xlsx"])
    if uploaded_file:
        with open(UPLOAD_PATH, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success("File uploaded successfully. Refreshing dashboard.")
        st.stop()
    st.stop()

# ------------------- FILE CHECK -------------------
if not os.path.exists(UPLOAD_PATH):
    upload_file()
else:
    age = time.time() - os.path.getmtime(UPLOAD_PATH)
    if age > EXPIRY_HOURS * 3600:
        st.warning("Uploaded file expired. Please upload a new one.")
        upload_file()

# ------------------- READ DATA -------------------
try:
    df = pd.read_excel(UPLOAD_PATH)
except Exception as e:
    st.error(f"Failed to read Excel file: {e}")
    st.stop()

# ------------------- STANDARDIZE COLUMN NAMES -------------------
df.columns = (
    df.columns
    .str.strip()
    .str.upper()
    .str.replace(" ", "_")
    .str.replace("/", "_")
    .str.replace("(", "", regex=False)
    .str.replace(")", "", regex=False)
    .str.replace("%", "PERCENT", regex=False)
)

# ------------------- REQUIRED COLUMNS CHECK -------------------
required_cols = [
    "DATE", "MACHINE", "MATERIAL", "PIPE",
    "EXPECTED_OUTPUTKG_HR",
    "EXPECTED_WEIGHTKG",
    "ACHIEVED_TOTAL_WEIGHTKG",
    "TOTAL_HOURS",
    "SUPERVISOR"
]

missing = [c for c in required_cols if c not in df.columns]
if missing:
    st.error(f"Missing required columns: {missing}")
    st.stop()

# ------------------- DATE HANDLING -------------------
df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")
df["YEAR"] = df["DATE"].dt.year
df["MONTH"] = df["DATE"].dt.month

# ------------------- NUMERIC CLEANING -------------------
numeric_cols = [
    "EXPECTED_OUTPUTKG_HR",
    "EXPECTED_WEIGHTKG",
    "ACHIEVED_TOTAL_WEIGHTKG",
    "TOTAL_HOURS"
]

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# ------------------- CALCULATED COLUMNS -------------------

# RECORDED OUTPUT (KG/HR)
df["RECORDED"] = (
    df["ACHIEVED_TOTAL_WEIGHTKG"]
    .div(df["TOTAL_HOURS"].replace(0, pd.NA))
    .fillna(0)
)

# % CHANGE
df["PERCENT_CHANGE"] = (
    (df["ACHIEVED_TOTAL_WEIGHTKG"] - df["EXPECTED_WEIGHTKG"])
    .div(df["EXPECTED_WEIGHTKG"].replace(0, pd.NA))
    * 100
).fillna(0)

# ------------------- SIDEBAR FILTERS -------------------
st.sidebar.header("Filters")

# Year
years = sorted(df["YEAR"].dropna().unique())
selected_years = st.sidebar.multiselect("Year", years, default=years)
df = df[df["YEAR"].isin(selected_years)]

# Material
materials = sorted(df["MATERIAL"].unique())
selected_materials = st.sidebar.multiselect("Material", materials, default=materials)
df = df[df["MATERIAL"].isin(selected_materials)]

# Machine
machines = sorted(df["MACHINE"].unique())
selected_machines = st.sidebar.multiselect("Machine", machines, default=machines)
df = df[df["MACHINE"].isin(selected_machines)]

# Pipe
pipes = sorted(df["PIPE"].unique())
selected_pipes = st.sidebar.multiselect("Pipe Size", pipes, default=pipes)
df = df[df["PIPE"].isin(selected_pipes)]

# ------------------- KPIs -------------------
total_expected_weight = round(df["EXPECTED_WEIGHTKG"].sum(), 2)
total_achieved_weight = round(df["ACHIEVED_TOTAL_WEIGHTKG"].sum(), 2)
avg_expected_output = round(df["EXPECTED_OUTPUTKG_HR"].mean(), 2)
avg_recorded_output = round(df["RECORDED"].mean(), 2)

percent_change = (
    round(((total_achieved_weight - total_expected_weight) /
           total_expected_weight) * 100, 2)
    if total_expected_weight != 0 else 0
)

color = "green" if -5 <= percent_change <= 5 else "red"

def kpi(label, value, color="black"):
    return f"""
    <div style="background:#f0f2f6;padding:12px;border-radius:10px;text-align:center">
        <div style="font-size:12px;color:grey">{label}</div>
        <div style="font-size:20px;color:{color};font-weight:bold">{value}</div>
    </div>
    """

c1, c2, c3, c4, c5 = st.columns(5)
c1.markdown(kpi("Achieved Weight (KG)", total_achieved_weight), unsafe_allow_html=True)
c2.markdown(kpi("Expected Weight (KG)", total_expected_weight), unsafe_allow_html=True)
c3.markdown(kpi("Avg Expected Output", avg_expected_output), unsafe_allow_html=True)
c4.markdown(kpi("Avg Recorded Output", avg_recorded_output), unsafe_allow_html=True)
c5.markdown(kpi("% Change", f"{percent_change}%", color), unsafe_allow_html=True)

# ------------------- BAR CHART -------------------
fig = px.bar(
    df,
    y="PIPE",
    x=["EXPECTED_OUTPUTKG_HR", "RECORDED"],
    barmode="group",
    orientation="h",
    title="Expected vs Recorded Output by Pipe Size"
)
st.plotly_chart(fig, use_container_width=True)

# ------------------- RAW DATA -------------------
with st.expander("View Raw Data"):
    st.dataframe(df[
        ["DATE", "MACHINE", "MATERIAL", "PIPE",
         "EXPECTED_OUTPUTKG_HR", "EXPECTED_WEIGHTKG",
         "ACHIEVED_TOTAL_WEIGHTKG", "TOTAL_HOURS",
         "RECORDED", "PERCENT_CHANGE", "SUPERVISOR"]
    ])

# ------------------- RESET BUTTON -------------------
if st.button("🔄 Upload a New File"):
    if os.path.exists(UPLOAD_PATH):
        os.remove(UPLOAD_PATH)
    st.success("File cleared. Please upload a new file.")
    st.stop()
