# Adjust working directory to project root if run from inside approch_v3 folder
import os
if os.path.basename(os.getcwd()) == 'approch_v3':
    os.chdir('..')

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import joblib
import time

# Page Configuration
st.set_page_config(
    page_title="Honeywell Temperature Alarm Predictor - Comparative Console",
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
        margin-bottom: 10px;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #f3f4f6;
    }
    .metric-label {
        font-size: 13px;
        color: #9ca3af;
        margin-bottom: 5px;
    }
    .alert-card-warning {
        background-color: rgba(245, 158, 11, 0.15);
        border: 1px solid rgb(245, 158, 11);
        border-radius: 8px;
        padding: 12px;
        color: rgb(245, 158, 11);
        margin-bottom: 10px;
    }
    .alert-card-critical {
        background-color: rgba(239, 68, 68, 0.15);
        border: 1px solid rgb(239, 68, 68);
        border-radius: 8px;
        padding: 12px;
        color: rgb(239, 68, 68);
        margin-bottom: 10px;
    }
    .alert-card-emergency {
        background-color: rgba(220, 38, 38, 0.25);
        border: 2px solid rgb(220, 38, 38);
        border-radius: 8px;
        padding: 12px;
        color: rgb(248, 113, 113);
        margin-bottom: 10px;
        font-weight: bold;
    }
    .vs-header {
        font-size: 18px;
        font-weight: bold;
        color: #3b82f6;
        text-align: center;
        padding: 5px;
        background-color: #1e293b;
        border-radius: 4px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Configuration & Paths
PATH_SELECTED_JSON = "outputs/selected_features_by_horizon.json"
PATH_ALL_TXT = "outputs/first_cut_v3/feature_names.txt"
SCENARIO_DIR = "scenarios"
ALARM_LIMIT = 21.0

# ----------------------------------------------------------------
# Load Models & Setup
# ----------------------------------------------------------------
@st.cache_resource
def load_all_models_and_features():
    models = {
        "Selected_Features_Baseline": {},
        "Selected_Features_Tuned": {},
        "All_Features_Baseline": {},
        "All_Features_Tuned": {}
    }
    
    # Selected Features models
    for h in [5, 15, 30, 60]:
        # Baseline
        path = f"models/first_cut_new/lgb_model_{h}m.pkl"
        if os.path.exists(path):
            models["Selected_Features_Baseline"][h] = joblib.load(path)
        # Tuned
        path = f"models/tuned_new/lgb_model_{h}m.pkl"
        if os.path.exists(path):
            models["Selected_Features_Tuned"][h] = joblib.load(path)
            
    # All Features models (v3)
    for h in [5, 15, 30, 60]:
        # Baseline
        path = f"models/first_cut_v3/lgb_model_{h}m.pkl"
        if os.path.exists(path):
            models["All_Features_Baseline"][h] = joblib.load(path)
        # Tuned
        path = f"models/tuned_v3/lgb_model_{h}m.pkl"
        if os.path.exists(path):
            models["All_Features_Tuned"][h] = joblib.load(path)
            
    # Load feature lists
    selected_features_by_horizon = {}
    if os.path.exists(PATH_SELECTED_JSON):
        import json
        with open(PATH_SELECTED_JSON, "r") as f:
            selected_features_by_horizon = json.load(f)
            
    all_features_list = []
    if os.path.exists(PATH_ALL_TXT):
        with open(PATH_ALL_TXT, "r") as f:
            all_features_list = f.read().split("\n")
            
    return models, selected_features_by_horizon, all_features_list


models, selected_features_by_horizon, all_features_list = load_all_models_and_features()

# ----------------------------------------------------------------
# Feature Engineering on the Fly
# ----------------------------------------------------------------
def compute_all_features_at_time(df_history, all_features_list):
    """
    Compute the complete set of 132 features for the latest timestamp
    """
    df_slice = df_history.tail(65).copy()
    
    # 1. Time Features
    current_time = df_slice.index[-1]
    df_slice['hour'] = current_time.hour
    df_slice['month'] = current_time.month
    df_slice['dayofweek'] = current_time.dayofweek
    
    # Key columns used for feature engineering
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
            
    feature_row = df_slice.tail(1)
    feature_df = feature_row[all_features_list].copy()
    return feature_df

# ----------------------------------------------------------------
# Sidebar & Controls
# ----------------------------------------------------------------
st.sidebar.title("Comparative Console")
st.sidebar.markdown("---")

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

speed = st.sidebar.slider("Playback Speed (x)", min_value=1, max_value=60, value=15, step=5)

# Session States for animation
if "sim_index" not in st.session_state or btn_reset:
    st.session_state.sim_index = 65
    st.session_state.is_playing = False
    st.session_state.alert_log_selected = []
    st.session_state.alert_log_all = []
    st.toast("Simulation reset successfully!")

if btn_play:
    st.session_state.is_playing = True
if btn_pause:
    st.session_state.is_playing = False

# Setup Tabs
tab1, tab2 = st.tabs(["📊 Real-Time Simulation Console", "🔄 Side-by-Side Model Comparison"])

# Safety Check
if st.session_state.sim_index >= len(df_scenario):
    st.warning("End of scenario data reached. Click Reset to restart.")
    st.session_state.is_playing = False

# Get data up to current tick
current_idx = st.session_state.sim_index
df_history = df_scenario.iloc[:current_idx]
current_time = df_scenario.index[current_idx]
current_temp = df_scenario.iloc[current_idx]['03TIC_1023.PV']

# Run Inference for ALL models
features_all = compute_all_features_at_time(df_history, all_features_list)

preds = {
    "Selected_Baseline": {5: np.nan, 15: np.nan, 30: np.nan, 60: np.nan},
    "Selected_Tuned": {5: np.nan, 15: np.nan, 30: np.nan, 60: np.nan},
    "All_Baseline": {5: np.nan, 15: np.nan, 30: np.nan, 60: np.nan},
    "All_Tuned": {5: np.nan, 15: np.nan, 30: np.nan, 60: np.nan}
}

# Selected Features inference (subset columns per horizon)
for ver in ["Selected_Baseline", "Selected_Tuned"]:
    model_key = "Selected_Features_Baseline" if "Baseline" in ver else "Selected_Features_Tuned"
    for h in [5, 15, 30, 60]:
        if h in models[model_key] and f"{h}m" in selected_features_by_horizon:
            cols = selected_features_by_horizon[f"{h}m"]
            features_h = features_all[cols]
            preds[ver][h] = models[model_key][h].predict(features_h)[0]

# All Features inference (pass all 132 columns)
for ver in ["All_Baseline", "All_Tuned"]:
    model_key = "All_Features_Baseline" if "Baseline" in ver else "All_Features_Tuned"
    for h in [5, 15, 30, 60]:
        if h in models[model_key]:
            preds[ver][h] = models[model_key][h].predict(features_all)[0]


# Helper to get recommendations
def get_recommendation(h_preds):
    if h_preds[5] >= ALARM_LIMIT:
        return "Emergency", "🚨 EMERGENCY ALERT (5m forecast >= 21°C): Activate manual cooling immediately!"
    elif h_preds[15] >= ALARM_LIMIT:
        return "Critical", "🚨 CRITICAL WARNING (15m forecast >= 21°C): Increase reflux flow & notify supervisor."
    elif h_preds[30] >= ALARM_LIMIT:
        return "Warning", "⚠️ Warning (30m forecast >= 21°C): Stable feed checks advised."
    elif h_preds[60] >= ALARM_LIMIT:
        return "Advisory", "ℹ️ Advisory (60m forecast >= 21°C): Monitor bottom temperature trend."
    return "Normal", "System operating normally."

# Log alerts
status_sel, rec_sel = get_recommendation(preds["Selected_Tuned"])
status_all, rec_all = get_recommendation(preds["All_Tuned"])

if status_sel != "Normal" and (len(st.session_state.alert_log_selected) == 0 or st.session_state.alert_log_selected[-1]['message'] != rec_sel):
    st.session_state.alert_log_selected.append({"time": current_time.strftime("%H:%M:%S"), "type": status_sel, "message": rec_sel})
if status_all != "Normal" and (len(st.session_state.alert_log_all) == 0 or st.session_state.alert_log_all[-1]['message'] != rec_all):
    st.session_state.alert_log_all.append({"time": current_time.strftime("%H:%M:%S"), "type": status_all, "message": rec_all})


# ----------------------------------------------------------------
# TAB 1: Real-Time Simulation Console
# ----------------------------------------------------------------
with tab1:
    col_sel_model, col_sim_info = st.columns([1, 3])
    with col_sel_model:
        selected_model_option = st.selectbox(
            "Select Active Model",
            ["Selected Features (Tuned)", "Selected Features (Baseline)", "All Features (Tuned)", "All Features (Baseline)"]
        )
        
        # Map choice to preds dictionary key
        opt_map = {
            "Selected Features (Tuned)": "Selected_Tuned",
            "Selected Features (Baseline)": "Selected_Baseline",
            "All Features (Tuned)": "All_Tuned",
            "All Features (Baseline)": "All_Baseline"
        }
        active_pred_key = opt_map[selected_model_option]
        
    st.title("⚡ Dynamic Simulation Console")
    
    # KPI Cards
    kpi_cols = st.columns(5)
    with kpi_cols[0]:
        st.markdown(f'<div class="metric-card" style="border-left: 5px solid #10b981;"><div class="metric-label">Current Temp</div><div class="metric-value">{current_temp:.2f} °C</div></div>', unsafe_allow_html=True)
    for idx, h in enumerate([5, 15, 30, 60]):
        p_val = preds[active_pred_key][h]
        color = "#ef4444" if p_val >= ALARM_LIMIT else ("#f59e0b" if h == 30 and p_val >= ALARM_LIMIT else "#10b981")
        with kpi_cols[idx+1]:
            st.markdown(f'<div class="metric-card" style="border-left: 5px solid {color};"><div class="metric-label">{h}m Forecast</div><div class="metric-value">{p_val:.2f} °C</div></div>', unsafe_allow_html=True)

    # Plot scrolling chart
    plot_history = df_scenario.iloc[max(0, current_idx-60):current_idx+1]
    time_points = [current_time + pd.Timedelta(minutes=m) for m in [0, 5, 15, 30, 60]]
    pred_points = [current_temp] + [preds[active_pred_key][m] for m in [5, 15, 30, 60]]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=plot_history.index, y=plot_history['03TIC_1023.PV'], mode='lines+markers', name='Actual Temp', line=dict(color='#3b82f6', width=3)))
    fig.add_trace(go.Scatter(x=time_points, y=pred_points, mode='lines+markers', name='Forecast', line=dict(color='#f59e0b', width=2.5, dash='dash')))
    fig.add_trace(go.Scatter(x=[plot_history.index.min(), time_points[-1]], y=[ALARM_LIMIT, ALARM_LIMIT], mode='lines', name='Alarm Limit', line=dict(color='#ef4444', width=2, dash='dot')))
    
    fig.update_layout(xaxis_title="Time", yaxis_title="Temperature (°C)", yaxis_range=[15, 25], height=400, template="plotly_dark", margin=dict(l=20, r=20, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

    # Logs
    c_log1, c_scen1 = st.columns([2, 1])
    with c_log1:
        st.markdown("### Advisory Log")
        active_log = st.session_state.alert_log_all if "All" in active_pred_key else st.session_state.alert_log_selected
        if len(active_log) == 0:
            st.info("System normal. No warnings or alerts active.")
        else:
            for log in reversed(active_log[-4:]):
                if log['type'] == "Emergency":
                    st.markdown(f'<div class="alert-card-emergency"><strong>🚨 EMERGENCY ({log["time"]}):</strong> {log["message"]}</div>', unsafe_allow_html=True)
                elif log['type'] == "Critical":
                    st.markdown(f'<div class="alert-card-critical"><strong>🚨 CRITICAL ({log["time"]}):</strong> {log["message"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="alert-card-warning"><strong>⚠️ WARNING ({log["time"]}):</strong> {log["message"]}</div>', unsafe_allow_html=True)
    with c_scen1:
        st.markdown("### Simulation Details")
        st.write(f"**Scenario:** {selected_scenario_name}")
        st.write(f"**Model Selected:** `{selected_model_option}`")
        st.write(f"**Simulated Timestamp:** `{current_time.strftime('%Y-%m-%d %H:%M:%S')}`")

# ----------------------------------------------------------------
# TAB 2: Side-by-Side Model Comparison
# ----------------------------------------------------------------
with tab2:
    st.title("🔄 Selected Features (25) vs. All Features (132) Comparison")
    
    col_comp_1, col_comp_2 = st.columns(2)
    
    with col_comp_1:
        st.markdown('<div class="vs-header">Selected Features Model (Tuned)</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("5m Forecast", f"{preds['Selected_Tuned'][5]:.2f} °C", f"{preds['Selected_Tuned'][5] - current_temp:+.2f}")
        c2.metric("15m Forecast", f"{preds['Selected_Tuned'][15]:.2f} °C", f"{preds['Selected_Tuned'][15] - current_temp:+.2f}")
        c3.metric("30m Forecast", f"{preds['Selected_Tuned'][30]:.2f} °C", f"{preds['Selected_Tuned'][30] - current_temp:+.2f}")
        c4.metric("60m Forecast", f"{preds['Selected_Tuned'][60]:.2f} °C", f"{preds['Selected_Tuned'][60] - current_temp:+.2f}")
        
    with col_comp_2:
        st.markdown('<div class="vs-header">All Features Model (Tuned, v3)</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("5m Forecast", f"{preds['All_Tuned'][5]:.2f} °C", f"{preds['All_Tuned'][5] - current_temp:+.2f}")
        c2.metric("15m Forecast", f"{preds['All_Tuned'][15]:.2f} °C", f"{preds['All_Tuned'][15] - current_temp:+.2f}")
        c3.metric("30m Forecast", f"{preds['All_Tuned'][30]:.2f} °C", f"{preds['All_Tuned'][30] - current_temp:+.2f}")
        c4.metric("60m Forecast", f"{preds['All_Tuned'][60]:.2f} °C", f"{preds['All_Tuned'][60] - current_temp:+.2f}")

    # Overlay comparison on the same Plotly Chart
    fig_comp = go.Figure()
    fig_comp.add_trace(go.Scatter(x=plot_history.index, y=plot_history['03TIC_1023.PV'], mode='lines', name='Actual History', line=dict(color='#9ca3af', width=2)))
    
    # Selected Features curve
    time_pts = [current_time + pd.Timedelta(minutes=m) for m in [0, 5, 15, 30, 60]]
    fig_comp.add_trace(go.Scatter(
        x=time_pts, 
        y=[current_temp] + [preds['Selected_Tuned'][m] for m in [5, 15, 30, 60]], 
        mode='lines+markers', 
        name='Selected Features (Tuned)', 
        line=dict(color='#f59e0b', width=2.5, dash='dash')
    ))
    
    # All Features curve
    fig_comp.add_trace(go.Scatter(
        x=time_pts, 
        y=[current_temp] + [preds['All_Tuned'][m] for m in [5, 15, 30, 60]], 
        mode='lines+markers', 
        name='All Features (Tuned, v3)', 
        line=dict(color='#10b981', width=2.5, dash='dash')
    ))
    
    fig_comp.add_trace(go.Scatter(x=[plot_history.index.min(), time_pts[-1]], y=[ALARM_LIMIT, ALARM_LIMIT], mode='lines', name='Alarm Limit', line=dict(color='#ef4444', width=2, dash='dot')))
    
    # If possible, get actual future values to compare directly!
    actual_future = []
    actual_times = []
    for m in [5, 15, 30, 60]:
        future_t = current_time + pd.Timedelta(minutes=m)
        if future_t in df_scenario.index:
            actual_future.append(df_scenario.loc[future_t, '03TIC_1023.PV'])
            actual_times.append(future_t)
            
    if len(actual_future) > 0:
        fig_comp.add_trace(go.Scatter(
            x=[current_time] + actual_times, 
            y=[current_temp] + actual_future, 
            mode='lines+markers', 
            name='Actual Future (Realized)', 
            line=dict(color='#3b82f6', width=3)
        ))
        
    fig_comp.update_layout(xaxis_title="Time", yaxis_title="Temperature (°C)", yaxis_range=[15, 25], height=400, template="plotly_dark", margin=dict(l=20, r=20, t=10, b=10))
    st.plotly_chart(fig_comp, use_container_width=True)

    # Real-Time Comparison Table
    st.markdown("### 📊 Horizon-by-Horizon Comparison (Tuned Models)")
    
    comparison_data = []
    for idx, m in enumerate([5, 15, 30, 60]):
        future_t = current_time + pd.Timedelta(minutes=m)
        act_val = df_scenario.loc[future_t, '03TIC_1023.PV'] if future_t in df_scenario.index else np.nan
        
        val_sel = preds['Selected_Tuned'][m]
        val_all = preds['All_Tuned'][m]
        
        err_sel = abs(val_sel - act_val) if not np.isnan(act_val) else np.nan
        err_all = abs(val_all - act_val) if not np.isnan(act_val) else np.nan
        
        status_sel_h = "🔴 ALARM" if val_sel >= ALARM_LIMIT else "🟢 Normal"
        status_all_h = "🔴 ALARM" if val_all >= ALARM_LIMIT else "🟢 Normal"
        status_act_h = "🔴 ALARM" if act_val >= ALARM_LIMIT else "🟢 Normal"
        
        comparison_data.append({
            "Horizon": f"{m} Minutes",
            "Actual Temp (°C)": f"{act_val:.2f}" if not np.isnan(act_val) else "N/A",
            "Selected Features Temp": f"{val_sel:.2f} °C",
            "All Features Temp": f"{val_all:.2f} °C",
            "Selected Error": f"{err_sel:.2f} °C" if not np.isnan(err_sel) else "N/A",
            "All Features Error": f"{err_all:.2f} °C" if not np.isnan(err_all) else "N/A",
            "Winner": "All Features" if err_all < err_sel else ("Selected Features" if err_sel < err_all else "Tie"),
            "Actual Alarm": status_act_h,
            "Selected Alarm": status_sel_h,
            "All Features Alarm": status_all_h
        })
        
    df_comp_table = pd.DataFrame(comparison_data)
    st.table(df_comp_table)

# Rerun Loop
if st.session_state.is_playing:
    sleep_time = max(0.01, 1.0 / speed)
    time.sleep(sleep_time)
    st.session_state.sim_index += 1
    st.rerun()
