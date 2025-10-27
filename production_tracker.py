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
        with open("uploaded_data.xlsx", "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.session_state.upload_time = time.time()  # Store upload timestamp
        st.success("✅ File uploaded successfully! Dashboard will now load.")
        st.rerun()
else:
    # ------------------- FILE EXPIRY CHECK (16 HOURS) -------------------
    upload_age = time.time() - st.session_state.get("upload_time", 0)
    if upload_age > 16 * 3600:
        st.error("⚠️ File access expired (16-hour limit reached). Please re-upload a new file.")
        st.session_state.uploaded_file = None
        st.stop()
    else:
        remaining_hours = round((16 * 3600 - upload_age) / 3600, 1)
        st.info(f"🕓 File valid for approximately {remaining_hours} more hour(s).")

    # ------------------- READ DATA -------------------
    df = pd.read_excel("uploaded_data.xlsx", sheet_name="POWERBI SUMMARY")

    # ------------------- LAST UPDATED -------------------
    file_path = "uploaded_data.xlsx"
    if os.path.exists(file_path):
        last_modified = os.path.getmtime(file_path)
        last_modified_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last_modified))

        time_diff = time.time() - last_modified
        hours_ago = int(time_diff // 3600)
        minutes_ago = int((time_diff % 3600) // 60)
        if hours_ago > 0:
            ago_text = f"{hours_ago} hour{'s' if hours_ago > 1 else ''} ago"
        elif minutes_ago > 0:
            ago_text = f"{minutes_ago} minute{'s' if minutes_ago_
