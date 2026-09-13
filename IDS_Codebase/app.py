import sys
import os
import time
import json
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Ensure terminal input is disabled to prevent Streamlit from hanging
import hybrid_iot_ids
hybrid_iot_ids.ENABLE_FEEDBACK = False

from hybrid_iot_ids import (
    load_data, DataConfig, ModelConfig, ReplayConfig, ThresholdConfig,
    engineer_features, train_rf_classifier, get_feature_columns,
    normalize_per_source, make_sequences, train_autoencoder,
    compute_reconstruction_error, estimate_threshold, _subset_bundle,
    _split_normal_sequences, _seed_history_buffers, NORMAL_LABEL,
    classify_window, build_sequence_feature_vector
)
from feedback_engine import add_feedback, load_feedback

st.set_page_config(
    page_title="Resilient IoT Intrusion Detection System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling for dark mode glassmorphism
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #1E88E5, #00BCD4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.0rem;
        color: #9E9E9E;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }
    .stAlert {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource(show_spinner="Initializing 3-Tier Hybrid IDS Engine (Loading Models & Data)...")
def initialize_system():
    data_config = DataConfig()
    model_config = ModelConfig()
    replay_config = ReplayConfig()
    threshold_config = ThresholdConfig()

    merged = load_data(data_config)
    engineered = engineer_features(merged, consistency_window=data_config.consistency_window)
    
    hybrid_iot_ids.global_engineered_df = engineered
    train_rf_classifier(engineered, window_size=data_config.window_size)
    
    feature_cols = get_feature_columns()
    normalized, scalers = normalize_per_source(engineered, feature_cols)
    bundle = make_sequences(normalized, window_size=data_config.window_size, feature_cols=feature_cols)

    labeled_bundle = bundle
    normal_mask = labeled_bundle.labels == NORMAL_LABEL
    normal_bundle = _subset_bundle(labeled_bundle, normal_mask)
    train_bundle, val_bundle = _split_normal_sequences(normal_bundle, model_config.validation_fraction)

    model, history = train_autoencoder(train_bundle.X, val_bundle.X, model_config)
    val_errors = compute_reconstruction_error(model, val_bundle.X)
    threshold_main = estimate_threshold(val_errors, sigma=3)

    history_buffers = _seed_history_buffers(train_bundle, replay_config)
    
    source = merged["source"].iloc[0]
    eval_bundle = labeled_bundle
    
    df_grouped = engineered.groupby("timestamp").agg({
        "temperature_c": ["mean", "std", "min", "max"],
        "humidity_percent": ["mean", "std"]
    })
    df_grouped.columns = ["temp_mean", "temp_std", "temp_min", "temp_max", "hum_mean", "hum_std"]
    df_grouped = df_grouped.reset_index()
    
    return {
        "model": model,
        "threshold_main": threshold_main,
        "history_buffers": history_buffers,
        "replay_config": replay_config,
        "threshold_config": threshold_config,
        "engineered_df": engineered,
        "df_grouped": df_grouped,
        "eval_bundle": eval_bundle,
        "source": source,
        "window_size": data_config.window_size
    }

sys_state = initialize_system()

# State Initialization
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "is_playing" not in st.session_state:
    st.session_state.is_playing = False
if "stats" not in st.session_state:
    st.session_state.stats = {
        "total_windows": 0,
        "rule_engine": 0,
        "ensemble": 0,
        "feedback_memory": 0
    }
if "processed_indices" not in st.session_state:
    st.session_state.processed_indices = set()
if "alert_log" not in st.session_state:
    st.session_state.alert_log = []
if "seen_alert_keys" not in st.session_state:
    st.session_state.seen_alert_keys = set()
if "timeline" not in st.session_state:
    st.session_state.timeline = []

eval_metadata = sys_state["eval_bundle"].metadata
max_index = len(eval_metadata) - 1

if st.session_state.current_index > max_index:
    st.session_state.current_index = max_index

# --- HEADER SECTION ---
st.markdown("<div class='main-header'>🏢 Resilient IoT Intrusion Detection System</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>Real-Time Edge Security & Dynamic Anomaly Detection for Smart Buildings</div>", unsafe_allow_html=True)

# Top Stream Control Bar
ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4, ctrl_col5 = st.columns([1, 1, 1, 2, 2])

with ctrl_col1:
    if st.button("▶️ Play" if not st.session_state.is_playing else "⏸️ Pause", use_container_width=True):
        st.session_state.is_playing = not st.session_state.is_playing

with ctrl_col2:
    if st.button("⏭️ Step Next", use_container_width=True):
        st.session_state.current_index = min(max_index, st.session_state.current_index + 1)
        st.rerun()

with ctrl_col3:
    if st.button("🔄 Reset", use_container_width=True):
        st.session_state.current_index = 0
        st.session_state.is_playing = False
        st.rerun()

with ctrl_col4:
    play_speed = st.slider("⚡ Speed (s)", min_value=0.2, max_value=2.0, value=0.5, step=0.1)

with ctrl_col5:
    st.session_state.current_index = st.slider(
        "Window Position",
        min_value=0,
        max_value=max_index,
        value=st.session_state.current_index
    )

# Current Window Data & Inference
idx = st.session_state.current_index
row = eval_metadata.iloc[idx]
source = sys_state["source"]
window_size = sys_state["window_size"]
df_grouped = sys_state["df_grouped"]

unique_times = df_grouped["timestamp"].values
window_times = unique_times[idx : idx + window_size]
window_df = sys_state["engineered_df"][sys_state["engineered_df"]["timestamp"].isin(window_times)].sort_values("timestamp")
window_grouped = df_grouped[df_grouped["timestamp"].isin(window_times)]

sequence = sys_state["eval_bundle"].X[idx]
result = classify_window(
    sequence=sequence,
    model=sys_state["model"],
    threshold=sys_state["threshold_main"],
    history_buffer=list(sys_state["history_buffers"][source]),
    replay_config=sys_state["replay_config"],
    threshold_config=sys_state["threshold_config"],
    timestamp=row["end_timestamp"],
    source=source,
    window_size=window_size
)

# Process Statistics & Alert Log
if idx not in st.session_state.processed_indices:
    st.session_state.processed_indices.add(idx)
    st.session_state.stats["total_windows"] += 1
    src = result.decision_source
    if src == "rule_engine":
        st.session_state.stats["rule_engine"] += 1
    elif src in ["ensemble_gb", "ensemble_rf", "ensemble_voting_consensus"]:
        st.session_state.stats["ensemble"] += 1
    elif src == "feedback_memory":
        st.session_state.stats["feedback_memory"] += 1
        
    st.session_state.timeline.append(result.predicted_label)
    st.session_state.timeline = st.session_state.timeline[-50:]

    if result.predicted_label != "Normal":
        alert_key = f"{row['end_timestamp']}_{result.predicted_label}"
        if alert_key not in st.session_state.seen_alert_keys:
            st.session_state.alert_log.insert(0, {
                "timestamp": str(row["end_timestamp"]),
                "attack": result.predicted_label,
                "confidence": str(result.confidence),
                "source": str(result.decision_source)
            })
            st.session_state.seen_alert_keys.add(alert_key)
            st.session_state.alert_log = st.session_state.alert_log[:50]

# --- METRIC CARDS ---
mcol1, mcol2, mcol3, mcol4, mcol5 = st.columns(5)
status_icon = "🟢" if result.predicted_label == "Normal" else "🚨"
mcol1.metric("Status", f"{status_icon} {result.predicted_label}")
mcol2.metric("Confidence", str(result.confidence))
mcol3.metric("Decision Engine", str(result.decision_source))
mcol4.metric("MSE Error", f"{result.reconstruction_error:.4f}" if result.reconstruction_error else "N/A")
mcol5.metric("Threshold (3-Sigma)", f"{result.threshold:.4f}" if result.threshold else "N/A")

st.divider()

# TABBED INTERFACE
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Live Telemetry & Attack Stream",
    "🧠 3-Tier IDS Engine Diagnostics",
    "🛡️ Network & Snort Rules Inspector",
    "🔄 Human-in-the-Loop Feedback Manager"
])

