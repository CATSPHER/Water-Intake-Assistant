"""
Standalone Streamlit UI for the hydration tracker.

This is for local testing / demoing the FastAPI service before it's wired
into your MERN app's React frontend. In production, your React app will
call the same FastAPI endpoints directly — this Streamlit app is not
meant to be embedded in the MERN app.

The "User ID" field below simulates the logged-in user's ID that your
Node backend would normally pass in after verifying the JWT.
"""
import os
import requests
import pandas as pd
import streamlit as st

API_BASE = st.secrets.get("API_BASE_URL", os.getenv("API_BASE_URL", "http://localhost:8000"))

st.set_page_config(page_title="Hydration Tracker", page_icon="💧", layout="centered")
st.title("💧 Hydration Tracker")

# --- Simulated login ---
with st.sidebar:
    st.header("User")
    user_id = st.text_input("User ID", value="demo-user-1")
    daily_goal_ml = st.number_input("Daily goal (ml)", min_value=500, max_value=6000, value=2500, step=100)

if not user_id:
    st.warning("Enter a User ID in the sidebar to continue.")
    st.stop()

# --- Log intake ---
st.subheader("Log water intake")
col1, col2 = st.columns([3, 1])
with col1:
    amount = st.number_input("Amount (ml)", min_value=50, max_value=2000, value=250, step=50)
with col2:
    st.write("")
    st.write("")
    if st.button("Log it", use_container_width=True):
        resp = requests.post(f"{API_BASE}/api/hydration/log", json={"user_id": user_id, "amount_ml": int(amount)})
        if resp.ok:
            st.success(f"Logged {amount}ml!")
            st.rerun()
        else:
            st.error(f"Failed to log: {resp.text}")

# --- Today's log table ---
st.subheader("Today's log")
resp = requests.get(f"{API_BASE}/api/hydration/logs/today", params={"user_id": user_id})
if resp.ok and resp.json():
    df_today = pd.DataFrame(resp.json())
    df_today["logged_at"] = pd.to_datetime(df_today["logged_at"]).dt.strftime("%I:%M %p")
    df_today = df_today[["logged_at", "amount_ml"]].rename(
        columns={"logged_at": "Time", "amount_ml": "Amount (ml)"}
    )
    st.dataframe(df_today, use_container_width=True, hide_index=True)
    st.metric("Total today", f"{df_today['Amount (ml)'].sum()} ml")
else:
    st.info("No entries logged today yet.")

# --- Monthly chart ---
st.subheader("Last 30 days")
resp = requests.get(f"{API_BASE}/api/hydration/logs/monthly", params={"user_id": user_id})
if resp.ok and resp.json():
    df_month = pd.DataFrame(resp.json())
    df_month["log_date"] = pd.to_datetime(df_month["log_date"])
    df_month = df_month.set_index("log_date")["total_ml"]
    st.bar_chart(df_month)
else:
    st.info("No data yet for the last 30 days.")

# --- AI feedback ---
st.subheader("🤖 Smart feedback")
if st.button("Get feedback from your AI hydration coach"):
    with st.spinner("Thinking..."):
        resp = requests.post(
            f"{API_BASE}/api/hydration/feedback",
            json={"user_id": user_id, "daily_goal_ml": int(daily_goal_ml)},
        )
    if resp.ok:
        data = resp.json()
        st.success(data["feedback"])
        st.caption(f"{data['today_total_ml']}ml / {data['goal_ml']}ml ({data['percent_of_goal']}% of goal)")
    else:
        st.error(f"Couldn't get feedback: {resp.text}")
