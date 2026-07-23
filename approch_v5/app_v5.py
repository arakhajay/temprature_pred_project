# Adjust working directory to project root if run from inside approch_v5 folder
import os
import sys
if os.path.basename(os.getcwd()) == 'approch_v5':
    os.chdir('..')
    print("Changed working directory to project root:", os.getcwd())
if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())
if os.path.join(os.getcwd(), 'approch_v5') not in sys.path:
    sys.path.append(os.path.join(os.getcwd(), 'approch_v5'))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import torch
import torch.nn as nn
import pickle
import time

# ----------------------------------------------------------------
# Page Configuration & Premium Dark Theme Styling
# ----------------------------------------------------------------
st.set_page_config(
    page_title="Honeywell Temperature Alarm Predictor - V5 Console",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .reportview-container {
        background: #0e1117;
    }
    .metric-card {
        background-color: #1f2937;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
        border-left: 5px solid #3b82f6;
    }
    .metric-value {
        font-size: 26px;
        font-weight: bold;
        color: #f3f4f6;
    }
    .metric-label {
        font-size: 13px;
        color: #9ca3af;
    }
    .alert-card-warning {
        background-color: rgba(245, 158, 11, 0.15);
        border: 1px solid rgb(245, 158, 11);
        border-radius: 8px;
        padding: 12px 15px;
        color: rgb(245, 158, 11);
        margin-bottom: 10px;
    }
    .alert-card-critical {
        background-color: rgba(239, 68, 68, 0.15);
        border: 1px solid rgb(239, 68, 68);
        border-radius: 8px;
        padding: 12px 15px;
        color: rgb(239, 68, 68);
        margin-bottom: 10px;
    }
    .alert-card-emergency {
        background-color: rgba(220, 38, 38, 0.25);
        border: 2px solid rgb(220, 38, 38);
        border-radius: 8px;
        padding: 12px 15px;
        color: rgb(248, 113, 113);
        margin-bottom: 10px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Configuration & Paths
PATH_MODELS_DIR = "models/v5" if os.path.exists("models/v5") else "approch_v5/models/v5"
SCENARIO_DIR = "scenarios" if os.path.exists("scenarios") else "approch_v5/scenarios"
ALARM_LIMIT = 21.0

# ----------------------------------------------------------------
# PyTorch Model Imports (From Official Approach V5 models.py)
# ----------------------------------------------------------------
try:
    from models import LSTMRegressor, Seq2Seq
except ImportError:
    from approch_v5.models import LSTMRegressor, Seq2Seq

# ----------------------------------------------------------------
# Load Models, Scaler, and Features
# ----------------------------------------------------------------
@st.cache_resource
def load_v5_artifacts():
    scaler = None
    features = []
    
    # 1. Load selected features list
    feat_path = os.path.join(PATH_MODELS_DIR, "selected_features_v5.pkl")
    if os.path.exists(feat_path):
        with open(feat_path, "rb") as f:
            features = pickle.load(f)
    else:
        # Fallback default V5 features
        features = [
            '03TIC_1023.PV', '03TI_1024.PV', '03PIC_1023.PV', '03TI_1081.PV', '03TIC_1009.PV',
            'temp_pressure_product', 'temp_delta_bottom_top', '03TIC_1023.PV_lag_1',
            '03TIC_1023.PV_lag_5', '03TIC_1023.PV_diff_5', '03TIC_1023.PV_roll_mean_10', 'hour'
        ]

    # 2. Load scaler
    scaler_path = os.path.join(PATH_MODELS_DIR, "scaler_v5.pkl")
    if os.path.exists(scaler_path):
        with open(scaler_path, "rb") as f:
            scaler = pickle.load(f)

    # 3. Load PyTorch Models
    lstm = LSTMRegressor(input_dim=len(features))
    lstm_path = os.path.join(PATH_MODELS_DIR, "lstm_model_v5.pth")
    if os.path.exists(lstm_path):
        lstm.load_state_dict(torch.load(lstm_path, map_location=torch.device('cpu')))
    lstm.eval()

    seq2seq = Seq2Seq(input_dim=len(features))
    seq2seq_path = os.path.join(PATH_MODELS_DIR, "seq2seq_model_v5.pth")
    if os.path.exists(seq2seq_path):
        seq2seq.load_state_dict(torch.load(seq2seq_path, map_location=torch.device('cpu')))
    seq2seq.eval()

    return lstm, seq2seq, scaler, features

lstm_model, seq2seq_model, scaler, features = load_v5_artifacts()

# ----------------------------------------------------------------
# Dynamic On-The-Fly V5 Feature Engineering
# ----------------------------------------------------------------
def compute_v5_features(df_history):
    """
    Computes the exact 12 selected features dynamically on-the-fly from df_history,
    returning a 10-step sequence window of shape (10, 12).
    """
    df_slice = df_history.tail(65).copy()
    current_time = df_slice.index[-1]

    for feat in features:
        if feat in df_slice.columns:
            continue
        elif feat == 'hour':
            df_slice['hour'] = current_time.hour
        elif feat == 'month':
            df_slice['month'] = current_time.month
        elif feat == 'dayofweek':
            df_slice['dayofweek'] = current_time.dayofweek
        elif feat == 'temp_pressure_product':
            df_slice['temp_pressure_product'] = df_slice['03TIC_1023.PV'] * df_slice['03PIC_1023.PV']
        elif feat == 'temp_delta_bottom_top':
            df_slice['temp_delta_bottom_top'] = df_slice['03TI_1024.PV'] - df_slice['03TIC_1023.PV']
        elif '_lag_' in feat:
            parts = feat.split('_lag_')
            base_col, lag_val = parts[0], int(parts[1])
            df_slice[feat] = df_slice[base_col].shift(lag_val)
        elif '_diff_' in feat:
            parts = feat.split('_diff_')
            base_col, diff_val = parts[0], int(parts[1])
            df_slice[feat] = df_slice[base_col] - df_slice[base_col].shift(diff_val)
        elif '_roll_mean_' in feat:
            parts = feat.split('_roll_mean_')
            base_col, w_val = parts[0], int(parts[1])
            df_slice[feat] = df_slice[base_col].rolling(window=w_val, min_periods=1).mean()
        elif '_roll_std_' in feat:
            parts = feat.split('_roll_std_')
            base_col, w_val = parts[0], int(parts[1])
            df_slice[feat] = df_slice[base_col].rolling(window=w_val, min_periods=1).std()
        elif '_roll_max_' in feat:
            parts = feat.split('_roll_max_')
            base_col, w_val = parts[0], int(parts[1])
            df_slice[feat] = df_slice[base_col].rolling(window=w_val, min_periods=1).max()
        elif '_roll_min_' in feat:
            parts = feat.split('_roll_min_')
            base_col, w_val = parts[0], int(parts[1])
            df_slice[feat] = df_slice[base_col].rolling(window=w_val, min_periods=1).min()
        elif '_expanding_mean' in feat:
            base_col = feat.split('_expanding_mean')[0]
            df_slice[feat] = df_slice[base_col].expanding(min_periods=1).mean()
        elif '_expanding_max' in feat:
            base_col = feat.split('_expanding_max')[0]
            df_slice[feat] = df_slice[base_col].expanding(min_periods=1).max()

    feature_window = df_slice[features].copy()
    if len(feature_window) < 10:
        pad_len = 10 - len(feature_window)
        pad_rows = pd.concat([feature_window.iloc[[0]]] * pad_len, ignore_index=True)
        feature_window = pd.concat([pad_rows, feature_window], ignore_index=True)
    else:
        feature_window = feature_window.tail(10)
        
    return feature_window

# ----------------------------------------------------------------
# Sidebar Controls & Configuration
# ----------------------------------------------------------------
st.sidebar.title("Simulation Console")
st.sidebar.markdown("---")

# 1. Model Selection Dropdown (LSTM vs Seq2Seq)
model_version = st.sidebar.selectbox("Model Version", ["LSTM Model", "Seq2Seq Model"])
st.sidebar.info(f"Active Model: **{model_version}**\nTrained on **12 Selected Features** via 3-Phase Selection (Distance Correlation + SHAP + Lasso L1).")

# 2. Scenario Selection
scenario_options = {
    "Critical Thermal Upset (July 17, 2025)": "upset_event_july_2025.parquet",
    "Stable Operation (Normal Day)": "normal_operation.parquet"
}
selected_scenario_name = st.sidebar.selectbox("Select Scenario", list(scenario_options.keys()))
scenario_file = scenario_options[selected_scenario_name]
scenario_path = os.path.join(SCENARIO_DIR, scenario_file)

@st.cache_data
def load_scenario_data(path):
    if os.path.exists(path):
        df = pd.read_parquet(path)
        df['TimeStamp'] = pd.to_datetime(df['TimeStamp'])
        df = df.set_index('TimeStamp')
        return df
    return None

df_scenario = load_scenario_data(scenario_path)

if df_scenario is None:
    st.error(f"Scenario file not found at {scenario_path}.")
    st.stop()

# 3. Playback Controls
col_p1, col_p2, col_p3 = st.sidebar.columns(3)
with col_p1:
    btn_play = st.button("▶️ Play")
with col_p2:
    btn_pause = st.button("⏸️ Pause")
with col_p3:
    btn_reset = st.button("🔄 Reset")

speed = st.sidebar.slider("Playback Speed (x)", min_value=1, max_value=60, value=10, step=5)

# Sidebar Selected Features View
st.sidebar.markdown("---")
st.sidebar.subheader("Selected Features (V5)")
for idx, feat in enumerate(features, 1):
    st.sidebar.markdown(f"**{idx}.** `{feat}`")

# 4. Session State Management for Real-Time Animation
if "sim_index" not in st.session_state or btn_reset:
    st.session_state.sim_index = 65 # Start after 65 rows for initial lag history
    st.session_state.is_playing = False
    st.session_state.alert_log = []
    st.toast("Simulation reset successfully!")

if btn_play:
    st.session_state.is_playing = True
if btn_pause:
    st.session_state.is_playing = False

# ----------------------------------------------------------------
# Main Control Panel Dashboard
# ----------------------------------------------------------------
st.title("⚡ Honeywell Temperature Alarm Predictor — Approach V5")
st.markdown(f"### Real-Time Control Panel ({model_version})")

# Safety Bounds Check
if st.session_state.sim_index >= len(df_scenario):
    st.warning("End of scenario data reached. Click Reset to restart.")
    st.session_state.is_playing = False

# Extract Current Simulation Slice
current_idx = min(st.session_state.sim_index, len(df_scenario) - 1)
df_history = df_scenario.iloc[:current_idx + 1]
current_time = df_scenario.index[current_idx]
current_temp = df_scenario.iloc[current_idx]['03TIC_1023.PV']

# ----------------------------------------------------------------
# Run Model Inference Across Horizons
# ----------------------------------------------------------------
pred_5m, pred_15m, pred_30m, pred_60m = np.nan, np.nan, np.nan, np.nan

try:
    feat_window = compute_v5_features(df_history)
    feat_scaled = scaler.transform(feat_window) if scaler is not None else feat_window.values
    feat_tensor = torch.tensor(feat_scaled, dtype=torch.float32).unsqueeze(0) # (1, 10, 12)
    
    with torch.no_grad():
        if model_version == "LSTM Model":
            lstm_15m_out = lstm_model(feat_tensor).item()
            pred_15m = lstm_15m_out
            delta = pred_15m - current_temp
            pred_5m = current_temp + delta * (5.0 / 15.0)
            pred_30m = current_temp + delta * (30.0 / 15.0)
            pred_60m = current_temp + delta * (60.0 / 15.0)
        else: # Seq2Seq Model
            seq_out = seq2seq_model(feat_tensor).numpy().flatten() # 60 steps forecast
            pred_5m = seq_out[4]
            pred_15m = seq_out[14]
            pred_30m = seq_out[29]
            pred_60m = seq_out[59]
except Exception as e:
    st.error(f"Inference Engine Error: {e}")

# ----------------------------------------------------------------
# Alert Generation & Logging
# ----------------------------------------------------------------
if pred_5m >= ALARM_LIMIT:
    alert_type = "Emergency"
    rec = "🚨 EMERGENCY CRITICAL ALERT: Over-temperature predicted in 5 minutes! Action: Immediately activate manual emergency cooling, check reactor trip signals, and alert operators."
elif pred_15m >= ALARM_LIMIT:
    alert_type = "Critical"
    rec = "CRITICAL ALERT: Over-temperature predicted in 15 minutes! Action: Increase reflux and secondary cooling water flow immediately; notify control room supervisor."
elif pred_30m >= ALARM_LIMIT:
    alert_type = "Warning"
    rec = "Tactical Warning: Temperature forecasted to breach 21.0°C in 30 minutes. Action: Verify feed rate stability and check C3 separator pressure (03PIC_1023.PV)."
elif pred_60m >= ALARM_LIMIT:
    alert_type = "Advisory"
    rec = "Strategic Advisory: High temperature trend forecast in 60 minutes. Action: Monitor column bottom inlet temp (03TI_1024.PV) and prepare cooling adjustments."
else:
    alert_type = "Normal"
    rec = None

if alert_type != "Normal" and (len(st.session_state.alert_log) == 0 or st.session_state.alert_log[-1]['message'] != rec):
    st.session_state.alert_log.append({
        "time": current_time.strftime("%H:%M:%S"),
        "type": alert_type,
        "message": rec
    })

# ----------------------------------------------------------------
# Top 5 KPI Metric Cards Banner
# ----------------------------------------------------------------
kpi_cols = st.columns(5)

with kpi_cols[0]:
    st.markdown(f"""
    <div class="metric-card" style="border-left: 5px solid #10b981;">
        <div class="metric-label">Current Temp</div>
        <div class="metric-value">{current_temp:.2f} °C</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[1]:
    color_5m = "#ef4444" if pred_5m >= ALARM_LIMIT else "#10b981"
    st.markdown(f"""
    <div class="metric-card" style="border-left: 5px solid {color_5m};">
        <div class="metric-label">5m Forecast</div>
        <div class="metric-value">{pred_5m:.2f} °C</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[2]:
    color_15m = "#ef4444" if pred_15m >= ALARM_LIMIT else "#10b981"
    st.markdown(f"""
    <div class="metric-card" style="border-left: 5px solid {color_15m};">
        <div class="metric-label">15m Forecast</div>
        <div class="metric-value">{pred_15m:.2f} °C</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[3]:
    color_30m = "#f59e0b" if pred_30m >= ALARM_LIMIT else "#10b981"
    st.markdown(f"""
    <div class="metric-card" style="border-left: 5px solid {color_30m};">
        <div class="metric-label">30m Forecast</div>
        <div class="metric-value">{pred_30m:.2f} °C</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[4]:
    color_60m = "#3b82f6" if pred_60m >= ALARM_LIMIT else "#10b981"
    st.markdown(f"""
    <div class="metric-card" style="border-left: 5px solid {color_60m};">
        <div class="metric-label">60m Forecast</div>
        <div class="metric-value">{pred_60m:.2f} °C</div>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------------------------------------------
# Plotly Real-Time Scrolling Trend & Forecast Curve
# ----------------------------------------------------------------
st.markdown("### Real-Time Scrolling Trend and Forecast Curve")

plot_history = df_scenario.iloc[max(0, current_idx - 60):current_idx + 1]

time_5m = current_time + pd.Timedelta(minutes=5)
time_15m = current_time + pd.Timedelta(minutes=15)
time_30m = current_time + pd.Timedelta(minutes=30)
time_60m = current_time + pd.Timedelta(minutes=60)

fig = go.Figure()

# Past actual historical line
fig.add_trace(go.Scatter(
    x=plot_history.index,
    y=plot_history['03TIC_1023.PV'],
    mode='lines+markers',
    name='Actual Temperature (Past 60m)',
    line=dict(color='#3b82f6', width=3),
    marker=dict(size=4)
))

# Model future predictions line
fig.add_trace(go.Scatter(
    x=[current_time, time_5m, time_15m, time_30m, time_60m],
    y=[current_temp, pred_5m, pred_15m, pred_30m, pred_60m],
    mode='lines+markers',
    name=f'{model_version} Forecast',
    line=dict(color='#f59e0b', width=2.5, dash='dash'),
    marker=dict(
        size=[0, 10, 10, 10, 10],
        color=[
            '#f59e0b',
            '#ef4444' if pred_5m >= ALARM_LIMIT else '#10b981',
            '#ef4444' if pred_15m >= ALARM_LIMIT else '#10b981',
            '#f59e0b' if pred_30m >= ALARM_LIMIT else '#10b981',
            '#3b82f6' if pred_60m >= ALARM_LIMIT else '#10b981'
        ]
    )
))

# Alarm limit horizontal line
fig.add_trace(go.Scatter(
    x=[plot_history.index.min(), time_60m],
    y=[ALARM_LIMIT, ALARM_LIMIT],
    mode='lines',
    name=f'Alarm Threshold ({ALARM_LIMIT}°C)',
    line=dict(color='#ef4444', width=2, dash='dot')
))

# Chart layout styling
fig.update_layout(
    xaxis_title="Time",
    yaxis_title="Overhead Temp (°C)",
    yaxis_range=[15, 25],
    height=480,
    margin=dict(l=20, r=20, t=20, b=20),
    template="plotly_dark",
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
)

# Highlight prediction window region
fig.add_vrect(
    x0=current_time, x1=time_60m,
    fillcolor="rgba(245, 158, 11, 0.05)", line_width=0,
    annotation_text="Prediction Window", annotation_position="top left"
)

st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------------
# Operator Advisory Log & Scenario Details Footer
# ----------------------------------------------------------------
c_log, c_scen = st.columns([2, 1])

with c_log:
    st.markdown("### 📋 Operator Advisory Log")
    if len(st.session_state.alert_log) == 0:
        st.info("System operating normally. No active warnings or alarms.")
    else:
        for log in reversed(st.session_state.alert_log[-5:]):
            if log['type'] == "Emergency":
                st.markdown(f"""
                <div class="alert-card-emergency">
                    <strong>🚨 EMERGENCY CRITICAL ALERT ({log['time']})</strong><br/>
                    {log['message']}
                </div>
                """, unsafe_allow_html=True)
            elif log['type'] == "Critical":
                st.markdown(f"""
                <div class="alert-card-critical">
                    <strong>🚨 CRITICAL ALERT ({log['time']})</strong><br/>
                    {log['message']}
                </div>
                """, unsafe_allow_html=True)
            elif log['type'] == "Warning":
                st.markdown(f"""
                <div class="alert-card-warning">
                    <strong>⚠️ WARNING ({log['time']})</strong><br/>
                    {log['message']}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="metric-card" style="border-left: 5px solid #3b82f6; text-align: left; padding: 10px; margin-bottom: 10px;">
                    <strong style="color: #3b82f6;">ℹ️ ADVISORY ({log['time']})</strong><br/>
                    <span style="font-size: 14px;">{log['message']}</span>
                </div>
                """, unsafe_allow_html=True)

with c_scen:
    st.markdown("### ℹ️ System Metadata")
    st.markdown(f"**Current Scenario:** {selected_scenario_name}")
    st.markdown(f"**Selected Model:** `{model_version}`")
    st.markdown(f"**Simulated Timestamp:** `{current_time.strftime('%Y-%m-%d %H:%M:%S')}`")
    st.markdown(f"**Total Records:** `{len(df_scenario)}`")
    
    if alert_type == "Emergency":
        st.markdown("**System Status:** 🚨 EMERGENCY CRITICAL")
    elif alert_type == "Critical":
        st.markdown("**System Status:** 🟥 CRITICAL UPSET")
    elif alert_type == "Warning":
        st.markdown("**System Status:** 🟨 TACTICAL WARNING")
    elif alert_type == "Advisory":
        st.markdown("**System Status:** 🟦 STRATEGIC ADVISORY")
    else:
        st.markdown("**System Status:** 🟩 NORMAL")

# ----------------------------------------------------------------
# Animation Rerun Loop
# ----------------------------------------------------------------
if st.session_state.is_playing:
    sleep_time = max(0.01, 1.0 / speed)
    time.sleep(sleep_time)
    st.session_state.sim_index += 1
    st.rerun()