# ==================== TAB 1 ====================
with tab1:
    col_left, col_right = st.columns([3, 1])

    with col_left:
        st.subheader(f"Sensor Window Analysis ({row['start_timestamp']} ➔ {row['end_timestamp']})")
        all_sensors = sorted(sys_state["engineered_df"]["sensor_id"].unique())
        selected_sensor = st.selectbox("Select Sensor Stream:", all_sensors, index=0)

        sensor_df = sys_state["engineered_df"][
            (sys_state["engineered_df"]["timestamp"].isin(window_times)) &
            (sys_state["engineered_df"]["sensor_id"] == selected_sensor)
        ].sort_values("timestamp")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=sensor_df["timestamp"],
            y=sensor_df["temperature_c"],
            mode="lines+markers",
            name=f"{selected_sensor} Temp (°C)",
            line=dict(color="#1E88E5", width=2.5)
        ))
        fig.add_trace(go.Scatter(
            x=sensor_df["timestamp"],
            y=sensor_df["humidity_percent"],
            mode="lines",
            name=f"{selected_sensor} Humidity (%)",
            line=dict(color="#00ACC1", width=1.5, dash="dot"),
            yaxis="y2"
        ))

        fig.update_layout(
            title=f"Telemetry Stream — {selected_sensor}",
            xaxis=dict(title="Timestamp"),
            yaxis=dict(title="Temperature (°C)", color="#1E88E5"),
            yaxis2=dict(title="Humidity (%)", overlaying="y", side="right", color="#00ACC1"),
            hovermode="x unified",
            margin=dict(l=20, r=20, t=40, b=20),
            template="plotly_dark"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("🚨 Active Alerts")
        if st.session_state.alert_log:
            for alert in st.session_state.alert_log[:6]:
                st.error(f"**{alert['attack']}**\n{alert['timestamp']}\nConf: {alert['confidence']} | {alert['source']}")
        else:
            st.success("No active intrusion alerts.")

# ==================== TAB 2 ====================
with tab2:
    st.subheader("🧠 3-Tier IDS Decision Architecture")
    d1, d2, d3 = st.columns(3)
    
    with d1:
        st.markdown("### Tier 1: LSTM Autoencoder")
        st.info(f"**Unsupervised Anomaly Flagging**\n- MSE Loss: `{result.reconstruction_error:.4f}`\n- Dynamic Threshold: `{result.threshold:.4f}`\n- Anomaly Status: `{'Flagged Anomaly' if result.anomaly_flag else 'Normal'}`")

    with d2:
        st.markdown("### Tier 2: ML Ensembles")
        st.warning(f"**Random Forest + Gradient Boosting**\n- Voting Status: `{result.decision_source}`\n- Classified Output: `{result.predicted_label}`\n- Confidence: `{result.confidence}`")

    with d3:
        st.markdown("### Tier 3: Deterministic Rules")
        st.success(f"**Physical Thermodynamic Boundaries**\n- Replay Detected: `{result.replay_flag}`\n- Replay Similarity: `{result.replay_similarity or 0.0:.2%}`\n- Reason: `{result.replay_reason or 'N/A'}`")

    st.divider()
    st.subheader("📊 Decision Source Distribution")
    if st.session_state.stats["total_windows"] > 0:
        df_stats = pd.DataFrame({
            "Source": ["Rule Engine", "ML Ensemble", "Feedback Memory"],
            "Count": [
                st.session_state.stats["rule_engine"], 
                st.session_state.stats["ensemble"], 
                st.session_state.stats["feedback_memory"]
            ]
        })
        fig_pie = go.Figure(data=[go.Pie(labels=df_stats["Source"], values=df_stats["Count"], hole=.4)])
        fig_pie.update_layout(margin=dict(t=20, b=20, l=20, r=20), template="plotly_dark")
        st.plotly_chart(fig_pie, use_container_width=True)

# ==================== TAB 3 ====================
with tab3:
    st.subheader("🛡️ Snort 3 Network Security Monitor")
    st.markdown("Network level passive monitoring on gateway interface (`eth0`, MQTT Port 1883).")
    
    snort_rules = [
        {"SID": 2000001, "Rule": "MQTT Connection Attempt", "Protocol": "TCP", "Target Port": 1883, "Action": "ALERT"},
        {"SID": 2000002, "Rule": "SYN Packet Scan Detection", "Protocol": "TCP", "Target Port": 1883, "Action": "ALERT & LOG"},
        {"SID": 2000003, "Rule": "High MQTT Traffic (DoS Flood)", "Protocol": "TCP", "Target Port": 1883, "Action": "DROP"},
        {"SID": 2000004, "Rule": "Reconnaissance Ping Detection", "Protocol": "ICMP", "Target Port": "ANY", "Action": "ALERT"},
    ]
    st.table(pd.DataFrame(snort_rules))

# ==================== TAB 4 ====================
with tab4:
    st.subheader("🔄 Human-in-the-Loop Feedback Manager")
    st.write("Correct model misclassifications in real-time. Overrides are saved atomically to `feedbackmemory.json`.")

    feature_dict = build_sequence_feature_vector(window_df.tail(window_size))
    current_features = np.array(list(feature_dict.values()), dtype=np.float32)

    fb_labels = ["Replay Attack", "Injection Attack", "Drop Attack", "Drift Attack", "Noise Attack", "Normal"]
    fb_cols = st.columns(len(fb_labels))
    for i, label in enumerate(fb_labels):
        if fb_cols[i].button(f"Set: {label}", key=f"tab4_btn_{label}", use_container_width=True):
            add_feedback(current_features.tolist(), label)
            st.toast(f"Stored feedback: {label}", icon="✅")
            st.success(f"Overrode prediction to **{label}**.")

    st.markdown("### 💾 Stored Feedback Memory")
    stored_mem = load_feedback()
    if stored_mem:
        st.json(stored_mem[-5:])
    else:
        st.info("Feedback memory is currently empty.")

# Auto-play loop logic
if st.session_state.is_playing:
    if st.session_state.current_index < max_index:
        time.sleep(play_speed)
        st.session_state.current_index += 1
        st.rerun()
    else:
        st.session_state.is_playing = False
