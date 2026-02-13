import streamlit as st
import pandas as pd
import plotly.express as px
import os
import time
from streamlit_autorefresh import st_autorefresh

# ------------------- PAGE CONFIG -------------------
st.set_page_config(page_title="Production Output Tracker", layout="wide")
st_autorefresh(interval=5 * 60 * 1000, key="refresh")

st.title("Production Output Tracker")

# ------------------- FILE SETTINGS -------------------
UPLOAD_PATH = "uploaded_data.xlsx"
EXPIRY_HOURS = 16

# ------------------- FILE UPLOAD -------------------
def upload_file():
    uploaded = st.file_uploader("Upload Production Excel File", type=["xlsx"])
    if uploaded:
        with open(UPLOAD_PATH, "wb") as f:
            f.write(uploaded.getbuffer())
        st.success("File uploaded. Reloading…")
        st.stop()
    st.stop()

# ------------------- FILE CHECK -------------------
if not os.path.exists(UPLOAD_PATH):
    upload_file()
elif time.time() - os.path.getmtime(UPLOAD_PATH) > EXPIRY_HOURS * 3600:
    st.warning("File expired. Upload a new one.")
    upload_file()

# ------------------- READ DATA -------------------
df = pd.read_excel(UPLOAD_PATH)

# ------------------- COLUMN MAPPING (CRITICAL FIX) -------------------
column_map = {
    "DATE": "DATE",
    "MACHINE": "MACHINE",
    "MATERIAL": "MATERIAL",
    "PIPE": "PIPE",
    "EXPECTED OUTPUT(KG/HR)": "EXPECTED_OUTPUT",
    "EXPECTED WEIGHT(KG)": "EXPECTED_WEIGHT",
    "ACHIEVED TOTAL WEIGHT(KG)": "ACHIEVED_WEIGHT",
    "TOTAL HOURS": "TOTAL_HOURS",
    "RECORDED": "RECORDED",
    "% CHANGE": "PERCENT_CHANGE",
    "SUPERVISOR": "SUPERVISOR"
}

# Strip Excel headers
df.columns = df.columns.str.strip()

# Rename only known columns
df = df.rename(columns=column_map)

# ------------------- REQUIRED COLUMNS CHECK -------------------
required_cols = [
    "DATE", "MACHINE", "MATERIAL", "PIPE",
    "EXPECTED_OUTPUT", "EXPECTED_WEIGHT",
    "ACHIEVED_WEIGHT", "TOTAL_HOURS", "SUPERVISOR"
]

missing = [c for c in required_cols if c not in df.columns]
if missing:
    st.error(f"Missing required columns: {missing}")
    st.stop()

# ------------------- DATA CLEANING -------------------
df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")

numeric_cols = [
    "EXPECTED_OUTPUT",
    "EXPECTED_WEIGHT",
    "ACHIEVED_WEIGHT",
    "TOTAL_HOURS"
]

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# ------------------- CALCULATED FIELDS -------------------
df["RECORDED"] = df["ACHIEVED_WEIGHT"].div(
    df["TOTAL_HOURS"].replace(0, pd.NA)
).fillna(0)

df["PERCENT_CHANGE"] = (
    (df["ACHIEVED_WEIGHT"] - df["EXPECTED_WEIGHT"])
    / df["EXPECTED_WEIGHT"].replace(0, pd.NA) * 100
).fillna(0)

df["YEAR"] = df["DATE"].dt.year
df["MONTH"] = df["DATE"].dt.month

# ------------------- SIDEBAR FILTERS -------------------
st.sidebar.header("Filters")

years = sorted(df["YEAR"].dropna().unique())
df = df[df["YEAR"].isin(st.sidebar.multiselect("Year", years, years))]

materials = sorted(df["MATERIAL"].unique())
df = df[df["MATERIAL"].isin(st.sidebar.multiselect("Material", materials, materials))]

machines = sorted(df["MACHINE"].unique())
df = df[df["MACHINE"].isin(st.sidebar.multiselect("Machine", machines, machines))]

pipes = sorted(df["PIPE"].unique())
df = df[df["PIPE"].isin(st.sidebar.multiselect("Pipe", pipes, pipes))]

# ------------------- KPIs -------------------
total_expected = df["EXPECTED_WEIGHT"].sum()
total_achieved = df["ACHIEVED_WEIGHT"].sum()

avg_expected = df["EXPECTED_OUTPUT"].mean()
avg_recorded = df["RECORDED"].mean()

percent_change = ((total_achieved - total_expected) / total_expected * 100) if total_expected else 0
color = "green" if -5 <= percent_change <= 5 else "red"

def kpi(label, value, color="black"):
    return f"""
    <div style="background:#f0f2f6;padding:12px;border-radius:10px;text-align:center">
        <div style="font-size:12px;color:grey">{label}</div>
        <div style="font-size:20px;color:{color};font-weight:bold">{value:.2f}</div>
    </div>
    """

c1, c2, c3, c4, c5 = st.columns(5)
c1.markdown(kpi("Achieved Weight", total_achieved), unsafe_allow_html=True)
c2.markdown(kpi("Expected Weight", total_expected), unsafe_allow_html=True)
c3.markdown(kpi("Avg Expected Output", avg_expected), unsafe_allow_html=True)
c4.markdown(kpi("Avg Recorded Output", avg_recorded), unsafe_allow_html=True)
c5.markdown(kpi("% Change", percent_change, color), unsafe_allow_html=True)

# ------------------- CHART -------------------
fig = px.bar(
    df,
    y="PIPE",
    x=["EXPECTED_OUTPUT", "RECORDED"],
    orientation="h",
    barmode="group",
    title="Expected vs Recorded Output"
)
st.plotly_chart(fig, use_container_width=True)

# ------------------- RAW DATA -------------------
with st.expander("View Raw Data"):
    st.dataframe(df)

# ------------------- RESET BUTTON -------------------
if st.button("🔄 Upload a New File"):
    if os.path.exists(UPLOAD_PATH):
        os.remove(UPLOAD_PATH)
    st.success("File cleared. Please upload a new file.")
    st.stop()
