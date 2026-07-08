# Adjust working directory to project root if run from inside new_approch folder
import os
if os.path.basename(os.getcwd()) == 'new_approch':
    os.chdir('..')

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import joblib
import time

# Page Configuration
st.set_page_config(
    page_title="Honeywell Temperature Alarm Predictor - New Approach",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Design
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
        font-size: 28px;
        font-weight: bold;
        color: #f3f4f6;
    }
    .metric-label {
        font-size: 14px;
        color: #9ca3af;
    }
    .alert-card-warning {
        background-color: rgba(245, 158, 11, 0.15);
        border: 1px solid rgb(245, 158, 11);
        border-radius: 8px;
        padding: 15px;
        color: rgb(245, 158, 11);
        margin-bottom: 10px;
    }
    .alert-card-critical {
        background-color: rgba(239, 68, 68, 0.15);
        border: 1px solid rgb(239, 68, 68);
        border-radius: 8px;
        padding: 15px;
        color: rgb(239, 68, 68);
        margin-bottom: 10px;
    }
    .alert-card-emergency {
        background-color: rgba(220, 38, 38, 0.25);
        border: 2px solid rgb(220, 38, 38);
        border-radius: 8px;
        padding: 15px;
        color: rgb(248, 113, 113);
        margin-bottom: 10px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Configuration & Paths
MODEL_DIR = "models/first_cut_new"
FEATURE_PATH = "outputs/first_cut_new/feature_names.txt"
SCENARIO_DIR = "scenarios"
ALARM_LIMIT = 21.0

# ----------------------------------------------------------------
# Load Models & Setup
# ----------------------------------------------------------------
@st.cache_resource
def load_models_and_features(model_dir):
    models = {}
    for h in [5, 15, 30, 60]:
        model_path = os.path.join(model_dir, f"lgb_model_{h}m.pkl")
        if os.path.exists(model_path):
            models[h] = joblib.load(model_path)
            
    if os.path.exists(FEATURE_PATH):
        with open(FEATURE_PATH, "r") as f:
            feature_cols = f.read().split("\n")
    else:
        feature_cols = []
        
    return models, feature_cols


# ----------------------------------------------------------------
# Feature Engineering on the Fly
# ----------------------------------------------------------------
def compute_features_at_time(df_history, feature_cols):
    """
    Given the historical dataframe up to current tick (at least 61 rows),
    compute the identical features expected by the LightGBM models.
    """
    # Grab the last 65 rows to compute lags (up to 60) and rolling windows
    df_slice = df_history.tail(65).copy()
    
    # 1. Time Features
    current_time = df_slice.index[-1]
    df_slice['hour'] = current_time.hour
    df_slice['month'] = current_time.month
    df_slice['dayofweek'] = current_time.dayofweek
    
    # Selected key columns based on Feature Selection Strategy:
    # 03TIC_1023.PV (Target)
    # 03TI_1024.PV (Column Bottom Inlet Temp)
    # 03PIC_1023.PV (C3 Separator Pressure)
    # 03TI_1081.PV (Downstream Cooling Temp)
    # 03TIC_1009.PV (Feed Temperature Controller)
    key_cols = ['03TIC_1023.PV', '03TI_1024.PV', '03PIC_1023.PV', '03TI_1081.PV', '03TIC_1009.PV']
    
    # 2. Lag Features
    for col in key_cols:
        for lag in [1, 2, 5, 10, 15, 30, 60]:
            df_slice[f'{col}_lag_{lag}'] = df_slice[col].shift(lag)
            
    # 3. Rolling Features
    for col in key_cols:
        for window in [10, 30, 60]:
            df_slice[f'{col}_roll_mean_{window}'] = df_slice[col].rolling(window=window, min_periods=1).mean()
            df_slice[f'{col}_roll_std_{window}'] = df_slice[col].rolling(window=window, min_periods=1).std()
            df_slice[f'{col}_roll_max_{window}'] = df_slice[col].rolling(window=window, min_periods=1).max()
            df_slice[f'{col}_roll_min_{window}'] = df_slice[col].rolling(window=window, min_periods=1).min()

    # 4. Differences
    for col in key_cols:
        for diff in [5, 15, 30]:
            df_slice[f'{col}_diff_{diff}'] = df_slice[col] - df_slice[col].shift(diff)
            
    # Extract the last row containing our computed features
    feature_row = df_slice.tail(1)
    
    # Reindex to match the training feature order
    feature_df = feature_row[feature_cols].copy()
    
    return feature_df

# ----------------------------------------------------------------
# Simulation Console
# ----------------------------------------------------------------
st.sidebar.title("Simulation Console")
st.sidebar.markdown("---")

model_version = st.sidebar.selectbox("Model Version", ["First-Cut Baseline", "Tuned Model"])
model_dir = "models/first_cut_new" if model_version == "First-Cut Baseline" else "models/tuned_new"

models, feature_cols = load_models_and_features(model_dir)

# Display Model Info
st.sidebar.info(f"Model: **{model_version}**\nFeatures selected based on Pearson, Spearman, and Distance Correlation filters + VLE thermodynamic reasoning.")

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
    st.error(f"Scenario file not found at {scenario_path}. Please run generate_scenarios.py first!")
    st.stop()

# Playback Controls
col1, col2, col3 = st.sidebar.columns(3)
with col1:
    btn_play = st.button("▶️ Play")
with col2:
    btn_pause = st.button("⏸️ Pause")
with col3:
    btn_reset = st.button("🔄 Reset")

speed = st.sidebar.slider("Playback Speed (x)", min_value=1, max_value=60, value=10, step=5)

# Session States for animation
if "sim_index" not in st.session_state or btn_reset:
    # Start simulation at index 65 (we need 60 minutes of history to compute rolling stats)
    st.session_state.sim_index = 65
    st.session_state.is_playing = False
    st.session_state.alert_log = []
    st.toast("Simulation reset successfully!")

if btn_play:
    st.session_state.is_playing = True
if btn_pause:
    st.session_state.is_playing = False

# ----------------------------------------------------------------
# Dashboard Layout
# ----------------------------------------------------------------
st.title("⚡ Honeywell Temperature Alarm Predictor — New Approach")
st.markdown("### Simulated Real-Time Control Panel (First-Cut LightGBM)")

# Safety Check
if st.session_state.sim_index >= len(df_scenario):
    st.warning("End of scenario data reached. Click Reset to restart.")
    st.session_state.is_playing = False

# Get data up to current tick
current_idx = st.session_state.sim_index
df_history = df_scenario.iloc[:current_idx]
current_time = df_scenario.index[current_idx]
current_temp = df_scenario.iloc[current_idx]['03TIC_1023.PV']

# Run Inference
pred_5m, pred_15m, pred_30m, pred_60m = np.nan, np.nan, np.nan, np.nan
if len(models) > 0 and len(feature_cols) > 0:
    try:
        features = compute_features_at_time(df_history, feature_cols)
        if 5 in models:
            pred_5m = models[5].predict(features)[0]
        if 15 in models:
            pred_15m = models[15].predict(features)[0]
        if 30 in models:
            pred_30m = models[30].predict(features)[0]
        if 60 in models:
            pred_60m = models[60].predict(features)[0]
    except Exception as e:
        st.error(f"Inference Error: {e}")

# Save alerts to session state log
if pred_5m >= ALARM_LIMIT:
    alert_type = "Emergency"
    rec = "🚨 EMERGENCY CRITICAL ALERT: Over-temperature predicted in 5 minutes! Action: Immediately activate manual cooling, check reactor trip signals, and warn site personnel."
elif pred_15m >= ALARM_LIMIT:
    alert_type = "Critical"
    rec = "CRITICAL ALERT: Over-temperature predicted in 15 minutes! Action: Immediately increase reflux/cooling flow, check bypass valves, and notify supervisor."
elif pred_30m >= ALARM_LIMIT:
    alert_type = "Warning"
    rec = "Tactical Warning: Temperature predicted to cross 21.0 in 30 minutes. Action: Verify that the feed flow is stable and reflux flows are behaving normally."
elif pred_60m >= ALARM_LIMIT:
    alert_type = "Advisory"
    rec = "Strategic Advisory: High temperature forecast in 60 minutes. Action: Monitor column bottom inlet temperature (03TI_1024.PV) and prepare to adjust cooling flows."
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
# KPI Cards
# ----------------------------------------------------------------
kpi_cols = st.columns(5)

with kpi_cols[0]:
    st.markdown(f"""
    <div class="metric-card" style="border-left: 5px solid #10b981;">
        <div class="metric-label">Current Temperature</div>
        <div class="metric-value">{current_temp:.2f} °C</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[1]:
    color = "#ef4444" if pred_5m >= ALARM_LIMIT else "#10b981"
    st.markdown(f"""
    <div class="metric-card" style="border-left: 5px solid {color};">
        <div class="metric-label">5m Forecast</div>
        <div class="metric-value">{pred_5m:.2f} °C</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[2]:
    color = "#ef4444" if pred_15m >= ALARM_LIMIT else "#10b981"
    st.markdown(f"""
    <div class="metric-card" style="border-left: 5px solid {color};">
        <div class="metric-label">15m Forecast</div>
        <div class="metric-value">{pred_15m:.2f} °C</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[3]:
    color = "#f59e0b" if pred_30m >= ALARM_LIMIT else "#10b981"
    st.markdown(f"""
    <div class="metric-card" style="border-left: 5px solid {color};">
        <div class="metric-label">30m Forecast</div>
        <div class="metric-value">{pred_30m:.2f} °C</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[4]:
    color = "#3b82f6" if pred_60m >= ALARM_LIMIT else "#10b981"
    st.markdown(f"""
    <div class="metric-card" style="border-left: 5px solid {color};">
        <div class="metric-label">60m Forecast</div>
        <div class="metric-value">{pred_60m:.2f} °C</div>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------------------------------------------
# Plotly Chart
# ----------------------------------------------------------------
st.markdown("### Real-Time Scrolling Trend and Forecast Curve")

# Extract past 60 mins for history plotting
plot_history = df_scenario.iloc[max(0, current_idx-60):current_idx+1]

# Forecast times
time_5m = current_time + pd.Timedelta(minutes=5)
time_15m = current_time + pd.Timedelta(minutes=15)
time_30m = current_time + pd.Timedelta(minutes=30)
time_60m = current_time + pd.Timedelta(minutes=60)

fig = go.Figure()

# Plot actual temperature history
fig.add_trace(go.Scatter(
    x=plot_history.index,
    y=plot_history['03TIC_1023.PV'],
    mode='lines+markers',
    name='Actual Temperature (Past)',
    line=dict(color='#3b82f6', width=3),
    marker=dict(size=4)
))

# Plot future predictions
fig.add_trace(go.Scatter(
    x=[current_time, time_5m, time_15m, time_30m, time_60m],
    y=[current_temp, pred_5m, pred_15m, pred_30m, pred_60m],
    mode='lines+markers',
    name='Model Forecast',
    line=dict(color='#f59e0b', width=2.5, dash='dash'),
    marker=dict(
        size=[0, 10, 10, 10, 10],
        color=['#f59e0b',
               '#ef4444' if pred_5m >= ALARM_LIMIT else '#10b981',
               '#ef4444' if pred_15m >= ALARM_LIMIT else '#10b981',
               '#f59e0b' if pred_30m >= ALARM_LIMIT else '#10b981',
               '#3b82f6' if pred_60m >= ALARM_LIMIT else '#10b981']
    )
))

# Add Alarm Limit line
fig.add_trace(go.Scatter(
    x=[plot_history.index.min(), time_60m],
    y=[ALARM_LIMIT, ALARM_LIMIT],
    mode='lines',
    name=f'Alarm Threshold ({ALARM_LIMIT}°C)',
    line=dict(color='#ef4444', width=2, dash='dot')
))

# Layout
fig.update_layout(
    xaxis_title="Time",
    yaxis_title="Temperature (°C)",
    yaxis_range=[15, 25],
    height=500,
    margin=dict(l=20, r=20, t=20, b=20),
    template="plotly_dark",
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
)

# Highlight warning region
fig.add_vrect(
    x0=current_time, x1=time_60m,
    fillcolor="rgba(245, 158, 11, 0.05)", line_width=0,
    annotation_text="Prediction Window", annotation_position="top left"
)

st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------------
# Operator Console Log & Scenario Details
# ----------------------------------------------------------------
c_log, c_scen = st.columns([2, 1])

with c_log:
    st.markdown("### 📋 Operator Advisory Log")
    if len(st.session_state.alert_log) == 0:
        st.info("System normal. No warnings or alerts active.")
    else:
        for log in reversed(st.session_state.alert_log[-5:]): # Show last 5 alerts
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
    st.markdown("### ℹ️ Scenario Details")
    st.markdown(f"**Current Scenario:** {selected_scenario_name}")
    st.markdown(f"**Model Version:** `FIRST_CUT_NEW`")
    st.markdown(f"**Simulated Time:** `{current_time.strftime('%Y-%m-%d %H:%M:%S')}`")
    st.markdown(f"**Total Records:** `{len(df_scenario)}`")
    
    # Real-time state check
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

# Rerun Loop
if st.session_state.is_playing:
    sleep_time = max(0.01, 1.0 / speed)
    time.sleep(sleep_time)
    st.session_state.sim_index += 1
    st.rerun()
