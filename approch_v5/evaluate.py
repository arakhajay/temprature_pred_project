"""
Approach v5 - Model Evaluation Module
Computes regression and classification metrics on out-of-sample datasets,
and generates overlay visualizations comparing predictions to actual values during alarm episodes.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error

def calculate_alert_metrics(actual_vals, predicted_vals, threshold=21.0):
    """
    Computes both continuous regression metrics and binary classification alarm metrics.
    
    Metrics:
    - MAE, RMSE (continuous temperature errors)
    - F1-Score, Precision, Recall, False Alarm Rate (FAR) (alarm state classification)
    
    Args:
        actual_vals (np.array): Ground truth temperatures.
        predicted_vals (np.array): Model predicted temperatures.
        threshold (float): Active alarm threshold temperature (e.g. 21.0 degC).
        
    Returns:
        dict: Performance summary dictionary.
    """
    # 1. Continuous metrics
    mae = mean_absolute_error(actual_vals, predicted_vals)
    rmse = np.sqrt(mean_squared_error(actual_vals, predicted_vals))
    
    # 2. Binary classifications
    actual_alarm = actual_vals >= threshold
    predicted_alarm = predicted_vals >= threshold
    
    tp = np.sum(actual_alarm & predicted_alarm)
    fp = np.sum((~actual_alarm) & predicted_alarm)
    fn = np.sum(actual_alarm & (~predicted_alarm))
    tn = np.sum((~actual_alarm) & (~predicted_alarm))
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    # FAR: False alarms / Total actual negatives (how often we call false alerts out of all non-alarms)
    far = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    
    metrics = {
        "mae": mae,
        "rmse": rmse,
        "f1": f1,
        "precision": precision,
        "recall": recall,
        "far": far,
        "confusion_matrix": {"tp": int(tp), "fp": int(fp), "fn": int(fn), "tn": int(tn)}
    }
    return metrics


def plot_actual_vs_predicted_scenarios(timestamps, actual_vals, predicted_vals, threshold=21.0, title="Alarm Scenario Forecast", output_path="outputs/v5/alarm_scenario.png"):
    """
    Critical Visualization: Overlays actual and predicted temperatures during a specific
    alarm episode. Draws a horizontal threshold line to show where alarms are triggered.
    
    Args:
        timestamps (pd.Series or np.array): Chronological index.
        actual_vals (np.array): Ground truth temperatures.
        predicted_vals (np.array): Predicted temperatures.
        threshold (float): The threshold dividing normal and alert states.
        title (str): Plot title.
        output_path (str): Filepath to save generated visualization.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    plt.figure(figsize=(10, 5))
    plt.plot(timestamps, actual_vals, label="Actual Temperature", color="#0A1931", linewidth=1.5)
    plt.plot(timestamps, predicted_vals, label="Predicted Temperature", color="#0D9488", linestyle="--", linewidth=1.5)
    
    # Horizontal alarm threshold line
    plt.axhline(y=threshold, color="#F96167", linestyle=":", label=f"Alarm Limit ({threshold} °C)", linewidth=1.2)
    
    # Highlight threshold crossings
    plt.fill_between(timestamps, actual_vals, threshold, where=(actual_vals >= threshold), color="#F96167", alpha=0.15, label="Actual Alarm Event")
    
    plt.title(title, fontsize=12, fontweight='bold', color="#0A1931")
    plt.xlabel("Timeline", fontsize=10)
    plt.ylabel("Temperature (°C)", fontsize=10)
    plt.legend(loc="upper left")
    plt.grid(True, linestyle=":", alpha=0.6)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Saved alert scenario plot to {output_path}")
